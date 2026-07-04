"""Knowledge Graph (bản đồ tri thức) — GROUNDED, RLS-scoped, KHÔNG LLM.

nodes = các Source người dùng được phép đọc (RLS ở tầng SQL, `source_scope_filter`), gom màu
theo `knowledge_type`, kích cỡ = số chunk.
edges = tương đồng ngữ nghĩa giữa 2 nguồn = cosine giữa CENTROID (avg embedding) của mỗi nguồn
(pgvector `avg` + `<=>`, tính hết trong SQL — rẻ, 31×31). Chunk lọc RLS ở CẢ HAI vế (Bất biến
#1). Cạnh là tương đồng embedding có thật, không phải LLM phịa (zero-hallucination).
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.database.models import Chunk, Source
from app.security.auth import require_permission
from app.security.rls import Identity, source_scope_filter

router = APIRouter()

# Ngưỡng cạnh tối thiểu ở BE (trả các cạnh có ý nghĩa); FE có thanh trượt lọc tiếp (mặc định
# ~0.8) để người xem điều chỉnh hiện nhiều/ít liên kết.
SIM_MIN = 0.6
_GENERIC_LABEL = "BRAVO 10 User Guide"


def _node_label(knowledge_type: str | None, filename: str | None) -> str:
    """Nhãn rõ ràng: chương giữ 'Chương N - X'; tài liệu chung/kỹ thuật -> tên file cho phân biệt."""
    if knowledge_type and knowledge_type != _GENERIC_LABEL:
        return knowledge_type
    stem = Path(filename or "tài liệu").stem
    return stem.replace("NB_", "").replace("_", " ").strip() or (knowledge_type or "tài liệu")


def _node_group(knowledge_type: str | None, filename: str | None) -> str:
    """Nhóm tô màu: Cẩm nang chương / Tài liệu kỹ thuật / BI / khác."""
    fn = (filename or "").lower()
    if "chapter" in fn:
        return "Cẩm nang nghiệp vụ"
    if "tailieukythuat" in fn:
        return "Tài liệu kỹ thuật"
    if "bi_guidelines" in fn or "bi " in (knowledge_type or "").lower():
        return "BI / Báo cáo"
    return "Khác"


class GraphNode(BaseModel):
    id: str
    label: str
    group: str | None = None      # knowledge_type -> tô màu
    size: int = 1                 # số chunk


class GraphEdge(BaseModel):
    source: str
    target: str
    weight: float                 # cosine similarity 0..1


class GraphOut(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


@router.get("/graph", response_model=GraphOut)
async def knowledge_graph(identity: Identity = Depends(require_permission("doc:read")),
                          db: AsyncSession = Depends(get_db)) -> GraphOut:
    # --- nodes: Source RLS-scoped + số chunk (RLS-scoped) ---
    src_rows = (await db.execute(
        select(Source.id, Source.filename, Source.knowledge_type)
        .where(source_scope_filter(identity, "read")).order_by(Source.knowledge_type)
    )).all()
    counts = dict((await db.execute(
        select(Chunk.source_id, func.count()).where(
            Chunk.source_id.isnot(None)).group_by(Chunk.source_id)
    )).all())
    nodes = [
        GraphNode(id=str(sid), label=_node_label(kt, fn), group=_node_group(kt, fn),
                  size=int(counts.get(sid, 0)))
        for sid, fn, kt in src_rows
    ]
    allowed = {n.id for n in nodes}

    # --- edges: cosine giữa centroid nguồn (avg embedding), tính trong SQL, RLS chunk 2 vế ---
    is_all = bool(identity.is_admin) or ("doc:read:all" in identity.permissions)
    depts = [str(d) for d in (identity.department_ids or [])]
    sql = text(
        """
        WITH scoped AS (
            SELECT source_id, embedding FROM chunks
            WHERE :is_all
               OR cardinality(department_ids) = 0
               OR (:has_depts AND department_ids && CAST(:depts AS uuid[]))
        ),
        cent AS (
            SELECT source_id, avg(embedding) AS c
            FROM scoped GROUP BY source_id
        )
        SELECT a.source_id::text AS a, b.source_id::text AS b,
               (1 - (a.c <=> b.c))::float AS sim
        FROM cent a JOIN cent b ON a.source_id < b.source_id
        WHERE (a.c <=> b.c) <= :maxdist
        ORDER BY sim DESC
        """
    ).bindparams(is_all=is_all, has_depts=bool(depts), depts=depts, maxdist=1.0 - SIM_MIN)
    edge_rows = (await db.execute(sql)).all()
    edges = [
        GraphEdge(source=a, target=b, weight=round(float(sim), 3))
        for a, b, sim in edge_rows
        if a in allowed and b in allowed
    ]
    return GraphOut(nodes=nodes, edges=edges)
