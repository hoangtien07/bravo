# Phân hệ Quản lý sản xuất

## 1. Định nghĩa Sản phẩm & Năng lực (Master Data)
### 1.1. Định nghĩa Sản phẩm & Quy trình
- **Danh mục Công đoạn sản xuất:** Thời gian sản xuất, Thời gian chờ, Sản lượng/lần, Công đoạn giá thành (Kế toán).
- **Quy trình sản xuất:** Thiết lập chuỗi các công đoạn nối tiếp nhau cho từng phân loại sản phẩm.
- **BOM (Định mức nguyên vật liệu):**
  - *BOM Nguyên sinh:* Dùng để dự báo, lập kế hoạch mua hàng.
  - *BOM Sản xuất:* Dùng để xuất vật tư thực tế và kiểm soát tiêu hao.
  - *Tham số:* Hao hụt cho phép (%), Phân loại vật liệu (Chính/Phụ).
- **Yêu cầu thay thế nguyên vật liệu:** Khai báo vật tư thay thế, hệ số quy đổi để sử dụng linh hoạt khi thiếu vật tư gốc.

### 1.2. Quản lý Năng lực Sản xuất
- **Nhà máy, Phân xưởng & Dây chuyền:** Khai báo cơ cấu tổ chức sản xuất.
- **Công suất & Hệ số:**
  - *Công suất giờ hoạt động:* Số giờ tối đa/ngày, số lượng nhân công, tỷ lệ sai hỏng cho phép.
  - *Năng lực dây chuyền:* Khai báo công suất sản lượng (SP/Giờ) cho từng thiết bị.
  - *Hệ số sản xuất:* Hệ số chia sẻ dây chuyền khi sản xuất nhiều sản phẩm cùng lúc.
- **Nhật ký & Hiệu suất:**
  - *Nhật ký giờ hoạt động máy:* Ghi nhận giờ chạy thực tế và các khoảng thời gian dừng máy (sự cố).
  - *Đánh giá OEE (Hiệu suất thiết bị tổng thể):* = A (Sử dụng) x P (Hiệu suất) x Q (Chất lượng).

## 2. Luồng Hoạch định & Điều phối (Planning & Scheduling)
### 2.1. Dự báo & Kế hoạch tổng thể
- **Dự báo kế hoạch sản xuất tổng thể:**
  - *Thuật toán:* Nhu cầu (Dự kiến tiêu thụ + Tồn tối thiểu + Xuất khác) - Khả năng đáp ứng (Tồn kho + Dự kiến mua + Nhập khác) = Số lượng cần sản xuất.
- **Kế hoạch sản xuất tổng thể:** Kế hoạch khung (Tháng/Quý/Năm).
- **Nhu cầu vật tư theo KHSX:** Nhân BOM dự báo với KHSX tổng thể để ra yêu cầu mua sắm.

### 2.2. Điều phối & Kế hoạch chi tiết
- **Kế hoạch sản xuất chi tiết:** Phân rã kế hoạch tổng thể xuống cấp độ Tuần/Ngày, giao đích danh cho Phân xưởng, Dây chuyền, Công đoạn.
- **Lệnh sản xuất:**
  - *Chức năng:* Lệnh thực thi giao cho tổ đội. Lấy trực tiếp từ KH chi tiết.
  - *Phân loại:* Lệnh mới, Lệnh điều chỉnh, Lệnh thay thế.
  - *Tiện ích:* Tự động tính "Nhu cầu NVL" từ BOM và Số lượng lệnh.

## 3. Luồng Thực thi Sản xuất (Execution)
### 3.1. Quản lý Vật tư Sản xuất
- **Yêu cầu xuất vật tư:** Gửi bộ phận kho để lĩnh vật tư phục vụ Lệnh sản xuất.
- **Yêu cầu nhập vật tư:** Trả vật tư thừa hoặc Nhập kho Thành phẩm / Bán thành phẩm sau khi hoàn thành.
- **Thống kê tiêu hao nguyên vật liệu:** Ghi nhận thực tế vật tư đã sử dụng.

### 3.2. Quản lý Tồn kho tại Xưởng (Shop-floor Inventory)
- *Tính năng:* Quản lý kho độc lập tại xưởng (không phụ thuộc kho kế toán).
- *Quy trình:* Tồn đầu kỳ -> Phiếu nhập/xuất tại xưởng -> Kiểm kê tại xưởng -> Xử lý chênh lệch kiểm kê tự động (Tạo phiếu nhập thừa/xuất thiếu) -> Chuyển tồn sang năm sau.

### 3.3. Thống kê Kết quả & Chấm công
- **Thống kê sản lượng:** Ghi nhận số lượng Đạt, Phế phẩm (NG) theo Ca, Máy, Nhân viên, Lệnh sản xuất.
- **Thống kê tồn kho & Chuyển ca:** Tính tự động Tiêu hao = Tồn đầu + Nhập - Xuất - Tồn cuối (kiểm kê chuyển ca).
- **Thống kê yếu tố ảnh hưởng:** Ghi nhận hỏng khuôn, thiếu vật tư, nhân sự vắng mặt.
- **Thống kê nhân sự & Tổng hợp lương:**
  - Lấy danh sách điểm danh theo Tổ/Ca.
  - Phân bổ lương sản phẩm: (1) Đích danh người trực tiếp, (2) Chia tỷ lệ theo Tổ/Hệ số cá nhân, (3) Phân bổ cho Gián tiếp (Quản đốc).

## 4. Xử lý Ngoại lệ & Quản trị dữ liệu (Control & Reports)
### 4.1. Khóa dữ liệu Sản xuất
- *Khóa số liệu thống kê:* Chốt dữ liệu sản lượng, tiêu hao, nhật ký máy theo giờ/phút.
- *Khóa kế hoạch, lệnh:* Chốt không cho sửa đổi theo thời gian vĩ mô (ngày/tháng).

### 4.2. Hệ thống Báo cáo
- **Báo cáo Kế hoạch:** Bảng theo dõi tiến độ thực hiện Kế hoạch/Đơn hàng/Lệnh sản xuất.
- **Báo cáo OEE & Nhật ký:** Tổng hợp giờ chạy máy, Phân tích hiệu suất OEE.
- **Báo cáo Truy xuất nguồn gốc:** Truy vết (Traceability) ngược từ Sản phẩm bán ra -> Lệnh sản xuất -> Lô vật tư -> Lịch sử kiểm tra chất lượng.
