"""Local storage layout for uploaded files + chat attachments (v2).

Single seam so a future MinIO/GCS swap (DOCUMENT-MANAGEMENT.md §4) touches one module.
Paths are grouped by owner so a personal file lives under its owner's directory:

    {upload_root}/workspace/{owner_id | "shared"}/{source_id}_{safe_filename}
    {upload_root}/attachments/{owner_id}/{attachment_id}{ext}

`safe_filename` strips path separators / traversal — the agent-ai P1 lesson: never let a
caller-supplied name escape its directory.
"""
from __future__ import annotations

import re
import uuid
from pathlib import Path

from app.config import get_settings

_settings = get_settings()


def _upload_root() -> Path:
    root = _settings.upload_root or "data/uploads"
    return Path(root)


def safe_filename(name: str | None) -> str:
    """Reduce an arbitrary upload name to a bare, separator-free basename."""
    base = Path(name or "upload").name          # drop any directory component
    base = base.replace("\x00", "")
    base = re.sub(r"[^\w.\- ]", "_", base, flags=re.UNICODE).strip() or "upload"
    return base[:200]


def workspace_path(source_id: uuid.UUID, filename: str, owner_id: uuid.UUID | None) -> Path:
    bucket = str(owner_id) if owner_id is not None else "shared"
    return _upload_root() / "workspace" / bucket / f"{source_id}_{safe_filename(filename)}"


def attachment_path(attachment_id: uuid.UUID, owner_id: uuid.UUID, filename: str) -> Path:
    ext = Path(safe_filename(filename)).suffix
    return _upload_root() / "attachments" / str(owner_id) / f"{attachment_id}{ext}"


def legacy_flat_path(source_id: uuid.UUID, filename: str) -> Path:
    """Pre-v2 flat layout: {upload_root}/{source_id}_{filename} — kept as a lookup fallback."""
    return _upload_root() / f"{source_id}_{filename}"
