# Các chức năng hệ thống (System)

## 1. Nhật ký sử dụng chương trình (Log)
- Theo dõi và lưu vết mọi hoạt động trên hệ thống để phục vụ kiểm soát, kiểm toán và bảo mật.
- **Phân loại nhật ký:**
  - **Nhật ký cập nhật dữ liệu:** Ghi lại thao tác Thêm mới, Sửa, Xóa bản ghi. Chỉ rõ giá trị cũ và giá trị mới của từng trường thông tin bị thay đổi.
  - **Nhật ký khai thác dữ liệu:** Ghi lại thao tác Mở xem báo cáo, In ấn, Kết xuất (Export), Tải file đính kèm.
  - **Nhật ký quản trị:** Ghi nhận lịch sử Đăng nhập/Đăng xuất, giao dịch API, các tác vụ sao lưu, thay đổi phân quyền.

## 2. Quản lý khóa dữ liệu
- Chốt số liệu, ngăn chặn thay đổi (sửa, xóa, thêm mới) sau khi đã quyết toán.
- **Phạm vi khóa:**
  - Khóa dữ liệu chung (năm làm việc).
  - Khóa dữ liệu theo phân hệ: Quản lý nhân sự (chấm công, lương), Kiểm tra chất lượng (QC), Sản xuất.
  - Khóa dữ liệu riêng theo từng Người dùng.

## 3. Quản trị Người dùng và Phân quyền truy cập
### Quản lý người sử dụng
- Quản lý tài khoản đăng nhập, phương thức xác thực (Mật khẩu, 2FA, SSO qua Google/Microsoft/Facebook).
- Quản lý thiết bị truy cập: Cấp phép truy cập chỉ từ một số thiết bị/máy tính cụ thể.
### Phân quyền linh hoạt
- **Phương pháp:** Phân quyền Trực tiếp, Phân quyền theo Nhóm, Phân quyền theo Vai trò (Role-based). Hỗ trợ Ủy quyền tạm thời theo lịch.
- **Đối tượng phân quyền:**
  - Đơn vị cơ sở (Công ty con, Chi nhánh).
  - Nền tảng sử dụng (Desktop, Web, Mobile).
  - Màn hình chức năng (Main, Dashboard, Màn hình phân hệ).
  - Lệnh chức năng (Cho phép/Cấm: Thêm, Sửa, Xóa, In, Kết xuất).
  - Cấp độ Layout và Control: Phân quyền ẩn/hiện từng màn hình nhập liệu, từng trường thông tin (ô nhập, nút bấm).
  - **Phân quyền dữ liệu đặc thù:** Phân quyền Kho (chỉ được thao tác trên kho được cấp), Ẩn cột giá trị (Limited Amount View) đối với thủ kho.

## 4. Khai báo Chứng từ và Quy trình
- **Danh mục chứng từ:** Quy định định dạng tự động đánh số chứng từ (ví dụ: `BCDDMMYY###`), trạng thái mặc định, tài khoản ngầm định.
- **Quy trình duyệt chứng từ:**
  - Thiết lập bước duyệt, vai trò duyệt.
  - Gán chữ ký số/chữ ký ảnh. Tự động thiết kế mẫu in để gắn chữ ký điện tử.
- **Danh mục kiểu giao dịch:** Quy định sẵn các mẫu định khoản để áp dụng cho chứng từ.

## 5. Tiện ích số liệu và Dữ liệu hệ thống
- **Kiểm tra số liệu:** Tự động rà soát tính toàn vẹn (Lỗi thiếu đối tượng công nợ, số dư lệch, xuất nhập vòng tròn...).
- **Dọn dẹp & Cắt dữ liệu:** Xóa vĩnh viễn hoặc nén dữ liệu cũ (nhật ký, thông báo) để tối ưu hiệu năng. Hỗ trợ cắt hẳn dữ liệu của năm tài chính cũ.
- **Chuyển số dư:** Chuyển số dư tài khoản và tồn kho vật tư sang năm tài chính mới.
- **Sao lưu cơ sở dữ liệu:** Thiết lập sao lưu tự động (Full, Differential, Copy_Only), mã hóa file sao lưu, đẩy lên Cloud (Google Drive, OneDrive).

## 6. Đặt lịch tự động (Job Scheduler)
- Lên lịch để chương trình tự động chạy các tác vụ: Hạch toán định kỳ, Sao lưu, Dọn dẹp dữ liệu, Kết xuất và Gửi báo cáo qua Email.
- Thiết lập tần suất: Hàng giờ, hàng ngày, hàng tuần, hàng tháng.

## 7. Hệ thống Thông báo và Email
- **Cấu hình Email/SMS:** Khai báo SMTP Server, tạo các bộ tham số và mẫu Email tự động (Ví dụ: Email nhắc việc, Email tuyển dụng).
- **Gửi thông báo:** Đẩy thông báo trực tiếp qua App Mobile, Web hoặc Desktop.
- **Quản lý lịch sử gửi Email:** Truy vết trạng thái Gửi thành công/Thất bại. Hỗ trợ chức năng "Gửi lại" hoặc "Chặn gửi lại".

## 8. Ứng dụng AI (Trí tuệ nhân tạo)
- **Scan CV:** Tự động nhận diện và bóc tách thông tin từ file hồ sơ ứng viên để điền vào hệ thống.
- **AI Tóm tắt văn bản:** Tóm tắt file đính kèm (PDF, Word) theo tùy chọn (Đoạn văn/Danh sách), phong cách (Trang trọng/Chuyên ngành/Thoải mái), độ dài (Ngắn/Vừa/Dài).
- **AI Dịch văn bản:** Dịch đa ngôn ngữ (Anh, Nhật, Hàn, Trung) cho các diễn giải chứng từ, tên tài liệu, hoặc văn bản trong báo cáo. Hỗ trợ chèn trực tiếp nội dung dịch vào trường dữ liệu.
