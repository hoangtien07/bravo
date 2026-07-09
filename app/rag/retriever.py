"""RAG retrieval — RLS-on-vector + hybrid (BM25 + vector) + rerank (findings/J).

Order of operations (all proven highest-ROI in findings/J):
  1. RLS-on-vector: scope predicate in the SQL query (NOT post-retrieval) — 0% leak.
  2. Hybrid: vector (semantic) + BM25 (lexical — catches doc codes/numbers) fused by RRF.
  3. Rerank: cross-encoder (ViRanker) on the fused candidates, top-150 -> top-20.
Every returned chunk carries provenance for citation (page/sheet/cell).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Chunk
from app.rag.bravo_intent import boost_for_bravo_intent
from app.rag.kb_lifecycle import apply_version_policy
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
    extra: dict = field(default_factory=dict)
    # Missing legacy metadata is sensitive by default for provider egress.
    is_sensitive: bool = True

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
                        k: int = 150, min_score: float = 0.0) -> list[Retrieved]:
    """Scope-filtered dense vector search (RLS enforced IN the query).

    `min_score`: bỏ chunk có cosine-sim < ngưỡng (giảm nhiễu ngữ nghĩa). 0 = không lọc.
    """
    qvec = embed_one(query)
    stmt = (
        select(Chunk, Chunk.embedding.cosine_distance(qvec).label("dist"))
        .where(chunk_scope_filter(identity, "read"))  # <-- RLS-on-vector
        .order_by("dist")
        .limit(k)
    )
    rows = (await db.execute(stmt)).all()
    out = [
        Retrieved(
            chunk_id=str(c.id), content=c.content, source_id=str(c.source_id),
            page_number=c.page_number, sheet_name=c.sheet_name, cell_range=c.cell_range,
            score=1.0 - float(dist), extra=c.extra or {},
            is_sensitive=bool((c.extra or {}).get("is_sensitive", True)),
        )
        for c, dist in rows
    ]
    return [r for r in out if r.score >= min_score] if min_score > 0 else out


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
            score=float(rank), extra=c.extra or {},
            is_sensitive=bool((c.extra or {}).get("is_sensitive", True)),
        )
        for c, rank in rows
    ]


async def retrieve(db: AsyncSession, identity: Identity, query: str, top_n: int = 20,
                   candidate_k: int = 150, use_rerank: bool | None = None,
                   min_score: float | None = None) -> list[Retrieved]:
    """Full hybrid pipeline (findings/J): vector + lexical -> RRF -> cross-encoder rerank.

    All branches enforce RLS in-query. Rerank defaults to settings.rerank_enabled
    (OFF in the cloud demo since ViRanker is a local model). `min_score` (mặc định theo
    settings.retrieval_min_score) lọc nhiễu dense; rỗng -> [] -> agent trả "không tìm thấy".
    """
    from app.config import get_settings
    _s = get_settings()
    if use_rerank is None:
        use_rerank = _s.rerank_enabled
    if min_score is None:
        min_score = _s.retrieval_min_score

    dense = await vector_search(db, identity, query, k=candidate_k, min_score=min_score)
    lexical = await lexical_search(db, identity, query, k=candidate_k)
    # intent boost -> version policy (current version wins over superseded/deprecated).
    fused = apply_version_policy(boost_for_bravo_intent(query, rrf_fuse(dense, lexical)))
    if not fused:
        return []   # không đủ căn cứ -> để loop trả "không tìm thấy" (zero-hallucination)

    if not use_rerank:
        return fused[:top_n]

    from app.config import get_settings
    provider = get_settings().rerank_provider

    if provider == "llm":
        # Listwise rerank top candidates via the cloud chat model (demo).
        pool = fused[:40]   # pool rộng hơn -> tăng recall (chương đúng lọt vào diện rerank)
        # Do not send mixed or unknown-sensitivity candidate sets to cloud rerank.
        if any(r.is_sensitive for r in pool):
            return pool[:top_n]
        order = await _rerank.llm_rerank(
            query, [r.content for r in pool], top_n, sensitive=False,
        )
        return [pool[i] for i in order][:top_n]

    # Cross-encoder rerank (ViRanker, local) over the fused candidates.
    scores = _rerank.rerank(query, [r.content for r in fused])
    for r, s in zip(fused, scores, strict=True):
        r.score = s
    fused = apply_version_policy(boost_for_bravo_intent(query, fused))
    return fused[:top_n]
