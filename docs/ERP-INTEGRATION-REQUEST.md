# Yêu cầu tích hợp với BRAVO ERP (gửi đội kỹ thuật/sản phẩm BRAVO 10)

> Tài liệu này mô tả **3 thứ BRAVO AI Copilot cần từ BRAVO ERP** để làm phần phân tích tài chính, kèm **lý do, hình hài cụ thể, và vị trí đề xuất trong BRAVO 10**. Viết để chuyển cho đội BRAVO ERP xin/triển khai.
>
> *Lưu ý: mô tả "vị trí trong BRAVO 10" dựa trên kiến trúc ERP phổ biến (.NET/SQL Server, có hệ thống báo cáo + chứng từ chờ ghi sổ); đội BRAVO ERP xác nhận lại đúng module/tên gọi thực tế.*

## Bối cảnh 30 giây
BRAVO AI Copilot là lớp AI hỏi-đáp/phân tích **đặt TRÊN** BRAVO ERP, không thay thế. Nó tuân thủ tuyệt đối **nguyên tắc không xâm lấn**: *chỉ ĐỌC dữ liệu ERP qua API một chiều; mọi đề xuất GHI chỉ là bản nháp chờ người duyệt trên giao diện ERP — không bao giờ ghi thẳng vào SQL Server gốc.* Ba yêu cầu dưới đây là hệ quả trực tiếp của nguyên tắc đó.

---

## YÊU CẦU 1 — API đọc một chiều (Read-only REST API)

### Lý do cần
- **An toàn tuyệt đối cho dữ liệu ERP.** AI **không** được kết nối trực tiếp vào SQL Server gốc (rủi ro ghi nhầm, lộ schema, mở rộng bề mặt tấn công). Một **API đọc** là *ranh giới tin cậy* duy nhất giữa AI và dữ liệu — AI chỉ thấy đúng cái API cho phép, không hơn.
- **AI cần số liệu thật để trả lời.** Để trả lời "công nợ quá hạn của khách X?", AI phải đọc được con số từ ERP. Không có API ⇒ AI không có dữ liệu ⇒ hoặc bịa (không chấp nhận được), hoặc vô dụng.
- **Read-only = rủi ro bằng 0 cho nghiệp vụ.** API chỉ đọc thì dù AI có lỗi cũng **không thể làm hỏng dữ liệu kế toán**. Đây là điều kiện để thuyết phục khách hàng cho AI chạm vào dữ liệu tài chính.

### Hình hài cụ thể (ví dụ)
- Một tập **REST endpoint trả JSON**, mỗi endpoint là một truy vấn *đã định nghĩa sẵn* (xem Yêu cầu 2), có tham số:
  ```
  GET /erp/api/v1/metrics/doanh-thu-thuan?ky=2026-Q1&don_vi=CN-HN
  → 200 { "value": 12500000000, "don_vi_tinh": "VND", "ky": "2026-Q1",
          "nguon": "Báo cáo KQKD", "cap_nhat_luc": "2026-06-09T08:00" }
  ```
- **Xác thực service-to-service:** API key hoặc OAuth2 client-credentials cho ứng dụng AI Copilot (không phải tài khoản người dùng).
- **Tài khoản DB phía sau là read-only** (chỉ quyền SELECT trên các view được duyệt).
- Có **rate-limit + audit log** mỗi lời gọi.

### Vị trí trong BRAVO 10
- BRAVO 10 hẳn đã có **tầng truy vấn/báo cáo** (các SQL view, stored procedure sinh ra báo cáo tài chính chuẩn). API đọc này là **một lớp web mỏng (.NET Web API)** đặt **trước** các view/proc đó — *không phải viết lại logic*, chỉ "phơi" cái đã có ra dạng REST có kiểm soát.
- Đặt cùng tầng với các service tích hợp hiện có của BRAVO 10 (nếu có cổng API/web service sẵn thì thêm nhóm endpoint read-only mới).

### Ai làm / mức ưu tiên
- Đội BRAVO ERP dựng. **Ưu tiên: CAO** — đây là cửa khẩu cho toàn bộ phần phân tích tài chính (Phase 2 của AI Copilot). Có thể làm **dần**: bắt đầu với 5–10 chỉ tiêu quan trọng nhất.

---

