# SƠ ĐỒ TƯ DUY NGHIỆP VỤ: QUẢN LÝ MUA HÀNG (BRAVO 10)
> *Bản Mindmap này được thiết kế theo tiêu chuẩn Business Analysis, bao gồm toàn bộ luồng dữ liệu, tham số nghiệp vụ, công thức tính toán và xử lý ngoại lệ.*

## 1. PHÁT SINH NHU CẦU & YÊU CẦU MUA HÀNG
### 1.1. Kế hoạch mua hàng (Master Plan)
- **Đối tượng áp dụng**: Mặt hàng có nhu cầu sử dụng lớn, cần lưu kho dự phòng, mặt hàng hiếm/khan hàng.
- **Chu kỳ lập**: Cuối năm (cho năm sau) hoặc cuối quý (cho quý sau).
- **Công cụ kế thừa tự động**: `Lấy nhu cầu theo dự kiến tiêu thụ`.
- **Tham số cấu hình trọng yếu**:
  - `Kỳ kế hoạch`: Theo Năm / Quý / Tháng.
  - `Kế hoạch điều chỉnh`: Cho phép cập nhật bổ sung. **Công thức**: `Tổng nhu cầu = Kế hoạch gốc + Tổng các kỳ điều chỉnh`.
  - `Vùng`: Phân mảnh kế hoạch theo khu vực địa lý.

### 1.2. Yêu cầu mua hàng (Phân loại theo mục đích)
*Được chia làm 3 nghiệp vụ chuyên biệt với luồng kế thừa dữ liệu (Data Lineage) khác nhau:*
1. **Mua Nguyên, nhiên, vật liệu** (Phục vụ sản xuất - Cấp thiết)
   - *Kế thừa từ*: Kế hoạch sản xuất / Lệnh sản xuất / Dự kiến tiêu thụ.
2. **Mua Vật tư sửa chữa, bảo dưỡng, lắp đặt** (Duy trì tuổi thọ máy móc)
   - *Kế thừa từ*: Kế hoạch bảo dưỡng (Hệ thống tự động tính từ *Định mức bảo dưỡng máy móc*).
3. **Mua hàng khác** (Công cụ, dụng cụ tiêu hao văn phòng)

**Các công cụ AI/Gợi ý tự động của hệ thống:**
- `Yêu cầu theo hạn mức tồn`: Đối chiếu Tồn kho hiện tại với Tồn Tối thiểu/Tối đa -> Tự động đưa ra số lượng "Gợi ý mua".
- `Xem tồn kho tức thời`: Hiển thị nhanh số lượng và giá trị tồn tại thời điểm thực.
- `Theo dõi kế hoạch mua hàng`: Cảnh báo tiến độ thực hiện so với ngân sách kế hoạch.

### 1.3. Tổng hợp yêu cầu mua hàng (Gom đơn)
- **Mục đích**: Chuyển từ "Mua lẻ tẻ" sang "Mua tập trung số lượng lớn" để ép giá (Discount) và phân bổ KPIs cho từng Nhân viên mua hàng.
- **Tính năng `Khoảng lấy dữ liệu`**: Tham số thời gian (Số ngày). Bằng tổng thời gian `NCC đáp ứng + Tìm kiếm + Phê duyệt`. Hệ thống dùng mốc này quét tất cả các Yêu cầu chưa hoàn thành để gom tự động.
- **Thuật toán gom**: Tự động cộng gộp (Sum) số lượng theo cùng `Mã vật tư`.
- **Ràng buộc**: Hiển thị `Nhóm hàng mua` để đảm bảo nhân viên không nhận mua chéo mảng của người khác. Tính toán ngược `Ngày cần đặt hàng muộn nhất`.

---

## 2. QUẢN LÝ ĐẶT HÀNG & CHỐT GIÁ
### 2.1. Hai luồng Chiến lược Đặt hàng (Core Strategy)
- **Luồng 1: Quy trình duyệt giá (Hỏi giá mua ngay)**
  - *Áp dụng*: Mặt hàng mới, hiếm, mua không thường xuyên (Spot Buy).
  - *Kết quả (Output)*: Sinh trực tiếp ra `Đơn đặt hàng (PO)`.
- **Luồng 2: Bảng giá mua được duyệt (Tạo bảng giá dài hạn)**
  - *Áp dụng*: Mặt hàng mua thường xuyên, số lượng nhiều, giá ổn định (Blanket Order / Hợp đồng nguyên tắc).
  - *Kết quả (Output)*: Sinh ra `Bảng giá`. Các PO sau này sẽ tự động ép giá theo Bảng giá này, không cần duyệt lại.

