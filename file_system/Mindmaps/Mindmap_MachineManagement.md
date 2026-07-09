# Phân hệ Quản lý máy móc, thiết bị

## 1. Quản lý Hồ sơ Máy móc, Thiết bị
### 1.1. Danh mục Máy móc, Thiết bị
- *Mục đích:* Lưu trữ thông tin tổng quát và chi tiết cấu hình của từng thiết bị.
- *Thông tin quản lý cốt lõi:* Mã, Số VIN/Serial, Nguồn gốc (Hãng, Xuất xứ), Thông số kỹ thuật (Công suất), Thời hạn bảo hành, Phân xưởng/Bộ phận quản lý.
- *Quản lý cấu trúc (Tab chi tiết):*
  - Danh mục chi tiết máy (Các cụm máy, bộ phận).
  - Danh mục linh kiện, phụ tùng đi kèm.
  - Chứng chỉ, kiểm định (Cảnh báo thời hạn).
  - Tài liệu đính kèm (Hướng dẫn sử dụng, Catalog).

### 1.2. Khai báo Chu kỳ & Định mức Bảo dưỡng
- *Mục đích:* Làm cơ sở cho việc lập kế hoạch bảo dưỡng tự động.
- *Tham số then chốt:* 
  - Mã máy/Bộ phận máy, Hạng mục bảo dưỡng.
  - Chu kỳ (Tính theo Ngày/Tháng/Năm hoặc Dựa trên Thống kê hoạt động).
  - Định mức nguyên vật liệu tiêu hao cho bảo dưỡng.

## 2. Luồng Nghiệp vụ Bảo dưỡng (Maintenance Workflow)
- **Quy trình chuẩn:** Kế hoạch / Yêu cầu -> Thực hiện Bảo dưỡng -> Bàn giao.
- **Kế hoạch bảo dưỡng:**
  - *Cơ sở lập:* Dựa trên dự tính chu kỳ bảo dưỡng hoặc kế hoạch sản xuất.
  - *Tham số:* Hạng mục bảo dưỡng, Dự kiến bắt đầu/hoàn thành, Phân loại Thuê ngoài hay Tự làm.
- **Phiếu yêu cầu bảo dưỡng:**
  - *Áp dụng:* Khi phát sinh nhu cầu gia cố, bảo dưỡng trước hạn từ bộ phận vận hành.
- **Phiếu bảo dưỡng máy móc, thiết bị:**
  - *Kế thừa:* Lấy chi tiết từ **Kế hoạch bảo dưỡng** hoặc **Phiếu yêu cầu bảo dưỡng**.
  - *Kết quả thực hiện:* Trạng thái sau bảo dưỡng, Chi phí phát sinh, Chi tiết vật tư tiêu hao thực tế.
- **Biên bản bàn giao:**
  - *Mục đích:* Xác nhận bàn giao thiết bị sau khi bảo dưỡng xong cho đơn vị vận hành.

## 3. Luồng Nghiệp vụ Sửa chữa (Repair Workflow)
- **Quy trình chuẩn:** Báo hỏng / Sự cố -> Kế hoạch sửa chữa (kèm Mua vật tư) -> Thực hiện Sửa chữa.
- **Ghi nhận sự cố:**
  - **Phiếu báo hỏng:** Ghi nhận lỗi/hiện tượng nhỏ từ bộ phận vận hành (thiết bị có thể vẫn đang chạy).
  - **Biên bản sự cố:** Áp dụng cho hỏng hóc lớn, dừng máy. *Kế thừa:* Có thể lấy dữ liệu từ **Phiếu báo hỏng**. Ghi nhận nguyên nhân và chốt phương án sửa chữa.
- **Kế hoạch sửa chữa:**
  - *Kế thừa:* Chọn máy từ **Phiếu báo hỏng** hoặc **Biên bản sự cố**.
  - *Chi tiết:* Hạng mục sửa chữa, thời gian dự kiến, thực hiện nội bộ hay thuê ngoài.
- **Yêu cầu mua vật tư sửa chữa, bảo dưỡng:**
  - *Tác dụng:* Đề xuất mua sắm linh kiện, vật tư khi trong kho không đủ để thực hiện sửa chữa.
- **Phiếu sửa chữa máy móc, thiết bị:**
  - *Kế thừa:* Từ **Kế hoạch sửa chữa**.
  - *Kết quả:* Cập nhật trạng thái thiết bị, ghi nhận chi phí và vật tư thực tế đã thay thế.

## 4. Các Nghiệp vụ Khác & Xử lý đặc thù
- **Thống kê hoạt động máy móc:**
  - *Mục đích:* Theo dõi tần suất, thời gian, số lượng hoạt động (VD: số km, số giờ chạy). Dữ liệu này được làm đầu vào để tính toán thời điểm bảo dưỡng thay vì mốc thời gian cố định.
- **Quản lý Chứng chỉ, Đăng kiểm:**
  - *Cảnh báo:* Tự động cảnh báo các chứng chỉ, kiểm định sắp hết hạn để gia hạn.
- **Biên bản thanh lý:**
  - *Xử lý thiết bị hết khấu hao/hỏng không thể phục hồi.* Thanh lý và loại bỏ thiết bị khỏi luồng vận hành.

## 5. Hệ thống Báo cáo Quản trị (Reports)
- **Báo cáo lịch sử bảo dưỡng, sửa chữa:**
  - Khả năng truy vết (Traceability) ngược lại chứng từ gốc. Nắm bắt được toàn bộ vòng đời bảo trì của thiết bị.
- **Báo cáo dự tính kế hoạch bảo dưỡng theo chu kỳ:**
  - Hiển thị trực quan mốc thời gian (bôi màu) các hạng mục cần bảo dưỡng trong tương lai dựa vào chu kỳ và thống kê hoạt động.
- **Báo cáo nhu cầu vật tư bảo dưỡng định kỳ:**
  - So sánh và tổng hợp lượng vật tư dự kiến cần dùng để chuẩn bị kho tồn.
- **Báo cáo lịch sử cấp mới/sửa đổi chứng chỉ:** 
  - Theo dõi biến động về pháp lý, kiểm định an toàn thiết bị.
