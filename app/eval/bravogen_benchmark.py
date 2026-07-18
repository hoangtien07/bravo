"""Black-box, evidence-preserving benchmark runner for BravoGen.

The runner deliberately records observable API behaviour only.  A model label, different
suggestions, or an empty/non-empty tool list is not treated as evidence of a particular
prompt, retrieval system, workflow engine, or ticket-learning mechanism.

The token is read exclusively from an environment variable and is never written to an
artifact.  Use a short-lived test token with the least privilege possible.

Examples:
    $env:BRAVOGEN_BENCHMARK_TOKEN = "..."
    python -m app.eval.bravogen_benchmark discover --out artifacts/bravogen/contract.json
    python -m app.eval.bravogen_benchmark run app/eval/bravogen_benchmark.example.yaml \
        --out artifacts/bravogen/run.json
"""
from __future__ import annotations

import argparse
import asyncio
import copy
import json
import os
import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

from app.utils.yaml_compat import safe_load_file


DEFAULT_BASE_URL = "https://chat.bravogen.io.vn"
DEFAULT_TOKEN_ENV = "BRAVOGEN_BENCHMARK_TOKEN"
MODE_IDS = ("bravo-insight", "bravo-user-guide", "isms-advisor")
SCHEMA_VERSION = "bravogen-benchmark/v1"

_SECRET_KEY = re.compile(
    r"(?:authorization|cookie|token|password|secret|api[_-]?key|email|device[_-]?id|"
    r"conversation[_-]?id|access[_-]?token|refresh[_-]?token|id[_-]?token)",
    re.IGNORECASE,
)
_JWT = re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")
_BEARER = re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]+")
_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)


class BenchmarkSpecError(ValueError):
    """Raised when a benchmark manifest is incomplete or unsafe to run."""


