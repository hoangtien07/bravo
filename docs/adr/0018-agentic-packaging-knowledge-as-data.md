# 0018. Đóng gói agentic bằng KNOWLEDGE/RULE-AS-DATA + CONFIG-AS-BOOT (single-tenant) — cổng L3 cho phần còn lại

- **Trạng thái:** Accepted (bản HẸP có cổng) — 2026-07-09, chủ dự án duyệt qua plan-mode.
- **Ngày:** 2026-07-09
- **Người quyết định:** Chủ dự án + Hội đồng cố vấn 5/5 (security · accounting · rag · onprem · product) họp trong phiên; đối chiếu reverse-engineer `../agent-ai` (Atlas Builder) + chuẩn ngành agent-runtime tính đến 7/2026.
- **Liên quan:** hiện thực hoá [ADR-0007](0007-code-strategy.md) (tri thức ngoài code); giữ 4 bất biến [0003](0003-hybrid-llm-strategy.md)/[0004](0004-llm-never-computes-numbers.md)/[0005](0005-no-free-form-sql.md); tôn trọng freeze + CUT#7 của [ADR-0016](0016-pivot-standalone-ap-vertical.md); xây trên [0010](0010-agent-loop-architecture.md)/[0012](0012-verify-gate-number-integrity.md)/[0014](0014-journal-entry-validator.md). Tham chiếu: [reference/agent-ai-notes.md](../reference/agent-ai-notes.md), [RUNBOOK-PACKAGING.md](../RUNBOOK-PACKAGING.md).

## Bối cảnh (Context)

Mục tiêu chủ dự án: **đóng gói quy trình agentic để triển khai theo phòng ban / phân hệ / nhóm người dùng / doanh nghiệp**. Reverse-engineer `../agent-ai` (customs, ĐÃ có user thật P&G/PV/Sumi) cho thấy công thức: **ENGINE (code domain-agnostic) + KNOWLEDGE-AS-DATA (dictionary/tariff/checklist/experiences) + MANIFEST + 2-STAGE GATE (audit-warn → handover-block) + HANDOVER ARTIFACT** — onboard domain mới ≈ 90% data + prose. Chuẩn ngành 2026 đồng thuận: *"outsource infrastructure, own your cognitive architecture"* (engine là commodity, domain-content là moat); single-tenant/silo cho dữ liệu nhạy; workflow-as-code thắng visual/DSL (OpenAI khai tử Agent Builder); Gartner **>40% dự án agent bị huỷ tới 2027**.

Bravo đang **L1, 0 user thật**. Xây "packaging platform / multi-tenant" ngay = breadth-before-proof, nhảy 2 bậc thang, vi phạm ADR-0016 CUT#7. Hội đồng phủ quyết ❌ platform-ngay, nhưng ✅ **lấy PATTERN (không lấy PLATFORM)** ở phạm vi hẹp — làm như **sản phẩm phụ của việc ship Copilot AP cho đúng**.

## Quyết định (Decision — bản HẸP có cổng)

**Chốt kiến trúc packaging của bravo** (đã hiện thực Phase 0–2 trong phiên):

1. **ENGINE = code, bất biến** — RLS filter, `payload_builder`/verify-gate, agent loop. Data/manifest **KHÔNG override được** engine.
2. **RULE/KNOWLEDGE-AS-DATA có governance** ([rules_governance.py](../../app/accounting/rules_governance.py)): mọi file rule mang header bắt buộc (`version/effective_from/reviewed_by/approved_for_prod/legal_basis`); **fail-loud ở prod** khi chưa duyệt; chọn theo **ngày lập chứng từ** (effective-date) — vá lỗi chứng từ giáp ranh kỳ. Phân tầng **STATUTORY** (luật — global, khoá; phòng ban KHÔNG override) / **POLICY** / **SUGGESTION** (luôn kéo `needs_review`).
3. **CONFIG-AS-DATA lúc BOOT (single-tenant)**: `BRAVO_KNOWLEDGE_DIR` overlay rule (cập nhật không rebuild image; fallback in-package — bravo luôn CHẠY ĐƯỢC, khác agent-ai ship rỗng) + `deploy/site.yaml` manifest (enabled_verticals/departments/flags) validate **fail-closed** trong `validate_boot()`. Đọc 1 lần lúc boot, **KHÔNG** resolve per-request.
4. **2-STAGE GATE** giữ nguyên tinh thần: Number-Integrity Gate + **statutory-consistency** (ngưỡng luật chỉ đến từ file STATUTORY theo kỳ, không có đường per-dept) + maker-checker (draft). **Ghi rõ: verify-gate ≠ chắn lỗi ngữ nghĩa** — đừng dùng nó làm luận điểm an toàn sai.
5. **HANDOVER ARTIFACT**: xuất Excel/CSV cho người nhập (ADR-0016), non-invasive.
6. **RLS scope cho draft do agent tạo** ([draft_queue.resolve_draft_department](../../app/erp/draft_queue.py)): fail-closed theo phòng, KHÔNG rơi về NULL/global (vá lỗ OWASP ASI03). Ingest corpus theo phòng (`--department`, fail-closed). Egress fail-closed khi không rõ scope.

