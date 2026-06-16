"""AP money-engine endpoint: tải hoá đơn điện tử XML -> bút toán nháp (Use-case A).

Đường deterministic, KHÔNG cần ERP: thả 1 hoá đơn -> 1 bút toán nháp cân Nợ=Có, map TK
TT99, có trích dẫn tới dòng hoá đơn -> vào hàng đợi duyệt (maker-checker). Yêu cầu quyền
`draft:create` (ghi = nháp, invariant #2).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.accounting.ap_service import create_invoice_draft
from app.database import get_db
from app.security.auth import require_permission
from app.security.rls import Identity

router = APIRouter()


@router.post("/invoices/draft", status_code=status.HTTP_201_CREATED)
async def invoice_to_draft(
    file: UploadFile = File(...),
    identity: Identity = Depends(require_permission("draft:create")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    xml = await file.read()
    try:
        draft, je = await create_invoice_draft(db, identity, xml, raw_xml_path=file.filename)
    except Exception as exc:  # parse/build lỗi -> 400 rõ ràng (không 500 trần)
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Không xử lý được hoá đơn: {exc}") from exc
    return {
        "draft_id": str(draft.id),
        "kind": draft.kind,
        "status": draft.status,
        "needs_review": je.needs_review,
        "validation_flags": je.validation_flags,
        "journal": je.model_dump(mode="json"),
    }
