# VAS ↔ IFRS — cơ hội ăn tiền cho BRAVO (phân tích sơ bộ)

> ⚠️⚠️ **TRẠNG THÁI: CHƯA WEB-VERIFY.** Deep-research bị **đụng giới hạn phiên** (session limit, reset 3:30pm Asia/Bangkok) → không chạy được. Đây là **phân tích từ kiến thức nền** (độ tin cậy thấp hơn báo cáo MONEY-SPOTS đã kiểm chứng 3-phiếu). **Phải chạy lại deep-research sau khi reset** để xác minh — đặc biệt: **mốc thời gian bắt buộc IFRS** (rất biến động), quy mô thị trường, giá đối thủ. Mọi số/mốc dưới đây **cần kiểm chứng**.

---

## 1. Lộ trình IFRS-VN (cần verify từng mốc)
- **Quyết định 345/QĐ-BTC (16/3/2020)** — lộ trình áp dụng IFRS:
  - **2022–2025: TỰ NGUYỆN** — công ty mẹ tập đoàn nhà nước, DN niêm yết, công ty đại chúng quy mô lớn, **DN FDI** có nhu cầu+năng lực (cho BCTC hợp nhất/riêng).
  - **Sau 2025: BTC quyết định phạm vi BẮT BUỘC** dựa trên đánh giá — dự kiến bắt buộc BCTC hợp nhất cho một số đối tượng; còn lại tự nguyện.
  - ⚠️ **Tới 2026, mốc bắt buộc CHƯA chốt cứng / có thể hoãn** — VN đang xây **VFRS** (chuẩn VN mới hướng IFRS) làm cầu nối. **PHẢI verify trạng thái hiện tại** (có thông tư/quyết định 2025-2026 mới không).
- **TT99/2025** = hiện đại hoá hệ tài khoản, **hướng dần IFRS** (một bước trong lộ trình).

## 2. "Pain" đắt tiền (vì sao có $)
- **Dual reporting (báo cáo SONG SONG):** giữ **VAS** cho luật định/thuế + lập **IFRS** cho công ty mẹ nước ngoài/chủ nợ quốc tế/IPO. → tốn 2 bộ sổ, đối chiếu liên tục.
- **Chuyển đổi nặng tư vấn:** phí **Big4 cao**, dự án nhiều tháng, judgment nhiều.
- **Đối tượng cần (sẵn sàng trả):** **FDI** (mẹ ép IFRS group reporting), **niêm yết/pre-IPO**, DN **vay vốn/gọi vốn nước ngoài**, mục tiêu **M&A**. → segment HẸP nhưng **túi sâu**.

## 3. Khác biệt VAS-IFRS khó/tốn — và ranh giới AI nên/KHÔNG nên
| Chuẩn mực | Độ judgment | AI giúp được? |
|---|---|---|
| IFRS 16 thuê (right-of-use, nợ thuê) | thấp-TB (cơ học) | ✅ tính/dựng bút toán, AI assist tốt |
| IAS 12 thuế hoãn lại | TB (cơ học) | ✅ tính chênh lệch tạm thời |
| IFRS 15 doanh thu (5 bước) | TB (vừa cơ học vừa judgment) | ⚠️ assist phần cơ học |
| IFRS 9 công cụ tài chính (ECL, fair value) | **CAO** | ❌ AI KHÔNG quyết — chỉ surface dữ liệu |
| IAS 36 suy giảm giá trị (impairment) | **RẤT CAO** | ❌ AI KHÔNG quyết — judgment con người |
| IFRS 13 giá trị hợp lý | **CAO** | ❌ KHÔNG quyết |
| IAS 40 BĐS đầu tư / IAS 41 nông nghiệp | CAO | ❌ (liên quan khách BĐS/SX của BRAVO) |

> **Nguyên tắc:** IFRS **nặng ước tính + rủi ro pháp lý/kiểm toán** → AI là **trợ lý phần cơ học (~80%) + tra cứu có dẫn chứng**, **con người sở hữu judgment**. BCTC IFRS sai do AI = rủi ro nghiêm trọng → **verify-gate + HITL + audit-trail của bravo là ĐIỀU KIỆN**, không phải tuỳ chọn.

