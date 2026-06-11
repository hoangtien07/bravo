# MOCK-DATA-SPEC — Dữ liệu giả cho demo Agentic (không cần ERP)

> Mục tiêu: cho phép **Demo B (Agentic AI)** chạy năng lực hỏi-đáp số liệu + soi bất thường + đề xuất nháp **mà không cần ERP read-only API**. Mọi số ở đây là **GIẢ, gắn nhãn "DEMO"**, chế độ kế toán **TT99/2025**. Khi ERP API + catalog thật về → thay `MockDataSource` bằng `DataSource` thật, **không đổi** phần còn lại (semantic layer ERP-agnostic — [semantic.py](../app/data_layer/semantic.py)).

---

## 1. Trả lời trực tiếp: 2 ảnh phân hệ / giải pháp ngành nghề có cho vào mock được không?

**Được — nhưng dùng đúng vai trò: làm METADATA & cấu trúc, KHÔNG phải số liệu.** Đây là thông tin sản phẩm công khai trên website BRAVO, hoàn toàn dùng được. Cụ thể:

| Ảnh | Dùng cho mock thế nào | KHÔNG cung cấp |
|---|---|---|
| **Phân hệ** (12 phân hệ: QH khách hàng, Công việc, Mua hàng, Bán hàng, Bán lẻ POS, Kho, Máy móc thiết bị, Chất lượng, HC-Nhân sự, **Tài chính-Kế toán**, Sản xuất, Quản trị hệ thống) | (a) Nội dung **Demo A** (giải thích "BRAVO có 12 phân hệ..."); (b) **Cấu trúc danh mục metric mock** — gom metric theo phân hệ (Tài chính-Kế toán→doanh thu/công nợ; Kho→tồn kho; Bán hàng→...); (c) Cấu trúc **phòng ban** cho demo RLS | Số liệu thật, công thức tính thật, schema ERP |
| **Giải pháp ngành nghề** (khách sạn, thép, BĐS, dệt may, chứng khoán, bao bì, ô tô, bia rượu, nội thất-VLXD, thiết bị điện, bê tông, vận tải, MDF, quỹ đầu tư...) | Chọn **một hồ sơ doanh nghiệp demo** để số liệu nhất quán & thuyết phục (vd "Sản xuất Thép xây dựng") | Dữ liệu tài chính thật của ngành |

> **Kết luận:** ảnh = **vốn quý cho mock** (làm khung phân hệ + chọn ngành demo + nội dung chat). **Số liệu tài chính** thì **ta tự sinh** (giả, gắn nhãn DEMO) — và điều đó **đủ** cho demo, vì demo trình diễn *năng lực agentic + rào chắn*, không trình diễn số liệu thật của ai.

**Thông tin "chính xác" chỉ cần ở PRODUCTION (không phải demo):** ngữ nghĩa metric thật (gộp/thuần, đã/chưa VAT, dồn-tích/tiền-mặt), **hệ tài khoản TT99 thật**, ánh xạ view/proc BRAVO 10 — đến từ **kế toán BRAVO + ERP API** ([METRIC-CATALOG-PROPOSAL.md](METRIC-CATALOG-PROPOSAL.md) cột mapping).

---

## 2. Hồ sơ doanh nghiệp demo (đề xuất)

> Chọn 1 ngành để số nhất quán. Đề xuất: **"Công ty CP Thép Xây Dựng DEMO"** (Sản xuất Thép xây dựng) — có đủ doanh thu/giá vốn/tồn kho/công nợ để minh hoạ phong phú. *(Chủ dự án có thể đổi ngành.)*

- **Phòng ban (cho RLS demo):** Ban Giám đốc, Phòng Kế toán, Phòng Kinh doanh, Phòng Mua hàng, Phòng Kho-Sản xuất, Phòng Nhân sự.
- **Người dùng demo (cho RLS):** `giamdoc` (thấy tất cả), `ketoan` (Tài chính-Kế toán + công nợ), `kinhdoanh` (doanh thu/khách hàng, **không** thấy lương), `nhansu` (HR/lương, **không** thấy công nợ chi tiết). → minh hoạ "ai thấy gì".
- **Kỳ:** dữ liệu 4 quý 2025 + 2 tháng 2026 (đủ để hỏi YoY, QoQ, xu hướng).

---

## 3. Danh mục metric mock (theo phân hệ, chế độ TT99/2025)