## YÊU CẦU 2 — Danh mục view/chỉ tiêu (metric) đã được kế toán duyệt

### Lý do cần (quan trọng nhất về mặt độ chính xác)
- **Không để AI tự viết SQL trên ERP.** Nghiên cứu (đã kiểm chứng): AI tự sinh SQL trên CSDL doanh nghiệp thật chỉ đúng **~21%** (so với 91% trên dữ liệu học thuật) — vì DB ERP có hàng nghìn cột, join phức tạp, dễ **đếm trùng (fan-out join)** ⇒ ra số sai *mà vẫn trông như có dẫn chứng*. Đó là kiểu sai nguy hiểm nhất.
- **Giải pháp duy nhất đạt độ chính xác ~100%:** một **"semantic layer"** — tập chỉ tiêu *đã được kế toán định nghĩa & duyệt sẵn*, có ngữ nghĩa đúng (kỳ, đơn vị, nợ/có, kỳ đã khoá sổ). AI **chỉ được chọn** trong danh mục này + điền tham số; **engine (SQL của BRAVO) tính**, AI không tự tính. Câu hỏi ngoài danh mục ⇒ AI **từ chối**, không bịa.
- Nói cách khác: thay vì để AI "đoán" cách tính doanh thu, ta dùng **đúng định nghĩa doanh thu mà BRAVO 10 đã dùng cho báo cáo chính thức** ⇒ số AI trả về **luôn khớp báo cáo BRAVO**, không bao giờ lệch.

### Hình hài cụ thể
- Một **danh sách chỉ tiêu có tên + tham số + định nghĩa SQL**, ví dụ:
  | Mã chỉ tiêu | Mô tả | Tham số | Nguồn (view/proc BRAVO) |
  |-------------|-------|---------|-------------------------|
  | `doanh_thu_thuan` | Doanh thu thuần | kỳ, đơn vị | `vw_KQKD` / proc báo cáo KQKD |
  | `cong_no_qua_han` | Công nợ phải thu quá hạn | kỳ, khách hàng | view công nợ |
  | `ton_kho_cuoi_ky` | Tồn kho cuối kỳ | kỳ, kho, mặt hàng | view tồn kho |
  | `chi_phi_theo_khoan_muc` | Chi phí theo khoản mục | kỳ, đơn vị | view chi phí |
- Mỗi chỉ tiêu = **một SQL view / stored procedure tham số hoá** (đã có hoặc dựng mới), trả về **đúng một con số + đơn vị + nguồn**. AI gọi nó qua Yêu cầu 1.

### Vị trí trong BRAVO 10
- **Đây chính là các báo cáo tài chính BRAVO 10 đã có sẵn** (Báo cáo KQKD, công nợ, tồn kho, chi phí...). BRAVO 10 *đã tính* những con số này cho báo cáo của mình → ta **tái sử dụng định nghĩa đó**, không phát minh lại.
- Cụ thể: nằm ở **tầng SQL view / stored procedure báo cáo** của BRAVO 10. Việc cần làm = **chọn ra ~10–20 chỉ tiêu quan trọng**, đảm bảo chúng **tham số hoá được** (kỳ/đơn vị/đối tượng) và **trả về dạng số gọn** để API phơi ra.
- **Kế toán/chuyên gia nghiệp vụ BRAVO duyệt** ngữ nghĩa từng chỉ tiêu (doanh thu gộp hay thuần? đã trừ VAT? kỳ dồn tích hay tiền mặt?) — đây là phần *con người phải chốt*, AI không tự quyết.

### Ai làm / mức ưu tiên
- **Kế toán/nghiệp vụ BRAVO** chốt danh mục + ngữ nghĩa; **kỹ thuật BRAVO** đảm bảo view/proc tham số hoá. **Ưu tiên: CAO**, làm song song Yêu cầu 1. *(AI Copilot có thể đề xuất danh mục nháp để BRAVO duyệt — giảm việc cho BRAVO.)*

---

## YÊU CẦU 3 — Hàng đợi bản nháp chờ duyệt (Staging / Draft queue)

