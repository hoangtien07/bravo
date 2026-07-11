from __future__ import annotations

from pathlib import Path

from app.eval.bravo_readiness import audit_readiness


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip(), encoding="utf-8")


def test_readiness_passes_minimal_valid_artifacts(tmp_path):
    root = tmp_path / "fs"
    for rel in (
        "ug.pdf", "mm.md", "kqpt.pdf", "tech.docx", "basic.pdf", "report.pdf",
    ):
        # Nội dung KHÁC nhau mỗi file -> sha256 khác nhau (audit corpus chặn trùng hash).
        _write(root / rel, f"noi dung mau cua {rel}")
    manifest = root / "manifest.yaml"
    _write(manifest, """
version: 1
sources:
  - path: ug.pdf
    source_type: user_guide
  - path: mm.md
    source_type: mindmap
  - path: kqpt.pdf
    source_type: kqpt_ptnv
  - path: tech.docx
    source_type: technical_manual
  - path: basic.pdf
    source_type: basic_rule
  - path: report.pdf
    source_type: report_template
""")
    playbook = root / "playbooks.yaml"
    _write(playbook, """
version: 1
playbooks:
  - mode: end_user_guidance
    usp: user_guide_helpdesk_copilot
    lifecycle_stage: end_user_guidance
    preferred_source_types: [user_guide]
  - mode: implementation_support
    usp: implementation_copilot
    lifecycle_stage: implementation
    preferred_source_types: [technical_manual]
  - mode: ba_support
    usp: ba_ptnv_copilot
    lifecycle_stage: ba_analysis
    preferred_source_types: [kqpt_ptnv]
  - mode: technical_impact
    usp: customization_impact_copilot
    lifecycle_stage: customization
    preferred_source_types: [technical_manual]
  - mode: qa_testcase
    usp: testcase_copilot
    lifecycle_stage: qa_testing
    preferred_source_types: [kqpt_ptnv]
  - mode: support_helpdesk
    usp: user_guide_helpdesk_copilot
    lifecycle_stage: support
    preferred_source_types: [user_guide]
  - mode: voucher_assistant
    usp: bravo_voucher_assistant
    lifecycle_stage: end_user_productivity
    preferred_source_types: [user_guide]
  - mode: dashboard_explainer
    usp: management_dashboard_explainer
    lifecycle_stage: management_reporting
    preferred_source_types: [report_template]
  - mode: governance_audit
    usp: governance_audit_copilot
    lifecycle_stage: governance
    preferred_source_types: [technical_manual]
""")
    use_cases = root / "use_cases.yaml"
    _write(use_cases, """
version: 1
use_cases:
  - id: uc_knowledge_helpdesk
    name: Knowledge
    mode: end_user_guidance
    usp: user_guide_helpdesk_copilot
    priority: P0
    stage: knowledge_pilot
    lifecycle_stage: end_user_guidance
    personas: [support]
    problem: x
    input_sources: [user_guide]
    output_artifacts: [a, b, c]
    guardrails: [g1, g2]
    success_metrics: [m1, m2]
    erp_dependency: none
    readiness: now
  - id: uc_implementation_checklist
    name: Impl
    mode: implementation_support
    usp: implementation_copilot
    priority: P0
    stage: knowledge_pilot
    lifecycle_stage: implementation
    personas: [support]
    problem: x
    input_sources: [technical_manual]
    output_artifacts: [a, b, c]
    guardrails: [g1, g2]
    success_metrics: [m1, m2]
    erp_dependency: none
    readiness: now
  - id: uc_ba_scope_assistant
    name: BA
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
  - id: uc_customization_impact
    name: Impact
    mode: technical_impact
    usp: customization_impact_copilot
    priority: P1
    stage: lifecycle_copilot
    lifecycle_stage: customization
    personas: [dev]
    problem: x
    input_sources: [technical_manual]
    output_artifacts: [a, b, c]
    guardrails: [g1, g2]
    success_metrics: [m1, m2]
    erp_dependency: none
    readiness: next
  - id: uc_testcase_generator
    name: Test
    mode: qa_testcase
    usp: testcase_copilot
    priority: P1
    stage: lifecycle_copilot
    lifecycle_stage: qa_testing
    personas: [qa]
    problem: x
    input_sources: [kqpt_ptnv]
    output_artifacts: [a, b, c]
    guardrails: [g1, g2]
    success_metrics: [m1, m2]
    erp_dependency: none
    readiness: next
  - id: uc_support_escalation_packet
    name: Support
    mode: support_helpdesk
    usp: user_guide_helpdesk_copilot
    priority: P1
    stage: lifecycle_copilot
    lifecycle_stage: support
    personas: [support]
    problem: x
    input_sources: [user_guide]
    output_artifacts: [a, b, c]
    guardrails: [g1, g2]
    success_metrics: [m1, m2]
    erp_dependency: optional_read
    readiness: next
  - id: uc_purchase_voucher_draft
    name: Voucher
    mode: voucher_assistant
    usp: bravo_voucher_assistant
    priority: P2
    stage: erp_aware_copilot
    lifecycle_stage: end_user_productivity
    personas: [accountant]
    problem: x
    input_sources: [user_guide]
    output_artifacts: [a, b, c]
    guardrails: [g1, g2]
    success_metrics: [m1, m2]
    erp_dependency: read_and_draft
    readiness: later
  - id: uc_dashboard_explainer
    name: Dash
    mode: dashboard_explainer
    usp: management_dashboard_explainer
    priority: P2
    stage: erp_aware_copilot
    lifecycle_stage: management_reporting
    personas: [manager]
    problem: x
    input_sources: [report_template]
    output_artifacts: [a, b, c]
    guardrails: [g1, g2]
    success_metrics: [m1, m2]
    erp_dependency: read_only
    readiness: later
  - id: uc_governance_audit
    name: Gov
    mode: governance_audit
    usp: governance_audit_copilot
    priority: P3
    stage: erp_aware_copilot
    lifecycle_stage: governance
    personas: [admin]
    problem: x
    input_sources: [technical_manual]
    output_artifacts: [a, b, c]
    guardrails: [g1, g2]
    success_metrics: [m1, m2]
    erp_dependency: read_only
    readiness: later
""")
    golden = root / "golden.yaml"
    _write(golden, """
- id: bravo-p2p-01
  question: q
  actor_email: a
  expected_source_types: [user_guide]
  expected_modules: [purchase]
- id: bravo-tech-01
  question: q
  actor_email: a
  expected_source_types: [technical_manual]
  expected_modules: [platform]
- id: bravo-ba-01
  question: q
  actor_email: a
  expected_source_types: [kqpt_ptnv]
  expected_modules: [purchase]
- id: bravo-impl-01
  question: q
  actor_email: a
  expected_source_types: [technical_manual]
  expected_modules: [system]
- id: bravo-qa-01
  question: q
  actor_email: a
  expected_source_types: [kqpt_ptnv]
  expected_modules: [qc]
- id: bravo-guard-01
  question: q
  actor_email: a
  expected_source_types: [basic_rule]
  expected_modules: [system]
  expected_behavior: abstain
""")

    report = audit_readiness(
        corpus_root=root,
        manifest_path=manifest,
        playbook_path=playbook,
        use_case_path=use_cases,
        golden_path=golden,
    )

    assert report.passed, report.errors
    assert report.metrics["manifest_sources"] == 6


def test_readiness_reports_missing_manifest_file(tmp_path):
    root = tmp_path / "fs"
    manifest = root / "manifest.yaml"
    _write(manifest, """
version: 1
sources:
  - path: missing.pdf
    source_type: user_guide
""")
    report = audit_readiness(
        corpus_root=root,
        manifest_path=manifest,
        playbook_path=root / "missing_playbooks.yaml",
        use_case_path=root / "missing_use_cases.yaml",
        golden_path=root / "missing_golden.yaml",
    )

    assert not report.passed
    assert any("manifest missing file" in e for e in report.errors)
