"""Evidence-only production gate for Consultant Intelligence.

This tool never infers that a workflow is ready from a benchmark score or a green test suite.
It aggregates an explicitly approved, redaction-safe release artifact and fails closed while
any required gate remains pending.  It is intentionally independent of provider credentials,
customer conversations, and the runtime database.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.utils.yaml_compat import safe_load_file


GATE_STATUSES = {"passed", "pending", "blocked", "not_applicable"}


class GateValidationError(ValueError):
    """Raised when a release-gate artifact cannot be treated as evidence."""


@dataclass(frozen=True)
class ReleaseGate:
    gate_id: str
    required: bool
    status: str
    owner: str | None
    evidence_refs: tuple[str, ...]


def _required_string(value: Any, field: str, index: int) -> str:
    result = str(value or "").strip()
    if not result:
        raise GateValidationError(f"gate {index}: {field} is required")
    return result


def load_release_gates(path: str | Path) -> list[ReleaseGate]:
    """Load a human-owned approval artifact; ``passed`` needs owner and evidence."""
    raw = safe_load_file(Path(path)) or {}
    if raw.get("schema_version") != "consultant-release-gates/v1":
        raise GateValidationError("schema_version must be consultant-release-gates/v1")
    gates_raw = raw.get("gates")
    if not isinstance(gates_raw, list) or not gates_raw:
        raise GateValidationError("gates must be a non-empty list")

    gates: list[ReleaseGate] = []
    seen: set[str] = set()
    for index, item in enumerate(gates_raw, start=1):
        if not isinstance(item, dict):
            raise GateValidationError(f"gate {index}: must be a mapping")
        gate_id = _required_string(item.get("gate_id"), "gate_id", index)
        if gate_id in seen:
            raise GateValidationError(f"gate {index}: duplicate gate_id {gate_id}")
        seen.add(gate_id)
        if not isinstance(item.get("required"), bool):
            raise GateValidationError(f"gate {index}: required must be boolean")
        status = _required_string(item.get("status"), "status", index)
        if status not in GATE_STATUSES:
            raise GateValidationError(f"gate {index}: status must be one of {sorted(GATE_STATUSES)}")
        owner = str(item.get("owner") or "").strip() or None
        evidence_raw = item.get("evidence_refs") or []
        if not isinstance(evidence_raw, list) or any(not str(ref).strip() for ref in evidence_raw):
            raise GateValidationError(f"gate {index}: evidence_refs must be a list of non-empty strings")
        evidence_refs = tuple(str(ref).strip() for ref in evidence_raw)
        if status == "passed" and (owner is None or not evidence_refs):
            raise GateValidationError(f"gate {index}: passed requires owner and evidence_refs")
        if item["required"] and status == "not_applicable":
            raise GateValidationError(f"gate {index}: required gate cannot be not_applicable")
        gates.append(ReleaseGate(gate_id, item["required"], status, owner, evidence_refs))
    return gates


def summarize_release_gates(gates: list[ReleaseGate]) -> dict[str, Any]:
    """Produce an auditable decision without manufacturing a product-ready verdict."""
    required = [gate for gate in gates if gate.required]
    open_required = [gate for gate in required if gate.status != "passed"]
    return {
        "gate_count": len(gates),
        "required_gate_count": len(required),
        "passed_required_gate_count": len(required) - len(open_required),
        "open_required_gates": [
            {"gate_id": gate.gate_id, "status": gate.status, "owner": gate.owner}
            for gate in open_required
        ],
        "ready_for_production_default": not open_required,
        "evidence_only": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate human-owned Consultant release gates.")
    parser.add_argument("gate_file")
    parser.add_argument("--out")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    try:
        report = summarize_release_gates(load_release_gates(args.gate_file))
    except GateValidationError as exc:
        print(f"INVALID RELEASE GATE ARTIFACT: {exc}")
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.out:
        Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 1 if args.require_ready and not report["ready_for_production_default"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
