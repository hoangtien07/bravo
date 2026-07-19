# DEPLOY-GCP — Triển khai BRAVO AI Copilot trên Google Cloud

Hướng dẫn đầy đủ để dựng bravo trên GCP: từ **demo công khai** đến **pilot có dữ liệu thật**,
kèm cách **xử lý file system** (corpus / tài liệu upload / DB) và wiring các thành phần Wave 1/2
(SSO/OIDC, observability, rate-limit, backup/DR).

> Muốn dựng demo NHANH nhất (1 VM + Caddy, ~30 phút): xem [DEPLOY-DEMO.md](DEPLOY-DEMO.md).
> Tài liệu này là bản **đầy đủ + production-minded**, giải thích *vì sao* và *các phần liên quan*.
> Nhắc lại định vị: **bản bán cho khách là ON-PREM**; deploy GCP ở đây là để TRÌNH DIỄN / pilot
> nội bộ. Dữ liệu nhạy (kế toán/HR/PII) **không** đặt trên cloud công khai (bất biến #4).

---

## 0. Chọn topology

| | **A. Demo/Pilot 1-VM** (khuyến nghị bắt đầu) | **B. Scale-out** (khi tải lớn) |
|---|---|---|
| Compute | 1 VM + Docker Compose | GKE/Cloud Run + Cloud SQL + GCS |
| DB | Postgres trong compose (volume `pgdata`) | Cloud SQL for PostgreSQL + pgvector |
| Uploads | Docker volume `uploads` | GCS bucket (mount qua gcsfuse) |
| LLM | Cloud (key) HOẶC Qwen local (GPU VM) | Vertex AI / cụm vLLM riêng |
| Khi nào | MVP, demo, pilot ≤ vài chục user | Nhiều phòng ban, HA, autoscale |

Phần dưới đi theo **topology A** (khớp thiết kế "1 compose" — ADR-0007). Mục §9 nêu đường scale.

---

## 1. Tài nguyên GCP

```bash
# Biến dùng chung
PROJECT=<gcp-project>; ZONE=asia-southeast1-a; REGION=asia-southeast1
gcloud config set project $PROJECT

# IP tĩnh + VM. e2-standard-4 (4 vCPU/16GB) cho thoải mái khi nạp corpus (Docling+bge-m3).
gcloud compute addresses create bravo-ip --region=$REGION
gcloud compute instances create bravo \
  --machine-type=e2-standard-4 --zone=$ZONE \
  --image-family=ubuntu-2204-lts --image-project=ubuntu-os-cloud \
  --boot-disk-size=80GB --address=bravo-ip --tags=http-server,https-server
```

- **Sizing:** demo cloud-LLM + embedding bge-m3 local **không cần GPU**. `e2-standard-2` (8GB) chạy
  được nếu thêm 4GB swap; `e2-standard-4` (16GB) mượt hơn. Disk **≥80GB** (torch+model+image nặng).
- **Chạy Qwen local (on-prem thật):** cần **GPU VM** — vd `g2-standard-8` + 1×L4 (24GB) cho
  Qwen2.5-14B-AWQ, hoặc A100 40GB cho 32B. Bật vLLM (xem §7.4). Đây là bước rời khỏi "cam kết" sang
  "chạy thật" mà IT manager đòi.
- **Firewall:** chỉ mở **80/443**; SSH (22) giới hạn IP của bạn; **KHÔNG** mở 5432/6379/8000/8080/3000.

```bash
gcloud compute firewall-rules create bravo-web --allow=tcp:80,tcp:443 --target-tags=https-server
gcloud compute firewall-rules create bravo-ssh --allow=tcp:22 --source-ranges=<YOUR_IP>/32 --target-tags=https-server
```

- **DNS:** A record `app.<domain>` → IP tĩnh vừa tạo (dùng cho Caddy auto-HTTPS).
- **Chi phí:** e2-standard-4 ~$100/tháng; **tắt VM khi không dùng** (`gcloud compute instances stop bravo`).
  Token LLM cloud tính **riêng** — đặt **budget alert** GCP.

---

## 2. Cài đặt trên VM

```bash
gcloud compute ssh bravo --zone=$ZONE
sudo apt-get update && sudo apt-get install -y docker.io docker-compose-plugin git postgresql-client
sudo usermod -aG docker $USER && newgrp docker
# Swap (nếu VM 8GB): sudo fallocate -l 4G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
git clone <repo-url> bravo && cd bravo && git checkout bravo-v0.1
```

---

## 3. XỬ LÝ FILE SYSTEM (phần cốt lõi)

bravo có **ba loại dữ liệu file**, xử lý KHÁC nhau. Hiểu đúng chỗ này là mấu chốt vận hành:

| Loại | Đường dẫn | Tính chất | Có trong image? | Persistence | Backup |
|------|-----------|-----------|:---:|-------------|:---:|
| **Corpus gốc** | `file_system/` | Đọc-only, tài liệu BRAVO 10 (118MB), **đã version trong git** | ❌ (bind-mount) | Bind-mount `:ro` từ host | Không cần (git pull lại được) |
| **Tài liệu upload** | `data/uploads/` (trong container `/app/data/uploads`) | Mutable, người dùng upload runtime | ❌ | **Named volume `uploads`** | ✅ BẮT BUỘC |
| **CSDL** | Postgres volume `pgdata` | Nháp/audit/hội thoại/chunk/vector | — | Named volume `pgdata` | ✅ BẮT BUỘC |

### 3.0 Runtime data policy vs VM mounts

`file_system/bravo_data_runtime_policy.yaml` is a runtime classification policy, not a VM provisioner.
It validates resolved paths and may create only mutable runtime dirs marked `ensure_exists`.
The actual VM/container paths must still be provided by env vars and Docker volumes:

```text
APP_ROOT=/app
DATA_ROOT=/app/data
CORPUS_ROOT=/app/file_system
UPLOAD_ROOT=/app/data/uploads
PRIVATE_DATA_ROOT=/app/data/private
DATA_RUNTIME_POLICY=/app/file_system/bravo_data_runtime_policy.yaml
```

`docker-compose.yml` and `docker-compose.prod.yml` mount `file_system` read-only and persist both
`uploads` and `private_data` named volumes.


### 3.1 Corpus `file_system/` — bind-mount read-only

Corpus **đã được version trong git** (bỏ gitignore) nên `git clone`/`git pull` trên VM là **có
sẵn corpus** — không phải scp 118MB. Nó **không** nằm trong Docker image (Dockerfile không COPY),
nên vẫn phải **bind-mount** vào container (đã cấu hình trong `docker-compose.prod.yml`:
`./file_system:/app/file_system:ro`).

```bash
# Trên VM: corpus có sẵn ngay sau git clone/pull. (Trước đây phải scp — nay không cần.)
cd ~/bravo && git pull
```

> Nếu corpus phình lớn (>vài trăm MB) hoặc thêm nhiều PDF nặng, chuyển sang **Git LFS** hoặc
> **GCS** — xem [DOCUMENT-MANAGEMENT.md](DOCUMENT-MANAGEMENT.md).

Vì sao read-only: corpus là nguồn tri thức bất biến; container chỉ **đọc** để (a) ingest lúc bootstrap,
(b) mở file gốc khi bấm trích dẫn (`routes_sources.py::source_file` tìm trong `file_system/`).

### 3.2 Tài liệu upload `data/uploads/` — named volume, PHẢI bền + backup

Khi người dùng upload tài liệu (trang `/documents`) hoặc hoá đơn (`/money-engine`), file gốc được
ghi vào `data/uploads/{source_id}_{filename}` **bên trong container**. Nếu không có volume, dữ liệu
này **mất khi tạo lại container** (bug độ bền). `docker-compose.prod.yml` đã gắn named volume
`uploads:/app/data/uploads` để giữ bền và nằm trong phạm vi backup.

> Nếu bạn muốn xem/backup thủ công nội dung upload:
> `docker run --rm -v bravo_uploads:/v busybox ls -la /v`

### 3.3 CSDL — volume `pgdata`

Mọi thứ "sống" (nháp bút toán, audit log, hội thoại, memory, chunk+vector) nằm trong Postgres
(`pgdata`). Đây là dữ liệu quan trọng nhất — xem §6 backup.

> ⚠️ **Ranh giới `EMBEDDING_DIM`:** cột `Vector` trong DB cố định theo `EMBEDDING_DIM` lúc migrate.
> bge-m3 = **1024**; OpenAI text-embedding-3-small = **1536**. Chọn provider/dim **TRƯỚC** khi
> `alembic upgrade` + ingest; đổi sau phải re-migrate + re-ingest toàn bộ.

---

## 4. Cấu hình `.env` production

> ⚠️ **Boot-guard P0.5 (fail-closed):** ở `ENV=production` app **từ chối boot** nếu `DATABASE_URL`
> còn `bravo:bravo`, `REDIS_URL` thiếu mật khẩu, `JWT_SECRET`/`MCP_TOKEN_PEPPER` mặc định,
> `allow_self_approval=true`, hoặc `cloud_only` thiếu bất kỳ `CLOUD_*`. Đừng chép creds mẫu tay.

Sinh secrets mạnh + `.env` production bằng script (nguồn sự thật duy nhất):
```bash
./deploy/gen-secrets.sh              # JWT/pepper/POSTGRES_PASSWORD/REDIS_PASSWORD ngẫu nhiên (chmod 600)
nano .env                            # điền <FILL: ...> = CLOUD_* (chat) + CLOUD_EMBEDDING_* (embedding)
```
Script đặt sẵn (khớp boot-guard): `ENV=production`, `POSTGRES_PASSWORD` + `DATABASE_URL` đồng bộ,
`REDIS_PASSWORD` + `REDIS_URL` có auth (`redis://:PASS@redis:6379/0`), `EGRESS_POLICY=cloud_only`,
`RERANK_ENABLED=true`, `CONSULTANT_ENABLED=true`. Embedding preset = **cloud** (`openai_compatible`,
1536-dim; corpus text egress — chấp nhận cho pilot). Muốn giữ corpus không rời máy: đổi
`EMBEDDING_PROVIDER=local` + `bge-m3` + `EMBEDDING_DIM=1024` (cần re-ingest, chậm CPU).

Xác nhận boot-guard TRƯỚC khi bootstrap:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm api \
  python -c "from app.config import get_settings; get_settings().validate_boot(); print('boot-guard OK')"
```

> **Quản lý secret tốt hơn (khuyến nghị pilot):** đưa secret vào **GCP Secret Manager**, kéo lúc
> khởi động thay vì để plaintext trong `.env`:
> ```bash
> echo -n "$(openssl rand -hex 32)" | gcloud secrets create bravo-jwt --data-file=-
> # trên VM: export JWT_SECRET=$(gcloud secrets versions access latest --secret=bravo-jwt)
> ```
> Cấp VM service-account quyền `roles/secretmanager.secretAccessor`.

---

## 5. Bootstrap (build → migrate → seed → ingest → up)

```bash
chmod +x deploy/bootstrap.sh && ./deploy/bootstrap.sh
```

Script (`deploy/bootstrap.sh`) chạy: build image (cài docling+sentence-transformers) → up
postgres/redis → `alembic upgrade head` → `seed_demo` (4 user demo, RLS) → `ingest_userguide
./file_system` (nạp 19 chương + docx, embed bge-m3 local) → up toàn bộ (api+worker+caddy).

Sửa `deploy/Caddyfile`: đổi `demo.example.com` → `app.<domain>` của bạn.

Smoke: `https://app.<domain>` lên (khoá HTTPS), login, hỏi cẩm nang → trả lời có trích dẫn trang,
hỏi ngoài corpus → từ chối. (Chi tiết kịch bản: [DEPLOY-DEMO.md §5](DEPLOY-DEMO.md).)

---

### 5.1 Nâng cấp sang frontier control plane (migration 0012)

Sau khi lấy commit có migration `0012_frontier_run_control_plane`, build lại cả `api` và `worker`
(SDK Agents được cài trong image), rồi migrate **trước** khi recreate application containers:

```bash
cd ~/bravo
dc() { docker compose -f docker-compose.yml -f docker-compose.prod.yml "$@"; }
git pull --ff-only
dc build api worker
dc up -d postgres redis
dc run --rm api alembic upgrade head
dc up -d --force-recreate api worker caddy
dc ps
curl -fsS https://app.<domain>/readyz
```

Migration thêm durable run events, approval records và artifacts; không thay đổi/chạy lại corpus
hay embeddings. Không chạy `down` trên VM production. Sau upgrade, đăng nhập rồi thử một lượt
**Nghiên cứu sâu**: câu trả lời kết thúc phải có nút tải báo cáo; `GET /api/agent-runs/<id>/events`
phải trả được plan/progress mà không trả token hay đối số tool.

Rollout runtime phải theo thứ tự, mỗi bước theo dõi lỗi/latency/citation trước khi tăng tiếp:

```ini
# Bước 0: giữ hành vi hiện tại nhưng có control plane/UI mới
AGENT_RUNTIME=legacy

# Bước 1: canary text-only; attachment, write tool vẫn bắt buộc legacy/HITL
AGENT_RUNTIME=canary
AGENT_RUNTIME_CANARY_PERCENT=5

# Chỉ sau khi canary vượt eval nghiệp vụ mới tăng dần 10 -> 25 -> 50 -> 100.
```

`REALTIME_ENABLED=false` và `COMPUTER_USE_ENABLED=false` phải giữ nguyên cho đến khi có session
broker/allowlist HTTPS đã được security review. Computer-use hiện là proposal-only, không được
phép tự thao tác ERP. GraphRAG cũng không bật bằng env: chỉ xem xét sau khi candidate vượt
`python -m app.eval.graphrag_gate baseline.json candidate.json` theo ADR-0028.

## 6. Backup & Disaster Recovery (W2.5)

Chi tiết restore + drill: [RUNBOOK-DR.md](RUNBOOK-DR.md). Trên GCP:

```bash
# Cron nightly 02:00 trên VM — dump DB + volume uploads (retention 14 bản)
crontab -e
0 2 * * * cd ~/bravo && DATABASE_URL='postgresql+asyncpg://bravo:bravo@localhost:5432/bravo' \
  UPLOAD_VOLUME=bravo_uploads bash scripts/backup.sh /var/backups/bravo >> /var/log/bravo-backup.log 2>&1
```

> `scripts/backup.sh` tự nhận biết uploads là **named volume** (prod) hay host dir (dev).
> Postgres chạy trong compose nên `pg_dump` trỏ `localhost:5432` (map từ container) — hoặc chạy
> `docker compose exec postgres pg_dump ...` nếu không map port ra host ở prod.

**Đẩy backup off-VM (chống mất VM) — GCS:**
```bash
gsutil mb -l $REGION gs://bravo-backups-$PROJECT
# thêm vào cuối cron: gsutil -m rsync -d /var/backups/bravo gs://bravo-backups-$PROJECT
```
Bật **Object Versioning** + lifecycle rule trên bucket để giữ lịch sử.

---

## 7. Wiring các thành phần Wave 1/2

### 7.1 Observability (metrics + tracing)
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  -f deploy/docker-compose.observability.yml up -d
```
Thêm `grafana/otel-lgtm` (Prometheus+Tempo+Loki+Grafana gộp). App phơi `/metrics` và đẩy OTLP trace.
**KHÔNG** publish cổng 3000 ra internet — truy cập Grafana qua **SSH tunnel**:
`gcloud compute ssh bravo -- -L 3000:localhost:3000` rồi mở `http://localhost:3000`.

### 7.2 Rate-limit
Đã bật qua `RATE_LIMIT_PER_MINUTE` (slowapi, per-user). Không cần cấu hình thêm ở GCP.

### 7.3 SSO / OIDC (Keycloak federate AD/LDAP)
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  -f deploy/docker-compose.keycloak.yml up -d
```
Cấu hình realm/client + `OIDC_*` trong `.env` theo [SSO-OIDC.md](SSO-OIDC.md).
- **`OIDC_REDIRECT_URI` phải là URL public HTTPS**: `https://app.<domain>/api/auth/oidc/callback`.
- Cho Keycloak qua Caddy (subdomain riêng `id.<domain>` → `reverse_proxy keycloak:8080`) hoặc chỉ
  dùng nội bộ + tunnel khi cấu hình. **Không** mở 8080 ra internet trần.
- boot-guard (W2.6) chặn prod nếu `OIDC_ENABLED=true` mà thiếu cấu hình / `SESSION_SECRET` yếu.

### 7.4 LLM local (Qwen) — bước "on-prem thật"
Trên **GPU VM**, bật service vllm trong `docker-compose.yml` (đang comment) rồi trỏ router về local:
```ini
CLOUD_ENABLED=false
LLM_LOCAL_BASE_URL=http://vllm:8001/v1
LLM_LOCAL_MODEL=Qwen/Qwen2.5-14B-Instruct-AWQ
LLM_MAX_CONCURRENCY=2          # GPU chịu ~1-2 stream đồng thời (W2.3 semaphore)
```
Kiểm chứng chủ quyền: chặn egress ra ngoài (firewall egress) và xác nhận app vẫn trả lời → chứng
minh "zero-egress" mà IT manager đòi. Đo pass^k local + tok/s để có GPU sizing note (Wave 3).

### 7.5 MCP `/mcp`
Đã mount sẵn (W1.5). Claude Desktop/Code kết nối `https://app.<domain>/mcp` với bearer = **MCP
token** (cấp qua `Employee.mcp_token_hash`). Đảm bảo Caddy proxy `/mcp` (mặc định `reverse_proxy
api:8000` đã bao gồm).

---

## 8. Checklist bảo mật trước khi mở public

- [ ] `JWT_SECRET`, `MCP_TOKEN_PEPPER`, `SESSION_SECRET` ≥32 byte ngẫu nhiên (boot-guard kiểm).
- [ ] `ALLOW_SELF_APPROVAL=false` (boot-guard cấm ở prod).
- [ ] KHÔNG publish 5432/6379/8000/8080/3000/4318 ra internet (chỉ Caddy 80/443).
- [ ] Caddy chặn `/docs` `/openapi.json` (đã cấu hình trong `deploy/Caddyfile`).
- [ ] `data/uploads` là volume bền + nằm trong backup; `pgdata` được backup nightly + đẩy GCS.
- [ ] Chạy **drill restore** một lần, điền RTO vào [RUNBOOK-DR.md](RUNBOOK-DR.md).
- [ ] GCP budget alert + tắt VM khi không dùng.
- [ ] Nếu để dữ liệu THẬT: **KHÔNG** dùng LLM cloud cho dữ liệu nhạy — chuyển Qwen local (§7.4).
- [ ] Nhãn "DEMO — dữ liệu mock" còn hiển thị trên các màn Anomaly/Tax (đã có sẵn) nếu chạy demo.

---

## 9. Đường scale (topology B) — khi cần

- **DB:** thay Postgres-in-compose bằng **Cloud SQL for PostgreSQL** (bật extension `vector`). Trỏ
  `DATABASE_URL` sang Cloud SQL (qua Cloud SQL Auth Proxy). Backup/HA do Cloud SQL lo.
- **Uploads:** thay named volume bằng **GCS bucket** mount qua `gcsfuse` vào `/app/data/uploads`
  (hoặc sửa `routes_sources.py` để ghi thẳng GCS SDK). Corpus `file_system/` cũng có thể để GCS ro.
- **Compute:** đóng gói image, deploy lên **Cloud Run** (api) + **GKE** (worker/vllm) — lưu ý worker
  `arq` là stateful, cần Redis quản lý (Memorystore).
- **LLM:** cụm vLLM riêng có autoscale GPU, hoặc Vertex AI (nếu chấp nhận rời on-prem cho lớp không nhạy).

---

## 10. Off-ramp: bản bán là ON-PREM

GCP ở đây là để trình diễn/pilot. Bản thương mại chạy **air-gapped on-prem** (đúng bất biến #4):
đóng gói offline bundle (`docker save` toàn bộ image + Qwen weights + wheels), cài từ USB, chạy sau
tường lửa khách. Xem roadmap Wave 3 trong [COUNCIL-REVIEW-2026-07.md](COUNCIL-REVIEW-2026-07.md).

---

## 11. Troubleshooting

| Triệu chứng | Nguyên nhân thường gặp |
|---|---|
| Ingest báo "không thấy file_system" | Quên scp corpus / quên bind-mount (dùng `docker-compose.prod.yml` đã gắn `:ro`). |
| Tài liệu upload biến mất sau `up -d` lại | Chạy thiếu overlay prod → không có volume `uploads`. Luôn kèm `-f docker-compose.prod.yml`. |
| App refuse boot ở prod | boot-guard: secret còn mặc định / `allow_self_approval=true` / OIDC thiếu cấu hình. Xem log startup. |
| Câu trả lời "treo"/timeout | `CLOUD_ENABLED=true` nhưng thiếu key, HOẶC router fail-closed về local mà không có LLM local. |
| Vector dim mismatch khi ingest | `EMBEDDING_DIM` không khớp cột DB — đặt đúng TRƯỚC khi migrate, re-migrate nếu đã lệch. |
| Caddy không ra HTTPS | DNS chưa trỏ đúng IP / cổng 80 bị chặn / `Caddyfile` còn `demo.example.com`. |
