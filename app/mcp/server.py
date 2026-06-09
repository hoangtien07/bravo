"""MCP server (scoped-by-token) — lets Claude Desktop/Code query the KB in-scope.

Rewritten from arkon PATTERNS (ADR-0008). The bearer token resolves to an Identity
(HMAC-hashed lookup); every tool runs retrieval through RLS so a token only ever
returns data its owner may see. Out-of-scope is hinted by count only (SECURITY-RLS §4).

NOTE: FastMCP's auth/context API is version-sensitive — `_token_from_context` is the
single integration point to verify against the pinned `mcp` package.
"""
from __future__ import annotations

from app.database import async_session_factory
from app.rag import retriever
from app.security.auth import resolve_mcp_identity


async def kb_search(token: str, query: str, top_n: int = 8) -> str:
    """Core scoped search used by the MCP tool. Returns a cited, plain-text answer body."""
    async with async_session_factory() as db:
        identity = await resolve_mcp_identity(token, db)
        if identity is None:
            return "Lỗi: token không hợp lệ hoặc đã bị thu hồi."
        results = await retriever.retrieve(db, identity, query, top_n=top_n)
        if not results:
            return "Không tìm thấy thông tin trong tài liệu bạn được phép truy cập."
        lines = [f"[{i+1}] {r.content}\n  {r.citation()}" for i, r in enumerate(results)]
        return "\n\n".join(lines)


def create_mcp_server():
    """Build the FastMCP server exposing scoped KB tools."""
    from mcp.server.fastmcp import Context, FastMCP  # lazy import

    mcp = FastMCP("bravo")

    def _token_from_context(ctx: Context) -> str | None:
        # TODO(verify): extract Authorization bearer from the MCP request context.
        req = getattr(ctx, "request_context", None)
        headers = getattr(getattr(req, "request", None), "headers", {}) or {}
        auth = headers.get("authorization") or headers.get("Authorization") or ""
        return auth.removeprefix("Bearer ").strip() or None

    @mcp.tool()
    async def search_kb(query: str, ctx: Context) -> str:
        """Tra cứu tri thức nội bộ BRAVO trong phạm vi quyền của token."""
        token = _token_from_context(ctx)
        if not token:
            return "Lỗi: thiếu token xác thực."
        return await kb_search(token, query)

    return mcp
