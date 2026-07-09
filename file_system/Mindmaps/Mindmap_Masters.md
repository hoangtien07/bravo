# Khai báo danh mục và cập nhật số liệu đầu kỳ (Masters)

## 1. Một số vấn đề chung về danh mục
- Là bước thiết lập cấu trúc nền tảng cho hệ thống (đối tượng, tài khoản, vật tư...). Cần tuân thủ quy tắc đặt mã để đảm bảo tính đồng bộ, khoa học.
- **Thao tác cơ bản:** 
  - Truy cập thông qua hệ thống Menu hoặc dùng chức năng tìm kiếm nhanh.
  - Cấu trúc giao diện danh mục gồm: Thanh công cụ, Cây danh mục / Nhóm dữ liệu, Khung hiển thị chi tiết bản ghi.
  - Phím tắt: Thêm (F2), Sửa (F3), Lưu (Ctrl+S / Ctrl+Enter).
- **Tính năng mở rộng:**
  - **Gộp mã (Ctrl+F6):** Dùng để gộp các mã bị trùng lặp (khách hàng, tài khoản) vào cùng một mã mới, dữ liệu phát sinh đi kèm tự động chuyển theo.
  - **Chuyển nhóm (F6):** Kéo thả bản ghi từ nhóm này sang nhóm khác trên cây danh mục.
  - **Tìm kiếm nâng cao:** Tìm kiếm theo điều kiện (Lớn hơn, Nhỏ hơn, Bằng) và theo các tiêu chí kết hợp.

## 2. Các danh mục cốt lõi
### Danh mục tài khoản kế toán
- Khai báo các tài khoản dùng để hạch toán nghiệp vụ.
- **Các cờ (flags) quan trọng:**
  - Tài khoản sổ cái: Có hiển thị lên sổ cái hay không.
  - Theo dõi chi tiết: Công nợ theo đối tượng, giá thành, ngoại tệ, ngân hàng, hợp đồng, khoản mục.
  - Vế tăng công nợ: Giúp tự động tính toán, hạch toán đối trừ công nợ.

### Danh mục đối tượng
- Quản lý Khách hàng, Nhà cung cấp, Nhân viên...
- **Phân loại đối tượng:** 0 - Khách lẻ, 1 - Cá nhân, 2 - Tổ chức, 3 - Đơn vị nội bộ.
- **Tính chất:** Cờ "Là khách hàng" sẽ liên kết với phân hệ CRM.

### Danh mục loại giao dịch
- Quy định chi tiết các mẫu nghiệp vụ trong từng loại chứng từ kế toán.
- **Tham số ngầm định:** Cấu hình sẵn Tài khoản hạch toán, Công đoạn, giúp tự động sinh bút toán khi lập chứng từ, giảm thiểu thao tác thủ công.
- Tùy chọn riêng theo đơn vị cơ sở nếu có đặc thù.

### Danh mục thuế GTGT
- Quản lý các loại thuế suất, cách tính thuế.
- **Phân loại:** Thuế đầu vào (1), Thuế đầu ra (2).
- **Tính chất:** Tính khấu trừ hay trực tiếp.
- **Cờ:** "Giá đã bao gồm thuế GTGT" giúp tự động tách thuế.

### Danh mục tiền tệ
- Quản lý đồng tiền và tỷ giá ngoại tệ.
- **Tham số quy tắc:** 
  - Cấu hình mức độ làm tròn số thập phân.
  - Cho phép khoảng "Chênh lệch tiền hàng" và "Chênh lệch tiền thuế" (để xử lý các sai số làm tròn khi làm việc với hóa đơn thực tế).
- **Tỷ giá chi tiết:** Quản lý tỷ giá mua vào, bán ra, trung bình theo từng ngày.

### Danh mục kho hàng
- Nơi lưu trữ vật tư hàng hóa.
- **Cờ (Flags) quản lý:**
  - "Cho phép xuất khi chưa đủ hàng" (cho phép xuất âm kho).
  - "Theo dõi tồn kho theo vị trí" (Bin/Location).
  - "Kho bán hàng online", "Kho hàng đi đường" (dùng cho luân chuyển hàng giữa các chi nhánh).

### Danh mục vật tư, hàng hóa
- Nơi quản lý thông tin sản phẩm, vật tư, dịch vụ.
- **Cờ (Flags) cấu hình đặc tính hàng hóa:**
  - Quản lý theo lô (Lot) / Hạn sử dụng.
  - Quản lý theo số Serial.
  - Cờ "Là đồng phục", "Nhóm hàng QC" (kiểm tra chất lượng).
  - Cờ In tem từ cân điện tử, Mã vạch (Barcode).
- **Thuế và chi phí:** Thiết lập sẵn mã thuế VAT bán lẻ, thuế TTĐB, thuế môi trường để tự động áp dụng khi bán.
- **Sản xuất:** Định nghĩa phân loại sản phẩm để tính giá thành, yếu tố chi phí dở dang...

## 3. Các danh mục phục vụ kết chuyển và định kỳ
### Danh mục bút toán định kỳ
- Khai báo các bút toán phát sinh lặp lại hàng tháng (tiền thuê nhà, phân bổ cố định...).
- Thông số: Giao dịch, Đối tượng, Số tiền, Số tháng thực hiện.

### Danh mục bút toán kết chuyển
- Thiết lập quy tắc kết chuyển cuối kỳ (kết chuyển doanh thu, chi phí xác định kết quả kinh doanh).
- **Loại kết chuyển:**
  - 1: Kết chuyển số dư cuối (đưa số dư về 0).
  - 2: Kết chuyển số phát sinh (cân bằng nợ - có).
  - 3: Kết chuyển riêng cho tài khoản VAT (133 và 331).
- Hỗ trợ kết chuyển theo Công đoạn để tính giá thành sản xuất.

## 4. Cập nhật Số dư và Dữ liệu đầu kỳ
Chỉ thực hiện MỘT LẦN khi bắt đầu triển khai hệ thống mới.
- **Số dư đầu kỳ tài khoản:** 
  - Nhập chi tiết theo Tài khoản, Đối tượng công nợ, Công trình. 
  - Bao gồm Dư Nợ/Có đầu kỳ (tiền hạch toán và nguyên tệ).
- **Tồn kho đầu kỳ:** 
  - Khai báo vật tư, kho chứa, số lượng, giá trị đầu kỳ.
  - Nếu vật tư có theo dõi Lô/Serial thì phải nhập chi tiết số lô/số serial tương ứng.
- **Kế hoạch tài chính:** Cập nhật Kế hoạch doanh thu, chi phí, doanh số ký theo phòng ban/vùng.
- **Phát sinh quá khứ:** Khai báo lại các chứng từ đã phát sinh ở kỳ trước để phục vụ đối chiếu công nợ, hạn thanh toán trong kỳ hiện tại.
- **Thông báo phát hành hóa đơn:** Khai báo dải số hóa đơn điện tử / hóa đơn tự in đã đăng ký với cơ quan thuế để tiếp tục xuất hóa đơn.
