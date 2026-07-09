# Các quy tắc cơ bản (General Rules)

## 1. Khởi động và làm quen với giao diện
- Cung cấp các thao tác ban đầu khi đăng nhập vào hệ thống BRAVO 10.
### Màn hình đăng nhập
- **Tham số then chốt:** Tên người dùng, Mật khẩu, Đơn vị cơ sở, Kết nối.
- **Quên mật khẩu:** Xác thực qua Email/Số điện thoại bằng mã OTP. Đổi mật khẩu sau khi xác thực thành công.
- **Xác thực 2 yếu tố (2FA):**
  - **Phương thức:** Ứng dụng Authenticator (Google, Microsoft) quét mã QR hoặc nhập mã; Xác thực qua SMS/Email.
  - **Xử lý ngoại lệ:** Nhập sai mã quá 5 lần sẽ khóa tài khoản trong 5 phút. 
- **Mã Captcha:** 
  - BRAVO Captcha (nhập tay khi sai mật khẩu quá 5 lần).
  - Google ReCaptcha V3 (tự động).
- **Đăng nhập SSO:** Cho phép sử dụng tài khoản Google, AppleId, Microsoft, Facebook.

## 2. Màn hình chính
- Giao diện tổng quan sau khi đăng nhập thành công.
### Các thành phần chính
- **Hệ thống Menu và Thanh công cụ:** Chứa các lệnh gọi đến chức năng trong chương trình.
- **Panel Phân hệ:** Phân chia các chức năng theo phân hệ. Liệt kê các chức năng liên quan ở dưới phân hệ đang chọn.
- **Dashboard:** Thể hiện thông tin tổng quan của phân hệ, gồm:
  - **Báo cáo nhanh (Widget):** Biểu đồ trực quan, hỗ trợ lọc ngày tháng, lọc danh sách giá trị. Tính năng kéo thả, phóng to, thay đổi loại biểu đồ, liên kết dữ liệu giữa báo cáo mẹ-con.
  - **Quy trình:** Sơ đồ quy trình nghiệp vụ, thể hiện luồng dữ liệu bắt đầu và kết thúc (ví dụ quy trình bán lẻ).
  - **Báo cáo:** Liệt kê các báo cáo liên quan phân hệ.

## 3. Hệ thống Menu và Thanh công cụ
### Hệ thống Menu
- **Cấu trúc phân cấp:** Danh mục, Chứng từ, Tổng hợp (tính giá, kết chuyển, số dư đầu kỳ), Báo cáo, Hệ thống (sao lưu, phân quyền), Tùy chọn (ngôn ngữ, cỡ chữ).
- **Tính năng tìm kiếm:** Tìm nhanh mọi chức năng không cần phân biệt dấu (ví dụ: "Danh muc vat tu").
### Thanh công cụ
- Chứa các lệnh thao tác thường xuyên tùy vào chức năng đang mở.
- **Phím tắt quan trọng:** Thêm mới (F2), Bản sao mới (Ctrl+F2), Mở (F3), Tải lại (F5), Tìm nhanh (Ctrl+F), Chuyển nhóm (F6), Gộp mã (Ctrl+F6), In (F7), Đình chỉ (F8).

## 4. Giao diện Danh sách (Explorer) & Giao diện cập nhật (Editor)
### Giao diện Danh sách (Explorer)
- **Danh mục:** Hiển thị cây danh mục (trái) và danh sách chi tiết (phải).
- **Chứng từ phát sinh:** Hiển thị danh sách chứng từ, mẫu in. Hỗ trợ "Duyệt" và "Duyệt và ký số" đảm bảo tính hợp lệ pháp lý.
### Giao diện cập nhật (Editor)
- Dùng để xem, sửa, thêm mới bản ghi.
- **Kiểm soát tính hợp lệ:** Cảnh báo đỏ (lỗi vi phạm, chặn lưu), Cảnh báo vàng (nhắc nhở, cho phép lưu).
- **Luồng thao tác:** Nhập liệu chi tiết, có thể copy/paste từ Excel vào Grid chi tiết.

## 5. Giao diện Báo cáo (Reporter)
- Khung điều kiện lọc (bên trái) và kết quả báo cáo (bên phải).

## 6. Các quy tắc hệ thống
### Quy tắc đặt mã
- Không chứa ký tự đặc biệt (`% [ , ; : | ] = { } '`).
- Độ dài nhỏ hơn hoặc bằng giới hạn quy định.
- Mã phải là duy nhất.
### Quy tắc làm tròn số
- Làm tròn Thành tiền: Nhập lại số tiền khác (kết quả Số lượng x Đơn giá) trong phạm vi Chênh lệch cho phép.
- Làm tròn Thuế GTGT: Nhập lại số tiền thuế GTGT khác kết quả tính toán trong phạm vi cho phép.

## 7. Các chức năng cơ bản trên bảng dữ liệu
### Tìm kiếm nhanh (Ctrl+F)
- **Tìm trong nội dung hiển thị:** Tô màu vàng kết quả.
- **Tìm theo cột hiện thời:**
  - Hỗ trợ phép toán AND, OR.
  - Các toán tử nâng cao: `%` (A%Z), `~` (A~Z), `&` (A&Z), `+` (A+Z).
  - Lọc nội dung chứa, bắt đầu, kết thúc, rỗng, không chứa.
### Thao tác trên bảng Grid
- **Sắp xếp:** A-Z, Z-A, sắp xếp theo nhiều cột.
- **Nhóm dữ liệu:** Gom nhóm các bản ghi theo 1 cột hoặc nhiều cột.
- **Tính tổng cộng:** Dòng trên cùng / Dòng dưới cùng.
- **Tùy chỉnh hiển thị:** Đánh số thứ tự dòng, Cố định cột, Ẩn/Hiện cột, Giãn cách dòng, Tùy chỉnh độ rộng cột tự động/mặc định.
### Import dữ liệu
- Nguồn: Excel, Txt, Xml.
- Các bước: Chọn file -> Ánh xạ trường dữ liệu (Mapping) -> Import.
- Hỗ trợ lưu thiết lập Import, báo lỗi Validate rõ ràng (cảnh báo đỏ, vàng).
### Export (Kết xuất) dữ liệu
- Nguồn ra: Excel, Word, PDF.
- Hỗ trợ kết xuất dữ liệu đang chọn, xuất theo định dạng đang hiển thị trên Grid, hoặc xuất dữ liệu thô (ItemId).
- Cho phép xuất mỗi báo cáo/nhóm ra file riêng hoặc sheet riêng.
- Có thể gửi email tự động sau khi kết xuất.

## 8. Danh sách Phím tắt (Phím nóng)
- F1: Trợ giúp.
- F2 / Ctrl+F2: Thêm mới / Bản sao mới.
- F3: Mở / Sửa.
- F5: Refresh.
- F8: Đình chỉ.
- Ctrl+F: Tìm kiếm.
- Ctrl+A: Chọn tất cả.
- Ctrl+S: Lưu dữ liệu và giữ màn hình.
- ESC: Hủy bỏ, thoát.
