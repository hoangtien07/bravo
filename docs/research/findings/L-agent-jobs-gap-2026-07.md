# L — Nghiệp vụ agent thực chạy của đối thủ + Gap-analysis cho BRAVO (2026-07)

> Deep research đa nguồn, kiểm chứng đối kháng 3 phiếu (25 claim verify → **20 confirmed, 5 refuted**),
> chạy 2026-07-05. Nối tiếp bộ [A–K](SUMMARY.md). Mục tiêu: xem BRAVO còn **thiếu nghiệp vụ gì** so
> với các AI agent kế toán/AP đang thực sự vận hành production.
> ⚠️ **Đọc kèm caveat §6:** phần lớn nguồn là trang sản phẩm/case study của chính vendor (best-case,
> chưa kiểm toán độc lập). Marketing MISA về AVA đặc biệt không đáng tin ở chi tiết (xem §5).

---

## 0. TL;DR

Bộ nghiệp vụ AP agent **hội tụ** (xuất hiện lặp ở cả đối thủ VN Bizzi lẫn quốc tế Basware/Stampli/Vic.ai):

> **capture đa kênh → GL coding tự học → 2/3-way match → duplicate/validity check → auto-post 2 chiều vào ERP.**

Danh sách này gần như trùng khớp giữa VN và quốc tế → đây là **lõi ngành**, không phải đặc thù thị trường.

**BRAVO đang có:** parse XML deterministic → định khoản nháp TT99 (rule-based) → maker-checker → **xuất Excel/CSV**.
**BRAVO thiếu (xếp hạng ở §4):** ① thu thập hoá đơn tự động, ② **ghi thẳng ERP 2 chiều** (moat cấu trúc), ③ validity+blacklist NCC, ④ duplicate detection, ⑤ 3-way match, ⑥ coding tự học, ⑦ KPI touchless, ⑧ OCR (ưu tiên thấp ở VN).

**Ba insight chiến lược:**
1. **Maker-checker KHÔNG phải điểm yếu.** Stampli — top thị trường — định vị chính thức *"Touchless AP is a myth"*, luôn để người duyệt trước khi post. BRAVO không cần bỏ maker-checker; cần **nâng phần "AI làm việc" TRƯỚC cổng duyệt**.
2. **"Ghi thẳng ERP" là killer feature — và là moat riêng của BRAVO.** Mọi vendor quốc tế thành công đều auto-post 2 chiều; đối thủ VN (Bizzi/Vic.ai) phải tích hợp ERP NGOÀI. **BRAVO SỞ HỮU ERP** → không đối thủ nào sao chép được lợi thế này. Nhưng nó mâu thuẫn với quyết định "xuất Excel, không ghi ERP" của [ADR-0016](../../adr/0016-pivot-standalone-ap-vertical.md) — xem §7.
3. **Đặc thù VN xoá gần hết bài toán OCR.** 100% hoá đơn nội địa là **XML có mã cơ quan thuế** → BRAVO đã parse deterministic; OCR giấy/PDF (mà đối thủ Tây tốn công) chỉ còn cần cho hoá đơn nước ngoài/chứng từ phi-hoá-đơn → ưu tiên thấp.

---

## 1. Nghiệp vụ agent thực chạy (Q1)

### (a) Đối thủ Việt Nam
- **Bizzi** (khách thật: Grab, GS25, Circle K, Tiki; >300 triệu USD hoá đơn/tháng theo báo chí vòng gọi vốn 2021):
  - **Capture đa kênh** — email định danh riêng (bot trực 24/7), tra cứu từ **hệ thống hoá đơn cơ quan thuế**, nhận XML/PDF/ảnh. *(confirmed 3-0)*
  - **Validity check + blacklist NCC** — kiểm chữ ký số, mã CQT, trạng thái MST; tra danh sách DN rủi ro cao từ CQT (20+ tiêu chí; GS25 đạt 90% tự động hoá). *(3-0)*
  - **3-way match** PO–GRN–invoice, xử lý ca nhiều-nhiều, khớp→auto-approve / lệch→exception. *(3-0, nhưng nguồn là trang vendor, chưa có case độc lập)*
  - **Duplicate detection** 4 trường (số HĐ/ngày/tiền/NCC) + fuzzy. *(3-0)*
