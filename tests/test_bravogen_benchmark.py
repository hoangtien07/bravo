from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path

from app.eval.bravogen_benchmark import (
    BravoGenClient,
    BravoGenRequestError,
    MODE_IDS,
    SCHEMA_VERSION,
    _wire_messages,
    expand_runs,
    load_benchmark,
    merge_artifacts,
    redact,
    run_benchmark,
)


class _DiscoveryClient(BravoGenClient):
    async def _get(self, path: str):
        if path == "/v1/models":
            return {"data": [{"id": model_id, "display_name": model_id} for model_id in MODE_IDS]}
        if path.startswith("/v1/tools"):
            return {"data": []}
        if path.startswith("/v1/suggestions"):
            return {"data": [{"title": path.rsplit("=", 1)[-1]}]}
        raise AssertionError(path)


class _RunClient:
    async def discover_contract(self):
        return {"schema_version": SCHEMA_VERSION, "mode_contract": []}

    async def chat(self, model: str, messages: list[dict[str, str]], **_kwargs):
        assert model in MODE_IDS
        assert messages[-1]["role"] == "user"
        return {
            "response_event_types": ["chat.completion"],
            "response_top_level_keys": ["choices"],
            "bravogen_answer": "OK",
            "citations": [],
            "finish_reason": "stop",
        }


class _RateLimitedClient(_RunClient):
    async def chat(self, *_args, **_kwargs):
        raise BravoGenRequestError("rate limited", status_code=429, retry_after_seconds=30)


def test_redact_removes_tokens_and_identifiers():
    value = redact(
        {"authorization": "Bearer abc", "email": "a@b.test", "note": "eyJx.abc.def a@b.test"}
    )
    assert value["authorization"] == "[REDACTED]"
    assert value["email"] == "[REDACTED]"
    assert value["note"] == "[REDACTED_JWT] [REDACTED_EMAIL]"


def test_wire_messages_supports_observed_text_and_explicit_parts_formats():
    messages = [{"role": "user", "content": "OK"}]
    assert _wire_messages(messages, "text") == messages
    assert _wire_messages(messages, "parts") == [
        {"role": "user", "content": [{"type": "text", "text": "OK"}]}
    ]


def test_manifest_has_48_cases_and_18_expanded_paired_runs():
    spec = load_benchmark("app/eval/bravogen_benchmark.example.yaml")
    runs = expand_runs(spec)
    assert spec["schema_version"] == SCHEMA_VERSION
    assert len(spec["cases"]) == 48
    assert len(spec["paired_probes"]) == 6
    assert len(runs) == 66
    assert {run["native_mode"] for run in runs} == set(MODE_IDS)
    categories = [case["problem_type"] for case in spec["cases"]]
    assert all(categories.count(category) == 6 for category in set(categories))


def test_discover_contract_is_observational_only():
    client = _DiscoveryClient(token="test-token")
    observed = asyncio.run(client.discover_contract())
    assert observed["schema_version"] == SCHEMA_VERSION
    assert [item["observed_model_id"] for item in observed["mode_contract"]] == list(MODE_IDS)
    assert all(item["evidence_level"] == "E2" for item in observed["mode_contract"])
    assert all("does not establish" in item["interpretation_limit"] for item in observed["mode_contract"])


def test_run_records_a_safe_openai_compatible_chat_response():
    result = asyncio.run(
        run_benchmark(
            "app/eval/bravogen_benchmark.example.yaml", token="ignored", client=_RunClient()
        )
    )
    assert result["run_summary"]["total_runs"] == 66
    assert all(record["bravogen_answer"] == "OK" for record in result["records"])
    assert any(len(record["turn_transcript"]) == 3 for record in result["records"])
    assert all(record["message_request_shape"]["stream"] for record in result["records"])
    assert result["run_summary"]["status"] == "ungraded"


