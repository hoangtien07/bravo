# 0021. Chế độ trả lời "kiến thức chung" có nhãn (thay hard-abstain)

- **Trạng thái:** Accepted (2026-07-12)
- **Ngày:** 2026-07-12
- **Amends:** [ADR-0012](0012-verify-gate-number-integrity.md) (phạm vi: số vẫn gated tuyệt đối).
- **Liên quan:** [ADR-0019](0019-cloud-only-llm-strategy.md), [ADR-0020](0020-positioning-v2-cloud.md); `app/agent/loop.py`; COUNCIL-REVIEW-2026-07-12.md.

## Bối cảnh (Context)

~30% điểm thua BravoGen là "chấm sai vai": người dùng hỏi câu tổng quát, bravo hard-abstain ("không tìm thấy trong tài liệu") trong khi Gemini trả lời bằng world-knowledge. Với cloud-only (ADR-0019), model CÓ world-knowledge — hard-abstain giờ là tự trói tay. Nhưng trả lời tự do lại phá bất biến #3 (bịa số) nếu không kiểm soát.

## Quyết định (Decision)

**Hợp đồng trả lời 2 tầng:**

1. **Phần có nguồn** — mệnh đề dựa trên context mang trích dẫn `[N]` như hiện tại.
2. **Phần kiến thức chung** — khi context thiếu/không đủ, model ĐƯỢC tiếp tục bằng kiến thức tổng quát **chỉ trong khối gắn nhãn tường minh**:
   `--- Ngoài tài liệu BRAVO (kiến thức chung, chưa kiểm chứng với BRAVO 10) ---`

**Ràng buộc cứng:**
- `_clip_abstain` → `_label_ungrounded`: KHÔNG cắt cụt nữa; verify cấu trúc nhãn, fail-closed cắt CHỈ khi model trộn bước quy trình không-trích-dẫn vào phần có nguồn.
- **Số luôn gated:** `verify_numbers` vẫn chạy khi có `engine_values`; THÊM cấm mọi số tiền VND/số dư tài khoản trong khối kiến-thức-chung (regex deterministic). Số nghiệp vụ = phải có nguồn, không có ngoại lệ.
- UI render khối kiến-thức-chung khác biệt thị giác (không lẫn với câu có nguồn).

## Hệ quả (Consequences)

- **Tích cực:** trung hoà 30% "sai vai" — hữu ích như Gemini ở câu tổng quát mà vẫn trung thực về nguồn. Đây đúng cách Gemini thắng, nhưng có nhãn.
- **Tiêu cực / rủi ro:** kỷ luật nhãn là prompt + check cấu trúc, KHÔNG phải chứng minh. Giảm thiểu: rubric parity-benchmark PHẠT world-knowledge không nhãn; probe golden-set ("menu không tồn tại" phải rơi vào khối nhãn hoặc abstain).
- **Bất biến:** #3 giữ tuyệt đối cho SỐ; nới chỉ áp cho văn xuôi tổng quát phi-số.

## Tham chiếu
`app/agent/loop.py` (`_SYSTEM`, `_COMPOSE_SYSTEM`, `_label_ungrounded`); COUNCIL-REVIEW-2026-07-12.md §role.