- **MISA** — đã đóng gói agent thành sản phẩm bán được: **"MISA Agentwork"** (có cổng đăng ký, help center, bảng giá — nhưng **không lộ giá**). ⚠️ **CẢNH BÁO:** 3 claim chi tiết về năng lực AVA (3-way match SKU, self-learning coding, kết nối real-time CSDL Tổng cục Thuế) đều **BỊ BÁC 0-3**. Năng lực thật hẹp hơn PR; phần lớn "AI Agent" là **tích hợp meInvoice deterministic có sẵn** đóng gói lại dưới nhãn agent. *(confirmed 3-0 cho việc đóng gói; refuted cho năng lực chi tiết)*
- **FPT AI Agents, Base.vn:** không có claim nào sống sót kiểm chứng → **không đủ bằng chứng** (không kết luận).

### (b) AP automation quốc tế (có scale)
- **Vic.ai** — mức autonomous cao nhất xác minh được về *phạm vi*: ingest→extract→**GL coding đa chiều** (tài khoản/phòng ban/địa điểm)→định tuyến duyệt→**auto-post thẳng ERP** (Sage Intacct, listing chính thức marketplace). Con số best-case vendor-reported: 80% Autopilot / 88% no-touch, coding 95%; giảm 4-5 phút → <2 phút/hoá đơn. *(phạm vi 3-0; các con số cụ thể **2 claim bị bác 0-3** — đọc là best-case marketing)*
- **Stampli** (Billy the Bot) — **human-approve có chủ đích**: AI định khoản từng dòng (học từ lịch sử + từ sửa của người, tự điền khi confidence >80%), 2/3-way match real-time, **nhưng luôn để người duyệt** trước post (*"Touchless AP is a myth"*). Có auto-approve theo rule cho HĐ khớp PO trong tolerance. *(3-0)*
- **Basware** — **kiến trúc chuẩn "tự động hoá phân tầng"**: SmartPDF (PDF→e-invoice) → HĐ **có PO**: auto-match rồi gửi thẳng ERP thanh toán không cần người AP (autonomous); HĐ **không PO**: SmartCoding ML đề xuất (suggest/human-approve). Case RadNet: 85% HĐ-PO không can thiệp, chu kỳ <5 ngày. **Bài học: tách luồng theo có-PO/không-PO và theo ngưỡng confidence, không chọn một mức tự động hoá duy nhất.** *(3-0)*
- **Bill.com / Ramp / Tipalti:** dữ liệu **doanh thu** mạnh (§2) nhưng chi tiết nghiệp vụ agent không qua được verify → không liệt kê job.

### (c) Close/accounting automation & (d) ERP-embedded
- **KHÔNG có claim nào sống sót verify.** Nguồn có tồn tại (Oracle 4 agent GA: Ledger/Payables/Payments/Expenses; Microsoft D365 Account Reconciliation Agent; BlackLine agentic; FloQast AI Agent Builder) nhưng **chưa kiểm chứng đủ** → **mảng đối soát ngân hàng / AR-collections / close / cash-flow forecast HOÀN TOÀN TRỐNG bằng chứng.** Cần vòng nghiên cứu riêng trước khi kết luận BRAVO có nên mở rộng sang đó (open question §6).

**Nghiệp vụ lặp nhiều nhất ở sản phẩm thành công:** capture đa kênh (3 vendor) · 2/3-way match (3) · self-learning coding (3) · auto-post 2 chiều ERP (3) · validity/compliance CQT (2, đặc thù VN) · duplicate detection (2).

---

## 2. Mô hình kiếm tiền (Q2) — trả lời được MỘT PHẦN

**Xác minh mạnh nhất — pricing model:**
- **Basware:** subscription theo **CAM KẾT KHỐI LƯỢNG hoá đơn** (commit càng nhiều → đơn giá/HĐ càng thấp), ICP >50.000 HĐ/năm, không niêm yết giá (bên thứ ba ước $80k–$1M+/năm). → **per-document/volume-tier**, không per-seat. Logic đúng cho AP copilot vì giá trị tỷ lệ số hoá đơn. *(3-0)*

**Doanh thu thật (trích từ nguồn, một số là primary — nhưng KHÔNG qua cổng verify 3-phiếu, đọc thận trọng):**
- **BILL (Bill.com):** ~**1,46 tỷ USD** doanh thu FY2025 (+13% YoY), lãi non-GAAP — **nguồn SEC filing (primary, tin cậy tự thân cao)**.
- **Ramp:** ~**1,5 tỷ USD** annualized (5/2026), underlying profitability +153% YoY, dương free-cash-flow.
- **Tipalti:** vượt **200 triệu USD ARR** (9/2025), $75 tỷ payment volume/năm (+30%).
- → Mô hình kiếm tiền lớn trong ngành nghiêng về **spend/payment volume** (Ramp/Tipalti/BILL) hơn là bán "AI theo seat".

