# Phân hệ Kiểm soát chất lượng (QC)

## 1. Tổng quan & Luồng quy trình (QC Workflow)
- **IQC (Input Quality Control - Kiểm soát đầu vào):** Kiểm tra nguyên vật liệu trước khi nhập kho.
  - *Luồng dữ liệu:* Lệnh nhập hàng -> Yêu cầu kiểm tra đầu vào -> Phiếu kiểm tra đầu vào.
  - *Phân nhánh:* Đạt -> Lập Phiếu nhập kho; Không đạt -> Trả về / Xử lý NVL không phù hợp.
- **PQC (Process Quality Control - Kiểm soát sản xuất):** Kiểm tra trong quá trình sản xuất (Bán thành phẩm, Thành phẩm).
  - *Luồng dữ liệu:* Lệnh sản xuất -> Yêu cầu kiểm tra sản xuất -> Phiếu kiểm tra sản xuất.
  - *Phân nhánh:* Đạt -> Nhập kho hoàn thành; Không đạt -> Sửa chữa/Tái sử dụng hoặc Lập Biên bản hủy sản phẩm.
- **OQC (Output Quality Control - Kiểm soát đầu ra):** Kiểm tra trước khi xuất xưởng/giao hàng.
  - *Luồng dữ liệu:* Lệnh xuất hàng -> Yêu cầu kiểm tra đầu ra -> Phiếu kiểm tra đầu ra.
  - *Phân nhánh:* Đạt -> Phiếu xuất kho; Không đạt -> Sửa chữa hoặc Lập Biên bản hủy sản phẩm bán.

## 2. Hệ thống Danh mục & Tiêu chuẩn
### 2.1. Thiết lập chỉ tiêu & Lỗi
- **Danh mục chỉ tiêu kiểm tra:** Định nghĩa các tiêu chí như màu sắc, kích thước, chất liệu.
- **Danh mục chuẩn chấp nhận:** Định nghĩa giới hạn trên, giới hạn dưới, dung sai cho các chỉ tiêu định lượng.
- **Danh mục lỗi kiểm tra:** Phân loại nguyên nhân gây ra lỗi (VD: xước xát, sai kích thước).
- **Danh mục nhóm tiêu chuẩn QC:** Phân nhóm các vật tư/thành phẩm có chung một bộ chỉ tiêu và chuẩn chấp nhận.
- **Danh mục mẫu kiểm tra:** Cấu hình quy tắc lấy mẫu (Số lượng mẫu cố định hoặc tỷ lệ % theo từng khung số lượng yêu cầu).

### 2.2. Khai báo tiêu chuẩn kiểm tra (Theo từng giai đoạn)
- **Khai báo tiêu chuẩn đầu vào / sản xuất / đầu ra:**
  - *Tham số then chốt:* Mã tiêu chuẩn, Ngày áp dụng / Hết hạn, Mã vật tư hoặc Nhóm hàng QC.
  - *Chi tiết tiêu chuẩn:* Gắn Chỉ tiêu kiểm tra + Chuẩn chấp nhận + Phương pháp kiểm tra tương ứng.

## 3. Luồng Nghiệp vụ cốt lõi (Standard Workflows)
### 3.1. Kiểm tra chất lượng đầu vào (IQC)
- **Yêu cầu kiểm tra chất lượng đầu vào:**
  - *Kế thừa:* Được tự động tạo ra từ **Lệnh nhập hàng**.
  - *Dữ liệu chính:* SL yêu cầu kiểm tra, SL mẫu cần kiểm tra (tính toán tự động theo Danh mục mẫu).
- **Phiếu kiểm tra chất lượng đầu vào:**
  - *Kế thừa:* Được tự động tạo từ **Yêu cầu kiểm tra đầu vào**.
  - *Tham số then chốt:* Đánh giá (OK/NG), Kết quả thực tế của từng mẫu/lô.
  - *Chi tiết lỗi:* Ghi nhận SL lỗi, mã lỗi và phương án xử lý nếu mẫu không đạt.

### 3.2. Kiểm tra chất lượng sản xuất (PQC)
- **Yêu cầu kiểm tra chất lượng sản xuất:**
  - *Kế thừa:* Được tự động tạo từ **Lệnh sản xuất**.
- **Phiếu kiểm tra chất lượng sản xuất:**
  - *Kế thừa:* Từ **Yêu cầu kiểm tra sản xuất**. Ghi nhận thông số thực tế của Bán thành phẩm / Thành phẩm trên dây chuyền.

### 3.3. Kiểm tra chất lượng đầu ra (OQC)
- **Yêu cầu kiểm tra chất lượng đầu ra:**
  - *Kế thừa:* Kế thừa từ **Lệnh xuất hàng**.
- **Phiếu kiểm tra chất lượng đầu ra:**
  - *Kế thừa:* Từ **Yêu cầu kiểm tra đầu ra**. Đảm bảo hàng hóa đạt chuẩn trước khi giao khách.

## 4. Xử lý ngoại lệ & Nghiệp vụ đặc thù (Exceptions)
### 4.1. Xử lý Nguyên vật liệu không phù hợp
- *Mục đích:* Ghi nhận lỗi NVL phát hiện sau khi đã nhập kho (do bộ phận sản xuất phản ánh lại).
- *Dữ liệu chính:* Bộ phận phát hiện lỗi, Mã vật tư, Số lượng lỗi, Nguyên nhân lỗi, Biện pháp giải quyết, Chi phí phát sinh.

### 4.2. Xử lý Hủy sản phẩm (Sản xuất & Bán hàng)
- **Biên bản hủy sản phẩm sản xuất:**
  - *Áp dụng:* Bán thành phẩm/Thành phẩm không đạt và không thể sửa chữa.
  - *Kế thừa:* Cung cấp công cụ "Lấy phiếu thống kê sản xuất" để lấy chi tiết phế phẩm.
- **Biên bản hủy sản phẩm bán:**
  - *Áp dụng:* Hàng hóa xuất bán không đạt yêu cầu và không thể sửa chữa/thanh lý.

### 4.3. Quản lý Sản phẩm không phù hợp (Sau bán hàng)
- *Mục đích:* Ghi nhận lỗi do khách hàng/bộ phận bán hàng phản ánh sau khi đã xuất bán (lỗi vận chuyển, lọt lỗi).
- *Hành động:* Thống kê tìm nguyên nhân, phương án giải quyết và giải pháp phòng ngừa.

## 5. Hệ thống Báo cáo Quản trị (Reports)
### 5.1. Báo cáo thống kê & Theo dõi
- **Bảng kê kết quả kiểm tra chất lượng:** Liệt kê các phiếu yêu cầu kiểm tra, phân loại theo IQC/PQC/OQC.
- **Báo cáo theo dõi tiến độ công việc bộ phận QC:** Hiển thị dưới dạng biểu đồ Gantt, theo dõi thời gian thực hiện, tình trạng hoàn thành các yêu cầu kiểm tra của từng nhân viên QC.
### 5.2. Báo cáo phân tích
- **Báo cáo phân tích tỷ lệ lỗi:** Phân tích trực quan (biểu đồ) các loại lỗi của vật tư, thành phẩm trong các giai đoạn (IQC, PQC, OQC), giúp tìm ra nguyên nhân và điểm yếu cần khắc phục.