## Phương án đã cân nhắc (Alternatives)

| Phương án | Vì sao loại / chọn |
|---|---|
| A. Packaging platform đầy đủ + multi-tenant NGAY | ❌ Loại: breadth-before-proof; vi phạm ADR-0016 CUT#7; Gartner >40% huỷ; chưa có payer. |
| B. Không làm gì (giữ hằng số hard-code) | ❌ Loại: đau TCO của CFO/CIO ("cần kỹ sư Python cho mỗi luật mới"); không đúng ADR-0007. |
| C. Bản HẸP: rule-as-data + config-as-boot, single-tenant, giữ freeze | ✅ Chọn: tạo nền packaging như sản phẩm phụ của ship AP; kế toán sửa rule 0 dòng code; giữ 4 bất biến; không nhảy bậc. |

## Hệ quả (Consequences)

**Tích cực:** kế toán/compliance cập nhật rule (đã duyệt) mà không cần kỹ sư/rebuild; đúng luật theo kỳ; nền "đóng gói theo doanh nghiệp = deployment riêng" sẵn sàng; giữ trọn 4 bất biến + freeze ADR-0016. Golden test bắt được **23 lỗi dữ liệu crosswalk** (lớp 6415) — data-as-truth có cổng người.

**Chi phí:** rule chưa kế toán duyệt → `approved_for_prod=false` (prod fail-loud tới khi duyệt — đúng thiết kế); overlay cần quy trình giao + checksum (RUNBOOK).

## GATE tới L3 + ≥1 khách thật (KHÔNG làm bây giờ)

Đối chiếu ADR-0016 CUT#7 + MATURITY-LADDER (packaging per-site = L3→L4) + chuẩn ngành:
- **Multi-tenant runtime** (nhiều DN/1 deployment) — cần `tenant_id` xuyên toàn bộ RLS; "global" định nghĩa lại thành "tenant-global". Nay: deployment/DB **riêng** mỗi DN.
- **Per-department vertical enablement như capability** — phải biên dịch xuống permission+RLS + probe-test (blueprint: arkon `kb_tool(requires=…)` + `ScopedToolsMiddleware`), KHÔNG để cờ RAM.
- **Playbook-as-instruction nhồi prompt / LLM skill-routing** — bề mặt ảo tưởng mới; routing phải tất định theo Identity/phòng, fail-loud.
- **DSL/console sinh vertical tổng quát; Helm/air-gap installer; per-site pricing.**
- **Ghi nhận tương lai:** DBOS (durable execution dạng thư viện trên Postgres — hợp bravo) + bundle kiểu Letta `.af` (rules + corpus-scope + descriptor + checksum) làm artifact "đóng gói 1 vertical, bê sang deployment khác".

## ⚠️ MỐC BẮT BUỘC — chuyển LOCAL trước dữ liệu THẬT

Demo dùng **OpenAI cloud** chỉ chấp nhận với dữ liệu "public/giả". Theo **PDPL Luật 91/2025 + NĐ 356/2025** (hiệu lực 1/1/2026): **thông tin tài chính = dữ liệu cá nhân nhạy cảm**; đẩy dữ liệu kế toán thật ra OpenAI = **chuyển dữ liệu nhạy xuyên biên giới** (phạt tới 5% doanh thu). Thêm **Luật AI 134/2025** (hiệu lực 1/3/2026; tài chính gia hạn 1/9/2027) + nội địa hoá (NĐ 53). ⇒ **TRƯỚC khi chạm dữ liệu thật**: `EMBEDDING_PROVIDER=local` (bge-m3) + `cloud_enabled=false` + LLM local (vLLM + Qwen3 Apache-2.0 / GLM-4.6 MIT — tránh Llama vì license). Gắn với lộ trình L2→L3 (Wave 3 GPU/pass^k). *(EU AI Act Điều 12 hoãn high-risk → 2/12/2027 theo Digital Omnibus; luật VN mới là driver chính.)*
