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

echo "==> Seed departments/roles + tài khoản test (RLS). Dogfood thật: đặt SEED_DEMO=false."
if [ "${SEED_DEMO:-true}" = "true" ]; then
  $COMPOSE run --rm api python -m scripts.seed_demo   # 5 tài khoản demo123 (dùng cho smoke/RLS test)
else
  echo "   (bỏ qua seed_demo — SEED_DEMO=false)"
fi
# Admin THẬT (mật khẩu mạnh từ env) — tạo tài khoản team qua trang Quản trị sau.
if [ -n "${BRAVO_ADMIN_EMAIL:-}" ]; then
  echo "==> Seed admin thật: ${BRAVO_ADMIN_EMAIL}"
  $COMPOSE run --rm -e BRAVO_ADMIN_EMAIL -e BRAVO_ADMIN_PASSWORD -e BRAVO_ADMIN_NAME \
    api python scripts/seed_admin.py
fi

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