def test_rate_limit_pauses_before_sending_remaining_prompts_and_writes_checkpoint():
    with tempfile.TemporaryDirectory() as directory:
        checkpoint = Path(directory) / "checkpoint.json"
        result = asyncio.run(
            run_benchmark(
                "app/eval/bravogen_benchmark.example.yaml",
                token="ignored",
                client=_RateLimitedClient(),
                checkpoint_path=checkpoint,
            )
        )
        saved = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert result["run_summary"]["status"] == "paused_rate_limited"
    assert result["run_summary"]["total_runs"] == 0
    assert result["run_summary"]["last_error"] == {
        "http_status": 429,
        "retry_after_seconds": 30,
    }
    assert saved["run_summary"]["status"] == "paused_rate_limited"


def test_resume_skips_successful_case_ids_without_resending_them():
    prior = {
        "schema_version": SCHEMA_VERSION,
        "started_at": "2026-07-14T00:00:00Z",
        "contract": {"schema_version": SCHEMA_VERSION, "mode_contract": []},
        "records": [{"case_id": "ug-01", "bravogen_answer": "already captured", "evidence_level": "E3"}],
    }
    with tempfile.TemporaryDirectory() as directory:
        checkpoint = Path(directory) / "checkpoint.json"
        checkpoint.write_text(json.dumps(prior), encoding="utf-8")
        result = asyncio.run(
            run_benchmark(
                "app/eval/bravogen_benchmark.example.yaml",
                token="ignored",
                client=_RunClient(),
                resume_path=checkpoint,
            )
        )
    assert result["run_summary"]["total_runs"] == 66
    assert result["records"][0]["bravogen_answer"] == "already captured"


def test_resume_retries_prior_request_errors_and_honours_a_case_shard():
    prior = {
        "schema_version": SCHEMA_VERSION,
        "started_at": "2026-07-14T00:00:00Z",
        "contract": {"schema_version": SCHEMA_VERSION, "mode_contract": []},
        "records": [
            {"case_id": "ug-01", "bravogen_answer": "already captured", "evidence_level": "E3"},
            {"case_id": "ug-02", "request_error": "429"},
        ],
    }
    with tempfile.TemporaryDirectory() as directory:
        checkpoint = Path(directory) / "checkpoint.json"
        checkpoint.write_text(json.dumps(prior), encoding="utf-8")
        result = asyncio.run(
            run_benchmark(
                "app/eval/bravogen_benchmark.example.yaml",
                token="ignored",
                client=_RunClient(),
                resume_path=checkpoint,
                case_ids={"ug-01", "ug-02"},
            )
        )
    assert result["run_summary"]["status"] == "partial"
    assert [record["case_id"] for record in result["records"]] == ["ug-01", "ug-02"]
    assert result["records"][1]["bravogen_answer"] == "OK"


def test_merge_keeps_successful_shard_records_and_discards_request_errors():
    base = {
        "schema_version": SCHEMA_VERSION,
        "started_at": "2026-07-14T00:00:00Z",
        "contract": {"schema_version": SCHEMA_VERSION, "mode_contract": []},
        "records": [{"case_id": "ug-01", "bravogen_answer": "A", "evidence_level": "E3"}],
    }
    shard = {
        **base,
        "records": [
            {"case_id": "ug-01", "bravogen_answer": "duplicate", "evidence_level": "E3"},
            {"case_id": "ug-02", "bravogen_answer": "B", "evidence_level": "E3"},
            {"case_id": "ug-03", "request_error": "401"},
        ],
    }
    with tempfile.TemporaryDirectory() as directory:
        first = Path(directory) / "first.json"
        second = Path(directory) / "second.json"
        first.write_text(json.dumps(base), encoding="utf-8")
        second.write_text(json.dumps(shard), encoding="utf-8")
        merged = merge_artifacts([first, second])
    assert [record["case_id"] for record in merged["records"]] == ["ug-01", "ug-02"]
    assert merged["records"][0]["bravogen_answer"] == "A"
    assert merged["run_summary"]["status"] == "partial"
