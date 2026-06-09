"""FastAPI application entrypoint (modular monolith — ADR-0007)."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import router as api_router
from app.config import get_settings

_FRONTEND = Path(__file__).resolve().parent.parent / "frontend"

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: (migrations run via alembic separately). Place warm-ups here.
    yield
    # Shutdown


app = FastAPI(
    title="BRAVO AI Copilot",
    version="0.1.0",
    summary="Enterprise Knowledge & Financial Analytics Hub (on-prem RAG on BRAVO ERP)",
    lifespan=lifespan,
)

app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.env}


# Minimal frontend (static). index.html at root, assets under /static.
if _FRONTEND.exists():
    app.mount("/static", StaticFiles(directory=str(_FRONTEND)), name="static")

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(str(_FRONTEND / "index.html"))