**KHÔNG xác minh được:** ARR/lợi nhuận của Vic.ai, Stampli, HighRadius; **giá bán cụ thể của MISA AVA/Agentwork và Bizzi tại VN** (đây là dữ liệu quan trọng nhất còn thiếu để định giá Copilot AP — cần mystery-shopping).

**Bài học pricing cho BRAVO:** với DN VN, **per-document/volume-tier** (theo số hoá đơn xử lý) hợp lý hơn per-seat — vì giá trị đo bằng khối lượng, và dễ chứng minh ROI. Nhưng cần biết trần giá MISA/Bizzi trước khi chốt (open question).

---

## 3. Yếu tố sống còn + benchmark (Q3)

**KPI khách trả tiền nhắc nhiều nhất:** touchless % · phút(ngày)/hoá đơn · tiền ngăn thất thoát · **tích hợp ERP 2 chiều** · audit trail.

**Benchmark touchless rate (vendor-reported, best-case):**
- Basware marketing: 89% touchless / 99.7% e-invoicing / 85% paid-on-time.
- Case khách THẬT Ritchie Bros: chỉ **65% end-to-end touchless giai đoạn đầu** (kèm ngăn $5M thanh toán trùng, thu $3.5M).
- Vic.ai best-case 78–88%.
- → **Dải thực tế: ~65% giai đoạn đầu, 78–89% best-case.** Đừng lấy 89% làm mục tiêu ra mắt.

**Benchmark chi phí (Ardent Partners 2025 — nguồn trung lập, trích ở tầng search):** cost/invoice ~$10.89 trung bình vs ~$2.78 best-in-class; thời gian xử lý ~10.9 ngày vs ~3.1 ngày. *(chưa qua verify 3-phiếu — dùng làm tham chiếu, không phải fact chốt)*

---

## 4. GAP-ANALYSIS — 8 nghiệp vụ BRAVO còn thiếu (Q4, xếp theo giá trị × khớp kiến trúc × khả thi VN)

| # | Nghiệp vụ thiếu | Vì sao ưu tiên | Khớp kiến trúc BRAVO |
|---|---|---|---|
| **1** | **Thu thập hoá đơn tự động** (cổng thuế + email bot) | Cả MISA lẫn Bizzi đã có; là **cửa vào toàn pipeline**; 100% HĐ VN là XML có mã CQT → chỉ thiếu khâu "kéo về" | Cao — đã parse XML deterministic, thêm connector |
| **2** | **Ghi bút toán 2 chiều vào ERP** (thay Excel/CSV) | Mọi vendor quốc tế thành công đều auto-post; **BRAVO SỞ HỮU ERP → moat không ai copy được** | Cao về dữ liệu, nhưng **mâu thuẫn ADR-0016** (§7) |
| **3** | **Validity check + blacklist NCC** từ CQT | Table-stakes tại VN, **deterministic** (khớp triết lý "không bịa số") | Rất cao — cùng lớp rule engine |
| **4** | **Duplicate detection** 4 trường + fuzzy | Rẻ, deterministic, ROI bằng tiền ($5M case Basware) | Rất cao — logic thuần |
| **5** | **3-way match** PO–GRN–invoice | BRAVO có sẵn **dữ liệu PO/phiếu nhập trong chính ERP** → lợi thế hơn Bizzi (phải tích hợp ngoài) | Cao khi có ERP read API |
| **6** | **Self-learning coding** (định khoản học từ sửa của kế toán) | Nâng nháp TT99 từ rule → học (mô hình Stampli: suggest + auto-fill khi confidence >80%, GIỮ maker-checker) | Trung bình — cần vòng feedback + lưu lịch sử sửa |
| **7** | **Touchless-rate dashboard/KPI** | Khách đo bằng touchless % + phút/HĐ → **không đo được thì không bán được** | Cao — đã có observability nền (W2.2) |
| **8** | **OCR PDF/SmartPDF** cho HĐ nước ngoài + chứng từ phi-HĐ | **Ưu tiên THẤP** ở VN vì XML bắt buộc đã loại nhu cầu OCR nội địa | Trung bình — chỉ cần cho biên |

