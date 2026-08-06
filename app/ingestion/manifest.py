"""BRAVO corpus manifest helpers.

The manifest is knowledge-as-data: it annotates each source with BRAVO taxonomy
metadata without changing the parser or database schema. Keep this module DB-free so
tests and packaging checks can validate manifests cheaply.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import re

from app.utils.yaml_compat import safe_load_file


_BRAVO_VERSION_IN_PATH = re.compile(r"(?:^|[_-])(B\d+R\d+)(?=[^A-Z0-9]|$)", re.IGNORECASE)
_APPROVED_STATUSES = frozenset({"approved", "draft", "superseded", "deprecated"})


def load_manifest(path: Path | None) -> dict:
    if path is None or not path.exists():
        return {}
    raw = safe_load_file(path) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"Manifest không hợp lệ: {path}")
    return raw


def _merge_meta(defaults: dict, entry: dict, rel_path: str) -> dict:
    meta = deepcopy(defaults)
    for k, v in entry.items():
        if k not in {"path", "glob"}:
            meta[k] = v
    meta["relative_path"] = rel_path
    return meta


def _validate_source_authority(meta: dict, rel_path: str, *, require_authority: bool) -> None:
    """Reject metadata that contradicts a version explicitly named by its file.

    A manifest default is useful for unversioned material, but it must never turn a
    B8R4 source into approved B10R1 evidence.  Keep this check DB-free so ingestion,
    packaging, and tests all share the same fail-closed boundary.
    """
    match = _BRAVO_VERSION_IN_PATH.search(rel_path)
    if require_authority:
        required = ("doc_version", "owner", "approved_status", "effective_date", "customer_scope")
        missing = [field for field in required if field not in meta]
        if missing:
            raise ValueError(f"manifest source {rel_path!r} is missing authority metadata: {', '.join(missing)}")
        if not str(meta["doc_version"] or "").strip() or not str(meta["owner"] or "").strip():
            raise ValueError(f"manifest source {rel_path!r} requires non-empty doc_version and owner")
        if str(meta["approved_status"] or "").strip().lower() not in _APPROVED_STATUSES:
            raise ValueError(f"manifest source {rel_path!r} has an invalid approved_status")
        if not str(meta["customer_scope"] or "").strip():
            raise ValueError(f"manifest source {rel_path!r} requires customer_scope")
    if not match:
        return
    filename_version = match.group(1).upper()
    declared_version = str(meta.get("doc_version") or "").strip().upper()
    if declared_version != filename_version:
        raise ValueError(
            f"manifest source {rel_path!r} declares doc_version {declared_version or '<missing>'!r} "
            f"but its filename declares {filename_version!r}"
        )


def manifest_index(manifest: dict, folder: Path) -> dict[str, dict]:
    """Map relative POSIX path -> manifest metadata.

    Supports exact `path` entries and glob entries. Exact entries are indexed even if
    the file is not present, so a separate existence check can report missing corpus
    files clearly.
    """
    defaults = manifest.get("defaults") or {}
    if defaults and not isinstance(defaults, dict):
        raise ValueError("manifest.defaults phải là mapping")
    sources = manifest.get("sources") or []
    if not isinstance(sources, list):
        raise ValueError("manifest.sources phải là list")

    idx: dict[str, dict] = {}
    # General manifest consumers use compact, versionless test manifests. The BRAVO corpus
    # declares `system_version`; that declaration makes source authority mandatory there.
    require_authority = bool(manifest.get("system_version"))
    for entry in sources:
        if not isinstance(entry, dict):
            raise ValueError("manifest source entry phải là mapping")
        pattern = entry.get("glob")
        exact = entry.get("path")
        if pattern and exact:
            raise ValueError("source entry chỉ được có một trong glob/path")
        if pattern:
            matches = sorted(folder.glob(str(pattern)), key=lambda p: str(p).lower())
            for p in matches:
                if p.is_file():
                    rel = p.relative_to(folder).as_posix()
                    meta = _merge_meta(defaults, entry, rel)
                    _validate_source_authority(meta, rel, require_authority=require_authority)
                    idx[rel] = meta
            continue
        if exact:
            rel = Path(str(exact)).as_posix()
            meta = _merge_meta(defaults, entry, rel)
            _validate_source_authority(meta, rel, require_authority=require_authority)
            idx[rel] = meta
    return idx


def source_extra(meta: dict, fallback_path: Path, folder: Path) -> dict:
    rel = fallback_path.relative_to(folder).as_posix()
    extra = {k: v for k, v in meta.items() if k != "knowledge_type"}
    extra.setdefault("relative_path", rel)
    return extra
