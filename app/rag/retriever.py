"""RAG retrieval — RLS-on-vector + hybrid (BM25 + vector) + rerank (findings/J).

Order of operations (all proven highest-ROI in findings/J):
  1. RLS-on-vector: scope predicate in the SQL query (NOT post-retrieval) — 0% leak.
  2. Hybrid: vector (semantic) + BM25 (lexical — catches doc codes/numbers) fused by RRF.
  3. Rerank: cross-encoder (ViRanker) on the fused candidates, top-150 -> top-20.
Every returned chunk carries provenance for citation (page/sheet/cell).
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Chunk
from app.rag import rerank as _rerank
from app.rag.embedding import embed_one
from app.security.rls import Identity, chunk_scope_filter

# Postgres FTS config — 'simple' tokenizes on whitespace (works for Vietnamese syllables
# and, crucially, exact doc codes/numbers that dense embeddings dilute — findings/J).
_FTS = "simple"


@dataclass
class Retrieved:
    chunk_id: str
    content: str
    source_id: str
    page_number: int | None
    sheet_name: str | None
    cell_range: str | None
    score: float

    def citation(self) -> str:
        loc = []
        if self.page_number is not None:
            loc.append(f"trang {self.page_number}")
        if self.sheet_name:
            loc.append(f"sheet {self.sheet_name}")
        if self.cell_range:
            loc.append(f"ô {self.cell_range}")
        return f"(nguồn: {self.source_id}{', ' + ', '.join(loc) if loc else ''})"


async def vector_search(db: AsyncSession, identity: Identity, query: str,
                        k: int = 150) -> list[Retrieved]:
    """Scope-filtered dense vector search (RLS enforced IN the query)."""
    qvec = embed_one(query)
    stmt = (
        select(Chunk, Chunk.embedding.cosine_distance(qvec).label("dist"))
        .where(chunk_scope_filter(identity, "read"))  # <-- RLS-on-vector
        .order_by("dist")
        .limit(k)
    )
    rows = (await db.execute(stmt)).all()
    return [
        Retrieved(
            chunk_id=str(c.id), content=c.content, source_id=str(c.source_id),
            page_number=c.page_number, sheet_name=c.sheet_name, cell_range=c.cell_range,
            score=1.0 - float(dist),
        )
        for c, dist in rows
    ]


def rrf_fuse(*ranked_lists: list[Retrieved], k: int = 60) -> list[Retrieved]:
    """Reciprocal Rank Fusion of multiple ranked candidate lists (hybrid search)."""
    scores: dict[str, float] = {}
    objs: dict[str, Retrieved] = {}
    for lst in ranked_lists:
        for rank, r in enumerate(lst):
            scores[r.chunk_id] = scores.get(r.chunk_id, 0.0) + 1.0 / (k + rank + 1)
            objs[r.chunk_id] = r
    fused = sorted(objs.values(), key=lambda r: scores[r.chunk_id], reverse=True)
    for r in fused:
        r.score = scores[r.chunk_id]
    return fused


async def lexical_search(db: AsyncSession, identity: Identity, query: str,
                         k: int = 150) -> list[Retrieved]:
    """Scope-filtered lexical search via Postgres full-text search (BM25-like).

    Catches exact terms/codes/numbers (e.g. số chứng từ, mã tài khoản) that dense
    embeddings miss — RLS enforced IN the query, same as vector_search.
    """
    tsv = func.to_tsvector(_FTS, Chunk.content)
    tsq = func.plainto_tsquery(_FTS, query)
    stmt = (
        select(Chunk, func.ts_rank(tsv, tsq).label("rank"))
        .where(chunk_scope_filter(identity, "read"))  # <-- RLS
        .where(tsv.op("@@")(tsq))
        .order_by(func.ts_rank(tsv, tsq).desc())
        .limit(k)
    )
    rows = (await db.execute(stmt)).all()
    return [
        Retrieved(
            chunk_id=str(c.id), content=c.content, source_id=str(c.source_id),
            page_number=c.page_number, sheet_name=c.sheet_name, cell_range=c.cell_range,
            score=float(rank),
        )
        for c, rank in rows
    ]


async def retrieve(db: AsyncSession, identity: Identity, query: str, top_n: int = 20,
                   candidate_k: int = 150, use_rerank: bool | None = None) -> list[Retrieved]:
    """Full hybrid pipeline (findings/J): vector + lexical -> RRF -> cross-encoder rerank.

    All branches enforce RLS in-query. Rerank defaults to settings.rerank_enabled
    (OFF in the cloud demo since ViRanker is a local model).
    """
    if use_rerank is None:
        from app.config import get_settings
        use_rerank = get_settings().rerank_enabled

    dense = await vector_search(db, identity, query, k=candidate_k)
    lexical = await lexical_search(db, identity, query, k=candidate_k)
    fused = rrf_fuse(dense, lexical)

    if not use_rerank or not fused:
        return fused[:top_n]

    # Cross-encoder rerank over the fused candidates (top-N kept).
    scores = _rerank.rerank(query, [r.content for r in fused])
    for r, s in zip(fused, scores, strict=True):
        r.score = s
    fused.sort(key=lambda r: r.score, reverse=True)
    return fused[:top_n]
