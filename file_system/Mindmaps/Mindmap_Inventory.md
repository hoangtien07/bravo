# Quản lý hàng tồn kho (Inventory)

## 1. Khai báo thông tin ban đầu
### Danh mục Kho hàng và Vị trí
- **Danh mục kho hàng:** Khai báo các kho. 
  - Các cờ (flags) quan trọng: Cho phép xuất khi chưa đủ hàng (xuất âm kho), Theo dõi tồn kho theo vị trí, Kho bán hàng online.
  - Kho hàng đi đường: Là kho trung gian dùng cho nghiệp vụ Điều chuyển nội bộ (khi 2 kho cách xa nhau về địa lý).
- **Danh mục vị trí:** Khai báo vị trí chi tiết trong kho theo định dạng Dãy - Tầng - Hàng.

### Danh mục Vật tư hàng hóa
- Cấu hình các đặc tính theo dõi: 
  - **Theo dõi lô (Lot):** Thêm tính chất Ngày sản xuất, Hạn sử dụng. Quản lý xuất kho theo hạn dùng.
  - **Theo dõi Serial:** Mỗi sản phẩm là 1 mã serial duy nhất (1 serial = 1 số lượng). Phục vụ truy xuất nguồn gốc, bảo hành.
  - **Theo dõi vị trí:** Khai báo tồn kho đến mức vị trí trong kho.
- Khai báo Tồn kho đầu kỳ: Chi tiết đến số lượng, giá trị theo từng kho, lô, vị trí.

## 2. Quản lý Hàng Nhập Kho
- **Nguồn từ bên ngoài:**
  - Lệnh nhập hàng (Thông báo trước để kho chuẩn bị diện tích, nhân sự).
  - Phiếu nhập mua / Phiếu nhập khẩu.
  - Phiếu nhập xuất thẳng (Mua về xuất luôn vào sản xuất/bán hàng).
  - Hàng bán bị trả lại.
- **Nguồn từ nội bộ:**
  - Yêu cầu nhập vật tư (Từ các phòng ban khác báo cho kho).
  - Phiếu nhập kho (Nhập thừa từ sản xuất, kiểm kê thừa...).
  - Phiếu nhập thành phẩm (Từ xưởng sản xuất).

## 3. Quản lý Hàng Xuất Kho
- **Xuất cho nội bộ:**
  - Yêu cầu xuất vật tư (Giấy đề nghị cấp vật tư, CCDC).
  - Phiếu xuất kho (Xuất cho sản xuất, xuất dùng nội bộ, xuất biếu tặng).
  - Phiếu xuất công cụ dụng cụ (Ghi nhận để phân bổ chi phí).
  - Phiếu xuất lắp ráp (Xuất nhiều linh kiện để tạo ra 1 thành phẩm hoàn chỉnh mà không qua quy trình sản xuất phức tạp).
- **Xuất ra ngoài:** 
  - Lệnh xuất hàng (Thông báo chuẩn bị hàng).
  - Hóa đơn bán hàng / Hóa đơn xuất khẩu / Phiếu giao hàng.

## 4. Quản lý Điều chuyển Nội bộ (Giữa các Chi nhánh/Kho)
- **Quy trình qua kho trung gian (Kho đi đường):**
  1. Lập "Yêu cầu điều chuyển nội bộ" (từ bên cần hàng).
  2. Lập "Phiếu xuất điều chuyển nội bộ" (từ kho xuất) -> Hàng đi vào Kho đi đường.
  3. Lập "Phiếu nhập điều chuyển nội bộ" (tại kho đích) -> Hàng xuất từ Kho đi đường sang Kho đích.
  4. Lập "Phiếu xử lý chênh lệch điều chuyển nội bộ" (nếu có hao hụt, mất mát trong quá trình vận chuyển).
- **Điều chuyển vị trí:** Di chuyển hàng hóa giữa các ô/kệ trong cùng 1 kho.

## 5. Kiểm kê Hàng Tồn kho
- **Quy trình:** Thông báo kiểm kê -> Phiếu kiểm kê -> Tổng hợp kiểm kê -> Xử lý chênh lệch kiểm kê.
- Hỗ trợ công cụ quét mã vạch (Barcode) / QR code để kiểm đếm nhanh.
- Xử lý chênh lệch:
  - Nếu thiếu: Tự động sinh Phiếu xuất kho, hạch toán vào TK 1381 (Tài sản thiếu chờ xử lý).
  - Nếu thừa: Tự động sinh Phiếu nhập kho, hạch toán vào TK 3381 (Tài sản thừa chờ giải quyết).

## 6. Tính Giá Vốn Hàng Xuất
- Hỗ trợ các phương pháp: Bình quân gia quyền cuối kỳ, Bình quân di động, Nhập trước xuất trước (FIFO), Thực tế đích danh.
- Chức năng tự động áp giá: Chạy định kỳ hoặc cuối tháng để hệ thống tự động tính và điền đơn giá/thành tiền vốn vào các phiếu xuất kho (có đánh dấu "Tự áp giá").
- Hỗ trợ tính giá vốn theo Ngoại tệ (áp dụng cho đơn vị dùng đa tiền tệ).

## 7. Hệ thống Báo cáo Quản trị Kho
- Báo cáo Tổng hợp Nhập - Xuất - Tồn (có thể bóc tách theo Lô, Vị trí, Serial).
- **Phân tích tồn kho theo tỷ trọng (ABC Analysis):** Chia nhóm hàng hóa quan trọng (A, B, C) theo giá trị tồn kho để ưu tiên quản lý.
- **Báo cáo cảnh báo:** Tồn kho dưới mức tối thiểu / vượt quá mức tối đa.
- Báo cáo vật tư chậm luân chuyển (Ứ đọng vốn).
- Báo cáo theo dõi hàng đi đường.
