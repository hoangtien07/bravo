# RUNBOOK — Backup & Disaster Recovery (W2.5)

Mục tiêu: khôi phục được dữ liệu duyệt/audit/hội thoại sau sự cố. **RTO mục tiêu < 30 phút.**
Air-gap-friendly: chỉ `pg_dump`/`pg_restore` + tar, không phụ thuộc SaaS.

## Backup (định kỳ)

```bash
# Thủ công
scripts/backup.sh /var/backups/bravo

# Cron nightly (02:00) — thêm vào crontab của host:
0 2 * * * cd /opt/bravo && DATABASE_URL=... scripts/backup.sh /var/backups/bravo >> /var/log/bravo-backup.log 2>&1
```

Sinh ra: `db_<ts>.dump` (Postgres custom-format, gồm schema+data+pgvector),
`uploads_<ts>.tgz` (tài liệu upload `data/uploads/`) và `private_data_<ts>.tgz`
(dữ liệu vận hành riêng `data/private/`). Giữ 14 bản gần nhất (retention trong script).

> Lưu ý: corpus `file_system/` là read-only (scp lên VM khi deploy) — không cần backup thường
> xuyên; nếu có, thêm vào script tuỳ site.

## Restore (khi hỏng)

```bash
# 1) Dừng app (không ghi trong lúc restore)
docker compose stop api worker

# 2) Tạo DB trống + extension vector (nếu cụm mới)
psql "$CONN" -c 'CREATE EXTENSION IF NOT EXISTS vector;'

# 3) Phục hồi DB (custom-format). --clean --if-exists để ghi đè an toàn.
pg_restore --clean --if-exists --no-owner -d "$CONN" /var/backups/bravo/db_<ts>.dump

# 4) Phục hồi tài liệu upload
tar xzf /var/backups/bravo/uploads_<ts>.tgz -C /opt/bravo
tar xzf /var/backups/bravo/private_data_<ts>.tgz -C /opt/bravo

# 5) Áp migration mới nhất (nếu bản code mới hơn dump)
alembic upgrade head

# 6) Khởi động lại + kiểm tra
docker compose start api worker
curl -sf localhost:8000/readyz   # {"ready": true, ...}
```

`CONN` = DATABASE_URL bỏ `+asyncpg`, vd `postgresql://bravo:bravo@localhost:5432/bravo`.

## Drill (bắt buộc — đừng tin backup chưa test)

Định kỳ (khuyến nghị hàng quý) chạy drill vào DB tạm:

```bash
createdb bravo_drill
pg_restore --no-owner -d "postgresql://bravo:bravo@localhost:5432/bravo_drill" db_<ts>.dump
# Kiểm: số bản ghi draft/audit/conversation khớp bản gốc; thời gian đo được (RTO).
psql ".../bravo_drill" -c 'SELECT count(*) FROM drafts; SELECT count(*) FROM audit_log;'
dropdb bravo_drill
```

Ghi lại **RTO đo được** + kết quả mỗi lần drill vào bảng dưới:

| Ngày drill | RTO đo | Kết quả | Ghi chú |
|-----------|--------|---------|---------|
| (chưa chạy) | — | — | Chạy drill đầu tiên trước khi pilot dữ liệu thật |
