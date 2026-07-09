# Một số chức năng quản trị (Managements)

## 1. Quản lý đơn đặt hàng và hợp đồng
### Quản lý đơn đặt hàng
- Quản lý xuyên suốt từ lập đơn, dự kiến giao, thực tế giao đến khi đóng/kết thúc.
- **Kế thừa dữ liệu:** Từ đơn đặt hàng có thể tự động tạo Phiếu nhập mua/Phiếu nhập khẩu.
- **Trạng thái đóng đơn:** Đóng tự động khi xuất/nhập đủ hàng (hoặc theo dung sai), hoặc đóng thủ công.
### Quản lý hợp đồng
- Dùng cho hợp đồng mua/bán chi tiết.
- Cập nhật điều khoản thanh toán, theo dõi tiến độ giao hàng và thanh toán.
- Báo cáo tổng hợp công nợ phải thu/phải trả theo hợp đồng.

## 2. Quản lý Khế ước vay và Bảo lãnh hợp đồng
### Khế ước vay / Hợp đồng tiền gửi
- **Theo dõi:** Lập khế ước, ghi nhận lãi/gốc dự kiến, kỳ đáo hạn.
- **Thực hiện:** Gắn mã khế ước vào các chứng từ phát sinh thanh toán/thu tiền.
- Báo cáo lịch trả nợ gốc/lãi vay.
### Bảo lãnh hợp đồng / Thư tín dụng L/C
- Thiết lập: Hợp đồng tín dụng -> Hạn mức tín dụng -> Đề nghị phát hành bảo lãnh -> Khai báo Bảo lãnh ngân hàng / L/C.
- Theo dõi chi phí bảo lãnh, tỷ lệ ký quỹ, tình trạng hạn mức tín dụng.

## 3. Quản lý Công nợ hạn thanh toán
### Thiết lập ban đầu
- Định nghĩa tuổi nợ (hạn nợ) cho từng đối tượng/tài khoản. 
- Thiết lập ngày đến hạn: Dựa trên ngày hóa đơn hoặc ngày chứng từ.
### Thực hiện Gạch nợ (Cấn trừ)
- Gạch nợ thủ công (chọn đích danh hóa đơn thanh toán).
- Gạch nợ tự động (hàng loạt) theo nguyên tắc trừ đuổi (FIFO).
- Cho phép điều chỉnh công nợ ngoài sổ (điều chỉnh chênh lệch nhỏ do tỷ giá mà không cần mở sổ kế toán).
### Bàn giao công nợ (Nhân viên kinh doanh)
- Theo dõi công nợ theo từng nhân viên. Hỗ trợ luân chuyển (bàn giao) tập khách hàng khi có nhân viên nghỉ việc/chuyển công tác.

## 4. Đánh giá Chênh lệch Tỷ giá
- **Đánh giá khi thanh toán/chi tiền:** Tự động tính chênh lệch tỷ giá dựa theo phương pháp trung bình di động.
- **Đánh giá cuối kỳ:** Đánh giá lại số dư ngoại tệ của các tài khoản công nợ, tiền, khế ước vay dựa trên tỷ giá cuối kỳ. 
- Tự động sinh chứng từ định khoản vào TK 5156 (lãi) hoặc 6356 (lỗ).

## 5. Hạch toán Bút toán định kỳ
- Thiết lập bút toán lặp lại hàng tháng (ví dụ chi phí cố định).
- Căn cứ khai báo để tự động chạy ra "Chứng từ tự động" hàng tháng.

## 6. Chuyển đổi Báo cáo Tài chính và Thuế về VND
- Phục vụ các doanh nghiệp hạch toán bằng ngoại tệ (ví dụ USD) nhưng cần nộp báo cáo bằng VND.
- Cấu hình Tỷ giá chuyển đổi (Tỷ giá cuối kỳ cho Bảng cân đối kế toán, Tỷ giá bình quân cho KQKD và LCTT).
- Tự động sinh chênh lệch tỷ giá do chuyển đổi báo cáo.

## 7. Quản lý Quy trình Duyệt chứng từ và Ký điện tử
### Quy trình Duyệt
- **Thiết lập linh hoạt:** Duyệt đa cấp, điều kiện duyệt theo số tiền/phòng ban (Ví dụ: > 10 triệu cần Giám đốc duyệt).
- **Phân quyền:** Phân quyền theo Nhóm người duyệt hoặc Người dùng cụ thể.
- **Tiện ích:** Gửi thông báo tự động (App/Web/Email) khi có chứng từ cần duyệt/trả lại. Đo lường KPI (thời gian duyệt chứng từ).
### Ký điện tử
- Hỗ trợ Ký số (chứng thư số có giá trị pháp lý, kết nối MISA, VNPT...) và Ký ảnh (nội bộ).
- Khai báo thiết kế mẫu in để tự động dán chữ ký/chữ ký số vào vị trí quy định trên file PDF. File PDF đã ký được lưu ở phần Tài liệu đính kèm.

## 8. Tích hợp Hóa đơn Điện tử (HĐĐT) đầu vào
- **Kết nối tự động:** Lấy dữ liệu qua các đối tác VAN (Ví dụ: Inbots MISA).
- **Quy đổi tự động (Mapping):** Quy đổi Mã vật tư, Đơn vị tính, Đối tượng, Thuế suất từ thông tin HĐĐT sang bộ mã của hệ thống BRAVO.
- **Tạo chứng từ:** 
  - Tự động tạo Phiếu nhập mua/Phiếu chi từ dữ liệu HĐĐT đã được map.
  - Phân bổ chiết khấu tự động (theo tỷ lệ giá trị hoặc mặt hàng lớn nhất).
- Bổ sung thông tin hóa đơn cho các Phiếu nhập kho đã lập trước đó (cho trường hợp hàng về trước, hóa đơn về sau).

## 9. Bài toán Phân bổ Chi phí Quản trị
- Phân bổ các chi phí gián tiếp (641, 642) cho từng sản phẩm, bộ phận, khu vực kinh doanh.
- **Tiêu thức phân bổ:** Dựa trên hệ số cố định, hoặc tự động lấy tỷ lệ từ doanh thu.
- Số liệu này KHÔNG ảnh hưởng sổ cái kế toán tài chính, chỉ lưu ở "Kết quả phân bổ" phục vụ xuất Báo cáo phân tích hiệu quả sinh lời chi tiết theo từng mặt hàng.

## 10. Hệ thống Báo cáo Quản trị - Phân tích Tài chính
- Cung cấp nhóm báo cáo biểu đồ trực quan.
- **Các báo cáo nổi bật:** Chỉ số sức khỏe doanh nghiệp (ROE, ROA...), Phân tích dòng tiền, So sánh doanh thu thực tế vs Kế hoạch, Phân tích hiệu quả kinh doanh cho từng sản phẩm.
