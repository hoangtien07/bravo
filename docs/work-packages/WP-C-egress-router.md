# WP-C — Egress: classify_context tự động + audit-then-egress

> Module: `app/llm`, `app/security`. **Đọc [CONTRACTS.md](CONTRACTS.md) trước.** Hiện thực [ADR-0011](../adr/0011-egress-classification-audit.md). Phụ thuộc: không.

## Mục tiêu
Cưỡng chế invariant #4 ở code: router **tự phân loại độ nhạy** từ nhãn nguồn (không nhận `sensitive` thủ công) và **ghi audit TRƯỚC khi** gọi cloud. Đặc biệt quan trọng vì **demo dùng cloud**.

## Reuse (ADR-0013)
REUSE library cho LLM client (openai SDK trỏ vLLM/Ollama — [router.py] đã có). **Không** LiteLLM 12-provider. Router hand-roll giữ vì mang invariant #4.

## Scope IN / OUT
**IN:** `classify_context(chunks, metric_results) -> bool` (nhạy nếu **bất kỳ** phần tử có `department.sensitive=True` hoặc `knowledge_type` nhạy; **không xác định → nhạy → local**); `router.chat(messages, *, context, ...)` tự gọi classify (bỏ `sensitive=None` ở [loop.py:64]); khi `backend=='cloud'` ghi `AuditLog(action='llm.egress', {provider, model, user, layer, prompt_hash, ts})` **trước**, audit lỗi → **fail (không egress)**.
**OUT (đừng làm):** LLM tự đánh giá độ nhạy (deterministic only); redaction PII (backlog); thêm provider.

## Files
`app/llm/router.py` (chat nhận context; audit-then-egress) · `app/security/sensitivity.py` (mới, `classify_context`) · dùng `AuditLog` ([database/models.py] đã có).

## Việc cụ thể
1. `classify_context`: đọc `department_ids`/`knowledge_type` của mọi chunk + metric_result; map qua `Department.sensitive` ([models.py]); trả True nếu bất kỳ nhạy; rỗng/không rõ → True.
2. `router.chat`: đổi chữ ký nhận `context` (chunks+results) thay `sensitive`; gọi `decide(classify_context(context))`.
3. Audit-then-egress: nhánh cloud → `await db.add(AuditLog(...))` + flush **trước** `client.chat.completions.create`; nếu ghi audit raise → không gọi cloud.

## Acceptance (test)
- prompt chứa chunk nhãn phòng Kế toán/HR → `decide().backend == "local"`.
- `cloud_enabled=True` + context không nhạy → cloud, và có 1 `AuditLog(llm.egress)` ghi **trước** lời gọi.
- giả lập audit ghi lỗi → KHÔNG có lời gọi cloud (fail-closed).
- không còn đường nào truyền `sensitive` thủ công (grep `sensitive=` = 0 ngoài classify).

## Invariant
#4 (chủ quyền — dữ liệu nhạy ghim local, audit egress) + #1 (tái dùng nhãn RLS làm nhãn nhạy).

## Phụ thuộc
Không. (WP-D gọi `router.chat(context=...)` theo seam CONTRACTS §3.)