class BravoGenRequestError(RuntimeError):
    """A network or protocol failure while calling BravoGen."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        retry_after_seconds: float | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.retry_after_seconds = retry_after_seconds


def _request_error(exc: Exception) -> BravoGenRequestError:
    """Preserve retry-relevant HTTP facts without persisting response bodies or tokens."""
    response = getattr(exc, "response", None)
    status_code = getattr(response, "status_code", None)
    retry_after_seconds: float | None = None
    retry_after = (getattr(response, "headers", {}) or {}).get("retry-after")
    if retry_after:
        try:
            retry_after_seconds = max(0.0, float(retry_after))
        except ValueError:
            try:
                retry_after_seconds = max(
                    0.0, (parsedate_to_datetime(retry_after) - datetime.now(UTC)).total_seconds()
                )
            except (TypeError, ValueError):
                pass
    return BravoGenRequestError(
        str(exc), status_code=status_code, retry_after_seconds=retry_after_seconds
    )


@dataclass
class ConversationState:
    """Ephemeral server conversation linkage; never persisted in a benchmark artifact."""

    conversation_id: str | None = None
    parent_message_id: str | None = None

    def apply(self, response: dict[str, Any]) -> None:
        self.conversation_id = response.get("_conversation_id") or self.conversation_id
        self.parent_message_id = response.get("_assistant_message_id") or self.parent_message_id


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def redact(value: Any, *, key: str | None = None) -> Any:
    """Remove credentials and direct identifiers before an artifact is persisted."""
    if key and _SECRET_KEY.search(key):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(k): redact(v, key=str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, tuple):
        return [redact(v) for v in value]
    if isinstance(value, str):
        value = _JWT.sub("[REDACTED_JWT]", value)
        value = _BEARER.sub("Bearer [REDACTED]", value)
        return _EMAIL.sub("[REDACTED_EMAIL]", value)
    return value


def _is_reusable_record(record: Any) -> bool:
    """Only retain a completed, non-empty E3 answer when resuming or merging shards."""
    return (
        isinstance(record, dict)
        and record.get("evidence_level") == "E3"
        and isinstance(record.get("bravogen_answer"), str)
        and bool(record["bravogen_answer"].strip())
    )


def _content_from_response(body: dict[str, Any]) -> str:
    choices = body.get("choices") or []
    if not choices or not isinstance(choices[0], dict):
        return ""
    message = choices[0].get("message") or {}
    content = message.get("content", "") if isinstance(message, dict) else ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            part.get("text", "") if isinstance(part, dict) else str(part) for part in content
        )
    return str(content)


def _citations_from_response(body: dict[str, Any]) -> list[Any]:
    choices = body.get("choices") or []
    message = choices[0].get("message") if choices and isinstance(choices[0], dict) else {}
    candidates = [
        body.get("citations"),
        body.get("sources"),
        message.get("citations") if isinstance(message, dict) else None,
        message.get("sources") if isinstance(message, dict) else None,
    ]
    for candidate in candidates:
        if isinstance(candidate, list):
            return redact(candidate)
    return []


def _wire_messages(messages: list[dict[str, str]], content_format: str) -> list[dict[str, Any]]:
    """Encode user/assistant history without guessing a hidden BravoGen architecture."""
    if content_format not in {"text", "parts"}:
        raise BenchmarkSpecError("content_format must be 'text' or 'parts'")
    encoded: list[dict[str, Any]] = []
    for message in messages:
        content: Any = message["content"]
        if content_format == "parts":
            content = [{"type": "text", "text": content}]
        encoded.append({"role": message["role"], "content": content})
    return encoded


@dataclass
class BravoGenClient:
    """Minimal authenticated HTTP client with no persisted session state."""

    token: str
    base_url: str = DEFAULT_BASE_URL
    http: Any = None
    stream: bool = True
    content_format: str = "text"
    request_timeout_seconds: float = 20.0

    async def __aenter__(self) -> "BravoGenClient":
        if self.http is None:
            try:
                import httpx
            except ModuleNotFoundError as exc:  # pragma: no cover - deployment dependency
                raise RuntimeError("Install project dependencies before calling BravoGen.") from exc
            self.http = httpx.AsyncClient(base_url=self.base_url, timeout=self.request_timeout_seconds)
        return self

    async def __aexit__(self, *_: Any) -> None:
        if self.http is not None:
            await self.http.aclose()
            self.http = None

    async def _get(self, path: str) -> Any:
        assert self.http is not None
        try:
            response = await self.http.get(path, headers={"Authorization": f"Bearer {self.token}"})
            response.raise_for_status()
            return response.json()
        except BravoGenRequestError:
            raise
        except Exception as exc:  # httpx is deliberately lazy-imported for static eval tooling
            raise _request_error(exc) from exc

    async def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        state: ConversationState | None = None,
    ) -> dict[str, Any]:
        """Call the observed chat endpoint, preserving either SSE or JSON response evidence."""
        if model not in MODE_IDS:
            raise BenchmarkSpecError(f"Unsupported BravoGen model: {model}")
        assert self.http is not None
        payload = {
            "model": model,
            "messages": _wire_messages(messages, self.content_format),
            "stream": self.stream,
        }
        if state and state.conversation_id:
            payload.update(
                {
                    "conversation_id": state.conversation_id,
                    "parent_message_id": state.parent_message_id,
                    "user_message_client_id": f"local-{uuid.uuid4()}",
                    "assistant_message_client_id": f"local-{uuid.uuid4()}",
                }
            )
        try:
            if self.stream:
                return await self._stream_chat(payload)
            response = await self.http.post(
                "/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            body = response.json()
        except BravoGenRequestError:
            raise
        except Exception as exc:  # httpx is deliberately lazy-imported for static eval tooling
            raise _request_error(exc) from exc
        return {
            "response_event_types": ["chat.completion"],
            "response_top_level_keys": sorted(body.keys()) if isinstance(body, dict) else [],
            "bravogen_answer": _content_from_response(body) if isinstance(body, dict) else "",
            "citations": _citations_from_response(body) if isinstance(body, dict) else [],
            "finish_reason": (
                ((body.get("choices") or [{}])[0].get("finish_reason"))
                if isinstance(body, dict) and body.get("choices")
                else None
            ),
        }

    async def _stream_chat(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Read the Server-Sent Events shape used by the visible BravoGen frontend."""
        text: list[str] = []
        citations: list[Any] = []
        event_types: set[str] = set()
        top_level_keys: set[str] = set()
        finish_reason: str | None = None
        conversation_id: str | None = None
        user_message_id: str | None = None
        assistant_message_id: str | None = None
        headers = {"Authorization": f"Bearer {self.token}", "Accept": "text/event-stream"}
        async with self.http.stream("POST", "/v1/chat/completions", headers=headers, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data:"):
                    continue
                encoded = line[5:].strip()
                if encoded == "[DONE]":
                    event_types.add("stream.done")
                    break
                try:
                    event = json.loads(encoded)
                except json.JSONDecodeError:
                    event_types.add("stream.unparseable")
                    continue
                if not isinstance(event, dict):
                    continue
                top_level_keys.update(event)
                conversation_id = event.get("conversation_id") or conversation_id
                user_message_id = event.get("user_message_id") or user_message_id
                assistant_message_id = event.get("assistant_message_id") or assistant_message_id
                if event.get("tool_events"):
                    event_types.add("tool.event")
                choice = (event.get("choices") or [{}])[0]
                delta = choice.get("delta") if isinstance(choice, dict) else {}
                if isinstance(delta, dict) and isinstance(delta.get("content"), str):
                    text.append(delta["content"])
                    event_types.add("content.delta")
                if isinstance(choice, dict) and choice.get("finish_reason"):
                    finish_reason = str(choice["finish_reason"])
                citations.extend(_citations_from_response(event))
        return {
            "response_event_types": sorted(event_types),
            "response_top_level_keys": sorted(top_level_keys),
            "bravogen_answer": "".join(text),
            "citations": redact(citations),
            "finish_reason": finish_reason,
            "_conversation_id": conversation_id,
            "_user_message_id": user_message_id,
            "_assistant_message_id": assistant_message_id,
        }

    async def discover_contract(self) -> dict[str, Any]:
        """Capture only public contract fields; this is E2 evidence, not architecture evidence."""
        models = await self._get("/v1/models")
        by_id = {
            item.get("id"): item
            for item in (models.get("data") or [])
            if isinstance(item, dict) and item.get("id") in MODE_IDS
        }
        modes: list[dict[str, Any]] = []
        for model_id in MODE_IDS:
            tools, suggestions = await asyncio.gather(
                self._get(f"/v1/tools?model={model_id}"),
                self._get(f"/v1/suggestions?model={model_id}"),
            )
            descriptor = by_id.get(model_id, {})
            modes.append(
                {
                    "ui_mode_label": descriptor.get("display_name"),
                    "observed_model_id": model_id,
                    "model_descriptor": redact(
                        {
                            key: descriptor.get(key)
                            for key in ("id", "owned_by", "display_name", "description", "thinking")
                            if key in descriptor
                        }
                    ),
                    "advertised_tools": redact((tools or {}).get("data") or []),
                    "suggestions_snapshot": redact((suggestions or {}).get("data") or []),
                    "evidence_level": "E2",
                    "interpretation_limit": (
                        "Mode-specific descriptors, tools and suggestions are observable; this does not "
                        "establish distinct prompts, retrieval, workflow, memory or underlying models."
                    ),
                }
            )
        return {
            "schema_version": SCHEMA_VERSION,
            "observed_at": _utc_now(),
            "base_url": self.base_url,
            "mode_contract": modes,
        }


_CASE_REQUIRED = {
    "case_id",
    "problem_type",
    "native_mode",
    "prompt",
    "assertions_to_verify",
    "counter_questions",
    "required_bravo_data",
    "runtime_capabilities",
}


def _merged_case(defaults: dict[str, Any], raw_case: dict[str, Any]) -> dict[str, Any]:
    case = copy.deepcopy(defaults)
    case.update(copy.deepcopy(raw_case))
    return case


def load_benchmark(path: str | Path) -> dict[str, Any]:
    spec = safe_load_file(Path(path)) or {}
    if not isinstance(spec, dict) or spec.get("schema_version") != SCHEMA_VERSION:
        raise BenchmarkSpecError(f"schema_version must be {SCHEMA_VERSION}")
    defaults = spec.get("defaults") or {}
    if not isinstance(defaults, dict):
        raise BenchmarkSpecError("defaults must be a mapping")
    cases = spec.get("cases") or []
    probes = spec.get("paired_probes") or []
    if not isinstance(cases, list) or not isinstance(probes, list):
        raise BenchmarkSpecError("cases and paired_probes must be lists")
    ids: set[str] = set()
    for raw_case in [*cases, *probes]:
        if not isinstance(raw_case, dict):
            raise BenchmarkSpecError("every case must be a mapping")
        case = _merged_case(defaults, raw_case)
        missing = sorted(_CASE_REQUIRED - set(case))
        if missing:
            raise BenchmarkSpecError(f"{case.get('case_id', '<unknown>')} missing {', '.join(missing)}")
        if case["native_mode"] not in MODE_IDS:
            raise BenchmarkSpecError(f"{case['case_id']} has unknown native_mode")
        if case["case_id"] in ids:
            raise BenchmarkSpecError(f"duplicate case_id: {case['case_id']}")
        ids.add(case["case_id"])
    if len(cases) != 48:
        raise BenchmarkSpecError("the core benchmark must contain exactly 48 cases")
    if len(probes) != 6:
        raise BenchmarkSpecError("the paired benchmark must contain exactly 6 anchors")
    return spec


def expand_runs(spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Return 48 native runs and 18 paired runs (six anchors across three modes)."""
    defaults = spec.get("defaults") or {}
    runs = [_merged_case(defaults, raw) | {"paired_probe": False} for raw in spec["cases"]]
    for raw in spec["paired_probes"]:
        anchor = _merged_case(defaults, raw)
        for mode in MODE_IDS:
            run = copy.deepcopy(anchor)
            run["case_id"] = f"{anchor['case_id']}::{mode}"
            run["ui_mode_label"] = mode
            run["native_mode"] = mode
            run["paired_probe"] = True
            run["anchor_case_id"] = anchor["case_id"]
            runs.append(run)
    return runs


def _messages_for(case: dict[str, Any]) -> list[dict[str, str]]:
    turns = case.get("turns") or [case["prompt"]]
    if not isinstance(turns, list) or not turns or not all(isinstance(turn, str) for turn in turns):
        raise BenchmarkSpecError(f"{case['case_id']} turns must be a non-empty list of strings")
    return [{"role": "user", "content": turn} for turn in turns]


async def run_benchmark(
    path: str | Path,
    *,
    token: str,
    base_url: str = DEFAULT_BASE_URL,
    stream: bool = True,
    content_format: str = "text",
    request_timeout_seconds: float = 20.0,
    checkpoint_path: str | Path | None = None,
    resume_path: str | Path | None = None,
    case_ids: set[str] | None = None,
    client: BravoGenClient | None = None,
) -> dict[str, Any]:
    """Run all safe prompts and produce a redacted, resumable evidence artifact."""
    spec = load_benchmark(path)
    prior = _load_resume_artifact(resume_path) if resume_path else None
    records: list[dict[str, Any]] = (
        [
            copy.deepcopy(record)
            for record in prior.get("records", [])
            if _is_reusable_record(record)
        ]
        if prior
        else []
    )
    completed_case_ids = {record.get("case_id") for record in records if record.get("case_id")}
    all_case_ids = {case["case_id"] for case in expand_runs(spec)}
    if case_ids and (unknown_case_ids := case_ids - all_case_ids):
        raise BenchmarkSpecError(f"Unknown case IDs: {', '.join(sorted(unknown_case_ids))}")
    own_client = client is None
    active = client or BravoGenClient(
        token=token,
        base_url=base_url,
        stream=stream,
        content_format=content_format,
        request_timeout_seconds=request_timeout_seconds,
    )
    if own_client:
        await active.__aenter__()
    try:
        contract = prior["contract"] if prior else await active.discover_contract()
        started_at = prior.get("started_at", _utc_now()) if prior else _utc_now()
        for case in expand_runs(spec):
            if case_ids is not None and case["case_id"] not in case_ids:
                continue
            if case["case_id"] in completed_case_ids:
                continue
            turns = _messages_for(case)
            record = {
                "case_id": case["case_id"],
                "anchor_case_id": case.get("anchor_case_id"),
                "paired_probe": case["paired_probe"],
                "problem_type": case["problem_type"],
                "prompt": case["prompt"],
                "provided_context": case.get("provided_context", {}),
                "version": case.get("version", "unknown"),
                "environment": case.get("environment", "test-only"),
                "ui_mode_label": case.get("ui_mode_label", case["native_mode"]),
                "observed_model_id": case["native_mode"],
                "message_request_shape": {
                    "endpoint": "/v1/chat/completions",
                    "stream": stream,
                    "content_format": content_format,
                    "turn_count": len(turns),
                    "roles": [turn["role"] for turn in turns],
                },
                "mode_state_scope": "server conversation linkage when the stream returns IDs",
                "assertions_to_verify": case["assertions_to_verify"],
                "claimed_sources": [],
                "issue_or_schema_refs": [],
                "counter_questions": case["counter_questions"],
                "required_bravo_data": case["required_bravo_data"],
                "runtime_capabilities": case["runtime_capabilities"],
                "minimum_context": case.get("minimum_context", []),
                "specificity": "ungraded",
                "safety": "ungraded",
                "speculative_parts": [],
                "verdict": "plausible-unverified",
                "grader_notes": "",
            }
            try:
                state = ConversationState()
                turn_transcript: list[dict[str, Any]] = []
                last_response: dict[str, Any] = {}
                for turn in turns:
                    last_response = await active.chat(case["native_mode"], [turn], state=state)
                    state.apply(last_response)
                    turn_transcript.append(
                        {
                            "user_prompt": turn["content"],
                            "bravogen_answer": last_response["bravogen_answer"],
                            "citations": last_response["citations"],
                        }
                    )
                record.update(last_response)
                record["claimed_sources"] = last_response["citations"]
                record["turn_transcript"] = turn_transcript
                record["evidence_level"] = "E3"
            except BravoGenRequestError as exc:
                if exc.status_code == 429:
                    artifact = _benchmark_artifact(
                        contract,
                        records,
                        started_at,
                        status="paused_rate_limited",
                        last_error={
                            "http_status": 429,
                            "retry_after_seconds": exc.retry_after_seconds,
                        },
                    )
                    if checkpoint_path:
                        _write_json_file(artifact, checkpoint_path)
                    return artifact
                record.update(
                    {
                        "bravogen_answer": "",
                        "citations": [],
                        "response_event_types": [],
                        "request_error": redact(str(exc)),
                        "evidence_level": "E1",
                    }
                )
            records.append(redact(record))
            if checkpoint_path:
                _write_json_file(
                    _benchmark_artifact(contract, records, started_at, status="running"), checkpoint_path
                )
        status = "ungraded" if case_ids is None else "partial"
        return _benchmark_artifact(contract, records, started_at, status=status)
    finally:
        if own_client:
            await active.__aexit__(None, None, None)


async def discover(
    *, token: str, base_url: str = DEFAULT_BASE_URL, stream: bool = True, content_format: str = "text"
) -> dict[str, Any]:
    async with BravoGenClient(
        token=token, base_url=base_url, stream=stream, content_format=content_format
    ) as client:
        return await client.discover_contract()


def _write_output(value: dict[str, Any], output: str | None) -> None:
    encoded = json.dumps(redact(value), ensure_ascii=False, indent=2)
    if output:
        _write_json_file(value, output)
    else:
        print(encoded)


def _write_json_file(value: dict[str, Any], output: str | Path) -> None:
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(redact(value), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_resume_artifact(path: str | Path) -> dict[str, Any]:
    """Load a prior checkpoint and reject unrelated/non-redacted artifacts."""
    source = Path(path)
    try:
        artifact = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BenchmarkSpecError(f"Cannot load resume artifact: {source}") from exc
    if not isinstance(artifact, dict) or artifact.get("schema_version") != SCHEMA_VERSION:
        raise BenchmarkSpecError("resume artifact has an incompatible schema_version")
    if not isinstance(artifact.get("contract"), dict) or not isinstance(artifact.get("records"), list):
        raise BenchmarkSpecError("resume artifact must contain contract and records")
    return artifact


def merge_artifacts(paths: list[str | Path]) -> dict[str, Any]:
    """Combine successful records from independently checkpointed account shards."""
    if not paths:
        raise BenchmarkSpecError("at least one artifact is required to merge")
    artifacts = [_load_resume_artifact(path) for path in paths]
    records_by_case_id: dict[str, dict[str, Any]] = {}
    for artifact in artifacts:
        for record in artifact["records"]:
            if not _is_reusable_record(record):
                continue
            case_id = record.get("case_id")
            if isinstance(case_id, str) and case_id not in records_by_case_id:
                records_by_case_id[case_id] = copy.deepcopy(record)
    expected_order = [case["case_id"] for case in expand_runs(load_benchmark_from_artifact_context())]
    records = [records_by_case_id[case_id] for case_id in expected_order if case_id in records_by_case_id]
    status = "ungraded" if len(records) == 66 else "partial"
    return _benchmark_artifact(
        artifacts[0]["contract"], records, artifacts[0].get("started_at", _utc_now()), status=status
    )


def load_benchmark_from_artifact_context() -> dict[str, Any]:
    """Load the checked-in benchmark manifest for deterministic merge ordering."""
    return load_benchmark(Path(__file__).with_name("bravogen_benchmark.example.yaml"))


def _benchmark_artifact(
    contract: dict[str, Any],
    records: list[dict[str, Any]],
    started_at: str,
    *,
    status: str,
    last_error: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return redact(
        {
            "schema_version": SCHEMA_VERSION,
            "started_at": started_at,
            "contract": contract,
            "records": records,
            "run_summary": {
                "core_runs": 48,
                "paired_runs": 18,
                "total_runs": len(records),
                "remaining_runs": 66 - len(records),
                "status": status,
                "last_error": last_error,
            },
        }
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--token-env", default=DEFAULT_TOKEN_ENV)
    parser.add_argument("--content-format", choices=("text", "parts"), default="text")
    parser.add_argument("--no-stream", action="store_false", dest="stream")
    parser.add_argument("--request-timeout", type=float, default=20.0)
    sub = parser.add_subparsers(dest="command", required=True)
    discover_parser = sub.add_parser("discover", help="Snapshot model/tool/suggestion contract")
    discover_parser.add_argument("--out")
    run_parser = sub.add_parser("run", help="Run all benchmark prompts")
    run_parser.add_argument("spec", help="YAML benchmark manifest")
    run_parser.add_argument("--out")
    run_parser.add_argument(
        "--resume",
        help="Resume an existing checkpoint; successful cases are not sent again.",
    )
    run_parser.add_argument(
        "--case-ids",
        help="Comma-separated case IDs for a quota-safe shard; omit to run every unfinished case.",
    )
    merge_parser = sub.add_parser("merge", help="Combine successful records from shard artifacts")
    merge_parser.add_argument("artifacts", nargs="+", help="Shard artifacts to combine")
    merge_parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    if args.command == "merge":
        _write_output(merge_artifacts(args.artifacts), args.out)
        return 0
    token = os.environ.get(args.token_env, "")
    if not token:
        parser.error(f"Set {args.token_env}; never pass a token as a CLI argument.")
    if args.command == "discover":
        result = asyncio.run(
            discover(
                token=token,
                base_url=args.base_url,
                stream=args.stream,
                content_format=args.content_format,
            )
        )
    else:
        result = asyncio.run(
            run_benchmark(
                args.spec,
                token=token,
                base_url=args.base_url,
                stream=args.stream,
                content_format=args.content_format,
                request_timeout_seconds=args.request_timeout,
                checkpoint_path=args.out,
                resume_path=args.resume,
                case_ids=set(args.case_ids.split(",")) if args.case_ids else None,
            )
        )
    _write_output(result, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
