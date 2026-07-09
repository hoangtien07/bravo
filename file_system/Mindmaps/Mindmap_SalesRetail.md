# Bán lẻ (Sales Retail)

## 1. Quy trình Bán lẻ tổng quát
- **Chuẩn bị:** Thiết lập Bảng giá bán lẻ, Chính sách khuyến mãi, Danh mục máy trạm (gắn với Kho bán lẻ).
- **Thực hiện bán hàng:** Mở phiên bán lẻ -> Tạo Phiếu bán lẻ (Quét mã vạch/Màn hình cảm ứng POS) -> Thanh toán (Tiền mặt, Thẻ, Ví điện tử, Điểm tích lũy, Voucher).
- **Xử lý sau bán:** Hàng bán lẻ bị trả lại -> Điều chỉnh hóa đơn bán lẻ.
- **Cuối ca/Ngày:** Cập nhật bảng kê nộp tiền -> Đóng phiên -> Lập Hóa đơn tổng hợp bán lẻ (để ghi nhận sổ cái kế toán và xuất hóa đơn GTGT).

## 2. Quản lý Thẻ thành viên và Khuyến mãi
### Thẻ thành viên & Điểm thưởng
- **Cấu hình:** Danh mục loại thẻ (Hội viên, Bạc, Vàng, Kim Cương), tỷ lệ quy đổi điểm.
- **Phát hành:** Danh mục thẻ thành viên (Lưu thông tin khách hàng, số điểm, doanh số lũy kế). Tự động nâng hạng thẻ khi đạt mức doanh số.
- **Thanh toán:** Quy định thanh toán bằng điểm thẻ (Số điểm tối đa/1 giao dịch, Khung giờ áp dụng). Hỗ trợ điều chỉnh thủ công điểm/doanh số khi cần.
### Voucher / Phiếu mua hàng
- Danh mục loại phiếu mua hàng (Định nghĩa mệnh giá, chiết khấu).
- Danh mục phiếu mua hàng: Phát hành mã Voucher/Coupon (Có thể sinh hàng loạt tự động). Mỗi mã chỉ dùng 1 lần.
### Chính sách khuyến mãi bán lẻ
- **Loại khuyến mãi:**
  - `BOGO` (Buy One Get One): Khuyến mãi tặng hàng.
  - `ITEM`: Chiết khấu/Giảm giá trên từng mặt hàng.
  - `TRANSACTION`: Chiết khấu trên tổng hóa đơn.
  - `PACK`: Khuyến mãi mua theo Combo/Gói.
  - `ROLLING`: Khuyến mãi lũy tiến theo các mức số lượng.
- **Điều kiện áp dụng linh hoạt:** Khung giờ vàng, Ngày cụ thể trong tuần, Sinh nhật khách hàng, hoặc theo Thẻ thành viên.

## 3. Quản lý Ca / Phiên làm việc & Thiết bị
- **Máy trạm làm việc:** Cấu hình tên máy trạm thu ngân, gắn mặc định với 1 Kho hàng bán lẻ.
- **Phiên bán lẻ:** 
  - Quản lý mở/đóng phiên theo từng thu ngân.
  - Cuối phiên lập "Bảng kê nộp tiền bán lẻ" (để bàn giao tiền mặt theo từng mệnh giá, biên lai quẹt thẻ).

## 4. Thực hiện Giao dịch Bán lẻ (POS)
### Phiếu bán lẻ
- Lược bỏ các trường hạch toán kế toán phức tạp. Tối ưu tốc độ bán hàng.
- Hỗ trợ mã vạch chuẩn (EAN13) và mã vạch sinh từ cân điện tử (Mã hàng + Số lượng/Trọng lượng).
- Hỗ trợ màn hình POS Cảm ứng (phù hợp mô hình F&B - Food & Beverage): Chia nhóm mặt hàng trực quan bằng hình ảnh, thêm ghi chú (ít đá, nhiều đường...).
- Cho phép mở đồng thời nhiều Tab (nhiều hóa đơn) cùng lúc để chờ thanh toán.
### Thanh toán Ví điện tử
- Khai báo tích hợp Ví điện tử (VNPay, MoMo...).
- Tạo mã QR động trực tiếp trên màn hình để khách quét thanh toán.
- Ghi nhận và đối soát qua "Giao dịch thanh toán ví điện tử", "Giao dịch hoàn tiền ví điện tử".
### Hàng bán lẻ bị trả lại & Điều chỉnh
- Nhập số Hóa đơn bán lẻ gốc để lấy lại danh sách mặt hàng và giá.
- Lập chứng từ hàng bán lẻ trả lại để hoàn tiền và nhập lại kho.
- Điều chỉnh hóa đơn bán lẻ dùng khi thu ngân thao tác sai (Điều chỉnh mặt hàng, số lượng, đơn giá).

## 5. Tổng hợp Kế toán và Báo cáo
### Hóa đơn tổng hợp bán lẻ
- Do các "Phiếu bán lẻ" không hạch toán sổ cái, cuối ngày kế toán sử dụng chức năng này để gom tất cả phiếu bán lẻ trong ngày thành 1 Hóa đơn GTGT tổng hợp, ghi nhận doanh thu, thuế, và giá vốn lên sổ kế toán.
### Báo cáo Bán lẻ
- Bảng kê chứng từ bán lẻ.
- Báo cáo tồn kho bán lẻ (Theo từng cửa hàng/đơn vị cơ sở).
- Phân tích hiệu quả điểm bán lẻ (Dựa trên diện tích sàn, số lượng nhân viên).
- Thống kê số lượng giao dịch và doanh số theo Thẻ thành viên.
- So sánh tình hình thực hiện chương trình khuyến mãi (Kỳ này vs Kỳ trước).
