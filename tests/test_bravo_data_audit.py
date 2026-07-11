from __future__ import annotations

from pathlib import Path

from app.eval.bravo_data_audit import audit_data_layout
from app.eval.bravo_data_policy import (
    REQUIRED_CLASSES,
    load_data_runtime_policy,
    validate_data_runtime_policy,
)
from app.ingestion.manifest import load_manifest, manifest_index
from scripts.ingest_userguide import _select_files


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _policy(path: Path, root: Path) -> Path:
    root_posix = root.as_posix()
    data_posix = (root / "Data").as_posix()
    manifest_posix = (root / "bravo_corpus_manifest.yaml").as_posix()
    _write(
        path,
        f"""
version: 1
policy_name: test_policy
default_class: private_operational_data
classes:
  shared_knowledge:
    shared_rag_allowed: true
    versioned: true
    runtime_scope: global
    ingestion_mode: manifest_only
  domain_rules:
    shared_rag_allowed: false
    versioned: true
    runtime_scope: engine
    ingestion_mode: never
  eval_fixtures:
    shared_rag_allowed: false
    versioned: true
    runtime_scope: test
    ingestion_mode: never
  private_operational_data:
    shared_rag_allowed: false
    versioned: false
    runtime_scope: private
    ingestion_mode: scoped_only
  runtime_uploads:
    shared_rag_allowed: false
    versioned: false
    runtime_scope: user_session
    ingestion_mode: scoped_only
  derived_summary:
    shared_rag_allowed: true
    versioned: true
    runtime_scope: global
    ingestion_mode: manifest_only
path_rules:
  - path: {root_posix}
    data_class: shared_knowledge
    required: false
    manifest: {manifest_posix}
    unmanifested_ingestible_policy: warn
    duplicate_policy: active_fail
  - path: {data_posix}
    data_class: private_operational_data
    required: false
    unmanifested_ingestible_policy: warn
    duplicate_policy: warn
source_type_classes:
  user_guide: shared_knowledge
  mindmap: derived_summary
required_classes: [shared_knowledge, domain_rules, eval_fixtures, private_operational_data, runtime_uploads, derived_summary]
""",
    )
    return path


def test_project_data_runtime_policy_is_valid():
    policy = load_data_runtime_policy()

    assert not validate_data_runtime_policy(policy)
    assert REQUIRED_CLASSES <= set(policy.classes)
    assert policy.source_type_classes["mindmap"] == "derived_summary"


def test_manifest_only_ingest_ignores_unmanifested_files(tmp_path):
    root = tmp_path / "file_system"
    _write(root / "UserGuide" / "chapter.pdf", "shared")
    _write(root / "Data" / "private.md", "private sample")
    manifest_path = root / "bravo_corpus_manifest.yaml"
    _write(
        manifest_path,
        """
version: 1
sources:
  - path: UserGuide/chapter.pdf
    knowledge_type: Chapter
    source_type: user_guide
""",
    )
    meta = manifest_index(load_manifest(manifest_path), root)

    files = _select_files(root, meta, manifest_only=True)

    assert [p.relative_to(root).as_posix() for p in files] == ["UserGuide/chapter.pdf"]


def test_data_audit_reports_unmanifested_private_data(tmp_path):
    root = tmp_path / "file_system"
    _write(root / "UserGuide" / "chapter.pdf", "shared")
    _write(root / "Data" / "private.md", "private sample")
    manifest_path = root / "bravo_corpus_manifest.yaml"
    _write(
        manifest_path,
        """
version: 1
sources:
  - path: UserGuide/chapter.pdf
    knowledge_type: Chapter
    source_type: user_guide
""",
    )

    policy_path = _policy(tmp_path / "policy.yaml", root)

    report = audit_data_layout(corpus_root=root, manifest_path=manifest_path, policy_path=policy_path)

    assert report.passed
    assert report.unmanifested_ingestible_files == ["Data/private.md"]
    assert report.metrics["unmanifested_ingestible_files"] == 1
    assert "private_operational_data" in report.metrics["files_by_class"]


def test_data_audit_fails_active_duplicate_payloads(tmp_path):
    root = tmp_path / "file_system"
    _write(root / "A.pdf", "same")
    _write(root / "B.pdf", "same")
    manifest_path = root / "bravo_corpus_manifest.yaml"
    _write(
        manifest_path,
        """
version: 1
sources:
  - path: A.pdf
    source_type: user_guide
  - path: B.pdf
    source_type: user_guide
""",
    )

    policy_path = _policy(tmp_path / "policy.yaml", root)

    report = audit_data_layout(corpus_root=root, manifest_path=manifest_path, policy_path=policy_path)

    assert not report.passed
    assert len(report.active_duplicate_hash_groups) == 1
    assert report.active_duplicate_hash_groups[0].paths == ("A.pdf", "B.pdf")