> Lấy từ [METRIC-CATALOG-PROPOSAL.md](METRIC-CATALOG-PROPOSAL.md) (đã có 18 metric) — **tái dùng nguyên mã metric**, chỉ thay nguồn tính bằng `MockDataSource`. Mỗi metric trả về **value-object** `(value, unit, scale, currency, period, entity, variant)`.

| Phân hệ (ảnh) | Mã metric (đã có) | Số mock (ví dụ, VND) | Biến thể gắn nhãn |
|---|---|---|---|
| Tài chính-Kế toán | `doanh_thu_thuan` | Q1: 45,2 tỷ · Q2: 52,8 tỷ | thuần, **chưa** VAT, dồn tích |
| Tài chính-Kế toán | `gia_von_hang_ban`, `loi_nhuan_gop` | GVHB Q2: 41,1 tỷ · LN gộp: 11,7 tỷ | — |
| Công nợ | `cong_no_phai_thu`, `cong_no_qua_han` | Phải thu: 18,3 tỷ · Quá hạn >30d: 2,1 tỷ | TK 131, aging |
| Công nợ | `cong_no_theo_khach_hang` (top_n) | KH A: 5,2 tỷ · KH B: 3,8 tỷ ... | — |
| Kho | `ton_kho_cuoi_ky`, `ton_kho_cham_luan_chuyen` | Tồn: 22,5 tỷ · Chậm >90d: 1,6 tỷ | TK 15x |
| Dòng tiền & Thuế | `so_du_tien`, `thue_gtgt_phai_nop` | Tiền: 8,9 tỷ · GTGT: 1,2 tỷ | TK 111+112, 3331 |
| (HR — **nhạy**) | `quy_luong_thang` *(thêm để demo egress/RLS)* | Tháng 1: 3,4 tỷ | **NHẠY → ghim local, chỉ `nhansu`/`giamdoc`** |

> **Lưu ý số liệu (council accounting):** mọi số là `Decimal`, VND làm tròn 0 chữ số thập phân; **Σ chi tiết phải == tổng** (reconciliation gate); engine giữ `scale='tỷ'` để verify-gate chặn nhầm "tỷ↔triệu".

### Dữ liệu bất thường cài sẵn (cho demo soi bất thường — Phase 3 nhẹ)
- 1 hoá đơn **trùng** (cùng số tiền + NCC + ngày) → `hoa_don_trung`.
- 1 bút toán **số tròn lớn** ngoài giờ → `but_toan_bat_thuong`.
- 1 khoản chi **vượt định mức** → `chi_vuot_dinh_muc`.
→ `MockDataSource` tính sẵn z-score/percentile; LLM **chỉ xếp hạng + giải thích + trích dẫn** (không tự tính — [ADR-0004](adr/0004-llm-never-computes-numbers.md)).

---

## 4. Tài liệu mock (cho demo suy luận liên-nguồn & draft-from-document)
- 1-2 **hợp đồng** giả (có hạn mức công nợ, điều khoản thanh toán) → nạp KB → demo *"khách nào vượt hạn mức công nợ so với hợp đồng?"* (nối tài liệu + số mock).
- 1 **hoá đơn** giả → demo *"đề xuất định khoản nháp từ hoá đơn này"* → tạo **bản nháp chờ duyệt** (không tự ghi).

---

## 5. Hợp đồng kỹ thuật (cho code)
- `MockDataSource(DataSource)` implement `fetch(metric_id, params, identity) -> (value_object, provenance)`:
  - Đọc từ file `tests/fixtures/mock_financials_tt99.yaml` (số + nhãn biến thể + chế độ TT99).
  - **Áp RLS theo `identity`**: metric nhạy (`quy_luong_thang`) chỉ trả cho `nhansu`/`giamdoc`; phòng khác → raise/abstain (demo RLS ở tầng số).
  - `provenance` = chuỗi trích dẫn giả nhưng có cấu trúc (vd `mock:doanh_thu_thuan ky=2026-Q1 entity=ThépDEMO`).
- Nhãn **"DEMO"** đính kèm mọi MetricResult → UI hiển thị rõ "số liệu minh hoạ".
- Khi ERP thật về: viết `BravoErpDataSource(DataSource)` cùng interface → thay 1 dòng cấu hình.

---

## 6. Cần chủ dự án quyết
- Chọn **ngành demo** (mặc định: Thép xây dựng) — đổi không?
- Mức "giống thật" của số: chỉ cần **hợp lý để demo** (mặc định) hay cần khớp một báo cáo mẫu cụ thể?
- Có muốn thêm phân hệ/metric nào ngoài danh mục 18 metric hiện có không?
