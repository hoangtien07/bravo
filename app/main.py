"""FastAPI application entrypoint (modular monolith — ADR-0007)."""
from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import router as api_router
from app.config import get_settings

# SPA React đã build. `if _FRONTEND.exists()` bên dưới cho phép app vẫn boot khi chưa
# `npm run build` (dev/test/CI thuần backend) — chỉ không phục vụ trang tĩnh.
_ROOT = Path(__file__).resolve().parent.parent
_FRONTEND = _ROOT / "frontend-react" / "dist"

settings = get_settings()

# Observability (W5.1) — cấu hình ở module-level để middleware/log chạy ngay (air-gapped,
# stdlib, KHÔNG SaaS). Log JSON-ish 1 dòng/request kèm request_id + latency để điều tra sự cố.
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO),
                    format="%(asctime)s %(levelname)s %(name)s %(message)s")
_log = logging.getLogger("bravo")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: boot-guard (fail-closed nếu prod còn secret mặc định) + nạp metric catalog.
    import logging

    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
    _log = logging.getLogger("bravo.startup")
    settings.validate_boot()
    # Import data_layer kích hoạt register_catalog() (side-effect) -> REGISTRY đầy đủ lúc runtime.
    from app.data_layer.semantic import REGISTRY

    _log.info("BRAVO startup: env=%s · metric catalog=%d metric", settings.env, len(REGISTRY.ids()))
    yield
    # Shutdown


app = FastAPI(
    title="BRAVO AI Copilot",
    version="0.1.0",
    summary="Enterprise Knowledge & Financial Analytics Hub (on-prem RAG on BRAVO ERP)",
    lifespan=lifespan,
)

app.include_router(api_router, prefix="/api")

# CORS: chỉ bật khi có origin cấu hình (dev Vite :5173). Prod để rỗng -> middleware không
# thêm header cross-origin (SPA same-origin, không cần).
if settings.cors_origin_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.middleware("http")
async def request_logger(request: Request, call_next):
    """Gắn X-Request-ID + đo latency + log mỗi request (W5.1)."""
    rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    t0 = time.monotonic()
    try:
        resp = await call_next(request)
    except Exception:
        _log.exception("request_id=%s %s %s -> EXCEPTION", rid, request.method, request.url.path)
        raise
    dt = (time.monotonic() - t0) * 1000
    _log.info("request_id=%s %s %s -> %d (%.0fms)", rid, request.method,
              request.url.path, resp.status_code, dt)
    resp.headers["X-Request-ID"] = rid
    return resp


@app.get("/livez")
async def livez() -> dict[str, str]:
    """Liveness: tiến trình còn sống (KHÔNG kiểm phụ thuộc)."""
    return {"status": "alive"}


@app.get("/readyz")
async def readyz():
    """Readiness: DB ping + metric catalog đã nạp. Chưa sẵn sàng -> 503 (LB không route)."""
    from sqlalchemy import text

    from app.data_layer.semantic import REGISTRY
    from app.database import async_session_factory

    checks: dict[str, object] = {"catalog": len(REGISTRY.ids())}
    try:
        async with async_session_factory() as db:
            await db.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["db"] = f"error: {exc}"
    ready = checks["db"] == "ok" and checks["catalog"] > 0
    return JSONResponse({"ready": ready, "checks": checks}, status_code=200 if ready else 503)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.env}


# Frontend SPA: assets dưới /static; deep-link (/c/:id, /money-engine, /shared/:token) ->
# SPA-fallback trả index.html để react-router xử lý (không 404). Guard exists(): app boot
# được ngay cả khi chưa build dist (dev backend / CI).
if _FRONTEND.exists():
    app.mount("/static", StaticFiles(directory=str(_FRONTEND)), name="static")

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(str(_FRONTEND / "index.html"))

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str) -> FileResponse:
        if full_path.startswith(("api/", "static/")) or full_path in (
                "livez", "readyz", "health", "metrics", "docs", "openapi.json"):
            raise HTTPException(status_code=404)
        return FileResponse(str(_FRONTEND / "index.html"))