## 4. Money spot VAS/IFRS (xếp hạng sơ bộ — cần verify $)
| # | Cơ hội | AI làm được | bravo | Đối thủ |
|---|---|---|---|---|
| 1 | **Mapping chuyển đổi VAS→IFRS** (tài khoản→dòng IFRS) | ✅ cơ học, reusable | ❌ thiếu (mở rộng map-TT99 engine) | Big4·Tagetik |
| 2 | **Dual-ledger / posting song song** | ✅ cơ học | ❌ thiếu | Tagetik·OneStream |
| 3 | **Sinh thuyết minh/footnote IFRS** (disclosure) | ✅ AI draft + người duyệt | ❌ thiếu (hợp draft+verify đã có) | Workiva |
| 4 | **Gap analysis / readiness** (sổ VAS vs yêu cầu IFRS) | ✅ khảo sát + cờ | ❌ thiếu | Big4 |
| 5 | **Tra cứu chuẩn mực + tuân thủ liên tục** (VAS/IFRS/TT99) | ✅ RAG có dẫn chứng | ✅ **CÓ** (thế mạnh chat) | Big4 (người) |
| 6 | Lập BCTC IFRS đầy đủ | ⚠️ nhiều judgment | ❌ (cao rủi ro) | Big4 |

## 5. Định giá + ai mua (sơ bộ — cần verify)
- **Hai dòng tiền:** (a) **dự án chuyển đổi** (one-time, cạnh Big4, rẻ hơn) + (b) **subscription dual-reporting/compliance liên tục** (recurring, biên cao).
- **Định vị bravo:** **on-prem + VN-native + rẻ hơn Big4 + grounded-không-bịa-số** cho một deliverable bị kiểm toán → khác biệt vs Big4 (đắt, người) và Workiva/Tagetik (đắt, quốc tế, không VN-native).
- **Đối thủ:** Big4 (tư vấn, đắt) · Workiva/CCH Tagetik/Fluence/OneStream (disclosure/CPM, đắt) · ERP nội (MISA/FAST/BRAVO — chủ yếu VAS, IFRS còn niche). **Cần verify cách họ tính tiền.**

## 6. GAP map về bravo
- 🔴 **BỔ SUNG:** engine mapping VAS→IFRS · dual-ledger · sinh disclosure · gap-analysis.
- 🟠 **TĂNG CƯỜNG:** **chat tra cứu chuẩn mực** (nạp corpus VAS/IFRS/TT99 — đúng thế mạnh RAG của bravo; money-spot #5 dễ nhất, làm được sớm).
- 🟢 **GIỮ:** verify-gate (BCTC IFRS sai = rủi ro → bán được niềm tin) · draft+HITL (judgment ở người) · citations (audit-trail kiểm toán) · RLS.
- 🟡 **SỬA định vị:** **đừng quảng cáo "AI lập BCTC IFRS"** (judgment+liability) → định vị "trợ lý phần cơ học + tra cứu chuẩn mực có dẫn chứng, kế toán/kiểm toán sở hữu kết luận".

## 7. Phán quyết chiến lược (trung thực)
VAS/IFRS là **money-spot giá trị cao NHƯNG HẸP + PHỨC TẠP + nặng JUDGMENT + nặng LIABILITY**. Hấp dẫn ($ + moat) nhưng **RỦI RO cho một AI chưa chứng minh** (sai trong BCTC kiểm toán = nghiêm trọng).
> **Khuyến nghị thứ tự:** VAS/IFRS nên là **nước đi SAU** — sau khi cụm **AP/TT99** (đơn giản hơn, $ rõ hơn, ít judgment hơn, demo được không cần ERP) đã chứng minh nền tảng. **Đừng nhảy vào IFRS conversion trước khi proven các money-spot dễ hơn.** Điểm vào AN TOÀN NHẤT cho VAS/IFRS ngay bây giờ = **#5 (chat tra cứu chuẩn mực)** — rủi ro thấp, dùng đúng thế mạnh RAG, làm được sớm; còn mapping/dual-ledger/disclosure để sau.

## 8. Cảnh báo (vì chưa verify)
- **Toàn bộ doc này CHƯA web-verify** — chạy lại deep-research sau 3:30pm để xác minh.
- **Mốc bắt buộc IFRS-VN không chắc** — QĐ 345 "sau 2025" có thể đã đổi/hoãn; PHẢI tra văn bản mới nhất trước khi dùng bán hàng.
- **Quy mô thị trường + willingness-to-pay + giá đối thủ** = chưa có dữ liệu (như MONEY-SPOTS: giá VN vẫn là ẩn số).
- **bravo hiện CHƯA có gì** trong mảng VAS/IFRS (gap lớn nhất) — mọi cơ hội = tiềm năng, chưa phải năng lực.
