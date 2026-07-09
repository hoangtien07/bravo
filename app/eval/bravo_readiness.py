"""Static readiness audit for BRAVO knowledge artifacts.

Runs without DB/embedding/LLM. It verifies that the BRAVO corpus manifest, lifecycle
playbooks, use-case matrix, and lifecycle golden set are internally consistent before a
demo or ingest run.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.agent.bravo_playbooks import load_playbooks
from app.agent.bravo_use_cases import load_use_cases, summarize_use_cases, validate_use_cases
from app.eval.bravo_lifecycle import load_items
from app.ingestion.manifest import load_manifest, manifest_index

CORPUS_ROOT = Path("file_system")
MANIFEST_PATH = CORPUS_ROOT / "bravo_corpus_manifest.yaml"
PLAYBOOK_PATH = CORPUS_ROOT / "bravo_lifecycle_playbooks.yaml"
USE_CASE_PATH = CORPUS_ROOT / "bravo_ai_use_cases.yaml"
GOLDEN_PATH = Path("app/eval/golden_set_bravo_lifecycle.example.yaml")

REQUIRED_SOURCE_TYPES = {
    "user_guide",
    "mindmap",
    "kqpt_ptnv",
    "technical_manual",
    "basic_rule",
    "report_template",
}
REQUIRED_PLAYBOOK_MODES = {
    "end_user_guidance",
    "implementation_support",
    "ba_support",
    "technical_impact",
    "qa_testcase",
    "support_helpdesk",
    "voucher_assistant",
    "dashboard_explainer",
    "governance_audit",
}
REQUIRED_USE_CASES = {
    "uc_knowledge_helpdesk",
    "uc_implementation_checklist",
    "uc_ba_scope_assistant",
    "uc_customization_impact",
    "uc_testcase_generator",
    "uc_support_escalation_packet",
    "uc_purchase_voucher_draft",
    "uc_dashboard_explainer",
    "uc_governance_audit",
}
REQUIRED_GOLDEN_IDS = {
    "bravo-p2p-01",
    "bravo-tech-01",
    "bravo-ba-01",
    "bravo-impl-01",
    "bravo-qa-01",
    "bravo-guard-01",
}
FUTURE_SOURCE_TYPES = {"operational_data", "support_ticket", "legal_standard", "implementation_note"}


@dataclass
class ReadinessReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict[str, object] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return not self.errors


def _source_files_missing(idx: dict[str, dict], root: Path) -> list[str]:
    return sorted(rel for rel in idx if not (root / rel).exists())


def _source_types(idx: dict[str, dict]) -> set[str]:
    return {str(meta.get("source_type")) for meta in idx.values() if meta.get("source_type")}


def audit_readiness(
    *,
    corpus_root: Path = CORPUS_ROOT,
    manifest_path: Path = MANIFEST_PATH,
    playbook_path: Path = PLAYBOOK_PATH,
    use_case_path: Path = USE_CASE_PATH,
    golden_path: Path = GOLDEN_PATH,
) -> ReadinessReport:
    report = ReadinessReport()

    try:
        manifest = load_manifest(manifest_path)
        idx = manifest_index(manifest, corpus_root)
    except Exception as exc:
        report.errors.append(f"manifest: {exc}")
        idx = {}
    missing = _source_files_missing(idx, corpus_root)
    if missing:
        report.errors.extend(f"manifest missing file: {rel}" for rel in missing[:20])
        if len(missing) > 20:
            report.errors.append(f"manifest missing file: ... {len(missing) - 20} more")
    stypes = _source_types(idx)
    missing_types = sorted(REQUIRED_SOURCE_TYPES - stypes)
    if missing_types:
        report.errors.append(f"manifest missing required source_type(s): {missing_types}")
    report.metrics["manifest_sources"] = len(idx)
    report.metrics["source_types"] = sorted(stypes)

    try:
        playbooks = load_playbooks(str(playbook_path))
    except Exception as exc:
        report.errors.append(f"playbooks: {exc}")
        playbooks = ()
    modes = {p.mode for p in playbooks}
    missing_modes = sorted(REQUIRED_PLAYBOOK_MODES - modes)
    extra_modes = sorted(modes - REQUIRED_PLAYBOOK_MODES)
    if missing_modes:
        report.errors.append(f"playbooks missing mode(s): {missing_modes}")
    if extra_modes:
        report.warnings.append(f"playbooks contain non-standard mode(s): {extra_modes}")
    report.metrics["playbook_modes"] = sorted(modes)

    try:
        use_cases = load_use_cases(str(use_case_path))
        report.errors.extend(
            f"use_cases: {issue}" for issue in validate_use_cases(
                use_case_path=str(use_case_path), playbook_path=str(playbook_path))
        )
    except Exception as exc:
        report.errors.append(f"use_cases: {exc}")
        use_cases = ()
    use_case_ids = {u.id for u in use_cases}
    missing_use_cases = sorted(REQUIRED_USE_CASES - use_case_ids)
    if missing_use_cases:
        report.errors.append(f"use_cases missing id(s): {missing_use_cases}")
    for uc in use_cases:
        future = sorted(set(uc.input_sources) & FUTURE_SOURCE_TYPES)
        if future and uc.readiness != "later":
            report.warnings.append(f"{uc.id}: uses future source type(s) before later readiness: {future}")
    report.metrics["use_cases"] = len(use_cases)
    report.metrics["use_case_summary"] = summarize_use_cases(use_cases) if use_cases else {}

    try:
        items = load_items(golden_path)
    except Exception as exc:
        report.errors.append(f"golden_lifecycle: {exc}")
        items = []
    golden_ids = {item.id for item in items}
    missing_golden = sorted(REQUIRED_GOLDEN_IDS - golden_ids)
    if missing_golden:
        report.errors.append(f"golden_lifecycle missing id(s): {missing_golden}")
    for item in items:
        if item.expected_behavior not in {"answer", "abstain", "clarify"}:
            report.errors.append(f"{item.id}: invalid expected_behavior {item.expected_behavior}")
        if not item.expected_source_types:
            report.errors.append(f"{item.id}: expected_source_types is empty")
        if not item.expected_modules:
            report.warnings.append(f"{item.id}: expected_modules is empty")
    report.metrics["golden_lifecycle_items"] = len(items)

    return report


def main() -> int:
    report = audit_readiness()
    print("BRAVO knowledge readiness:", "PASS" if report.passed else "FAIL")
    print("metrics:", report.metrics)
    for warning in report.warnings:
        print("WARN:", warning)
    for error in report.errors:
        print("ERROR:", error)
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