### 2.2. Trình tự chứng từ báo giá
1. **Yêu cầu báo giá**: Kế thừa từ `Tổng hợp yêu cầu mua`. Gửi RFQ cho nhiều NCC. Đặt `Ngày đến hạn` để làm deadline.
2. **Báo giá từ NCC**: 
   - Nhập liệu nhiều lần cho cùng 1 yêu cầu (Giá thương lượng Lần 1, Lần 2).
   - Cho phép nhập `Báo giá hàng thay thế` hoặc `Giá theo khoảng số lượng` (Khung giá Volume Discount).
3. **Đề nghị duyệt giá** (Trình Ban Giám Đốc):
   - Quy đổi ngoại tệ (tự động theo tỷ giá tạm tính) để chung mặt bằng so sánh NCC nội/ngoại.
   - Không chỉ so sánh giá gốc, phải nhập chiết khấu, điều khoản thương mại, phí vận chuyển.
   - **Tham số `Giá trị tạm tính`**: 
     - *Toàn đơn*: Chi phí dự tính nếu mua 100% của 1 NCC.
     - *Theo lựa chọn*: Chi phí dự tính theo đúng số lượng thực tế chốt mua (vì có thể chia nhỏ đơn cho nhiều NCC).

### 2.3. Đơn đặt hàng mua (PO)
- **Quy tắc kế thừa**: 
  - Nếu đi theo *Luồng 1*, lấy thẳng từ Đề nghị duyệt giá. 
  - Nếu đi theo *Luồng 2*, lập PO mới và hệ thống chỉ cho phép chọn vật tư có trong Bảng giá (tự ép đơn giá).
- **Phân bổ ngược**: 1 Đơn hàng (mua tập trung) tự động phân bổ số lượng trả về các `Yêu cầu mua hàng` lẻ ban đầu để đóng tiến độ.
- **Trạng thái `Đơn hàng đóng`**: Đóng tự động khi kho nhập đủ hàng, HOẶC tích đóng thủ công để ép kết thúc hợp đồng trước hạn.

---

## 3. QUẢN LÝ NHẬP HÀNG & NGOẠI LỆ
- **Lệnh nhập hàng**: Phiếu trung gian báo trước cho Thủ kho chuẩn bị vị trí, nguồn lực và cho KCS chuẩn bị dụng cụ kiểm tra chất lượng.

### 3.1. Các loại Phiếu Nhập Kho
*Mỗi loại phiếu có bộ hạch toán Tài khoản (TK) khác biệt hoàn toàn:*
1. **Phiếu nhập mua (Hàng nội địa)**
   - Khai báo Hóa đơn (1 hoặc nhiều VAT).
   - **Xử lý Chiết khấu (CK)**: 
     - *CK mặt hàng* = % CK * Thành tiền mặt hàng.
     - *CK tổng* = Phân bổ ngược số tiền CK tổng xuống từng mặt hàng theo cơ sở `Tỷ lệ Giá trị` hoặc `Tỷ lệ Số lượng`.
     - *Tiền thanh toán* = Thành tiền gốc - (CK mặt hàng + CK tổng đã phân bổ).
   - **Hạch toán**: Tăng Tồn kho (152/156), Tăng Thuế (1331), Tăng Công nợ (331). Mã kho bắt buộc nhập đúng để hệ thống tính Giá vốn.

2. **Phiếu nhập khẩu (Hàng quốc tế)**
   - Sử dụng `Tỷ giá hải quan` riêng biệt.
   - **Tự động tính 4 loại thuế chuyên ngành** (Căn cứ trên Giá trị tính thuế của Hải quan):
     - Thuế Nhập khẩu (TK 33332)
     - Thuế Tiêu thụ đặc biệt (TTĐB - TK 3332)
     - Thuế Bảo vệ môi trường (TK 3338)
     - Thuế GTGT hàng nhập khẩu (TK 33312)
   - **Công thức Giá trị Nhập kho**: `Tiền hàng gốc - Chiết khấu + Thuế NK + Thuế TTĐB + Thuế BVMT`.

3. **Phiếu nhập xuất thẳng (Mua về xài ngay)**
   - Vừa là phiếu nhập, vừa kiêm phiếu xuất. (Số lượng Nhập = Xuất).
   - **Hạch toán ngoại lệ**: `TK Nợ` không ghi vào Tồn kho mà ghi thẳng vào **Tài khoản Chi phí/Sử dụng** (TK Xuất). Mã kho tại đây không có ý nghĩa tính giá vốn.

