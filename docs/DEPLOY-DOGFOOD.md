# DEPLOY-DOGFOOD — dựng bản nội bộ cho team test (GCP 1-VM, cloud, data thật)

> Mục tiêu: đưa BRAVO lên **1 VM GCP** cho ~5–15 người nội bộ dùng thử + flag lỗi, chạy trên
> **corpus thật** với **LLM/embedding cloud** (chủ dự án đã cho phép cloud-only chạm data thật —
> ADR-0030). Runbook này là bản rút gọn end-to-end sau khi P0 containment đã đóng; chi tiết/scale
> xem [DEPLOY-GCP.md](DEPLOY-GCP.md). **Khác demo công khai:** đây là nội bộ, hạn chế truy cập.

## 0. Điều kiện tiên quyết (chủ dự án cung cấp)
- GCP project + billing + **budget alert** (token LLM tính TIỀN RIÊNG, không thuộc credit VM).
- Tên miền (A record) HOẶC chỉ dùng IP + hạn chế firewall theo IP team (không cần HTTPS công khai nếu LAN/VPN).
- Cloud LLM + embedding: `CLOUD_BASE_URL/CLOUD_MODEL/CLOUD_API_KEY` + `CLOUD_EMBEDDING_*` (OpenAI-compatible).
- Corpus thật trong `file_system/` (bị gitignore — copy lên VM riêng).

## 1. VM + mạng
```bash
gcloud compute addresses create bravo-ip --region=asia-southeast1
gcloud compute instances create bravo --machine-type=e2-standard-4 --zone=asia-southeast1-a \
  --image-family=ubuntu-2204-lts --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB --address=bravo-ip --tags=https-server
# Firewall: 80/443 CHỈ cho IP team (nội bộ), 22 chỉ từ IP admin. KHÔNG mở 5432/6379/8000.
```
DNS: A record `bravo.<tên-miền>` → IP (nếu dùng HTTPS công khai). Sửa `deploy/Caddyfile` domain.

## 2. Cài Docker + code + corpus
```bash
sudo apt-get update && sudo apt-get install -y docker.io docker-compose-plugin git openssl
sudo fallocate -l 4G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
git clone <repo> bravo && cd bravo && git checkout feat/v2-p0-containment
gcloud compute scp --recurse ./file_system bravo:~/bravo/file_system --zone=asia-southeast1-a  # corpus
```

## 3. Secrets (BẮT BUỘC — boot-guard fail-closed)
```bash
./deploy/gen-secrets.sh          # sinh .env: JWT/pepper/POSTGRES_PASSWORD/REDIS_PASSWORD ngẫu nhiên
nano .env                        # điền <FILL: ...> = CLOUD_* (chat) + CLOUD_EMBEDDING_* (embedding)
# Xác nhận boot-guard PASS trước khi bootstrap:
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm api \
  python -c "from app.config import get_settings; get_settings().validate_boot(); print('boot-guard OK')"
```

## 4. Bootstrap (build → migrate → seed → ingest → backfill → up)
```bash
# Admin THẬT (không dùng demo123); team dùng thì tạo tài khoản qua trang Quản trị sau.
export BRAVO_ADMIN_EMAIL="it@congty.vn" BRAVO_ADMIN_PASSWORD='<mật khẩu mạnh ≥10>'
export SEED_DEMO=true            # giữ 5 tài khoản demo cho smoke RLS; đặt false nếu chỉ muốn tài khoản thật
chmod +x deploy/bootstrap.sh && ./deploy/bootstrap.sh
```
Bootstrap tự chạy `backfill_chunk_sensitivity --apply` (giữ reranker sống) sau ingest.

## 5. Smoke test (định nghĩa "deploy thành công")
1. `https://bravo.<domain>` (hoặc `http://IP`) lên; login `it@congty.vn`.
2. **Trích dẫn:** hỏi một mục trong cẩm nang → trả lời **có trích dẫn (tên tài liệu + trang)**.
3. **Abstain:** hỏi ngoài corpus → "Tôi không tìm thấy…" (không bịa).
4. **RLS (nếu SEED_DEMO):** `kinhdoanh@bravo.vn`/demo123 hỏi lương → **từ chối**; `nhansu@bravo.vn` → trả lời.
5. **Số có nguồn:** hỏi một con số → chỉ hiện nếu truy được nguồn; số bịa bị mask `[số chưa kiểm chứng]`.
6. **Feedback loop:** bấm 👎 + "báo lỗi cho IT" trên một câu → đăng nhập admin → trang **Quản trị → Phản hồi chất lượng** thấy câu đó.
7. **Metrics:** `/metrics` (internal) có `bravo_answer_outcomes_total`, `bravo_ungrounded_numbers_total`.

## 6. Onboard team
- Admin tạo tài khoản từng người: **Quản trị → Tạo user** (email + họ tên + mật khẩu + phòng ban + quyền `doc:read:own_dept`, kế toán thêm `metric:read`/`draft:create:own_dept`).
- Nếu chạy dogfood thuần tài khoản thật: `SEED_DEMO=false` và xoá/đổi mật khẩu 5 tài khoản demo.
- Gửi team [TEAM-DOGFOOD-GUIDE.md](TEAM-DOGFOOD-GUIDE.md).

## 7. Vận hành
- **Backup nightly:** cron `0 2 * * * cd ~/bravo && DATABASE_URL='<prod>' ./scripts/backup.sh ~/backups` (đã backup DB+uploads+private_data). Chạy thử 1 lần restore theo [RUNBOOK-DR.md](RUNBOOK-DR.md).
- **Tắt VM khi không dùng** để tiết kiệm; token LLM vẫn tính riêng.
- **Rollback:** giữ image tag trước; `git checkout <tag> && ./deploy/bootstrap.sh` (DB migration reversible qua alembic downgrade).
