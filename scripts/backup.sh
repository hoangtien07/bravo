#!/usr/bin/env bash
# BRAVO backup (W2.5) — pg_dump custom-format + tài liệu upload. Chạy cron nightly.
# Dùng: scripts/backup.sh [thư_mục_đích]   (mặc định ./backups)
# Khôi phục: xem docs/RUNBOOK-DR.md
set -euo pipefail

DEST="${1:-./backups}"
TS="$(date +%Y%m%d_%H%M%S)"
mkdir -p "$DEST"

# DATABASE_URL dạng postgresql+asyncpg://user:pass@host:port/db -> tách cho pg_dump.
DBURL="${DATABASE_URL:-postgresql+asyncpg://bravo:bravo@localhost:5432/bravo}"
CONN="$(printf '%s' "$DBURL" | sed 's#+asyncpg##')"

echo "[backup] pg_dump -> $DEST/db_$TS.dump"
pg_dump -Fc "$CONN" -f "$DEST/db_$TS.dump"

# Tài liệu upload (mutable, KHÔNG nằm trong DB). Hai trường hợp:
#  - Dev/bind-mount: thư mục host data/uploads tồn tại -> tar thẳng.
#  - Prod/named-volume 'uploads' (docker-compose.prod.yml): tar nội dung volume qua busybox.
UPLOAD_VOL="${UPLOAD_VOLUME:-bravo_uploads}"   # đổi nếu tên project compose khác
if [ -d data/uploads ]; then
  echo "[backup] tar data/uploads (host) -> $DEST/uploads_$TS.tgz"
  tar czf "$DEST/uploads_$TS.tgz" data/uploads
elif command -v docker >/dev/null && docker volume inspect "$UPLOAD_VOL" >/dev/null 2>&1; then
  echo "[backup] tar docker volume $UPLOAD_VOL -> $DEST/uploads_$TS.tgz"
  docker run --rm -v "$UPLOAD_VOL":/vol -v "$(cd "$DEST" && pwd)":/out busybox \
    tar czf "/out/uploads_$TS.tgz" -C /vol .
else
  echo "[backup] (bỏ qua uploads: không thấy host dir lẫn volume $UPLOAD_VOL)"
fi

# Giữ 14 bản gần nhất (retention).
ls -1t "$DEST"/db_*.dump 2>/dev/null | tail -n +15 | xargs -r rm -f
ls -1t "$DEST"/uploads_*.tgz 2>/dev/null | tail -n +15 | xargs -r rm -f

echo "[backup] xong: $DEST/db_$TS.dump"