### 3.2. Xử lý Chi phí mua hàng
- **Loại phí**: Vận chuyển, bốc dỡ, lưu bãi, chạy thử.
- **Tiêu thức phân bổ**: Chia tiền phí này đập vào giá trị hàng nhập kho theo 1 trong 3 cơ sở: `Giá trị`, `Số lượng`, hoặc `Trọng lượng`.
- *Lưu ý*: Có thể thực hiện lập phiếu Chi phí riêng, hoặc nếu biết chính xác thì ghi thẳng tiền phí vào từng dòng trên Phiếu nhập mua.

### 3.3. Xuất trả lại nhà cung cấp
- **Lý do**: Sai quy cách, rớt KCS, kém phẩm chất.
- **Logic Tài chính**: Hạch toán Nợ/Có NGƯỢC với phiếu nhập. Hệ thống khóa cứng `Đơn giá` và `Giá vốn` bằng đúng phiếu nhập gốc để giảm trừ công nợ chính xác.

---

## 4. QUẢN LÝ THANH TOÁN
- **Quy trình**: Phiếu nhập kho (Công nợ) -> Đề nghị thanh toán -> Phiếu Chi / Ủy nhiệm chi (UNC) / Séc / Báo nợ (Thực hiện bởi Kế toán).

---

## 5. QUẢN TRỊ NHÀ CUNG CẤP (VENDOR MANAGEMENT)
### 5.1. Thiết lập Cấu trúc Đánh giá
- **Tiêu chí đánh giá**:
  - *Theo điểm số*: Có `Hệ số` (Trọng số) và `Điểm tối đa`.
  - *Theo mô tả*: Đánh giá định tính văn bản.
- **Tham số đánh giá (Bộ tiêu chuẩn)**: 
  - Khớp nối các Tiêu chí thành 1 nhóm. Map vào từng loại `Ngành hàng/Vật tư` (Ví dụ: VPP sẽ dùng Bộ tham số A, Máy móc dùng Bộ tham số B).
  - *Constraint*: Không được phép sửa/xóa Bộ tiêu chuẩn nếu đã có phiếu đánh giá phát sinh (Đảm bảo tính toàn vẹn dữ liệu).

### 5.2. Vận hành Đánh giá (PDCA Flow)
1. **Kế hoạch đánh giá (Plan)**: 
   - *Phân loại*: Đánh giá định kỳ (NCC cũ) / Đánh giá NCC mới.
   - *Kỳ hạn*: Tháng/Quý/Năm.
2. **Tự động Giao việc (Do)**: Hệ thống sinh hàng loạt phiếu đánh giá (Auto-gen) -> Tạo `Công việc` (Task) giao cho từng nhân sự phụ trách kèm Deadline.
3. **Phiếu đánh giá (Check)**: Người dùng chấm điểm. Hệ thống tự nhân với Hệ số tính ra `Tổng điểm đạt được` và quy đổi ra `Tỷ trọng` so với điểm tối đa.

---

## 6. HỆ THỐNG BÁO CÁO MUA HÀNG (DASHBOARDS)
*Hệ thống được chia làm 4 nhóm mục tiêu quản trị:*

### 6.1. Nhóm Quản trị Giá (Pricing)
- **Lịch sử biến động giá mua**: So sánh đối chiếu `Giá gốc` (giá mua trần) và `Giá NET` (Giá cuối sau khi trừ Chiết khấu và cộng Thuế nhập khẩu/TTĐB/BVMT). Giúp dự báo xu hướng thị trường.
- **Phân tích mua hàng**: Xem đa chiều (Cấp 1: Phân tích theo NCC -> Cấp 2: Drill-down theo Từng mặt hàng).

### 6.2. Nhóm Kiểm soát Tiến độ (Tracking)
- **Sổ theo dõi yêu cầu mua hàng (Tổng hợp/Chi tiết)**: Bản đồ nhiệt cho thấy tiến độ của 1 Yêu cầu hiện đang mắc kẹt ở khâu nào (Đang báo giá, Đã đặt hàng, hay Đã lệnh nhập).
- **Theo dõi tổng hợp hàng đặt mua**: Giám sát Đơn hàng (PO), biết chính xác hàng nào trễ hẹn.

### 6.3. Nhóm Quản trị Rủi ro NCC (Vendor Performance)
- **Báo cáo phân tích đánh giá theo Kế hoạch**: So khớp Tổng điểm thực tế vs Kỳ vọng để sàng lọc.
- **Báo cáo phân tích theo Thời gian**: Vẽ biểu đồ Performance Trend. Biết được NCC này đang tốt lên hay tệ đi qua các quý.

### 6.4. Nhóm Quản trị Tài chính (AP - Accounts Payable)
- **Sổ tổng hợp phải trả người bán**: Bức tranh Công nợ (Dư Nợ đầu kỳ -> Phát sinh mua -> Phát sinh trả -> Dư cuối kỳ).
