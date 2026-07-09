# Quản lý quan hệ khách hàng (CRM)

## 1. Quy trình tổng quát
Hệ thống CRM hỗ trợ quản lý xuyên suốt 3 giai đoạn:
- **Marketing:** Thu thập đầu mối (Leads) từ nhiều nguồn, triển khai các chiến dịch tiếp thị.
- **Bán hàng (Sales):** Chuyển đổi đầu mối thành Khách hàng tiềm năng, quản lý Cơ hội bán hàng và chốt đơn.
- **Chăm sóc khách hàng (CSKH):** Quản lý khiếu nại, hỗ trợ sau bán, khảo sát mức độ hài lòng.

## 2. Quản lý Dữ liệu Khách hàng
### Quản lý Đầu mối (Leads)
- Lưu trữ thông tin sơ bộ của cá nhân/tổ chức quan tâm.
- Nguồn thu thập: Lấy tự động qua API từ Facebook, Zalo, Website hoặc nhập thủ công.
- **Xử lý dữ liệu:** Hệ thống cung cấp tính năng "Kiểm tra trùng lặp dữ liệu đầu mối" (theo Số điện thoại, Email, CMND/CCCD, Mã số thuế) để gộp và loại bỏ các bản ghi rác.
### Khách hàng tiềm năng (Prospects)
- Đầu mối được chuyển đổi thành Khách hàng tiềm năng khi xác nhận có nhu cầu thực tế.
- **Phân loại và Theo dõi:** 
  - Phân loại theo Mức độ quan tâm, Ngành nghề, Nguồn tìm kiếm.
  - Kanban view: Kéo thả trạng thái khách hàng (Quan tâm, Đã liên hệ, Đã gửi báo giá...).
- Có thể chuyển đổi lên Khách hàng chính thức.
### Quản lý Đối thủ cạnh tranh
- Lưu trữ thông tin đối thủ (Điểm mạnh, Điểm yếu, Giá cạnh tranh) phục vụ cho đánh giá cơ hội bán hàng.

## 3. Marketing và Tương tác tự động
### Chiến dịch Marketing
- Khai báo ngân sách, mục tiêu doanh thu, chi phí dự kiến/thực tế, và các vật phẩm (POSM) sử dụng trong chiến dịch.
- Đánh giá hiệu quả chiến dịch thông qua việc gán các Đầu mối, Cơ hội bán hàng vào Chiến dịch.
### Tích hợp Gửi Email (Mailchimp) và SMS (Brandname)
- Cấu hình API liên kết với nhà cung cấp (Mailchimp, Stringee...).
- Xây dựng kho Mẫu Email (định dạng HTML) và Mẫu Tin nhắn.
- Tự động lấy danh sách khách hàng (Audience) vào các chiến dịch gửi Email/SMS. Hỗ trợ các thẻ cá nhân hóa (`{=CustomerName}`, `{=Tel}`).
- Theo dõi nhật ký gửi: Số lượng thành công, lỗi, tỷ lệ mở email.

## 4. Quản lý Cơ hội Bán hàng (Opportunities)
- Ghi nhận thông tin nhu cầu: Sản phẩm quan tâm, Số lượng, Đơn giá dự kiến, Giá trị cơ hội, Tỷ lệ thành công.
- Theo dõi lịch sử giao dịch: Ghi chú lại từng lần gọi điện, gặp mặt, email với khách hàng.
- Kết thúc cơ hội: Đánh dấu Thành công (tạo báo giá, đơn hàng) hoặc Thất bại (Khai báo Lý do thất bại).

## 5. Chăm sóc Khách hàng và Khảo sát
### Quản lý Giao dịch và Khiếu nại
- **Giao dịch CSKH:** Ghi nhận các hoạt động tương tác (gọi điện, bảo hành, hỏi thăm). Đánh giá chất lượng dịch vụ và thái độ nhân viên.
- **Yêu cầu / Khiếu nại:** Ghi nhận sự cố, phân công nhân sự xử lý, theo dõi trạng thái (Chờ xử lý, Đang xử lý, Hoàn thành), và ghi nhận biện pháp phòng ngừa.
### Khảo sát Khách hàng
- **Thiết kế bộ câu hỏi:** Trực quan trên giao diện Web (Kéo thả). Hỗ trợ các dạng: Text ngắn, Checkbox, Radio, Rating, Hình ảnh, Tải file.
- Gửi phiếu khảo sát qua Email/SMS chứa link khảo sát (dạng Web/Mobile view).
- Thu thập và lưu trữ kết quả trả lời tự động vào hệ thống.

## 6. Hệ thống Báo cáo Quản trị CRM
- **Báo cáo Marketing:** Báo cáo tăng trưởng khách hàng theo chiến dịch, Thống kê số lượng khảo sát, Phân tích kết quả khảo sát (Tỷ lệ %).
- **Báo cáo Bán hàng:** Phân tích cơ hội bán hàng giữa các kỳ (Tỷ lệ chuyển đổi), Tổng hợp phễu bán hàng (Sales Funnel).
- **Báo cáo CSKH:** Phân tích mức độ hài lòng, Thống kê khiếu nại theo sản phẩm/lý do.
