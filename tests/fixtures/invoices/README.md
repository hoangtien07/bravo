# Fixture hoá đơn điện tử (DEMO — ẩn danh)

Hoá đơn XML mẫu theo schema NĐ123/2020 + TT78/2021 (QĐ 1450/TCT). **Tất cả ẩn danh**:
MST là số giả nhưng HỢP LỆ checksum (để validator chạy thật), tên → "CÔNG TY DEMO".
KHÔNG phải hoá đơn thật.

| File | Ca phủ |
|---|---|
| `inv_single_10pct_goods.xml` | 1 dòng hàng hóa, thuế suất 10% |
| `inv_multi_rate.xml` | nhiều dòng, thuế suất khác nhau (dịch vụ 8% + vật tư 10%) |
| `inv_bad_totals.xml` | tổng thanh toán SAI — test validator bắt cờ |

## Thả hoá đơn THẬT vào đây
Đặt file `.xml` thật (đã ẩn danh nếu cần) vào thư mục này. Parser
`app/ingestion/invoice_parser.py` đọc theo TÊN TAG (namespace-agnostic) nên bám được
biến thể nhà cung cấp. Nếu schema lệch (NĐ70/2025, tag khác), bổ sung alias tag trong
parser + thêm 1 fixture biến thể.

Cấu trúc tag chính: `HDon/DLHDon/NDHDon`: `NBan·NMua(Ten·MST)`,
`DSHHDVu/HHDVu(THHDVu·DVTinh·SLuong·DGia·ThTien·TSuat·TThue)`,
`TToan(TgTCThue·TgTThue·TgTTTBSo)`.
