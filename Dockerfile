# syntax=docker/dockerfile:1.7
# BRAVO AI Copilot — API + worker image (modular monolith, ADR-0007).
# On-prem target: build once, run air-gapped. Models (Qwen/bge-m3) served separately.

# --- Frontend build stage: biên dịch canonical FigmaMake SPA ----------------------------
# dist bị .gitignore nên phải build trong image. Không build được -> app vẫn boot, chỉ
# không phục vụ trang tĩnh (app/main.py guard _FRONTEND.exists()).
FROM node:20-slim AS frontend-build
WORKDIR /fe
COPY FigmaMake_UI/package.json FigmaMake_UI/pnpm-lock.yaml ./
# Optional BuildKit secret.  Corporate TLS inspection uses a private CA that is not present in
# Debian/Node's default trust stores; mount its public root/intermediate PEM chain only for this
# dependency-fetch step.  It is deliberately not copied into the repository or app stage.
RUN --mount=type=secret,id=corporate_ca,target=/run/secrets/corporate-ca,required=false \
    if [ -s /run/secrets/corporate-ca ]; then \
        export NODE_EXTRA_CA_CERTS=/run/secrets/corporate-ca; \
    fi; \
    corepack enable && pnpm install --frozen-lockfile
COPY FigmaMake_UI/ ./
RUN pnpm build         # -> /fe/dist (base=/)

# --- Python runtime --------------------------------------------------------------------
FROM python:3.11-slim AS app-base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_CERT=/etc/ssl/certs/ca-certificates.crt \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

WORKDIR /app

# System deps (psycopg/asyncpg build, etc.).  When supplied, the same corporate CA is baked into
# the Linux trust store before apt or pip access a TLS endpoint.  The source secret mount itself
# does not persist; only the public CA becomes part of the standard consolidated trust bundle.
RUN --mount=type=secret,id=corporate_ca,target=/usr/local/share/ca-certificates/bravo-corporate-ca.crt,required=false \
    if [ -s /usr/local/share/ca-certificates/bravo-corporate-ca.crt ]; then \
        update-ca-certificates; \
    fi; \
    apt-get update && apt-get install -y --no-install-recommends \
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
