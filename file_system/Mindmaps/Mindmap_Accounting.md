# Phân hệ Quản lý Kế toán – Tài chính

## 1. Kế toán Vốn bằng tiền
### 1.1. Tiền mặt & Tiền gửi Ngân hàng
- **Tiền mặt:** Phiếu thu, Phiếu chi tiền mặt.
- **Tiền gửi Ngân hàng:** Báo có, Báo nợ.
- **Kết nối Ngân hàng điện tử (E-banking):**
  - Khai báo danh mục tài khoản ngân hàng điện tử.
  - Truy vấn số dư và Lịch sử giao dịch trực tuyến.
  - Tạo lệnh chuyển tiền (Từng lệnh hoặc theo File danh sách).
  - Cập nhật trạng thái giao dịch & Tạo chứng từ (Báo có) tự động từ lịch sử giao dịch.
### 1.2. Quản lý Tạm ứng - Thanh toán
- *Luồng quy trình:* Đề nghị tạm ứng -> Chi tiền -> Đề nghị thanh toán (Quyết toán) -> Hạch toán thu/chi chênh lệch.
- Áp dụng cho: Tạm ứng nhân viên và Thanh toán nhà cung cấp.

## 2. Kế toán Mua hàng, Bán hàng & Tồn kho
- *Vai trò Kế toán:* Kiểm soát, hoàn thiện định khoản, hạch toán, đối trừ công nợ, tính giá vốn, quản lý hóa đơn (Đầu vào/Đầu ra) từ các chứng từ do bộ phận Mua hàng, Bán hàng, Kho lập (Phiếu nhập, Phiếu xuất, Hóa đơn bán hàng...).

## 3. Kế toán TSCĐ, CCDC, Chi phí chờ phân bổ (CPCPB)
### 3.1. Quản lý Tài sản cố định (TSCĐ) - VAS
- **Đăng ký tài sản:** Khai báo thông tin TSCĐ, nguyên giá, phương pháp khấu hao, bộ phận sử dụng, nguồn vốn.
- **Biến động tài sản:** Điều chỉnh hạch toán, Điều chuyển bộ phận, Thay đổi giá trị/thời gian, Tạm dừng/Tiếp tục khấu hao, Thanh lý tài sản.
- **Trích khấu hao:** Khai báo hệ số phân bổ -> Tính & Điều chỉnh khấu hao tháng -> Phân bổ và Hạch toán tạo chứng từ.
- **Kiểm kê TSCĐ:** Lập Thông báo kiểm kê -> Nhập Phiếu kiểm kê (hỗ trợ quét mã vạch) -> Báo cáo chênh lệch -> Xử lý chênh lệch (Thừa/Thiếu).
### 3.2. Quản lý CCDC & CPCPB
- Khai báo mã CCDC / CPCPB.
- Ghi nhận biến động, Thanh lý, Tất toán.
- Tính và Hạch toán phân bổ chi phí hàng kỳ (Tương tự trích khấu hao TSCĐ).
### 3.3. Quản lý Tài sản thuê (IFRS 16)
- Khai báo tài sản thuê lần đầu (Giá trị hiện tại của dòng tiền, lãi suất, kỳ thanh toán).
- Điều chỉnh tài sản thuê, Hủy ngang.
- Hạch toán tài sản thuê hàng kỳ (Nợ thuê phải trả, Khấu hao).

## 4. Kế toán Giá thành
### 4.1. Danh mục Cơ sở tính Giá thành
- Công đoạn giá thành, Trung tâm chi phí (Phân xưởng).
- Sản phẩm, Công trình (Đối tượng tập hợp chi phí).
- Yếu tố chi phí, Tài khoản chi phí giá thành (621, 622, 627, 154).
### 4.2. Luồng Dữ liệu & Tập hợp Chi phí
- Khai báo định mức nguyên vật liệu (BOM) & Yêu cầu thay thế vật tư.
- Chuyển công đoạn sản xuất (Ghi nhận chi phí công đoạn trước chuyển sang công đoạn sau).
- Khai báo Dở dang đầu kỳ / Cuối kỳ (Theo yếu tố hoặc Theo bán thành phẩm trên dây chuyền).
### 4.3. Các Phương pháp Phân bổ Chi phí Chung
- Phân bổ trực tiếp (Cho đích danh sản phẩm/công đoạn).
- Phân bổ theo Hệ số / Trọng lượng.
- Phân bổ theo Tỷ lệ.
- Phân bổ theo Định mức.
### 4.4. Quy trình Tính Giá thành
- Thuật toán (6 bước): (1) Xác định thành phẩm -> (2) Tập hợp chi phí, dở dang cuối kỳ -> (3) Kết chuyển chi phí trực tiếp -> (4) Phân bổ chi phí (hệ số, tỷ lệ, định mức) -> (5) Tính và cập nhật giá thành -> (6) Tính giá vốn thành phẩm.
- Tính giá thành theo thứ tự công đoạn (Tự động chạy kịch bản theo danh mục tập hợp các công đoạn).

## 5. Kế toán Tổng hợp & Cuối kỳ
- **Thiết lập:** Khai báo tham số hạch toán lương (để tự động sinh bút toán lương).
- **Nghiệp vụ tính toán:**
  - Tính giá vốn hàng xuất (Bình quân tháng, Đích danh, FIFO, Bình quân di động).
  - Đánh giá chênh lệch tỷ giá cuối kỳ.
- **Hạch toán & Khóa sổ:**
  - Hạch toán kết chuyển cuối kỳ (Tự động tạo bút toán khóa sổ kết chuyển doanh thu, chi phí sang 911).
  - Khóa sổ dữ liệu kế toán.
- **Báo cáo Tài chính (BCTC) & Thuế:**
  - Lên các BCTC: Tình hình tài chính (Bảng CĐKT), Kết quả HĐKD, Lưu chuyển tiền tệ (Trực tiếp/Gián tiếp), Thuyết minh BCTC.
  - *Khai báo công thức BCTC:* Tùy biến công thức lấy dữ liệu (Loại PS, Mã tài khoản, Loại trừ đối ứng) cho từng chỉ tiêu trên Báo cáo.
  - *Thuế TNCN:* Quản lý Chứng từ khấu trừ thuế TNCN, Phát hành Chứng từ điện tử (Tích hợp với Nhà cung cấp Hóa đơn điện tử). Kết xuất XML nộp hệ thống HTKK.
