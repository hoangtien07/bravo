"""Offline structural benchmark for Consultant Intelligence trajectories.

This complements the BravoGen black-box benchmark: it evaluates our workflow/state
contracts without treating any external answer as ground truth.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from app.consultant.catalog import load_catalog, match_workflow
from app.consultant.contracts import TaskState
from app.consultant.service import ConsultantService
from app.utils.yaml_compat import safe_load_file


@dataclass(frozen=True)
class FixtureResult:
    case_id: str
    passed: bool
    failures: list[str]


def evaluate_fixture(path: str | Path) -> list[FixtureResult]:
    """Replay fixture turns through deterministic interpreter/state reconciler."""
    raw = safe_load_file(Path(path)) or {}
    _goals, workflows = load_catalog()
    results: list[FixtureResult] = []
    service = object.__new__(ConsultantService)  # evaluator needs only pure reconciliation
    for case in raw.get("cases", []):
        state = TaskState()
        failures: list[str] = []
        for index, turn in enumerate(case.get("turns", []), start=1):
            question = str(turn["user"])
            workflow = match_workflow(question) or (workflows.get(state.workflow_id) if state.workflow_id else None)
            state = service._reconcile(state, question, workflow)
            expected = turn.get("expected", {})
            if expected.get("workflow") and state.workflow_id != expected["workflow"]:
                failures.append(f"turn {index}: workflow={state.workflow_id}, expected={expected['workflow']}")
            if expected.get("current_node") and state.current_node != expected["current_node"]:
                failures.append(f"turn {index}: current_node={state.current_node}, expected={expected['current_node']}")
            for key, value in (expected.get("facts") or {}).items():
                if state.facts.get(key) != value:
                    failures.append(f"turn {index}: fact {key}={state.facts.get(key)!r}, expected={value!r}")
            if expected.get("status") and state.status != expected["status"]:
                failures.append(f"turn {index}: status={state.status}, expected={expected['status']}")
        results.append(FixtureResult(case_id=str(case.get("case_id", "unknown")),
                                     passed=not failures, failures=failures))
    return results


def fixture_coverage(path: str | Path) -> dict[str, int]:
    """Report declared structural coverage without overstating it as SME quality evidence."""
    raw = safe_load_file(Path(path)) or {}
    cases = raw.get("cases", [])
    default = int(raw.get("default_structural_variants", 1))
    return {"scenarios": len(cases),
            "structural_variants": sum(int(case.get("structural_variants", default)) for case in cases),
            "turns": sum(len(case.get("turns", [])) for case in cases)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", nargs="?", default="app/eval/consultant_benchmark.example.yaml")
    parser.add_argument("--out")
    args = parser.parse_args()
    results = evaluate_fixture(args.fixture)
    report = {"fixture": str(args.fixture), **fixture_coverage(args.fixture),
              "passed": sum(r.passed for r in results), "total": len(results),
              "results": [r.__dict__ for r in results]}
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0 if report["passed"] == report["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
