# 0011. Phân loại độ nhạy tự động & audit-then-egress cho Model Router

- **Trạng thái:** Accepted (Hội đồng 2026-06-11 xác nhận — [ADR-0013](0013-reuse-vs-rewrite-and-topology.md))
- **Ngày:** 2026-06-10 (Accepted 2026-06-11)
- **Người quyết định:** Đội dự án BRAVO AI Copilot (Hội đồng — security Critical, quyền phủ quyết)
- **Liên quan:** [ADR-0003](0003-hybrid-llm-strategy.md) (bổ sung), [../SECURITY-RLS.md §9](../SECURITY-RLS.md), [../SOVEREIGNTY-DEMO-NOTE.md](../SOVEREIGNTY-DEMO-NOTE.md), [../app/llm/router.py](../../app/llm/router.py)

## Bối cảnh (Context)
[ADR-0003](0003-hybrid-llm-strategy.md) chốt hybrid: dữ liệu nhạy ghim local, cloud chỉ cho dữ liệu whitelist, fail-closed. Nhưng **code hiện tại chưa cưỡng chế** điều đó:
- [router.py](../../app/llm/router.py): `decide()` nhận `sensitive: bool|None` **truyền tay từ caller**; [loop.py:64](../../app/agent/loop.py) hardcode `sensitive=None`.
- Comment "Audit decision on egress" nhưng **không có dòng nào ghi AuditLog**.

Khi mở agent loop tool-call (nhiều bước, nhiều ngữ cảnh), một bước truyền nhầm `sensitive=False` cho ngữ cảnh chứa lương/HR → **dữ liệu nhạy egress ra cloud không để lại vết audit** → vi phạm SECURITY-RLS §9 + Luật BVDLCN 91/2025 (CTIA). **Demo đang dùng cloud** càng làm đường egress thành bề mặt rủi ro phải khoá. Hội đồng đánh giá đây là **Critical — quyền phủ quyết**.

## Các phương án đã cân nhắc (Options)
1. **Giữ nguyên (caller truyền `sensitive`).** Nhược: con người/LLM dễ truyền nhầm; không có nguồn sự thật; không audit. **Bị loại.**
2. **LLM tự đánh giá độ nhạy.** Nhược: LLM-judge bị prompt-injection bypass; không deterministic. **Bị loại** (ràng buộc cứng phải deterministic).
3. **Tự-phân-loại deterministic từ nhãn nguồn + audit-then-egress.** Router tính độ nhạy từ `department_ids`/`knowledge_type` của **mọi** phần tử trong prompt; ghi audit **trước** khi gọi cloud.

## Quyết định (Decision)
Chọn **Phương án 3**. Cụ thể:

1. **`classify_context(chunks, metric_results) -> sensitive: bool`** — deterministic, tái dùng nhãn RLS: **nhạy nếu BẤT KỲ phần tử nào** có `department.sensitive=True` hoặc `knowledge_type` nhạy (kế toán/lương/HR/PII); **không xác định ⇒ nhạy ⇒ local** (fail-closed).
2. **Router KHÔNG nhận `sensitive` thủ công.** `router.chat()` nhận *ngữ cảnh* và tự gọi `classify_context`. Bỏ `sensitive=None` hardcode ở loop.py.
3. **Audit-then-egress.** Khi `backend=='cloud'`: ghi `AuditLog(action='llm.egress', detail={provider, model, user, layer, prompt_hash=sha256(messages), ts})` **TRƯỚC** khi gọi cloud; **audit ghi lỗi ⇒ fail (không egress)**.
4. **CI test bắt buộc:** prompt chứa chunk nhãn Kế toán/HR ⇒ `backend=='local'`; cloud call không có AuditLog trước đó ⇒ fail. `egress-leak` là **HARD FAIL** trong eval.

## Hệ quả (Consequences)
- **Tích cực:** cưỡng chế invariant 4 ở code (không phải lời hứa); chứng minh tuân thủ khi A05 thanh tra; demo trình diễn được "dữ liệu nhạy fail-closed về local"; nền cho phân loại độ nhạy mà ADR-0003 còn để mở.
- **Tiêu cực / nợ kỹ thuật:** cần nhãn `sensitive`/`knowledge_type` đầy đủ trên Department/Source (một phần đã có — [models.py](../../app/database/models.py)); classify_context phải phủ mọi đường đưa ngữ cảnh vào prompt.
- **Ảnh hưởng 4 nguyên tắc:** trực tiếp cưỡng chế #4 (chủ quyền); tái dùng #1 (nhãn RLS làm nhãn nhạy).
- **Việc tiếp:** lược đồ phân loại độ nhạy chi tiết + (tuỳ chọn) redaction PII trước cloud (ADR-0003 backlog).

## Tham chiếu
[../SECURITY-RLS.md §9](../SECURITY-RLS.md) · Hội đồng security Critical #1 + mandatory_change "EGRESS + AUDIT" · [../research/findings/K-agentic-architecture.md](../research/findings/K-agentic-architecture.md) (pitfall #8 lệ thuộc cloud/egress im lặng).
