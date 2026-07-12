"""MCP server (scoped-by-token) — lets Claude Desktop/Code query the KB in-scope.

Rewritten from arkon PATTERNS (ADR-0008). The bearer token resolves to an Identity
(HMAC-hashed lookup); every tool runs retrieval through RLS so a token only ever
returns data its owner may see. Out-of-scope is hinted by count only (SECURITY-RLS §4).

NOTE: FastMCP's auth/context API is version-sensitive — `_token_from_context` is the
single integration point to verify against the pinned `mcp` package.
"""
from mcp.server.fastmcp import Context, FastMCP

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


async def list_pending_drafts(token: str) -> str:
    """T6: pending drafts in the token's scope (RLS-in-SQL) — symmetric with the in-process tool."""
    async with async_session_factory() as db:
        identity = await resolve_mcp_identity(token, db)
        if identity is None:
            return "Lỗi: token không hợp lệ hoặc đã bị thu hồi."
        from app.erp import draft_queue
        rows = await draft_queue.list_pending(db, identity)
        if not rows:
            return "Không có bút toán nháp nào đang chờ duyệt."
        return "\n".join(
            f"- Nháp {d.id} ({getattr(d, 'kind', '?')}, trạng thái {getattr(d, 'status', '?')})"
            for d in rows[:50])


def create_mcp_server():
    """Build the FastMCP server exposing scoped KB tools."""
    mcp = FastMCP("bravo")

    def _token_from_context(ctx: Context) -> str | None:
        """Trích bearer token từ MCP request context (streamable-HTTP).

        FastMCP đặt request ASGI tại ctx.request_context.request; header là Starlette Headers
        (case-insensitive). Nhiều lớp getattr để bền với thay đổi phiên bản `mcp` (đã pin >=1.2).
        """
        req = getattr(ctx, "request_context", None)
        request = getattr(req, "request", None)
        headers = getattr(request, "headers", None)
        auth = ""
        if headers is not None:
            # Starlette Headers hỗ trợ .get() case-insensitive; fallback dict.
            try:
                auth = headers.get("authorization") or ""
            except Exception:
                auth = ""
        return auth.removeprefix("Bearer ").removeprefix("bearer ").strip() or None

    @mcp.tool()
    async def search_kb(query: str, ctx: Context) -> str:
        """Tra cứu tri thức nội bộ BRAVO trong phạm vi quyền của token."""
        token = _token_from_context(ctx)
        if not token:
            return "Lỗi: thiếu token xác thực."
        return await kb_search(token, query)

    @mcp.tool()
    async def list_drafts(ctx: Context) -> str:
        """Liệt kê bút toán nháp đang chờ duyệt trong phạm vi quyền của token."""
        token = _token_from_context(ctx)
        if not token:
            return "Lỗi: thiếu token xác thực."
        return await list_pending_drafts(token)

    return mcp
