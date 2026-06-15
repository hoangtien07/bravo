# MONEY-ENGINE-ROADMAP — bản đồ "chỗ ăn tiền" của BRAVO (tổng kết 1 trang)

> Gộp toàn bộ bộ research + design: [MONEY-SPOTS](research/MONEY-SPOTS.md) · [VAS-IFRS](research/VAS-IFRS-MONEY-SPOTS.md) · [AGENT-OPPORTUNITIES](research/AGENT-OPPORTUNITIES.md) · [Tax&AP engine](MONEY-ENGINE-AP-TAX.md) · [AR](AR-COLLECTIONS-AGENT.md) · [Anomaly](ANOMALY-AGENT.md) · [Tax-assistant](TAX-ASSISTANT-AGENT.md). **Chưa code.**

## 1. Một câu định vị
> **BRAVO Finance AI OS** = một **engine tất định + họ AGENT "đóng vòng lặp"** trên ERP BRAVO, **on-prem · kiểm-toán-được · không bịa số · hiểu chế độ kế toán-thuế VN** — bán bằng **chủ quyền + tuân thủ + outcome đo được**, KHÔNG bằng "rẻ" hay ROI vendor.

## 2. Nền móng (ĐÃ CÓ) = đòn bẩy + MOAT cho mọi agent
`verify-gate` (không bịa số) · `draft + maker-checker` (close-the-loop HITL) · `RLS-in-SQL` · `AgentRun + complete_on_approval` · `semantic/calc Decimal` · `Model Router` (egress-audit) · `citations/audit-trail`.
> 🛡️ **MOAT (research-verified):** verify-gate + HITL + audit-trail = **ĐIỀU KIỆN để output AI tài chính kiểm-toán-được** (Big4; SR 11-7; EU AI Act 8/2026). Nhiều công cụ AI thiếu — bravo đã có sẵn.

## 3. Thứ tự "ăn tiền" (xếp theo: đã-chốt-quy-định × $ × bravo-fit × ít-judgment)
| Bậc | Sản phẩm | Vì sao | judgment | Trạng thái |
|---|---|---|---|---|
| **0** | **Tax & AP engine** (hoá đơn XML → định khoản nháp · cross-check hoá đơn-tờ khai) | hoá đơn điện tử = XML cấu trúc → trích xuất tất định, $ rõ | thấp | thiết kế xong |
| **0+** | **Tuân thủ TT99** (remap CoA cấp≥2 + sinh "Accounting Policy Regulation" + bù-trừ hợp nhất) | **quy định ĐÃ CHỐT 1/1/2026, phổ cập, cơ học** | thấp | chat-opus đang code `app/accounting/` |
| **1** | **AR collections** (aging → draft nhắc nợ chờ duyệt) | close-the-loop khớp nhất; outcome = DSO | thấp | thiết kế xong |
| **2** | **Anomaly/fraud** (engine cờ + LLM diễn giải) | chỉ FLAG → judgment thấp; chống thất thoát | thấp | thiết kế xong |
| **3** | **Trợ lý thuế VN** (cross-check + quyết toán + giải trình) | **VN-native moat** cao | thấp-TB | thiết kế xong |
| **Sau** | **Agent VAS↔IFRS** (mapping/dual-ledger/disclosure) | thị trường hẹp, **judgment RẤT cao**, lộ trình biến động | **cao** ⚠️ | để sau, cần pilot |

> Mọi agent **dùng chung 1 khuôn**: đọc ERP (read-only) → engine tất định tính → LLM gợi ý/diễn giải (không sinh số) → verify-gate → **draft chờ duyệt** → outcome đo được. ⇒ xây thêm agent = **thêm "đầu", tái dùng "đuôi"**.

## 4. Định giá (khung — CẦN khảo sát giá VN)
- **HYBRID per-site/per-module + outcome credits** (số hoá đơn xử lý · draft duyệt · cờ hợp lệ) — KHÔNG per-query (on-prem).
- **Freemium:** chat tra cứu "included" (mồi); **agent tài chính/AP/anomaly/thuế = trả tiền**.
- **On-prem** dịch inference cost sang CapEx khách → **biên có thể > 50-60% peers cloud**.
- ⚠️ **Giá thị trường VN + willingness-to-pay = chưa có dữ liệu** (mọi vòng research đều thiếu) → **cần khảo sát sơ cấp**.

## 5. Lộ trình BUILD (bám [MATURITY-LADDER](MATURITY-LADDER.md))
1. **L1→L2 (gần nhất):** deploy demo online ([DEPLOY-DEMO](DEPLOY-DEMO.md)) + product-surface ([PRODUCT-SURFACE](PRODUCT-SURFACE.md)) + corpus thật (Docling/bge-m3). Cổng: người lạ tự dùng online.
2. **Engine bậc 0/0+:** use-case A (parser hoá đơn) + TT99 compliance (chat-opus đang làm) — demo được trên mock/hoá đơn mẫu, **không cần ERP**.
3. **Agent #1 AR collections** (mock trước) → **#2 Anomaly** → **#3 Thuế** — mỗi cái **pilot đo ROI** trước khi mở rộng.
4. **Mở khoá data thật:** khi BRAVO giao **ERP read-only API** → cắm DataSource thật (engine ERP-agnostic, đổi 1 lớp).
5. **Sàn chủ quyền thật:** Qwen local (Ollama/vLLM) → moat on-prem hết "ảo" + đo pass^k.

## 6. Cảnh báo trung thực (xuyên suốt 3 vòng research)
- **ROI agent tài chính công bố = vendor-marketing, không sống sót kiểm chứng** (9 claim bị bác) → **đừng trích vào sales; đo bằng pilot.**
- **0 dữ liệu giá/đối thủ VN** ở mọi vòng → cần **khảo sát sơ cấp**.
- **Phụ thuộc cứng:** ERP read-only API chưa có (chặn data thật) · Qwen local chưa chạy (sovereignty còn "ảo") · pilot/user thật = 0.
- **Ranh giới bất biến:** AI **không tự quyết** fair value/impairment/xử-lý-thuế-phức-tạp/xoá-nợ; **không tự gửi/nộp/ghi**; chỉ draft chờ duyệt. Mọi ROI = **kỳ vọng phải chứng minh qua pilot**.

---
> **Tinh thần:** một engine + nhiều agent dùng chung khuôn *"deterministic + LLM-in-slot + draft chờ duyệt"*; ưu tiên cái **đã-chốt-quy-định + ít-judgment + tái-dùng-nhiều** (TT99 → AP → AR → Anomaly → Thuế), để IFRS judgment-heavy lại sau. Thắng bằng **leo bậc (deploy → pilot → bán)**, không bằng thêm tính năng.
