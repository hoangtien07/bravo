"""Ingest the BRAVO 10 shared knowledge corpus.

The shared BRAVO corpus under ``file_system/`` is manifest-only by default. Files
outside ``bravo_corpus_manifest.yaml`` are ignored so local/demo/private samples do
not leak into the GLOBAL RAG corpus. Use ``--allow-unmanifested`` only for an
explicitly scoped non-shared import.
"""
from __future__ import annotations

import argparse
import asyncio
import re
from pathlib import Path

from app.ingestion.manifest import load_manifest, manifest_index, source_extra

DEFAULT_DIR = Path("file_system")
DEFAULT_MANIFEST = DEFAULT_DIR / "bravo_corpus_manifest.yaml"
_SUFFIXES = {".pdf", ".docx", ".xlsx", ".xlsm", ".md", ".markdown"}


def _knowledge_type(filename: str) -> str:
    """Derive a friendly citation label when a manifest label is unavailable."""
    m = re.search(r"Chapter(\d+)_(\w+)", filename, re.IGNORECASE)
    if m:
        return f"Chuong {int(m.group(1))} - {m.group(2)}"
    stem = Path(filename).stem
    if "BI_Guidelines" in filename:
        return "BRAVO BI Guidelines"
    if "Basic rules" in filename:
        return "BRAVO 10 - Basic rules"
    if filename.lower().endswith(".docx"):
        return f"Tai lieu ky thuat - {stem}"
    if filename.lower().endswith((".md", ".markdown")):
        return f"Mindmap - {stem.replace('Mindmap_', '')}"
    return "BRAVO 10 User Guide"


def _collect(folder: Path) -> list[Path]:
    """All ingestible files under ``folder`` (recursive), sorted for stable order."""
    files = [p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in _SUFFIXES]
    return sorted(files, key=lambda p: str(p).lower())


def _collect_from_manifest(folder: Path, manifest_meta: dict[str, dict]) -> tuple[list[Path], list[str]]:
    """Return existing ingestible manifest files and missing manifest entries."""
    files: list[Path] = []
    missing: list[str] = []
    for rel in sorted(manifest_meta):
        path = folder / rel
        if not path.exists():
            missing.append(rel)
            continue
        if path.is_file() and path.suffix.lower() in _SUFFIXES:
            files.append(path)
    return files, missing


def _unmanifested_ingestible(folder: Path, manifest_meta: dict[str, dict]) -> list[str]:
    declared = {Path(rel).as_posix() for rel in manifest_meta}
    out: list[str] = []
    for path in _collect(folder):
        rel = path.relative_to(folder).as_posix()
        if rel not in declared:
            out.append(rel)
    return out


async def _resolve_department(db, name: str):
    """Resolve Department by name; fail closed instead of importing private data globally."""
    from sqlalchemy import select

    from app.database.models import Department

    did = (await db.execute(select(Department.id).where(Department.name == name))).scalar_one_or_none()
    if did is None:
        raise SystemExit(
            f"[ingest] Department '{name}' not found. Create it first; refusing GLOBAL import."
        )
    return did


def _load_manifest_meta(folder: Path, manifest_path: Path | None) -> dict[str, dict]:
    try:
        manifest = load_manifest(manifest_path)
        return manifest_index(manifest, folder) if manifest else {}
    except ValueError as exc:
        raise SystemExit(f"[ingest] {exc}") from exc


def _select_files(
    folder: Path,
    manifest_meta: dict[str, dict],
    *,
    manifest_only: bool,
) -> list[Path]:
    if not manifest_only:
        return _collect(folder)
    if not manifest_meta:
        raise SystemExit(
            "[ingest] Manifest-only mode requires bravo_corpus_manifest.yaml. "
            "Use --allow-unmanifested only for explicitly scoped non-shared imports."
        )
    files, missing = _collect_from_manifest(folder, manifest_meta)
    if missing:
        preview = ", ".join(missing[:10])
        more = f" (+{len(missing) - 10} more)" if len(missing) > 10 else ""
        raise SystemExit(f"[ingest] Manifest references missing file(s): {preview}{more}")
    ignored = _unmanifested_ingestible(folder, manifest_meta)
    if ignored:
        preview = ", ".join(ignored[:10])
        more = f" (+{len(ignored) - 10} more)" if len(ignored) > 10 else ""
        print(f"[ingest] Ignoring unmanifested ingestible file(s): {preview}{more}")
    return files


async def main(
    folder: Path,
    department: str | None = None,
    manifest_path: Path | None = DEFAULT_MANIFEST,
    manifest_only: bool = True,
) -> None:
    manifest_meta = _load_manifest_meta(folder, manifest_path)
    files = _select_files(folder, manifest_meta, manifest_only=manifest_only)
    if not files:
        print(f"No ingestible documents (pdf/docx/xlsx/md) found in {folder}")
        return

    scope = f"department '{department}'" if department else "GLOBAL"
    mode = "manifest-only" if manifest_only else "all ingestible files"
    print(f"Ingesting {len(files)} BRAVO document(s) from {folder} ({mode}); scope: {scope} ...")
    from sqlalchemy import delete, select

    from app.database import async_session_factory
    from app.database.models import Chunk, Source, SourceDepartment
    from app.ingestion.pipeline import ingest_source

    async with async_session_factory() as db:
        dept_id = await _resolve_department(db, department) if department else None
        for f in files:
            rel = f.relative_to(folder).as_posix()
            meta = manifest_meta.get(rel, {})
            kt = str(meta.get("knowledge_type") or _knowledge_type(f.name))

            old = list(
                (await db.execute(select(Source.id).where(Source.filename == f.name))).scalars().all()
            )
            for sid in old:
                await db.execute(delete(Chunk).where(Chunk.source_id == sid))
                await db.execute(delete(SourceDepartment).where(SourceDepartment.source_id == sid))
                await db.execute(delete(Source).where(Source.id == sid))
            if old:
                await db.commit()

            src = Source(filename=f.name, knowledge_type=kt, status="pending")
            db.add(src)
            await db.flush()
            if dept_id is not None:
                db.add(SourceDepartment(source_id=src.id, department_id=dept_id))
                await db.flush()
            try:
                n = await ingest_source(
                    db, src.id, str(f), source_extra=source_extra(meta, f, folder),
                    trusted_knowledge_type=kt,
                )
                print(f"  ok {f.name}: {n} chunks [{kt}]")
            except Exception as exc:  # noqa: BLE001
                src.status = "failed"
                await db.commit()
                print(f"  error {f.name}: {exc}")
    print("Done.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Ingest BRAVO knowledge corpus.")
    ap.add_argument("folder", nargs="?", default=str(DEFAULT_DIR), help="Document folder")
    ap.add_argument(
        "--department",
        "-d",
        default=None,
        help="Scope import to one existing department. Empty means GLOBAL shared corpus.",
    )
    ap.add_argument(
        "--manifest",
        default=str(DEFAULT_MANIFEST),
        help="YAML manifest with corpus metadata.",
    )
    ap.add_argument(
        "--allow-unmanifested",
        action="store_true",
        help="Allow importing files outside the manifest. Do not use for shared BRAVO corpus.",
    )
    args = ap.parse_args()
    asyncio.run(
        main(
            Path(args.folder),
            args.department,
            Path(args.manifest),
            manifest_only=not args.allow_unmanifested,
        )
    )
