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

echo "==> Seed demo users/departments (RLS) — 5 tài khoản phủ mọi vai + token MCP demo"
$COMPOSE run --rm api python -m scripts.seed_demo

echo "==> Ingest corpus THẬT (pypdf cho PDF text, Docling cho .docx/bảng)"
$COMPOSE run --rm api python -m scripts.ingest_userguide ./file_system

echo "==> Backfill chunk sensitivity (reactivate reranker — chunk thiếu flag làm rerank bị skip)"
$COMPOSE run --rm api python scripts/backfill_chunk_sensitivity.py --apply

echo "==> Seed dữ liệu mẫu (bút toán nháp chờ duyệt) — để màn hình không rỗng khi test"
$COMPOSE run --rm api python -m scripts.seed_content

echo "==> Up toàn bộ (api + worker + caddy auto-HTTPS)"
$COMPOSE up -d

echo "DONE. Mở https://<tên-miền>"
echo "  Tài khoản test (mật khẩu demo123):"
echo "   - giamdoc@bravo.vn       ADMIN (trang Quản trị, cost/usage)"
echo "   - ketoan@bravo.vn        Maker (tạo bút toán nháp)"
echo "   - ketoantruong@bravo.vn  Checker (DUYỆT nháp — maker-checker) + token MCP"
echo "   - kinhdoanh@bravo.vn     Ngoài phòng KT (test RLS không thấy nháp/lương)"
echo "   - nhansu@bravo.vn        HR (thấy chỉ tiêu lương nhạy)"
