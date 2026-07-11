"""Static data-layout audit for BRAVO AI runtime artifacts.

This module does not parse documents, call embeddings, or touch the database. It checks
the filesystem contract around the shared RAG corpus:

- only manifest-declared ingestible files belong to the active shared corpus;
- local/private samples are visible as unmanifested files, not silently ingested;
- manifest entries must exist;
- duplicate payloads are detected by SHA-256.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path

from app.eval.bravo_data_policy import (
    DEFAULT_POLICY_PATH,
    DataRuntimePolicy,
    PathRule,
    load_data_runtime_policy,
    validate_data_runtime_policy,
)
from app.ingestion.manifest import load_manifest, manifest_index

INGESTIBLE_SUFFIXES = {".pdf", ".docx", ".xlsx", ".xlsm", ".md", ".markdown"}


@dataclass(frozen=True)
class DuplicateGroup:
    hash: str
    paths: tuple[str, ...]


@dataclass
class DataAuditReport:
    policy_errors: list[str] = field(default_factory=list)
    required_path_missing: list[str] = field(default_factory=list)
    missing_manifest_files: list[str] = field(default_factory=list)
    unmanifested_ingestible_files: list[str] = field(default_factory=list)
    unmanifested_ingestible_errors: list[str] = field(default_factory=list)
    duplicate_hash_groups: list[DuplicateGroup] = field(default_factory=list)
    active_duplicate_hash_groups: list[DuplicateGroup] = field(default_factory=list)
    derived_summary_warnings: list[str] = field(default_factory=list)
    file_classes: dict[str, str] = field(default_factory=dict)
    metrics: dict[str, object] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return not (
            self.policy_errors
            or self.required_path_missing
            or self.missing_manifest_files
            or self.unmanifested_ingestible_errors
            or self.active_duplicate_hash_groups
        )


def _rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _sha256(path: Path) -> str:
    h = sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _files(root: Path, *, ingestible_only: bool) -> list[Path]:
    out: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if ingestible_only and path.suffix.lower() not in INGESTIBLE_SUFFIXES:
            continue
        out.append(path)
    return sorted(out, key=lambda p: str(p).lower())


def _all_project_files(policy: DataRuntimePolicy) -> list[Path]:
    roots = [rule.path for rule in policy.path_rules if rule.path.exists()]
    files: dict[str, Path] = {}
    for root in roots:
        for path in _files(root, ingestible_only=False):
            files[path.as_posix().lower()] = path
    return sorted(files.values(), key=lambda p: str(p).lower())


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _best_rule(path: Path, policy: DataRuntimePolicy) -> PathRule | None:
    matches = [rule for rule in policy.path_rules if _is_relative_to(path, rule.path)]
    if not matches:
        return None
    return max(matches, key=lambda rule: len(rule.path.parts))


def _classify_file(
    path: Path,
    policy: DataRuntimePolicy,
    *,
    corpus_root: Path,
    manifest_idx: dict[str, dict],
) -> str:
    if _is_relative_to(path, corpus_root):
        rel = path.resolve().relative_to(corpus_root.resolve()).as_posix()
        meta = manifest_idx.get(rel)
        if meta:
            source_type = str(meta.get("source_type") or "")
            if source_type in policy.source_type_classes:
                return policy.source_type_classes[source_type]
    rule = _best_rule(path, policy)
    return rule.data_class if rule else policy.default_class


def _count_by_class(file_classes: dict[str, str], policy: DataRuntimePolicy) -> dict[str, int]:
    counts: dict[str, int] = {name: 0 for name in policy.classes}
    for data_class in file_classes.values():
        counts[data_class] = counts.get(data_class, 0) + 1
    return dict(sorted(counts.items()))


def _duplicate_groups(paths: list[Path], root: Path) -> list[DuplicateGroup]:
    by_hash: dict[str, list[str]] = {}
    for path in paths:
        by_hash.setdefault(_sha256(path), []).append(_rel(path, root))
    return [
        DuplicateGroup(hash=digest, paths=tuple(sorted(group)))
        for digest, group in sorted(by_hash.items())
        if len(group) > 1
    ]


def _derived_summary_warnings(idx: dict[str, dict]) -> list[str]:
    warnings: list[str] = []
    for rel, meta in sorted(idx.items()):
        evidence = str(meta.get("evidence_level") or "").lower()
        source_type = str(meta.get("source_type") or "").lower()
        if evidence == "derived_summary" and source_type != "mindmap":
            warnings.append(f"{rel}: derived_summary should not replace primary source citations")
    return warnings


def audit_data_layout(
    *,
    corpus_root: Path | None = None,
    manifest_path: Path | None = None,
    policy_path: Path = DEFAULT_POLICY_PATH,
    policy: DataRuntimePolicy | None = None,
) -> DataAuditReport:
    policy = policy or load_data_runtime_policy(policy_path)
    corpus_root = (corpus_root or Path(policy.variables["CORPUS_ROOT"])).resolve()
    manifest_path = (manifest_path or corpus_root / "bravo_corpus_manifest.yaml").resolve()
    manifest = load_manifest(manifest_path)
    idx = manifest_index(manifest, corpus_root) if manifest else {}
    declared = set(idx)

    ingestible = _files(corpus_root, ingestible_only=True) if corpus_root.exists() else []
    all_files = _files(corpus_root, ingestible_only=False) if corpus_root.exists() else []
    active_files = [corpus_root / rel for rel in declared if (corpus_root / rel).is_file()]

    report = DataAuditReport()
    report.policy_errors = validate_data_runtime_policy(policy)
    source_types = {str(meta.get("source_type")) for meta in idx.values() if meta.get("source_type")}
    unmapped_source_types = sorted(source_types - set(policy.source_type_classes))
    if unmapped_source_types:
        report.policy_errors.append(f"manifest source_type(s) missing data class: {unmapped_source_types}")
    report.required_path_missing = sorted(
        rule.path.as_posix() for rule in policy.path_rules if rule.required and not rule.path.exists()
    )
    project_files = _all_project_files(policy)
    report.file_classes = {
        path.as_posix(): _classify_file(
            path,
            policy,
            corpus_root=corpus_root,
            manifest_idx=idx,
        )
        for path in project_files
    }
    report.missing_manifest_files = sorted(rel for rel in declared if not (corpus_root / rel).exists())
    report.unmanifested_ingestible_files = [
        _rel(path, corpus_root) for path in ingestible if _rel(path, corpus_root) not in declared
    ]
    corpus_rule = next((rule for rule in policy.path_rules if rule.path == corpus_root), None)
    unmanifested_policy = (
        corpus_rule.unmanifested_ingestible_policy if corpus_rule else "warn"
    )
    if unmanifested_policy == "fail":
        report.unmanifested_ingestible_errors = list(report.unmanifested_ingestible_files)
    report.duplicate_hash_groups = _duplicate_groups(all_files, corpus_root)
    report.active_duplicate_hash_groups = _duplicate_groups(active_files, corpus_root)
    report.derived_summary_warnings = _derived_summary_warnings(idx)
    report.metrics = {
        "policy_name": policy.policy_name,
        "manifest_sources": len(idx),
        "ingestible_files": len(ingestible),
        "classified_files": len(report.file_classes),
        "files_by_class": _count_by_class(report.file_classes, policy),
        "unmanifested_ingestible_files": len(report.unmanifested_ingestible_files),
        "unmanifested_ingestible_policy": unmanifested_policy,
        "missing_manifest_files": len(report.missing_manifest_files),
        "duplicate_hash_groups": len(report.duplicate_hash_groups),
        "active_duplicate_hash_groups": len(report.active_duplicate_hash_groups),
        "derived_summary_warnings": len(report.derived_summary_warnings),
    }
    return report


def main() -> int:
    report = audit_data_layout()
    print("BRAVO data layout:", "PASS" if report.passed else "FAIL")
    print("metrics:", report.metrics)
    for error in report.policy_errors:
        print("ERROR: policy:", error)
    for rel in report.required_path_missing:
        print("ERROR: required path missing:", rel)
    for rel in report.unmanifested_ingestible_files[:20]:
        print("WARN: unmanifested ingestible file:", rel)
    if len(report.unmanifested_ingestible_files) > 20:
        print("WARN: unmanifested ingestible file: ... more")
    for group in report.duplicate_hash_groups:
        print("WARN: duplicate sha256:", group.hash, "=>", ", ".join(group.paths))
    for rel in report.missing_manifest_files:
        print("ERROR: manifest missing file:", rel)
    for rel in report.unmanifested_ingestible_errors:
        print("ERROR: unmanifested ingestible file:", rel)
    for group in report.active_duplicate_hash_groups:
        print("ERROR: active duplicate sha256:", group.hash, "=>", ", ".join(group.paths))
    for warning in report.derived_summary_warnings:
        print("WARN:", warning)
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
