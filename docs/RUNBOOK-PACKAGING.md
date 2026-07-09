# RUNBOOK — Đóng gói & triển khai theo deployment (config-as-data)

> Bản HẸP (ADR-0018). Áp dụng cho MỘT deployment / MỘT doanh nghiệp (single-tenant). Multi-tenant
> runtime, per-department enablement như capability, DSL sinh vertical = **GATE tới L3** (ADR-0016
> CUT#7). "Đóng gói theo doanh nghiệp" = deployment/DB **riêng** mỗi công ty.

## 1. Overlay knowledge/rule (không rebuild image)

Rule kế toán/thuế là **DỮ LIỆU** (`app/accounting/data/*.yaml`), không phải hằng số code. Bản
in-package luôn **chạy được** (khác agent-ai ship rỗng). Để cập nhật rule đã kế toán duyệt mà
không build lại image:

```bash
# Thư mục overlay chứa bản đã duyệt (coa_tt99_*.yaml, mapping_rules_*.yaml, statutory_rules_vn.yaml)
export BRAVO_KNOWLEDGE_DIR=/etc/bravo/knowledge     # bind-mount read-only
```
File có trong overlay → dùng bản overlay; thiếu → fallback in-package (`resolve_data_file`).

**Governance bắt buộc** (fail-loud ở prod, `rules_governance`): mỗi file mang `version`,
`effective_from`, `reviewed_by`, `approved_for_prod`, `legal_basis`. Prod **từ chối** nạp file
`approved_for_prod != true`. Ngưỡng LUẬT (TSCĐ 30tr/TT45, VAT 20tr/TT219, thuế suất) chọn theo
**ngày lập chứng từ** — sửa `effective_from`/thêm `periods` khi văn bản pháp luật đổi.

### 1b. KB version-awareness (chống trả lời SAI phiên bản)

Manifest gắn version metadata (`defaults` hoặc per-source) → chảy vào `Chunk.extra`:
`doc_version`, `owner`, `approved_status` (`approved`|`draft`|`superseded`|`deprecated`),
tuỳ chọn `superseded_by`/`effective_date`. Khi có bản mới, chủ nội dung set bản cũ
`approved_status: superseded` (+ `superseded_by: <id>`). Truy hồi ([kb_lifecycle.py](../app/rag/kb_lifecycle.py))
**hạ bậc** (không xoá) chunk superseded/deprecated/draft → bản hiện hành thắng khi cả hai cùng
được kéo (giảm lỗi "đúng nguồn nhưng sai phiên bản" — VersionRAG, Findings O #5). Metadata mới
chỉ có hiệu lực sau khi **ingest lại** nguồn đó.

## 2. Manifest deploy — `deploy/site.yaml`

```bash
export SITE_CONFIG=/etc/bravo/site.yaml             # xem deploy/site.yaml.example
```
Đọc + validate **một lần lúc boot** (`Settings.validate_boot`), **fail-closed** nếu sai (thiếu
`site`, `enabled_verticals` rỗng, vertical lạ). Khai: `site`, `enabled_verticals`
(`ap|anomaly|tax|graph`), `departments` (nhãn onboarding — RLS thực thi ở DB).

## 3. Nạp corpus theo phòng ban (RLS scope)

```bash
# Corpus Demo A công khai -> GLOBAL.
# Gồm user guide, mindmap, KQPT/PTNV, tài liệu kỹ thuật, BI/basic rules.
# Metadata lấy từ file_system/bravo_corpus_manifest.yaml.
python -m scripts.ingest_userguide file_system/
# Corpus của một phòng -> scope RLS theo phòng (fail-closed nếu phòng chưa tồn tại):
python -m scripts.ingest_userguide /data/ketoan --department "Kế toán"
```
`--department` tạo `SourceDepartment` → pipeline tự lan `department_ids` xuống chunk. Tài liệu
nhạy **không rõ scope** (global + không knowledge_type) bị coi là nhạy → embed **local** (vá lỗ
egress). Eval per-domain: `retrieval_eval.main(identity=<Identity phòng>)` + `probes.assert_no_leak`
(chặn rò chéo phòng).

BRAVO lifecycle retrieval gate:

```bash
python -m app.eval.bravo_lifecycle app/eval/golden_set_bravo_lifecycle.example.yaml
```
Gate này kiểm `Chunk.extra.source_type/module` để phát hiện câu hỏi schema bị kéo nhầm sang user
guide, hoặc câu hỏi thao tác bị kéo nhầm sang tài liệu kỹ thuật.

Lifecycle playbooks:

```text
file_system/bravo_lifecycle_playbooks.yaml
file_system/bravo_ai_use_cases.yaml
```
Playbook định nghĩa output contract cho từng mode: end-user guidance, implementation support,
BA/PTNV, technical impact, QA testcase, support/helpdesk, voucher assistant, dashboard explainer,
governance/audit. Agent render playbook hint ngắn qua `app.agent.bravo_playbooks`; sửa playbook
không cần đổi code nếu chỉ thay required output/guardrail/metric.

Use-case matrix định nghĩa priority, stage, dependency và ROI metric. Kiểm nhất quán với playbook
bằng `app.agent.bravo_use_cases.validate_use_cases`.

Static readiness audit trước khi demo/ingest:

```bash
python -m app.eval.bravo_readiness
```
Audit này không cần DB/embedding/LLM; nó kiểm manifest có đủ file, playbook đủ mode, use-case khớp
playbook, và golden lifecycle có đủ nhóm câu hỏi trọng yếu.

## 4. Air-gap payload — verify integrity

```python
from app.site_config import payload_checksum
payload_checksum("coa_tt99_v2025.yaml")   # SHA-256; sinh ở nguồn, đối chiếu ở nơi nhận
```
Giao payload kèm checksum; **không** dùng flag-service/remote config từ xa (lỗi chí mạng cho khách
air-gap) — mọi cấu hình đọc file **LOCAL** lúc boot.

## 5. ⚠️ MỐC BẮT BUỘC: chuyển LOCAL trước dữ liệu THẬT

Demo hiện dùng **OpenAI cloud** (embedding/answer) — CHỈ chấp nhận với dữ liệu "public/giả".
Theo **PDPL Luật 91/2025 + NĐ 356/2025** (hiệu lực 1/1/2026), **thông tin tài chính = dữ liệu cá
nhân nhạy cảm**; đẩy dữ liệu kế toán thật ra OpenAI = **chuyển dữ liệu nhạy xuyên biên giới** (phạt
tới 5% doanh thu). ⇒ TRƯỚC khi chạm dữ liệu thật: `EMBEDDING_PROVIDER=local` (bge-m3) +
`cloud_enabled=false` + LLM local (vLLM + Qwen3 Apache-2.0 / GLM-4.6 MIT — tránh Llama vì license).
Xem ADR-0018 + lộ trình L2→L3 (Wave 3 GPU/pass^k).