*(Đối soát ngân hàng, AR/collections, close, cash-flow forecast: **không đủ bằng chứng** để xếp hạng — mảng trống, cần nghiên cứu riêng.)*

---

## 5. Claim BỊ BÁC (đừng tin marketing)
- ✗ AVA kết nối **real-time** CSDL Tổng cục Thuế kiểm trạng thái MST. *(0-3)*
- ✗ AVA làm **3-way match** SKU/số lượng/đơn giá vs PO. *(0-3)*
- ✗ AVA **self-learning coding** theo thói quen kế toán. *(0-3)*
- ✗ Vic.ai 98% accuracy toàn trường / 10+→2 phút. *(0-3)*
- ✗ Countsy 78% Autopilot no-touch. *(0-3)*
→ **Bài học:** không lấy PR của MISA/Vic.ai làm chuẩn năng lực. Năng lực thật hẹp hơn quảng cáo.

## 6. Caveat & câu hỏi mở
- Nguồn **chủ yếu là vendor** (best-case, chưa kiểm toán). Con số touchless/accuracy/phút đọc là "vendor-reported".
- **Coverage thủng:** không claim nào sống sót cho FPT/Base.vn/Tipalti-jobs/close-suite/ERP-embedded → mảng **AR/collections/bank-rec/close/forecast trống bằng chứng**.
- **Câu hỏi mở cần vòng sau:** (1) giá thật MISA Agentwork/Bizzi tại VN? (2) nghiệp vụ agent thật của Oracle/D365/BlackLine/FloQast trong production? (3) touchless trung bình ngành theo nguồn trung lập (Ardent/Hackett)? (4) **API cổng thuế hoadondientu.gdt.gov.vn cho phép tích hợp tự động đến đâu về pháp lý-kỹ thuật** — quyết định độ khả thi gap #1.

---

## 7. Ý nghĩa cho roadmap (đối chiếu ADR-0016 + danh sách đóng băng)

**Xác nhận đúng của ADR-0016:** "ship trên chứng từ upload trước, maker-checker" là đúng — Stampli (top thị trường) chứng minh human-approve vẫn thắng. Giữ nguyên triết lý.

**Căng thẳng cần chủ dự án quyết:**
1. **Gap #2 (ghi thẳng ERP 2 chiều) là killer feature + moat riêng của BRAVO**, nhưng ADR-0016 cố ý **hoãn** ghi-ERP (xuất Excel) để né phụ thuộc .NET API. Nghiên cứu này nói: **xuất Excel chỉ đủ cho pilot; bản bán phải có write-back ERP** — nên **xin ERP read/write API phải nằm trên critical path** cho bản thương mại, không "đóng băng vô thời hạn". Đề nghị: giữ Excel cho L2/pilot, nhưng mở lại đàm phán .NET API song song (nó là moat, không phải nợ).
2. **Gap #3 (validity+blacklist) và #4 (duplicate) trùng một phần với Anomaly agent đang ĐÓNG BĂNG 🧊.** Nghiên cứu cho thấy đây là **table-stakes có người trả tiền**, deterministic, khớp kiến trúc. → Cân nhắc **rã đông có kiểm soát**: không mở lại Anomaly agent chung chung, mà **rút đúng 2 nghiệp vụ này vào Copilot AP** (validity check + duplicate) như tính năng lõi, vì chúng là "cửa" của AP thật.
3. **Gap #1 (thu thập tự động)** là bước rời "upload thủ công" — nên là **hạng mục Wave 3 hàng đầu** ngay sau khi AP chạy trên hoá đơn thật, vì cả 2 đối thủ VN đều đã có và nó là điểm khách so sánh đầu tiên.

**Không nên làm sớm:** AR/collections, close, cash-flow forecast — chưa có bằng chứng khách VN trả tiền + trống dữ liệu nghiên cứu. Giữ đóng băng.

**Nguồn chính:** bizzi.vn (invoice-processing, 3-way, duplicate), amis.misa.vn (AI Agent AVA, bảng giá Agentwork), vic.ai (case studies), stampli.com (Billy, PO-matching, touchless-myth), basware.com (touchless, Ritchie Bros, pricing), sec.gov (BILL 8-K), ardentpartners.com (AP metrics 2025). Danh sách đầy đủ + phiếu verify: transcript workflow `wf_b963e988-af7`.
