"""RAG retrieval — RLS-on-vector + hybrid (BM25 + vector) + rerank (findings/J).

Order of operations (all proven highest-ROI in findings/J):
  1. RLS-on-vector: scope predicate in the SQL query (NOT post-retrieval) — 0% leak.
  2. Hybrid: vector (semantic) + BM25 (lexical — catches doc codes/numbers) fused by RRF.
  3. Rerank: cross-encoder (ViRanker) on the fused candidates, top-150 -> top-20.
Every returned chunk carries provenance for citation (page/sheet/cell).
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Iterable

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Chunk
from app.rag.bravo_intent import boost_for_bravo_intent
from app.rag.filters import RetrievalFilters
from app.rag.kb_lifecycle import apply_version_policy
from app.rag import rerank as _rerank
from app.rag.embedding import embed_one
from app.security.rls import Identity, chunk_scope_filter

# Postgres FTS config — 'simple' tokenizes on whitespace (works for Vietnamese syllables
# and, crucially, exact doc codes/numbers that dense embeddings dilute — findings/J).
_FTS = "simple"

_log = logging.getLogger("bravo.rag")


def _record_zero_hit() -> None:
    """F9: đẩy counter zero-hit (best-effort; observability là tuỳ chọn)."""
    try:
        from app.observability import record_zero_hit
        record_zero_hit()
    except Exception:
        pass


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


def _clean_values(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(v.strip() for v in values if v and v.strip()))


def _apply_metadata_filters(stmt, filters: RetrievalFilters | None):
    """Apply manifest metadata filters to a Chunk statement without weakening RLS."""
    if not filters or not filters.active:
        return stmt
    source_types = _clean_values(filters.source_types)
    modules = _clean_values(filters.modules)
    stages = _clean_values(filters.lifecycle_stages)
    if source_types:
        stmt = stmt.where(Chunk.extra["source_type"].astext.in_(source_types))
    if modules:
        stmt = stmt.where(Chunk.extra["module"].astext.in_(modules))
    if stages:
        stmt = stmt.where(Chunk.extra["lifecycle_stage"].astext.in_(stages))
    return stmt


async def vector_search(db: AsyncSession, identity: Identity, query: str,
                        k: int = 150, min_score: float = 0.0,
                        filters: RetrievalFilters | None = None) -> list[Retrieved]:
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
    stmt = _apply_metadata_filters(stmt, filters)
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
                         k: int = 150,
                         filters: RetrievalFilters | None = None) -> list[Retrieved]:
    """Scope-filtered lexical search via Postgres full-text search (BM25-like).

    Catches exact terms/codes/numbers (e.g. số chứng từ, mã tài khoản) that dense
    embeddings miss — RLS enforced IN the query, same as vector_search.
    """
    # unaccent CẢ HAI phía (migration 0008): người dùng VN gõ không dấu rất phổ biến
    # ("cach len bao cao can doi phat sinh") — so khớp thô trượt hết nội dung có dấu ->
    # retrieval nhiễu -> abstain/clarify sai. Câu CÓ dấu không đổi hành vi (2 phía cùng
    # bỏ dấu); nhập nhằng đồng-tự-khác-dấu (bán/bàn) đã có dense + rerank phân xử qua RRF.
    tsv = func.to_tsvector(_FTS, func.unaccent(Chunk.content))
    tsq = func.plainto_tsquery(_FTS, func.unaccent(query))
    stmt = (
        select(Chunk, func.ts_rank(tsv, tsq).label("rank"))
        .where(chunk_scope_filter(identity, "read"))  # <-- RLS
        .where(tsv.op("@@")(tsq))
        .order_by(func.ts_rank(tsv, tsq).desc())
        .limit(k)
    )
    stmt = _apply_metadata_filters(stmt, filters)
    rows = list((await db.execute(stmt)).all())

    # OR-fallback (council 2026-07-12 #2): plainto = AND-toàn-bộ-từ + 'simple' không có
    # stopword tiếng Việt -> câu hỏi tự nhiên dài ("cách nhập phiếu nhập mua công nợ kèm
    # hóa đơn và hạn thanh toán") gần như chắc chắn 0 dòng -> hybrid thoái hoá dense-only.
    # Fallback theo CẶP ÂM TIẾT liền kề ("cân <-> đối") + ts_rank_cd: tiếng Việt từ = cụm
    # âm tiết, OR âm tiết rời quá nhiễu (đo: chunk đúng rớt khỏi top-150; bigram -> #19).
    # Kết quả AND đứng trước, OR bổ sung phía sau (RRF dùng thứ tự).
    if len(rows) < 3:
        words = [w for w in dict.fromkeys(
            w.lower() for w in re.findall(r"\w+", query, re.UNICODE))
            if len(w) >= 2][:12]
        terms = ([f"({a} <-> {b})" for a, b in zip(words, words[1:], strict=False)]
                 if len(words) >= 2 else words)
        if terms:
            tsq_or = func.to_tsquery(_FTS, func.unaccent(" | ".join(terms)))
            rank_or = func.ts_rank_cd(tsv, tsq_or)
            stmt_or = (
                select(Chunk, rank_or.label("rank"))
                .where(chunk_scope_filter(identity, "read"))  # <-- RLS
                .where(tsv.op("@@")(tsq_or))
                .order_by(rank_or.desc())
                .limit(k)
            )
            stmt_or = _apply_metadata_filters(stmt_or, filters)
            seen = {c.id for c, _ in rows}
            rows.extend((c, r) for c, r in (await db.execute(stmt_or)).all()
                        if c.id not in seen)
            rows = rows[:k]

    return [
        Retrieved(
            chunk_id=str(c.id), content=c.content, source_id=str(c.source_id),
            page_number=c.page_number, sheet_name=c.sheet_name, cell_range=c.cell_range,
            score=float(rank), extra=c.extra or {},
            is_sensitive=bool((c.extra or {}).get("is_sensitive", True)),
        )
        for c, rank in rows
    ]


async def expand_sections(db: AsyncSession, identity: Identity, hits: list[Retrieved],
                          *, top: int = 6, token_cap: int = 2000) -> list[Retrieved]:
    """Q6 parent-document expansion: replace each of the top finalist chunks with its FULL
    section — the sibling chunks sharing the same (source_id, heading_path) — concatenated up
    to `token_cap`. Long procedures cut at ~900 tokens are then answered whole. RLS is enforced
    on the sibling query. Hits sharing a section are de-duplicated (expanded once)."""
    import uuid as _uuid

    from app.config import get_settings
    seen_sections: set[tuple[str, str]] = set()
    out: list[Retrieved] = []
    _ = get_settings()
    for i, h in enumerate(hits):
        hp = getattr(h, "heading_path", None) or (h.extra or {}).get("heading_path")
        if i >= top or not hp or not h.source_id:
            out.append(h)
            continue
        key = (h.source_id, hp)
        if key in seen_sections:
            continue                      # section already emitted via an earlier finalist
        seen_sections.add(key)
        try:
            rows = (await db.execute(
                select(Chunk).where(
                    chunk_scope_filter(identity, "read"),
                    Chunk.source_id == _uuid.UUID(h.source_id),
                    Chunk.heading_path == hp,
                ).order_by(Chunk.page_number.nullslast(), Chunk.id)
            )).scalars().all()
        except Exception:
            out.append(h)
            continue
        if len(rows) <= 1:
            out.append(h)
            continue
        merged, budget = [], token_cap
        for c in rows:
            piece = c.content or ""
            approx = len(piece) // 4          # cheap token estimate
            if approx > budget and merged:
                break
            merged.append(piece)
            budget -= approx
        h.content = "\n".join(merged)
        out.append(h)
    return out


async def _maybe_expand(db: AsyncSession, identity: Identity,
                        hits: list[Retrieved]) -> list[Retrieved]:
    from app.config import get_settings
    s = get_settings()
    if not s.retrieval_expand_sections or not hits:
        return hits
    return await expand_sections(db, identity, hits, top=s.retrieval_expand_top,
                                 token_cap=s.retrieval_section_token_cap)


async def retrieve(db: AsyncSession, identity: Identity, query: str, top_n: int = 20,
                   candidate_k: int = 150, use_rerank: bool | None = None,
                   min_score: float | None = None,
                   filters: RetrievalFilters | None = None) -> list[Retrieved]:
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
        min_score = _s.resolved_min_score()

    # Viết tắt nghiệp vụ VN ("khai báo CCDC") -> chèn cụm đầy đủ trước khi retrieve
    # (tất định — council 2026-07-12 #6).
    from app.rag.vn_terms import expand_abbreviations
    query = expand_abbreviations(query)

    dense = await vector_search(db, identity, query, k=candidate_k, min_score=min_score,
                                filters=filters)
    lexical = await lexical_search(db, identity, query, k=candidate_k, filters=filters)
    # intent boost -> version policy (current version wins over superseded/deprecated).
    fused = apply_version_policy(boost_for_bravo_intent(query, rrf_fuse(dense, lexical)))
    if not fused:
        # Q10 corpus-ops: a zero-hit query is a corpus gap signal — log it so the weekly
        # ritual (docs/CORPUS-OPS.md) can turn recurring gaps into acquisition work.
        _log.info("retrieval.gap zero_hit query=%r", query[:160])
        _record_zero_hit()   # F9: đếm để corpus-ops thấy lỗ (không còn chỉ nằm trong log text)
        return []   # không đủ căn cứ -> để loop trả "không tìm thấy" (zero-hallucination)

    if not use_rerank:
        return await _maybe_expand(db, identity, fused[:top_n])

    from app.config import get_settings
    _rs = get_settings()
    provider = _rs.rerank_provider

    if provider == "llm":
        # Listwise rerank top candidates via the cloud chat model (demo).
        pool = fused[:getattr(_rs, "rerank_pool_size", 80)]   # pool rộng -> chunk-đúng-rank-thấp vào diện rerank
        # Do not send mixed or unknown-sensitivity candidate sets to cloud rerank.
        if any(r.is_sensitive for r in pool):
            # Skip ÂM THẦM là bẫy vận hành (council #1): 1 chunk legacy thiếu flag làm mất
            # rerank cho cả câu hỏi mà không ai biết -> log để lộ ra ở /metrics-log.
            _log.warning("llm_rerank skipped: %d/%d candidates sensitive/unknown",
                         sum(1 for r in pool if r.is_sensitive), len(pool))
            return await _maybe_expand(db, identity, pool[:top_n])
        order = await _rerank.llm_rerank(
            query, [r.content for r in pool], top_n, sensitive=False,
        )
        return await _maybe_expand(db, identity, [pool[i] for i in order][:top_n])

    # Cross-encoder rerank (ViRanker, local) over the fused candidates.
    scores = _rerank.rerank(query, [r.content for r in fused])
    for r, s in zip(fused, scores, strict=True):
        r.score = s
    fused = apply_version_policy(boost_for_bravo_intent(query, fused))
    return await _maybe_expand(db, identity, fused[:top_n])


async def retrieve_multi(db: AsyncSession, identity: Identity, queries: list[str],
                         top_n: int = 20, candidate_k: int = 150,
                         use_rerank: bool | None = None,
                         min_score: float | None = None,
                         filters: RetrievalFilters | None = None) -> list[Retrieved]:
    """Multi-query hybrid retrieval (Q2): run each query's dense+lexical branches, RRF-fuse
    ALL branches together, then boost/version/rerank ONCE against the primary query.

    A single query degrades to `retrieve()`. Multi-intent questions ("nhập phiếu mua VÀ kê
    khai thuế") no longer get one embedding — each intent contributes candidates. RLS is
    enforced in every branch (chunk_scope_filter), so scope is preserved across the union.
    """
    qs = [q for q in dict.fromkeys(q.strip() for q in queries) if q.strip()]
    if len(qs) <= 1:
        return await retrieve(db, identity, qs[0] if qs else "", top_n=top_n,
                              candidate_k=candidate_k, use_rerank=use_rerank, min_score=min_score,
                              filters=filters)

    from app.config import get_settings
    from app.rag.vn_terms import expand_abbreviations
    _s = get_settings()
    if use_rerank is None:
        use_rerank = _s.rerank_enabled
    if min_score is None:
        min_score = _s.resolved_min_score()
    primary = expand_abbreviations(qs[0])

    branches: list[list[Retrieved]] = []
    for q in qs:
        qx = expand_abbreviations(q)
        branches.append(await vector_search(
            db, identity, qx, k=candidate_k, min_score=min_score, filters=filters))
        branches.append(await lexical_search(db, identity, qx, k=candidate_k, filters=filters))
    fused = apply_version_policy(boost_for_bravo_intent(primary, rrf_fuse(*branches)))
    if not fused:
        _log.info("retrieval.gap zero_hit (multi) primary=%r", primary[:160])
        _record_zero_hit()   # F9
        return []
    if not use_rerank:
        return await _maybe_expand(db, identity, fused[:top_n])

    provider = _s.rerank_provider
    if provider == "llm":
        pool = fused[:40]
        if any(r.is_sensitive for r in pool):
            _log.warning("llm_rerank skipped (multi): %d/%d sensitive",
                         sum(1 for r in pool if r.is_sensitive), len(pool))
            return await _maybe_expand(db, identity, pool[:top_n])
        order = await _rerank.llm_rerank(primary, [r.content for r in pool], top_n, sensitive=False)
        return await _maybe_expand(db, identity, [pool[i] for i in order][:top_n])

    scores = _rerank.rerank(primary, [r.content for r in fused])
    for r, s in zip(fused, scores, strict=True):
        r.score = s
    fused = apply_version_policy(boost_for_bravo_intent(primary, fused))
    return await _maybe_expand(db, identity, fused[:top_n])
