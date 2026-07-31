"""Freeze a synthetic, matched legacy-versus-consultant A/B replay as a new evidence artifact.

The module intentionally does not call a model or the network. It validates a completed replay
from :mod:`app.eval.consultant_replay`, binds it to hashes for the fixture/evidence/prompt inputs,
and refuses to overwrite an existing run directory. Provider credentials and raw configuration
values are never accepted as command-line arguments or written into the artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "bravo-v2/frozen-ab-baseline/v1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class FrozenBaselineError(ValueError):
    """Raised when replay evidence is incomplete, unsafe, or would overwrite history."""


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _non_empty(value: Any, field: str) -> str:
    result = str(value or "").strip()
    if not result:
        raise FrozenBaselineError(f"{field} is required")
    return result


def _hash(value: Any, field: str) -> str:
    result = _non_empty(value, field).lower()
    if not _SHA256.fullmatch(result):
        raise FrozenBaselineError(f"{field} must be a lowercase SHA-256")
    return result


def _prompt_hashes(values: list[str]) -> dict[str, str]:
    output: dict[str, str] = {}
    for item in values:
        name, separator, digest = item.partition("=")
        if not separator or not name.strip():
            raise FrozenBaselineError("prompt hashes must use component=sha256")
        name = name.strip()
        if name in output:
            raise FrozenBaselineError(f"duplicate prompt hash component: {name}")
        output[name] = _hash(digest, f"prompt hash for {name}")
    if not output:
        raise FrozenBaselineError("at least one prompt hash is required")
    return dict(sorted(output.items()))


def _normalized_replay(replay: dict[str, Any]) -> list[dict[str, Any]]:
    if replay.get("persist_answers") is not True:
        raise FrozenBaselineError("replay must set persist_answers=true")
    cases = replay.get("runs")
    if not isinstance(cases, list) or not cases:
        raise FrozenBaselineError("replay must contain at least one completed case")

    normalized: list[dict[str, Any]] = []
    seen_case_ids: set[str] = set()
    for index, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            raise FrozenBaselineError(f"case {index} must be an object")
        case_id = _non_empty(case.get("case_id"), f"case {index} id")
        if case_id in seen_case_ids:
            raise FrozenBaselineError(f"duplicate case id: {case_id}")
        seen_case_ids.add(case_id)
        runs = case.get("runs")
        if not isinstance(runs, list):
            raise FrozenBaselineError(f"case {case_id} runs must be a list")
        by_mode: dict[str, dict[str, Any]] = {}
        for run in runs:
            if not isinstance(run, dict):
                raise FrozenBaselineError(f"case {case_id} has an invalid run")
            mode = str(run.get("mode") or "")
            if mode not in {"off", "on"} or mode in by_mode:
                raise FrozenBaselineError(f"case {case_id} must contain one off and one on run")
            if run.get("http_status") != 200 or "answer" not in run:
                raise FrozenBaselineError(f"case {case_id}/{mode} did not capture a successful answer")
            by_mode[mode] = {
                "answer": str(run["answer"]),
                "grounded": bool(run.get("grounded")),
                "citations": list(run.get("citations") or []),
                "workflow_id": run.get("workflow_id"),
                "current_node": run.get("current_node"),
                "state_revision": run.get("state_revision"),
                "latency_ms": run.get("latency_ms"),
            }
        if set(by_mode) != {"off", "on"}:
            raise FrozenBaselineError(f"case {case_id} must contain one off and one on run")
        normalized.append({"case_id": case_id, "system_a_legacy": by_mode["off"],
                           "system_b_consultant": by_mode["on"]})
    return normalized


def build_baseline(
    *, fixture_path: str | Path, replay_path: str | Path, baseline_commit: str,
    model_provider: str, model: str, model_version: str, evidence_snapshot_sha256: str,
    prompt_hashes: list[str], captured_at: str | None = None,
) -> dict[str, Any]:
    """Build a canonical, secret-free baseline artifact from an already completed replay."""
    fixture_path = Path(fixture_path)
    replay_path = Path(replay_path)
    try:
        replay = json.loads(replay_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise FrozenBaselineError("replay must be valid JSON") from exc
    if not isinstance(replay, dict):
        raise FrozenBaselineError("replay root must be an object")
    artifact = {
        "schema_version": SCHEMA_VERSION,
        "captured_at": captured_at or datetime.now(UTC).isoformat(),
        "source": {
            "fixture_path": str(fixture_path).replace("\\", "/"),
            "fixture_sha256": sha256_file(fixture_path),
            "replay_path": str(replay_path).replace("\\", "/"),
            "replay_sha256": sha256_file(replay_path),
        },
        "controls": {
            "baseline_commit": _non_empty(baseline_commit, "baseline commit"),
            "model_provider": _non_empty(model_provider, "model provider"),
            "model": _non_empty(model, "model"),
            "model_version": _non_empty(model_version, "model version"),
            "evidence_snapshot_sha256": _hash(evidence_snapshot_sha256, "evidence snapshot hash"),
            "prompt_hashes": _prompt_hashes(prompt_hashes),
            "credentials_recorded": False,
        },
        "cases": _normalized_replay(replay),
    }
    artifact["payload_sha256"] = hashlib.sha256(_canonical_bytes(artifact)).hexdigest()
    return artifact


def freeze_baseline(artifact: dict[str, Any], output_dir: str | Path) -> Path:
    """Write exactly one new baseline directory; any existing directory is immutable history."""
    directory = Path(output_dir)
    if directory.exists():
        raise FrozenBaselineError(f"refusing to overwrite existing baseline directory: {directory}")
    directory.mkdir(parents=True)
    baseline_path = directory / "baseline.json"
    payload = json.dumps(artifact, ensure_ascii=False, indent=2) + "\n"
    baseline_path.write_text(payload, encoding="utf-8")
    checksum = sha256_file(baseline_path)
    (directory / "SHA256SUMS").write_text(f"{checksum}  baseline.json\n", encoding="utf-8")
    return baseline_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--replay", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--baseline-commit", required=True)
    parser.add_argument("--model-provider", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--model-version", required=True)
    parser.add_argument("--evidence-snapshot-sha256", required=True)
    parser.add_argument("--prompt-hash", action="append", default=[])
    parser.add_argument("--captured-at")
    args = parser.parse_args()
    try:
        artifact = build_baseline(
            fixture_path=args.fixture, replay_path=args.replay, baseline_commit=args.baseline_commit,
            model_provider=args.model_provider, model=args.model, model_version=args.model_version,
            evidence_snapshot_sha256=args.evidence_snapshot_sha256, prompt_hashes=args.prompt_hash,
            captured_at=args.captured_at,
        )
        path = freeze_baseline(artifact, args.out_dir)
    except FrozenBaselineError as exc:
        print(f"FROZEN BASELINE REJECTED: {exc}")
        return 2
    print(f"Frozen A/B baseline written: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
