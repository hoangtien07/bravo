# Đề xuất danh mục chỉ tiêu tài chính (Semantic Layer) — bản nháp để BRAVO duyệt

> Hiện thực [Yêu cầu 2 trong ERP-INTEGRATION-REQUEST](ERP-INTEGRATION-REQUEST.md). Đây là **danh mục NHÁP do AI Copilot đề xuất** để **giảm việc cho BRAVO**: kế toán/kỹ thuật BRAVO chỉ cần **ánh xạ mỗi chỉ tiêu sang view/proc sẵn có của BRAVO 10** và **xác nhận ngữ nghĩa** (cột cuối). AI **chỉ chọn chỉ tiêu trong danh mục này** → engine BRAVO tính → số luôn khớp báo cáo BRAVO (ADR-0005).
>
> ⚠️ Mọi ngữ nghĩa dưới đây là **đề xuất cần kế toán BRAVO xác nhận** (đặc biệt: gộp/thuần, đã/chưa VAT, dồn tích/tiền mặt, xử lý kỳ đã khoá sổ). Tham số chuẩn: `ky` (kỳ kế toán), `don_vi` (đơn vị cơ sở), `tu_ngay`/`den_ngay` khi cần khoảng.

## Nhóm 1 — Doanh thu & Bán hàng
| Mã chỉ tiêu | Mô tả | Tham số | Ngữ nghĩa cần BRAVO xác nhận | View/proc BRAVO 10 (BRAVO điền) |
|-------------|-------|---------|------------------------------|--------------------------------|
| `doanh_thu_thuan` | Doanh thu thuần | ky, don_vi | Sau giảm trừ; **chưa** gồm VAT; dồn tích (TK 511) | |
| `doanh_thu_theo_khach_hang` | Doanh thu theo khách hàng | ky, don_vi, top_n | Xếp hạng KH theo doanh thu | |
| `doanh_thu_theo_san_pham` | Doanh thu theo mặt hàng | ky, don_vi, top_n | | |
| `doanh_thu_cung_ky_truoc` | Doanh thu kỳ trước (so sánh) | ky, don_vi | Cùng kỳ năm trước | |

## Nhóm 2 — Công nợ
| Mã | Mô tả | Tham số | Ngữ nghĩa | Mapping |
|----|-------|---------|-----------|---------|
| `cong_no_phai_thu` | Tổng phải thu khách hàng | ky, don_vi | Số dư TK 131 | |
| `cong_no_qua_han` | Phải thu **quá hạn** | ky, don_vi, so_ngay | Quá hạn theo điều khoản thanh toán | |
| `cong_no_theo_khach_hang` | Công nợ theo KH | ky, don_vi, top_n | Tuổi nợ (aging) | |
| `cong_no_phai_tra` | Tổng phải trả NCC | ky, don_vi | Số dư TK 331 | |

## Nhóm 3 — Chi phí & Lợi nhuận
| Mã | Mô tả | Tham số | Ngữ nghĩa | Mapping |
|----|-------|---------|-----------|---------|
| `chi_phi_theo_khoan_muc` | Chi phí theo khoản mục | ky, don_vi | TK 6xx theo khoản mục | |
| `gia_von_hang_ban` | Giá vốn hàng bán | ky, don_vi | TK 632 | |
| `loi_nhuan_gop` | Lợi nhuận gộp | ky, don_vi | DT thuần − GVHB | |
| `loi_nhuan_truoc_thue` | LN trước thuế | ky, don_vi | | |
| `loi_nhuan_sau_thue` | LN sau thuế | ky, don_vi | | |

## Nhóm 4 — Tồn kho
| Mã | Mô tả | Tham số | Ngữ nghĩa | Mapping |
|----|-------|---------|-----------|---------|
| `ton_kho_cuoi_ky` | Giá trị tồn kho cuối kỳ | ky, kho, mat_hang | TK 15x | |
| `ton_kho_cham_luan_chuyen` | Hàng chậm luân chuyển | ky, kho, so_ngay | Không xuất trong N ngày | |

## Nhóm 5 — Dòng tiền & Thuế
| Mã | Mô tả | Tham số | Ngữ nghĩa | Mapping |
|----|-------|---------|-----------|---------|
| `so_du_tien` | Số dư tiền (mặt + gửi NH) | ky, don_vi | TK 111 + 112 | |
| `dong_tien_thuan` | Dòng tiền thuần trong kỳ | ky, don_vi | Vào − ra | |
| `thue_gtgt_phai_nop` | Thuế GTGT phải nộp | ky, don_vi | TK 3331 | |

## Nhóm 6 — Phát hiện bất thường (Phase 3 — agent nền)
| Mã | Mô tả | Tham số | Ghi chú |
|----|-------|---------|---------|
| `but_toan_bat_thuong` | Bút toán nghi bất thường | ky, don_vi | Số tròn lớn, ngoài giờ, lệch tổng-chi tiết |
| `hoa_don_trung` | Hoá đơn nghi trùng | ky, don_vi | Trùng số tiền + NCC + ngày |
| `chi_vuot_dinh_muc` | Chi vượt định mức | ky, don_vi, khoan_muc | So định mức/ngân sách |

---

## Cách dùng (kỹ thuật)
- Mỗi dòng → một entry trong `app/data_layer/semantic.py::REGISTRY` (id + required_params).
- Cột "View/proc BRAVO 10" → cấu hình của `DataSource` thật (Phase 2, sau khi BRAVO cung cấp).
- AI map câu hỏi NL → (mã chỉ tiêu + tham số) qua LLM cục bộ; nếu không map được chỉ tiêu nào → **từ chối** (không bịa, không SQL tự do).

## Việc cho BRAVO (gọn)
1. **Ánh xạ** mỗi chỉ tiêu sang view/proc báo cáo sẵn có của BRAVO 10 (cột cuối).
2. **Xác nhận/ sửa ngữ nghĩa** (cột "Ngữ nghĩa cần xác nhận").
3. Bổ sung/loại chỉ tiêu theo thực tế khách hàng.
→ Sau đó AI Copilot ráp `DataSource` vào là chạy phần phân tích tài chính.
