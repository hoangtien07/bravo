"""Ingest the BRAVO 10 user-guide corpus (the MVP internal knowledge base).

Each source -> a GLOBAL Source (company-wide technical knowledge — no departments, so
RLS lets everyone read; none of this corpus is sensitive). knowledge_type is derived
from the filename, then the file is parsed (pypdf for text-PDF, Docling for table-PDF /
docx / xlsx) + chunked + embedded into pgvector.

Corpus (WP-A, Demo A) under `file_system/`:
  - UserGuide_B10_TV_PDF/*.pdf  : the 19 Vietnamese chapter guides (pypdf fast-path)
  - UserGuide_B10_Basic rules.pdf, BRAVO_BI_Guidelines_Full.pdf : extra PDFs
  - Tài liệu bravo 10 cho khối kỹ thuật.docx : DOCX (needs Docling — pypdf can't read it)

Run (after env up + alembic upgrade): `python -m scripts.ingest_userguide [folder]`
Default folder: ./file_system  (recursively picks up the chapter subfolder).
"""
from __future__ import annotations

import argparse
import asyncio
import re
from pathlib import Path

from sqlalchemy import delete, select

from app.database import async_session_factory
from app.database.models import Chunk, Department, Source, SourceDepartment
from app.ingestion.pipeline import ingest_source

DEFAULT_DIR = Path("file_system")
_SUFFIXES = {".pdf", ".docx", ".xlsx", ".xlsm"}


def _knowledge_type(filename: str) -> str:
    """Derive a human label from the filename.

    'NB_UserGuide_B10_Chapter17_Accounting.pdf' -> 'Chương 17 - Accounting'; the extra
    file_system docs get descriptive labels.
    """
    m = re.search(r"Chapter(\d+)_(\w+)", filename, re.IGNORECASE)
    if m:
        return f"Chương {int(m.group(1))} - {m.group(2)}"
    stem = Path(filename).stem
    if "BI_Guidelines" in filename:
        return "BRAVO BI Guidelines"
    if "Basic rules" in filename:
        return "BRAVO 10 - Basic rules"
    if filename.lower().endswith(".docx"):
        return f"Tài liệu kỹ thuật - {stem}"
    return "BRAVO 10 User Guide"


def _collect(folder: Path) -> list[Path]:
    """All ingestible files under `folder` (recursive), sorted for stable order."""
    files = [p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in _SUFFIXES]
    return sorted(files, key=lambda p: str(p).lower())


async def _resolve_department(db, name: str):
    """Tra Department theo tên -> id. Fail-closed: không thấy -> DỪNG (không nạp nhầm GLOBAL)."""
    did = (await db.execute(
        select(Department.id).where(Department.name == name))).scalar_one_or_none()
    if did is None:
        raise SystemExit(f"[ingest] Không tìm thấy phòng ban '{name}'. Tạo phòng ban trước "
                         f"(fail-closed — KHÔNG nạp tài liệu phòng vào phạm vi GLOBAL).")
    return did


async def main(folder: Path, department: str | None = None) -> None:
    files = _collect(folder)
    if not files:
        print(f"Không thấy tài liệu (pdf/docx/xlsx) trong {folder}")
        return
    scope = f"phòng '{department}'" if department else "GLOBAL (toàn công ty)"
    print(f"Nạp {len(files)} tài liệu BRAVO 10 từ {folder} — scope: {scope} ...")
    async with async_session_factory() as db:
        dept_id = await _resolve_department(db, department) if department else None
        for f in files:
            kt = _knowledge_type(f.name)
            # Idempotent: xoá MỌI source cùng filename (+chunks/scope) trước khi nạp lại — chạy
            # lại script KHÔNG còn nhân đôi corpus (deep-dive: bản cũ tạo Source mới mỗi lần).
            old = list((await db.execute(
                select(Source.id).where(Source.filename == f.name))).scalars().all())
            for sid in old:
                await db.execute(delete(Chunk).where(Chunk.source_id == sid))
                await db.execute(delete(SourceDepartment).where(SourceDepartment.source_id == sid))
                await db.execute(delete(Source).where(Source.id == sid))
            if old:
                await db.commit()
            src = Source(filename=f.name, knowledge_type=kt, status="pending")
            db.add(src)
            await db.flush()
            # Scope RLS: có --department -> SourceDepartment (pipeline tự lan department_ids xuống
            # chunk). Không có -> GLOBAL (chỉ dùng cho corpus công khai như user-guide).
            if dept_id is not None:
                db.add(SourceDepartment(source_id=src.id, department_id=dept_id))
                await db.flush()
            try:
                n = await ingest_source(db, src.id, str(f))
                print(f"  ✓ {f.name}: {n} chunks  [{kt}]")
            except Exception as exc:  # noqa: BLE001
                src.status = "failed"
                await db.commit()
                print(f"  ✗ {f.name}: LỖI {exc}")
    print("Xong.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Nạp corpus tri thức (GLOBAL hoặc theo phòng ban).")
    ap.add_argument("folder", nargs="?", default=str(DEFAULT_DIR), help="Thư mục tài liệu")
    ap.add_argument("--department", "-d", default=None,
                    help="Scope corpus vào 1 phòng ban (RLS). Bỏ trống = GLOBAL (chỉ cho corpus "
                         "công khai). Phòng phải tồn tại (fail-closed).")
    args = ap.parse_args()
    asyncio.run(main(Path(args.folder), args.department))
