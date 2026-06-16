#!/usr/bin/env bash
# One-time bootstrap trên VM sau khi: git clone + tạo .env + copy corpus vào file_system/.
# Cài Docling + sentence-transformers tự động (trong image build) -> nạp corpus THẬT.
set -euo pipefail
COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

echo "==> Build image (cài docling + sentence-transformers + bge-m3 deps)"
$COMPOSE build

echo "==> Up hạ tầng (postgres + redis)"
$COMPOSE up -d postgres redis
sleep 8

echo "==> Migrate schema"
$COMPOSE run --rm api alembic upgrade head

echo "==> Seed demo users/departments (RLS)"
$COMPOSE run --rm api python -m scripts.seed_demo

echo "==> Ingest corpus THẬT (pypdf cho PDF text, Docling cho .docx/bảng) — embedding bge-m3 local"
$COMPOSE run --rm api python -m scripts.ingest_userguide ./file_system

echo "==> Up toàn bộ (api + worker + caddy auto-HTTPS)"
$COMPOSE up -d

echo "DONE. Mở https://<tên-miền>  — login ketoan@bravo.vn / demo123"
