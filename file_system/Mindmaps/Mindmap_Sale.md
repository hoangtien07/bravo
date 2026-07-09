# Quản lý bán hàng (Sale)

## 1. Tổng quan và Quy trình Bán hàng
- Phân hệ giúp tối ưu hóa quy trình bán hàng, tăng cường minh bạch và linh hoạt, kiểm soát công nợ và đánh giá hiệu suất.
- **Quy trình chuẩn:** 
  1. Lập Dự kiến tiêu thụ / Kế hoạch bán hàng
  2. Thiết lập Bảng giá bán buôn / Chính sách khuyến mãi
  3. Cơ hội bán hàng -> Báo giá/Chào hàng -> Hợp đồng nguyên tắc
  4. Đơn đặt hàng bán -> Lệnh xuất hàng -> Kiểm tra chất lượng (QC)
  5. Hóa đơn bán hàng (kiêm xuất kho) / Phiếu giao hàng
  6. Ghi nhận Thanh toán / Xử lý Hàng bán bị trả lại.

## 2. Dự báo và Kế hoạch
### Dự kiến tiêu thụ
- Lập dự kiến số lượng sản phẩm bán ra theo kỳ (Năm, Quý, Tháng). Là đầu vào để bộ phận Sản xuất và Mua hàng lập kế hoạch.
### Kế hoạch bán hàng
- Giao chỉ tiêu Doanh thu cho từng Nhân viên, Kênh bán hàng, Vùng tiêu thụ. 
### Kế hoạch doanh số ký
- Dự báo giá trị hợp đồng ký kết trong tương lai, phục vụ các doanh nghiệp có thời gian thực hiện đơn hàng kéo dài.

## 3. Xúc tiến bán hàng
### Bảng giá và Khuyến mãi
- **Bảng giá bán buôn:** Thiết lập giá bán tiêu chuẩn theo thời điểm. Tự động áp giá khi lập đơn hàng.
- **Chính sách khuyến mãi:** Khai báo điều kiện chiết khấu thương mại (theo tỷ lệ %, theo doanh số đạt được). Tự động tính chiết khấu khi đạt điều kiện.
### Báo giá, Hợp đồng và Đơn hàng
- **Báo giá/Chào hàng:** Ghi nhận giá, chiết khấu, điều khoản thương mại gửi khách hàng.
- **Hợp đồng bán (nguyên tắc):** Thỏa thuận dài hạn về giá cả và chính sách.
- **Đơn đặt hàng bán:** Cam kết pháp lý giao dịch. 
  - **Tính năng nổi bật:** Cờ "Cần giữ hàng" (trừ vào tồn kho khả dụng), Tự động cập nhật trạng thái "Đóng đơn hàng" khi xuất đủ số lượng.
- **Lệnh xuất hàng:** Lệnh nội bộ để bộ phận kho chuẩn bị hàng, làm căn cứ lập Yêu cầu kiểm tra chất lượng (QC) trước khi xuất.

## 4. Thực hiện Bán hàng
### Hóa đơn bán hàng
- Ghi nhận doanh thu, công nợ, thuế GTGT. Tích hợp kiêm Phiếu xuất kho (tự động tính giá vốn).
- Theo dõi mở rộng: Kênh bán hàng, Vùng tiêu thụ, Nhân viên, Hạn thanh toán (tuổi nợ), Biển số xe.
- **Hóa đơn xuất khẩu:** Bổ sung thông tin Số vận đơn, Container, Hãng vận chuyển (không có thuế GTGT, TTĐB).
### Quản lý Hóa đơn Điện tử (HĐĐT)
- **Phát hành:** Tích hợp trực tiếp các nhà cung cấp VAN (Viettel, VNPT, MISA...). Ký số và cấp số hóa đơn tự động.
- **Xử lý sai sót:** 
  - Điều chỉnh hóa đơn (Tăng/Giảm/Điều chỉnh thông tin).
  - Thay thế hóa đơn.
  - Chuyển đổi hóa đơn (In ra giấy đi đường).
  - Giải trình tên người mua/địa chỉ sai.
### Quản lý Giao hàng và Trả lại
- **Phiếu giao hàng:** Kế thừa từ Hóa đơn, xác nhận việc chuyển nhượng hàng hóa.
- **Hàng bán bị trả lại:** Tự động tạo 3 bút toán (Giảm doanh thu, Nhập lại kho đúng giá vốn xuất, Giảm thuế GTGT).
### Thu tiền khách hàng
- Lập Phiếu thu / Báo có. Đối trừ trực tiếp công nợ theo từng hóa đơn cụ thể (Gạch nợ).

## 5. Hệ thống Báo cáo Quản trị Bán hàng
- **Theo dõi thực hiện đơn hàng:** Báo cáo số lượng thực hiện đơn hàng (Giao thiếu/đủ), Báo cáo tiến độ thực hiện đơn hàng (Từ sản xuất -> Xuất kho).
- **Phân tích Tồn kho khả dụng:** Số lượng tồn kho hiện tại + Dự kiến nhập - Tồn tối thiểu - Đơn hàng đã giữ = Khả năng xuất sẵn có / dự kiến.
- **Báo cáo Phân tích đa chiều:** 
  - Phân tích doanh thu, lợi nhuận gộp theo Kênh, Vùng, Nhân viên, Mặt hàng.
  - Phân tích tăng trưởng bán hàng qua các kỳ.
  - So sánh Kế hoạch vs Thực tế.
- **Báo cáo Công nợ:** Sổ tổng hợp phải thu, Báo cáo công nợ phải thu theo hạn thanh toán (Quá hạn/Trong hạn), Công nợ theo Hợp đồng.
- **Bảng KPIs Phòng Kinh doanh:** Tổng hợp bức tranh toàn cảnh (Doanh số, Doanh thu, Tỷ lệ chuyển đổi đơn hàng, Chăm sóc khách hàng) để tính thưởng.
