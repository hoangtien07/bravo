# BRAVO AI Copilot — API + worker image (modular monolith, ADR-0007).
# On-prem target: build once, run air-gapped. Models (Qwen/bge-m3) served separately.

# --- Frontend build stage: biên dịch canonical FigmaMake SPA ----------------------------
# dist bị .gitignore nên phải build trong image. Không build được -> app vẫn boot, chỉ
# không phục vụ trang tĩnh (app/main.py guard _FRONTEND.exists()).
FROM node:20-slim AS frontend-build
WORKDIR /fe
COPY FigmaMake_UI/package.json FigmaMake_UI/pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile
COPY FigmaMake_UI/ ./
RUN pnpm build         # -> /fe/dist (base=/)

# --- Python runtime --------------------------------------------------------------------
FROM python:3.11-slim AS app-base

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
# AccountingCase V2's local synthetic demonstrator loads these frozen fixtures at runtime.
# Keep the runtime image narrow: do not copy the test suite, only the versioned demo inputs.
COPY tests/fixtures/core_v2/wp01 ./tests/fixtures/core_v2/wp01

# Test image is deliberately separate from the runtime image: it carries development
# dependencies and the test suite, but does not pay the cost of the frontend build.
FROM app-base AS test
RUN pip install -e ".[dev]"
COPY tests ./tests

FROM app-base AS base
# Canonical FigmaMake SPA đã build.
COPY --from=frontend-build /fe/dist ./FigmaMake_UI/dist

EXPOSE 8000

# Default: API. The `worker` service overrides command to run arq.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
