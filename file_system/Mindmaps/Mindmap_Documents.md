# Cập nhật chứng từ (Documents)

## 1. Đặc điểm và thao tác chung trên chứng từ
### Phân loại chứng từ
- **Chứng từ kế toán:** Phiếu thu (PT), Phiếu chi (PC), Báo có (BC), Báo nợ (BN), Bù trừ (BT), Phiếu kế toán khác (PK), Chứng từ tự động (TD).
- **Chứng từ vật tư:** Nhập mua (NM), Nhập khẩu (NK), Nhập thành phẩm (TP), Chi phí mua (CP), Xuất trả NCC (XT), Nhập/Xuất kho (PN/PX), Điều chuyển kho (DC), Hóa đơn bán hàng (HD), v.v.

### Các phím tắt chức năng dùng chung
- **F2 / Ctrl+F2:** Thêm mới / Nhân bản chứng từ.
- **F3:** Mở / Sửa chứng từ hiện thời.
- **F7 / F8:** In chứng từ / Đình chỉ (xóa mềm).
- **Ctrl+F:** Tìm kiếm chứng từ.
- **Ctrl+S:** Lưu tạm thời và giữ nguyên màn hình nhập.

### Nguyên tắc nhập liệu
- Các trường có dấu nháy đỏ là **Bắt buộc nhập**.
- Khai báo Thuế GTGT: Chứng từ kế toán kê khai trên lưới chi tiết hạch toán (nếu cùng số lượng dòng hóa đơn và định khoản), hoặc ở tab "Chứng từ đi kèm". Chứng từ vật tư chỉ cho phép khai 1 hóa đơn GTGT trên một phiếu (nhập ở phần dưới màn hình).
- Lựa chọn lưu: "Lưu và thêm mới", "Lưu và quay ra", "Lưu tạm". 
- Trạng thái chứng từ (Đã hoàn thiện, Đã khóa) quyết định việc chứng từ có được lên báo cáo sổ sách hay không.

## 2. Các loại chứng từ kế toán cơ bản (Thu, Chi, Báo có, Báo nợ)
- Quản lý thanh toán tiền mặt, tiền gửi, chi phí, lương.
- Hỗ trợ hạch toán **Nhiều Nợ - Có** (Nhiều định khoản trên một chứng từ).
- Liên kết đối trừ công nợ trực tiếp cho các "Hóa đơn có theo dõi hạn thanh toán".
- Quản lý chi tiết **Khoản mục dòng tiền** (tài chính và quản trị) để lên báo cáo lưu chuyển tiền tệ.
- In trực tiếp Ủy nhiệm chi (Báo nợ) theo form chuẩn của từng ngân hàng (Vietcombank, BIDV, Techcombank...).

## 3. Phiếu hóa đơn bán hàng
- Ghi nhận doanh thu, thuế GTGT đầu ra, công nợ phải thu và kiêm phiếu xuất kho.
- **Phân loại:** Hóa đơn bán hàng trong nước, Hóa đơn xuất khẩu, Hóa đơn điều chỉnh, Hàng bán bị trả lại.
- **Thông tin quản trị mở rộng:**
  - Theo dõi theo: Kênh bán hàng, Vùng tiêu thụ, Nhân viên.
  - Liên kết với: Đơn hàng bán (để theo dõi tiến độ), Hạn thanh toán (tuổi nợ), Biển số xe vận chuyển.
- **Phát hành hóa đơn điện tử:** Kết nối API trực tiếp với các nhà cung cấp VAN (Viettel, VNPT, BKAV, MISA...) để phát hành và cấp số ngay trên BRAVO.

## 4. Phiếu nhập mua hàng
- Ghi nhận nhập kho, công nợ phải trả, thuế GTGT đầu vào.
- **Phân loại:** Nhập mua trong nước, Nhập khẩu (kèm thuế Nhập khẩu, TTĐB, BVMT), Chi phí mua hàng (phân bổ vào giá vốn vật tư), Xuất trả lại nhà cung cấp.
- **Thông tin quản trị mở rộng:**
  - Theo dõi theo: Nhân viên mua hàng, Bộ phận yêu cầu.
  - Liên kết: Đơn hàng/Hợp đồng mua, Loại duyệt giá mua, Số ngày dự kiến hàng về.
  - Tỷ lệ chiết khấu: Phân bổ chiết khấu theo Giá trị hoặc Số lượng.

## 5. Phiếu nhập/xuất kho vật tư
- Xử lý các luồng hàng hóa nội bộ.
- **Phân loại:** Nhập/Xuất kho thông thường, Nhập thành phẩm, Nhập xuất thẳng (mua về xuất ngay vào sản xuất), Điều chuyển kho, Xuất lắp ráp, Xuất CCDC (chuyển vật tư thành CCDC để phân bổ chi phí).
- **Tính giá vốn:** Chương trình tự động áp giá xuất nếu cấu hình "Tự áp giá". Nếu không, có thể nhập tay.
- **Liên kết sản xuất:** Gắn với Lệnh sản xuất, Công đoạn (để tập hợp chi phí tính giá thành).
- Phải nhập chi tiết số Lô, Serial, Vị trí (nếu vật tư có cấu hình theo dõi các thuộc tính này).

## 6. Bút toán bù trừ
- Chuyển đổi và đối trừ công nợ/chi phí.
- **Ứng dụng:** 
  - Bù trừ công nợ giữa 2 đối tượng (khách hàng/nhà cung cấp).
  - Bù trừ chi phí giữa 2 sản phẩm công trình, hoặc 2 khoản mục chi phí.
  - Bù trừ giữa các đơn hàng, khế ước.
- **Bù trừ đa tiền tệ:** Hỗ trợ bù trừ chéo ngoại tệ (VD: USD bù trừ EUR) qua cột Tỷ giá và loại tiền tệ chi tiết.

## 7. Các chứng từ đặc thù khác
- **Chứng từ tự động:** Được sinh ra từ các chức năng xử lý cuối kỳ (Khấu hao TSCĐ, Phân bổ chi phí, Kết chuyển doanh thu chi phí).
- **Phiếu điều chuyển vị trí:** Di chuyển hàng hóa giữa các Vị trí (Bin/Location) bên trong cùng một Kho.
- **Phiếu chuyển công đoạn sản xuất:** Chuyển bán thành phẩm từ công đoạn này sang công đoạn khác.
