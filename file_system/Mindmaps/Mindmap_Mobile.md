# Ứng dụng Mobile (BRAVO 10)

## 1. Tổng quan & Khởi động
- **Hỗ trợ Đa nền tảng:** iOS (từ 14.0) và Android (từ 7.0).
- **Màn hình khởi động:** Splash screen, Quét mã QR hoặc cấu hình để kết nối với máy chủ hệ thống.
- **Xác thực & Đăng nhập (Login/Authentication):**
  - Đăng nhập cơ bản (Tài khoản/Mật khẩu).
  - Đăng nhập Sinh trắc học (Vân tay, FaceID).
  - Đăng nhập OTP (Xác thực qua SMS/Email).
  - Đăng nhập SSO (Google, Apple, Microsoft Office, Facebook).
  - Đăng nhập Active Directory (AD).
  - Xác thực hai yếu tố (2FA - Two-Factor Authentication): Authenticator App, SMS, Email.
  - Bảo mật bằng Mã Captcha (Google ReCaptcha V3 hoặc Bravo Captcha).
  - Quên mật khẩu.

## 2. Giao diện & Tiện ích Hệ thống
- **Cấu trúc Màn hình chính:**
  - *Tổng quan:* Tất cả chức năng.
  - *Yêu thích:* Các chức năng ghim truy cập nhanh.
  - *Thông báo:* Tin báo từ hệ thống, phân loại (Chưa đọc, Quan trọng, Duyệt chứng từ, Hệ thống).
- **Thiết lập Ứng dụng (Settings):**
  - Giao diện (Sáng / Tối).
  - Ngôn ngữ, Định dạng ngày giờ, Định dạng số, Cỡ chữ.
  - Chuyển đổi Đơn vị cơ sở / Năm làm việc.
- **Tiện ích Tìm kiếm & Thao tác dữ liệu:**
  - Tìm kiếm bằng Giọng nói (Voice search).
  - Tìm kiếm bằng Quét mã vạch (Barcode Scanner).
  - Lọc (Filter), Sắp xếp (Sort), Thêm/Sửa/Xóa/Sao chép bản ghi.
  - Nhập liệu vị trí trực tiếp từ Bản đồ (Google Maps/Apple Maps).
  - Upload & Đính kèm: Hình ảnh, Video, File tài liệu, Link URL.

## 3. Quản lý Chức năng & Nghiệp vụ (Modules)
### 3.1. Quản lý Danh mục & Chứng từ (Master Data & Documents)
- *Giao diện Danh sách:* Hiển thị dạng danh sách / dạng hình ảnh (Ví dụ: Danh sách Hàng hóa, Cơ hội bán hàng).
- *Lập chứng từ trực tiếp:* Đơn đặt hàng bán, Báo giá, Phiếu xuất/Nhập kho, Phiếu kiểm kê.
- *Quản lý Nhân sự - Công ca:*
  - Tạo đơn: Xin nghỉ phép, Đi công tác, Đi trễ/về sớm, Làm thêm giờ, Giải trình công.
  - Check in / Check out: Chấm công bằng tọa độ GPS trực tiếp trên Mobile.
  - Xem & Xác nhận Bảng công, Bảng lương cá nhân (Có tính năng gửi phản hồi).
### 3.2. Quản lý Duyệt (Approval Workflow)
- **Trạng thái duyệt:** Chờ duyệt / Đã duyệt / Đã hủy.
- **Màn hình Quản lý Duyệt:** Chờ duyệt, Chờ ký, Nhật ký.
- **Thao tác Duyệt:**
  - Duyệt đơn lẻ / Duyệt hàng loạt.
  - Xem File Mẫu in PDF đính kèm trước khi duyệt.
  - Ký số (Tích hợp App ký số bên thứ 3) hoặc Ký ảnh.

## 4. Tích hợp Trí tuệ Nhân tạo (AI Features)
- **AI Tóm tắt văn bản (Summarize):**
  - Tự động đọc file đính kèm (pdf, docx) và rút gọn nội dung.
  - *Tùy chỉnh:* Hình thức (Đoạn văn / Gạch đầu dòng), Văn phong (Chuyên ngành, Trang trọng, Thoải mái), Ngôn ngữ, Độ dài, Phạm vi trang.
- **AI Dịch văn bản (Translate):**
  - Dịch tự động các trường mô tả, ghi chú sang các ngôn ngữ khác (Anh, Việt, Nhật, Hàn, Trung).
  - *Thao tác:* Chèn đè nội dung gốc hoặc Chèn nối tiếp (Phân tách bằng dấu gạch nối, dấu sẹc...).

## 5. Hệ thống Báo cáo & Bảng điều khiển (Reporting & Dashboard)
### 5.1. Báo cáo (Reports)
- Thể hiện dưới dạng Bảng số liệu hoặc Biểu đồ.
- *Tính năng:* Tùy chỉnh ẩn/hiện cột, ghim cột, sắp xếp, lọc theo tiêu chí (Tháng, Quý, Mã KH...).
- *Xuất & Chia sẻ:* Xem trước mẫu in, Tải xuống File (Excel, PDF, XML), Gửi Email báo cáo trực tiếp từ App.
### 5.2. Dashboard (Bảng điều khiển BI)
- **Thẻ dữ liệu (Card):** Hiển thị số liệu chốt nhanh (Tổng doanh thu, Tổng đơn hàng chờ duyệt).
- **Biểu đồ (Charts):** Cột, Đường, Tròn, Treemap... phục vụ phân tích (Ví dụ: Doanh thu theo vùng, Nhân viên xuất sắc).
- **Phân tích động:**
  - *Mối quan hệ dữ liệu (Relation):* Bấm vào 1 phần tử của biểu đồ này sẽ tự động lọc dữ liệu của biểu đồ khác.
  - Tùy chỉnh bảng màu, Phóng to / Thu nhỏ biểu đồ, Sắp xếp thứ tự các biểu đồ.

## 6. Chế độ Ngoại tuyến (Offline Mode)
- **Mục đích:** Hoạt động khi mất mạng Internet hoặc giảm tải cho máy chủ (Ví dụ: Mang điện thoại vào kho sâu không có Wifi để quét mã vạch kiểm kê).
- **Quy trình:**
  - (1) Thiết lập vùng dữ liệu cần tải (Giới hạn danh mục/chứng từ).
  - (2) Tải xuống dữ liệu (Đồng bộ về thiết bị).
  - (3) Làm việc Offline (Thêm mới, sửa chứng từ kiểm kê).
  - (4) Đồng bộ lên máy chủ (Khi có mạng, đẩy dữ liệu lên và xử lý xung đột nếu có).
  - (5) Dọn dẹp dữ liệu tải xuống (Giải phóng bộ nhớ).
