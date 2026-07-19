# DEPLOY-DEMO — đưa demo lên online (GCP $300 + tên miền)

> Mục tiêu: chạy **demo công khai** (Demo A tra cứu + Demo B agentic trên mock) trên một máy khác, có HTTPS + tên miền. **Demo dùng data demo** (corpus cẩm nang không nhạy + số GIẢ) — KHÔNG có dữ liệu thật của ai, nên đặt trên cloud công khai là chấp nhận được. Khi demo thành công → bước sau chuyển on-prem + data thật (đúng quy trình).
> Quan trọng (để không tự mâu thuẫn pitch): đây là **bản demo để TRÌNH DIỄN**; bản bán cho khách là **on-prem**. Nói rõ điều này khi demo.

## 0. Kiến trúc deploy (chốt)
**1 VM GCP + Docker Compose + Caddy (auto-HTTPS).** Đơn giản, rẻ, khớp thiết kế "1 compose" (ADR-0007). LLM = **cloud** (key sẵn có); embedding = **bge-m3 LOCAL ngay trên VM** (bước chủ quyền thật — không phụ thuộc embedding cloud). Không cần GPU.

> *Vì sao không Cloud Run + Cloud SQL:* nhiều thành phần hơn, Cloud SQL pgvector đắt hơn, worker `arq` là stateful → overkill cho demo. Giữ lại làm phương án scale sau.

## 1. Tài nguyên & chi phí
- **VM:** Compute Engine `e2-standard-2` (2 vCPU, 8GB) + **4GB swap** (đủ để Docling+bge-m3 nạp corpus); hoặc `e2-standard-4` (16GB) cho thoải mái. Ubuntu 22.04. **Disk 50GB** (torch + model + image nặng).
- **IP tĩnh** (reserve) + **A record** `demo.<tên-miền>` → IP.
- **Chi phí:** e2-standard-2 ~$50/tháng; **$300 đủ ~3-6 tháng** nếu **tắt VM khi không demo** (`gcloud compute instances stop`). ⚠️ **Token LLM cloud tính TIỀN RIÊNG** (không trừ vào $300 GCP, trừ khi dùng Vertex AI). Đặt **budget alert** GCP.

## 2. Các bước (runbook)
```bash
# --- 2.1 Tạo VM (gcloud, máy bạn) ---
gcloud compute addresses create bravo-demo-ip --region=asia-southeast1
gcloud compute instances create bravo-demo \
  --machine-type=e2-standard-2 --zone=asia-southeast1-a \
  --image-family=ubuntu-2204-lts --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB --address=bravo-demo-ip \
  --tags=http-server,https-server
# Firewall: 80/443 mở; 22 chỉ từ IP của bạn; KHÔNG mở 5432/6379/8000.

# --- 2.2 DNS ---  A record: demo.<tên-miền> -> <IP tĩnh vừa tạo>

# --- 2.3 Trên VM: cài Docker ---
sudo apt-get update && sudo apt-get install -y docker.io docker-compose-plugin git
sudo fallocate -l 4G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile

# --- 2.4 Code + corpus ---
git clone <repo> bravo && cd bravo && git checkout feat/agentic-demo
# Corpus bị gitignore -> copy lên VM:
gcloud compute scp --recurse ./file_system bravo-demo:~/bravo/file_system --zone=asia-southeast1-a

# --- 2.5 Tạo .env (BÍ MẬT THẬT — xem §3) ---
cp .env.example .env && nano .env   # điền secrets + cloud key + domain

# --- 2.6 Bootstrap (build + migrate + seed + ingest + up) ---
chmod +x deploy/bootstrap.sh && ./deploy/bootstrap.sh
# (build cài docling + sentence-transformers; ingest nạp 19 chương + .docx qua Docling, embed bge-m3 local)
```
Sửa `deploy/Caddyfile`: đổi `demo.example.com` → tên miền của bạn.

## 3. Secrets & cấu hình `.env` cho production (BẮT BUỘC)

> ⚠️ **Boot-guard P0.5 fail-closed:** ở `ENV=production`, app **từ chối boot** nếu `DATABASE_URL`
> còn `bravo:bravo`, `REDIS_URL` không có mật khẩu, hoặc `JWT_SECRET`/`MCP_TOKEN_PEPPER` mặc định.
> **Đừng sao chép creds mẫu.** Dùng script sinh secrets:

```bash
./deploy/gen-secrets.sh          # sinh .env với JWT/pepper/Postgres/Redis ngẫu nhiên (chmod 600)
nano .env                        # điền các giá trị <FILL: ...> (CLOUD_* + CLOUD_EMBEDDING_*)
# Xác nhận boot-guard sẽ pass TRƯỚC khi bootstrap:
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm api \
  python -c "from app.config import get_settings; get_settings().validate_boot(); print('boot-guard OK')"
```

Ghi chú: embedding preset là **cloud** (`openai_compatible`, 1536-dim) — không cần GPU; nội dung
corpus đi qua API embedding (chấp nhận cho pilot cloud-only). Muốn giữ corpus không rời máy thì đổi
`EMBEDDING_PROVIDER=local` + `EMBEDDING_MODEL=BAAI/bge-m3` + `EMBEDDING_DIM=1024` (cần re-ingest).

## 4. Checklist cứng trước khi mở public (council security)
- [ ] Đổi `JWT_SECRET` + `MCP_TOKEN_PEPPER` (≥32 byte ngẫu nhiên). Demo data nhạy=0 nhưng vẫn phải đổi.
- [ ] **Không** publish cổng 5432/6379/8000 (overlay đã set `ports: []`; firewall chỉ 80/443).
- [ ] Caddy chặn `/docs` `/openapi.json` (đã set) — tránh lộ bề mặt API.
- [ ] CORS giới hạn domain demo (kiểm `app/main.py` nếu thêm CORS).
- [ ] Rate-limit cơ bản (Caddy plugin hoặc trước app) chống lạm dụng key LLM.
- [ ] Backup volume `pgdata` (demo dữ liệu nhỏ — `docker run --rm -v bravo_pgdata:/d busybox tar ...`).
- [ ] GCP **budget alert** + tắt VM khi không demo.
- [ ] Đặt nhãn rõ trên UI: *"Bản demo — số liệu minh hoạ (DEMO), không phải dữ liệu thật."*

## 5. Smoke online (định nghĩa "demo thành công")
1. `https://demo.<domain>` lên, có khoá HTTPS.
2. Login `ketoan@bravo.vn` / `demo123` → `/api/me` trả đúng quyền.
3. Demo A: hỏi *"Quy trình nghỉ phép?"* / một mục trong cẩm nang → trả lời **có trích dẫn (tên tài liệu + trang)**; hỏi ngoài corpus → **từ chối**.
4. Demo B: hỏi *"Doanh thu thuần Q2?"* → số mock + verify-gate; hỏi *"Quỹ lương tháng 1?"* bằng `kinhdoanh@bravo.vn` → **từ chối (RLS)**; bằng `nhansu@bravo.vn` → trả lời.
5. (Nếu nạp được) hỏi một số nằm trong **bảng** của `.docx`/PDF → trích dẫn tới **ô/sheet** (chứng minh Docling).

## 6. Sau demo thành công → bước tiếp (đúng quy trình bạn nêu)
- Chuyển sang **data thật** (cần ERP read-only API + catalog metric kế toán duyệt).
- Chuyển LLM sang **Qwen local** (Ollama/vLLM) để đạt sàn on-prem thật — xem [FIX-REUSE-PLAN.md §R5](FIX-REUSE-PLAN.md).
- Đóng gói **air-gapped** (bake model offline) cho bản bán on-prem.
