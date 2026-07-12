# 0019. Chiến lược LLM CLOUD-ONLY cho v2.0 (nghỉ hưu đường chạy local mặc định)

- **Trạng thái:** Accepted (2026-07-12) — chủ dự án quyết qua hỏi-đáp lập kế hoạch v2.0.
- **Ngày:** 2026-07-12
- **Người quyết định:** Chủ dự án + rà soát phản biện (đối chiếu code thật + pilot `.env`).
- **Supersedes:** [ADR-0003](0003-hybrid-llm-strategy.md) (hybrid local-default), [ADR-0009](0009-local-model-stack.md) (Qwen/bge-m3/ViRanker local stack, gồm cả descope OCR).
- **Amends:** [ADR-0011](0011-egress-classification-audit.md) → xem [ADR-0022](0022-egress-guard-to-audit.md); [ADR-0006](0006-market-positioning.md) → xem [ADR-0020](0020-positioning-v2-cloud.md).
- **Liên quan:** cập nhật CLAUDE.md nguyên tắc bất biến #4; [MATURITY-LADDER.md](../MATURITY-LADDER.md); `docs/COUNCIL-REVIEW-2026-07-12.md`.

## Bối cảnh (Context)

Pilot nội bộ bị người dùng đánh giá "trả lời không hữu ích" so với **chat.bravogen.io.vn** (LibreChat + Google Gemini). Đối chiếu thực tế:

1. **Đường chạy "sovereign/local" chưa từng chạy thật.** Pilot `.env` trỏ `LLM_LOCAL_BASE_URL` sang OpenAI `gpt-4o`; `CLOUD_ENABLED=true`; embedding `text-embedding-3-small`; rerank LLM. Dịch vụ vLLM/Qwen trong `docker-compose.yml` bị comment ("uncomment when GPU available"). Tức bất biến #4 (offline-capable mặc định) tồn tại trong tài liệu nhưng **không tồn tại trong sản phẩm đang chạy**.
2. **Không có GPU on-prem.** Máy demo yếu; `llm_max_concurrency=2` theo GPU "~1-2 stream". Đầu tư hạ tầng local (GPU + tuning Qwen-VL) là nhiều tháng, và chất lượng khó đuổi kịp Gemini trong ngắn hạn.
3. **Benchmark là Gemini.** Đối thủ nội bộ (BravoGen) chính là Gemini cloud. Chạy cùng lớp model cloud loại bỏ biến "thua vì model", cô lập đúng phần retrieval+corpus để cải thiện.
4. **Cloud mở khoá năng lực v2 cần:** vision (attachment ảnh, OCR hoá đơn scan — 70% hoá đơn thật là scan), fluency tiếng Việt.

## Quyết định (Decision — ĐÃ CHỐT)

**Cloud là runtime DUY NHẤT cho v2.0.** Bỏ đường chạy local mặc định khỏi phạm vi.

- Thêm `egress_policy` (config): `hybrid` (hành vi ADR-0003 cũ, giữ cho khách on-prem tương lai) | **`cloud_only`** (v2 pilot). Dưới `cloud_only`: `router.decide()` luôn trả cloud; guard raise-sensitive ở `embedding.embed()` hạ xuống AUDIT (vẫn ghi vết, không chặn); `validate_boot()` fail-closed nếu thiếu cấu hình cloud.
- **KHÔNG xoá** `router.decide()`/`sensitivity.py`/egress guard — nghỉ hưu bằng CONFIG. Khách enterprise on-prem có thể quay lại `hybrid`; xây lại từ đầu thì đắt. Đây là điểm tái nhập nếu tầng sovereign quay lại.
- **Router giữ vai trò provider-abstraction** + cấu hình model per-task (`decide_model`/`compose_model`/`rerank_model`) để trộn OpenAI (decide-JSON) và Gemini (compose/rerank rẻ) qua endpoint OpenAI-compatible.
- **Mở lại OCR/vision** (đảo descope của ADR-0009): parser vision cho PDF scan (số từ scan = quote-level + trích trang, KHÔNG vào verify-gate như engine-truth).
- **Nâng budget agent** (`agent_max_tokens=120_000`) vì attachment inject ≤50k token phải vừa một lượt (context gpt-4o 128k).

## Phương án đã cân nhắc (Alternatives)

| Phương án | Vì sao loại / chọn |
|---|---|
| A. Giữ hybrid, đầu tư GPU + Qwen-VL local ngay | ❌ Chậm nhiều tháng; chất lượng khó đuổi Gemini; sovereign chưa bán được (xem ADR-0020). |
| B. Cloud-only, bỏ sovereign (chọn) | ✅ Nhanh tới "hữu ích như BravoGen"; mở vision/OCR; benchmark công bằng cùng lớp model. |
| C. Giữ nguyên tài liệu "local-default" nhưng chạy cloud | ❌ Tuyên bố ↔ thực tế lệch — chính lỗi ADR này sửa; rủi ro tuân thủ (nói offline mà egress). |

## Hệ quả (Consequences)

**Tích cực:** ship nhanh; vision/OCR mở khoá; benchmark cô lập được retrieval; plumbing đổi tối thiểu (đổi config, không viết lại router).

**Tiêu cực / chi phí:**
- **Bỏ moat "chủ quyền/on-prem"** — định vị lại (ADR-0020).
- **Tuân thủ PDPL/Luật 91-2025:** cloud-only = chuyển dữ liệu xuyên biên giới với BẤT KỲ thứ gì người dùng dán vào chat (có thể là PII khách). Bắt buộc **paid tier** (free tier train trên input). Egress AUDIT (ADR-0022) trở thành chứng cứ tuân thủ thay cho egress-block. **Rà soát pháp lý là launch gate**, ngoài phạm vi code.
- **Phụ thuộc nhà cung cấp ngoài** (OpenAI/Google) — chấp nhận cho pilot; `hybrid` giữ đường lui.
- Bất biến #4 (CLAUDE.md) đổi nghĩa: từ "offline mặc định" → "chủ quyền là TÙY CHỌN triển khai (hybrid), pilot chạy cloud có audit".

**Bất biến GIỮ NGUYÊN:** #1 RLS-in-SQL · #2 non-invasive (draft-only) · #3 zero-hallucination số.

## Tham chiếu
Pilot `.env`, `docker-compose.yml`; `app/config.py::egress_policy`; `app/llm/router.py::decide`; `app/rag/embedding.py`; COUNCIL-REVIEW-2026-07-12.md.