### Phần này là gì & lý do cần
- **Là gì:** một nơi để AI **đề xuất** bản ghi nghiệp vụ (vd: một **chứng từ/định khoản nháp**) mà **con người phải xem và duyệt** trước khi nó trở thành dữ liệu thật. AI **không bao giờ** ghi thẳng vào sổ.
- **Lý do:** đây là cách *an toàn duy nhất* để AI hỗ trợ tác vụ ghi (Phase 3: soạn nháp chứng từ từ hoá đơn, đề xuất định khoản) mà **không vi phạm nguyên tắc không xâm lấn**. Con người — không phải AI — chịu trách nhiệm cuối cùng. Nghiên cứu cho thấy **79% doanh nghiệp còn thiếu cơ chế giám sát AI agent** → "AI đề xuất, người duyệt" là **điểm bán dẫn đầu thị trường**, không phải hạn chế.

### Hình hài cụ thể
- Một bản ghi nháp có trạng thái **`chờ duyệt`**, gắn cờ **`nguồn = AI Copilot`**, hiện trong một **màn hình "hàng đợi duyệt"** cho kế toán: xem nội dung AI đề xuất → **Duyệt / Sửa / Từ chối**.
- Khi **Duyệt** → bản ghi đi tiếp vào quy trình **ghi sổ bình thường của BRAVO** (như một chứng từ do nhân viên nhập rồi được duyệt). Khi **Từ chối** → huỷ, có ghi lý do.
- AI chỉ được **tạo bản ghi ở trạng thái nháp**; **không** có đường nào để AI tự "ghi sổ".

### Vị trí trong BRAVO 10
- BRAVO 10 hẳn đã có khái niệm **chứng từ chưa ghi sổ / chứng từ chờ duyệt** (luồng *lập chứng từ → duyệt → ghi sổ* là chuẩn của ERP kế toán VN). → **Tận dụng đúng luồng đó:** AI tạo một **chứng từ nháp/chưa ghi sổ** ở *chính nơi* nhân viên nhập liệu tạo ra, **gắn thêm cờ "do AI đề xuất"**, rồi nó chảy qua **quy trình duyệt sẵn có** của BRAVO 10.
- Nếu BRAVO 10 **chưa** phân biệt "nháp do AI": chỉ cần thêm **một trường nguồn (created_by/source = AI)** + (tuỳ chọn) một bộ lọc trong màn hình duyệt để kế toán nhìn riêng các đề xuất của AI.
- Kỹ thuật: cần **một endpoint ghi RẤT HẠN CHẾ** — chỉ tạo được bản ghi **trạng thái nháp/chưa ghi sổ**, tuyệt đối không có khả năng ghi sổ/duyệt.

### Ai làm / mức ưu tiên
- Đội BRAVO ERP (tận dụng workflow duyệt sẵn có). **Ưu tiên: TRUNG BÌNH** — cần cho **Phase 3** (soạn nháp chứng từ), *sau* phần đọc/phân tích. Có thời gian chuẩn bị.

---

## Tóm tắt: BRAVO cần làm gì

| # | Yêu cầu | Bản chất | Ưu tiên | Ai chính |
|---|---------|----------|---------|----------|
| 1 | **API đọc một chiều** | Lớp REST mỏng phơi các view báo cáo (read-only) | 🔴 Cao | Kỹ thuật BRAVO |
| 2 | **Danh mục chỉ tiêu đã duyệt** | Chọn ~10–20 báo cáo/view sẵn có, tham số hoá + duyệt ngữ nghĩa | 🔴 Cao | Kế toán + Kỹ thuật BRAVO |
| 3 | **Hàng đợi nháp chờ duyệt** | Tận dụng luồng chứng từ-chờ-duyệt sẵn có + cờ "do AI" | 🟡 TB (Phase 3) | Kỹ thuật BRAVO |

**Thông điệp chính cho đội BRAVO:** ba thứ này **phần lớn là PHƠI RA cái BRAVO 10 đã có** (báo cáo, view, luồng duyệt chứng từ) qua một lớp API có kiểm soát — *không phải xây lại nghiệp vụ*. AI Copilot chỉ đọc qua cửa đó và đề xuất nháp, giữ an toàn tuyệt đối cho dữ liệu kế toán.

**Phía AI Copilot có thể làm trước (không chờ BRAVO):** toàn bộ tầng tính toán/semantic layer đã code & test với *DataSource giả lập*; khi có Yêu cầu 1+2, chỉ cần ráp `DataSource` thật vào là chạy. (Xem [PLAN.md](PLAN.md) Phase 2.)
