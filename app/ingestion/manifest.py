"""BRAVO corpus manifest helpers.

The manifest is knowledge-as-data: it annotates each source with BRAVO taxonomy
metadata without changing the parser or database schema. Keep this module DB-free so
tests and packaging checks can validate manifests cheaply.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from app.utils.yaml_compat import safe_load_file


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
                    idx[rel] = _merge_meta(defaults, entry, rel)
            continue
        if exact:
            rel = Path(str(exact)).as_posix()
            idx[rel] = _merge_meta(defaults, entry, rel)
    return idx


def source_extra(meta: dict, fallback_path: Path, folder: Path) -> dict:
    rel = fallback_path.relative_to(folder).as_posix()
    extra = {k: v for k, v in meta.items() if k != "knowledge_type"}
    extra.setdefault("relative_path", rel)
    return extra
