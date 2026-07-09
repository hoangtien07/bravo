from __future__ import annotations

from pathlib import Path

from app.agent.bravo_playbooks import load_playbooks, render_playbook_hint, select_playbooks


def _write_playbooks(path: Path) -> None:
    path.write_text(
        """
version: 1
playbooks:
  - mode: ba_support
    usp: ba_ptnv_copilot
    lifecycle_stage: ba_analysis
    preferred_source_types: [kqpt_ptnv]
    triggers: [kqpt, testcase]
    required_outputs: [scope, acceptance criteria]
    guardrails: [do not add requirements beyond cited scope]
  - mode: technical_impact
    usp: customization_impact_copilot
    lifecycle_stage: technical_design
    preferred_source_types: [technical_manual]
    triggers: [b30, procedure]
    required_outputs: [affected tables]
    guardrails: [do not generate free-form SQL]
""".strip(),
        encoding="utf-8",
    )


def test_load_playbooks_validates_modes(tmp_path):
    p = tmp_path / "playbooks.yaml"
    _write_playbooks(p)

    playbooks = load_playbooks(str(p))

    assert {pb.mode for pb in playbooks} == {"ba_support", "technical_impact"}


def test_select_playbook_from_query(tmp_path):
    p = tmp_path / "playbooks.yaml"
    _write_playbooks(p)

    selected = select_playbooks("Bảng B30BizDoc dùng lưu gì?", path=str(p))

    assert selected[0].mode == "technical_impact"


def test_render_playbook_hint_contains_guardrails(tmp_path):
    p = tmp_path / "playbooks.yaml"
    _write_playbooks(p)

    hint = render_playbook_hint("KQPT/PTNV dùng cho đối tượng nào?", path=str(p))

    assert "mode=ba_support" in hint
    assert "required_outputs" in hint
    assert "guardrails" in hint
