from __future__ import annotations

import pytest

from app.eval.consultant_release_gates import (
    GateValidationError,
    ReleaseGate,
    load_release_gates,
    summarize_release_gates,
)


def test_summary_fails_closed_for_open_required_gate():
    report = summarize_release_gates([
        ReleaseGate("sme", True, "passed", "sme-owner", ("review-2026-07",)),
        ReleaseGate("canary", True, "pending", None, ()),
        ReleaseGate("external", False, "not_applicable", None, ()),
    ])

    assert report["ready_for_production_default"] is False
    assert report["passed_required_gate_count"] == 1
    assert report["open_required_gates"] == [
        {"gate_id": "canary", "status": "pending", "owner": None}
    ]


def test_loader_requires_evidence_for_a_passed_gate(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text("""schema_version: consultant-release-gates/v1
gates:
  - gate_id: sme
    required: true
    status: passed
    owner: sme-owner
    evidence_refs: []
""", encoding="utf-8")

    with pytest.raises(GateValidationError, match="passed requires owner"):
        load_release_gates(path)
