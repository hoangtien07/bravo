# 0012. Verify-gate value-object & toàn vẹn số liệu (nối gate vào loop, đơn vị, Decimal)

- **Trạng thái:** Accepted (Hội đồng 2026-06-11 xác nhận — [ADR-0013](0013-reuse-vs-rewrite-and-topology.md)); **CHƯA IMPLEMENT** (BLOCKING Phase 2 số)
- **Ngày:** 2026-06-10 (Accepted 2026-06-11)
- **Người quyết định:** Đội dự án BRAVO AI Copilot (Hội đồng — accounting + rag Critical, quyền phủ quyết)
- **Liên quan:** [ADR-0004](0004-llm-never-computes-numbers.md), [ADR-0005](0005-no-free-form-sql.md), [ADR-0010](0010-agent-loop-architecture.md), [../app/data_layer/grounding.py](../../app/data_layer/grounding.py), [../app/data_layer/calc.py](../../app/data_layer/calc.py), [../app/data_layer/semantic.py](../../app/data_layer/semantic.py)

## Bối cảnh (Context)
Invariant 3 (zero hallucination số) phụ thuộc verify-gate. Hội đồng soi code và tìm **3 lỗ Critical** làm gate **không thực sự bảo vệ**:
1. **Gate chưa nối loop:** [loop.py:68](../../app/agent/loop.py) trả `grounded=True` **hardcode**, **không gọi** `verify_numbers()` → số bịa lọt qua dù gate đã viết.
2. **So float trần, không đơn vị:** [grounding.py](../../app/data_layer/grounding.py) so trị tuyệt đối → engine trả `12.5` (tỷ) mà LLM viết "12,5 triệu" vẫn **PASS** → **số sai 1.000 lần lọt gate**.
3. **Calc dùng float cho tiền:** [calc.py](../../app/data_layer/calc.py) → cộng dồn làm **tổng ≠ chi tiết** (cross-foot fail), chênh 1 đồng = sổ không cân.

Nghiên cứu củng cố: grounding có cấu trúc đạt 94% vs LLM trần 11% (Daloopa); cautionary tale AccountingBench (reward-hacking bù số ~$500k); Air Canada (DN chịu trách nhiệm pháp lý cho số sai của chatbot).

## Các phương án đã cân nhắc (Options)
1. **Giữ float + tin LLM tự nhất quán đơn vị.** Nhược: sai bội số lọt, tổng không cân. **Bị loại.**
2. **Để LLM tự "soi lại" số (self-critique).** Nhược: Huang 2024 — self-correction nội tại *giảm* accuracy khi thiếu external feedback. **Bị loại.**
3. **Value-object + Decimal + gate cứng nối loop, so với ground-truth engine.** Số mang đơn vị/scale; tiền là Decimal; gate chặn cứng trong loop.

## Quyết định (Decision)
Chọn **Phương án 3**. Cụ thể:

1. **MetricResult là value-object** `(value, unit, scale, currency, period, entity, variant)` thay `float` trần ([semantic.py:30](../../app/data_layer/semantic.py)). Verify-gate **chuẩn hoá về đơn vị cơ sở (VND)** trước khi so; **cấm LLM tự đổi tỷ↔triệu** (đổi đơn vị = phép tính ở calc, không phải việc của LLM).
2. **Nối `verify_numbers()` thành GATE CỨNG trong loop** ([loop.py](../../app/agent/loop.py)): bỏ `grounded=True` hardcode; tính `grounded` từ verdict thật; mỗi token số phải khớp **đúng một** engine value (ưu tiên buộc LLM cite metric-id/chunk-id cho từng số); số chưa khớp ⇒ **mask/abstain**.
3. **Calc dùng `decimal.Decimal`** ([calc.py](../../app/data_layer/calc.py)) với policy làm tròn tường minh (`ROUND_HALF_UP`; VND 0 chữ số thập phân, ngoại tệ 2), khai báo per-metric; chia/tỷ-lệ giữ Decimal, quantize bước cuối; verify so Decimal đã quantize (không float tolerance).
4. **Reconciliation gate:** khi trả tổng+chi tiết, kiểm `Σ(chi tiết Decimal) == tổng` (dung sai **0 đồng**); lệch ⇒ cảnh báo/từ chối (chống fan-out đếm trùng).
5. **HARD FAIL trong eval:** bịa-số · sai-đơn-vị/bội-số · cross-foot lệch — chặn release.

## Hệ quả (Consequences)
- **Tích cực:** cưỡng chế invariant 3 thật sự (gate sống, không code-chết); chặn lớp lỗi nguy hiểm nhất (sai bội số, tổng không cân); là tài sản bán hàng "không bịa số"; chống reward-hacking (agent không tự bù số — số khớp/không do engine phán).
- **Tiêu cực / nợ kỹ thuật:** mọi nguồn số (mock & ERP thật sau này) phải trả value-object đầy đủ; cần parser số tiếng Việt nhận biết đơn vị; ràng buộc "mỗi số cite một nguồn" làm prompt chặt hơn.
- **Ảnh hưởng 4 nguyên tắc:** trực tiếp cưỡng chế #3; hỗ trợ #2 (số trong draft đáng tin trước khi chờ duyệt).
- **Việc tiếp:** áp cho mock DataSource ([../MOCK-DATA-SPEC.md](../MOCK-DATA-SPEC.md)); journal-entry validator (Phase 3) tái dùng Decimal + reconciliation.

## Tham chiếu
[../research/findings/K-agentic-architecture.md](../research/findings/K-agentic-architecture.md) (strength #1, finance lessons) · Hội đồng accounting Critical #1/#2 + rag Critical #1 + mandatory_change "VERIFY-GATE / CALC-Decimal". Daloopa FinRetrieval (arXiv 2603.04403) · AccountingBench (Penrose) · Huang 2024 (arXiv 2310.01798).
