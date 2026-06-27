# BRAVO AI Copilot — API + worker image (modular monolith, ADR-0007).
# On-prem target: build once, run air-gapped. Models (Qwen/bge-m3) served separately.

# --- Frontend build stage: biên dịch React SPA (frontend-react/dist) -------------------
# Không có stage này thì runtime rơi về bản tĩnh cũ frontend/ (dist bị .gitignore).
FROM node:20-slim AS frontend-build
WORKDIR /fe
COPY frontend-react/package.json frontend-react/package-lock.json* ./
RUN npm install --no-audit --no-fund
COPY frontend-react/ ./
RUN npm run build      # -> /fe/dist (base=/static/)

# --- Python runtime --------------------------------------------------------------------
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps (psycopg/asyncpg build, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (layer cache)
COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install -e .

# App code
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
COPY scripts ./scripts
COPY frontend ./frontend
# React SPA đã build (ưu tiên hơn frontend/ — app/main.py:19-21)
COPY --from=frontend-build /fe/dist ./frontend-react/dist

EXPOSE 8000

# Default: API. The `worker` service overrides command to run arq.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
