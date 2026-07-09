from __future__ import annotations

from pathlib import Path

from app.agent.bravo_use_cases import load_use_cases, summarize_use_cases, validate_use_cases


def _write(path: Path, text: str) -> None:
    path.write_text(text.strip(), encoding="utf-8")


def test_validate_use_cases_against_playbooks(tmp_path):
    playbooks = tmp_path / "playbooks.yaml"
    use_cases = tmp_path / "use_cases.yaml"
    _write(playbooks, """
version: 1
playbooks:
  - mode: ba_support
    usp: ba_ptnv_copilot
    lifecycle_stage: ba_analysis
    preferred_source_types: [kqpt_ptnv, user_guide]
""")
    _write(use_cases, """
version: 1
use_cases:
  - id: uc_ba
    name: BA scope
    mode: ba_support
    usp: ba_ptnv_copilot
    priority: P1
    stage: lifecycle_copilot
    lifecycle_stage: ba_analysis
    personas: [ba]
    problem: hard to reuse KQPT
    input_sources: [kqpt_ptnv]
    output_artifacts: [scope, questions, acceptance]
    guardrails: [cite scope, mark assumptions]
    success_metrics: [drafting time, reuse rate]
    erp_dependency: none
    readiness: next
""")

    assert validate_use_cases(use_case_path=str(use_cases), playbook_path=str(playbooks)) == []


def test_validate_use_cases_catches_mode_mismatch(tmp_path):
    playbooks = tmp_path / "playbooks.yaml"
    use_cases = tmp_path / "use_cases.yaml"
    _write(playbooks, """
version: 1
playbooks:
  - mode: ba_support
    usp: ba_ptnv_copilot
    lifecycle_stage: ba_analysis
    preferred_source_types: [kqpt_ptnv]
""")
    _write(use_cases, """
version: 1
use_cases:
  - id: uc_bad
    name: Bad
    mode: missing_mode
    usp: ba_ptnv_copilot
    priority: P1
    stage: lifecycle_copilot
    lifecycle_stage: ba_analysis
    personas: [ba]
    problem: x
    input_sources: [kqpt_ptnv]
    output_artifacts: [a, b, c]
    guardrails: [g1, g2]
    success_metrics: [m1, m2]
    erp_dependency: none
    readiness: next
""")

    issues = validate_use_cases(use_case_path=str(use_cases), playbook_path=str(playbooks))
    assert issues == ["uc_bad: unknown playbook mode missing_mode"]


def test_summarize_use_cases(tmp_path):
    use_cases = tmp_path / "use_cases.yaml"
    _write(use_cases, """
version: 1
use_cases:
  - id: uc_1
    name: One
    mode: ba_support
    usp: ba_ptnv_copilot
    priority: P1
    stage: lifecycle_copilot
    lifecycle_stage: ba_analysis
    personas: [ba]
    problem: x
    input_sources: [kqpt_ptnv]
    output_artifacts: [a, b, c]
    guardrails: [g1, g2]
    success_metrics: [m1, m2]
    erp_dependency: none
    readiness: next
""")
    loaded = load_use_cases(str(use_cases))
    summary = summarize_use_cases(loaded)

    assert summary["by_priority"] == {"P1": 1}
    assert summary["by_readiness"] == {"next": 1}
