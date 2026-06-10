"""Ingest the BRAVO 10 user-guide corpus (the MVP internal knowledge base).

Each PDF -> a global Source (company-wide technical knowledge), knowledge_type derived
from the chapter in the filename, then parsed (pypdf) + chunked + embedded into pgvector.

Run (after env up + alembic upgrade): `python -m scripts.ingest_userguide [folder]`
Default folder: ./UserGuide_B10_TV_PDF
"""
from __future__ import annotations

import asyncio
import re
import sys
from pathlib import Path

from app.database import async_session_factory
from app.database.models import Source
from app.ingestion.pipeline import ingest_source

DEFAULT_DIR = Path("UserGuide_B10_TV_PDF")


def _knowledge_type(filename: str) -> str:
    """'NB_UserGuide_B10_Chapter17_Accounting.pdf' -> 'Chương 17 - Accounting'."""
    m = re.search(r"Chapter(\d+)_(\w+)", filename, re.IGNORECASE)
    return f"Chương {int(m.group(1))} - {m.group(2)}" if m else "BRAVO 10 User Guide"


async def main(folder: Path) -> None:
    pdfs = sorted(folder.glob("*.pdf"))
    if not pdfs:
        print(f"Không thấy PDF trong {folder}")
        return
    print(f"Nạp {len(pdfs)} cẩm nang BRAVO 10 từ {folder} ...")
    async with async_session_factory() as db:
        for pdf in pdfs:
            kt = _knowledge_type(pdf.name)
            src = Source(filename=pdf.name, knowledge_type=kt, status="pending")
            db.add(src)
            await db.flush()  # scope: no departments => GLOBAL (toàn công ty đọc được)
            try:
                n = await ingest_source(db, src.id, str(pdf))
                print(f"  ✓ {pdf.name}: {n} chunks  [{kt}]")
            except Exception as exc:  # noqa: BLE001
                src.status = "failed"
                await db.commit()
                print(f"  ✗ {pdf.name}: LỖI {exc}")
    print("Xong.")


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DIR
    asyncio.run(main(target))
