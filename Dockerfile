# BRAVO AI Copilot — API + worker image (modular monolith, ADR-0007).
# On-prem target: build once, run air-gapped. Models (Qwen/bge-m3) served separately.
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

EXPOSE 8000

# Default: API. The `worker` service overrides command to run arq.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
