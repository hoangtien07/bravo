"""Approved metric catalog (code form of docs/METRIC-CATALOG-PROPOSAL.md).

Registers the vetted financial metrics into the semantic-layer REGISTRY so the system
knows exactly which metrics are allowed. Questions outside this catalog -> ABSTAIN
(no free SQL, no invented numbers — ADR-0005). The actual computation comes from a
DataSource backed by BRAVO ERP views (Phase 2, after BRAVO maps each metric).

⚠️ Semantics (gross/net, VAT, accrual/cash, locked periods) must be confirmed by BRAVO
accountants — see the proposal doc.
"""
from __future__ import annotations

from app.data_layer.semantic import REGISTRY, Metric

# scope_columns: cột RLS metric lọc theo (BẮT BUỘC — fail-at-load nếu thiếu). variant: nhãn nghĩa.
_S = ("don_vi", "ky")   # scope mặc định: đơn vị cơ sở + kỳ kế toán
_SK = ("kho", "ky")     # tồn kho: theo kho + kỳ
_CATALOG: list[Metric] = [
    # Doanh thu
    Metric("doanh_thu_thuan", "Doanh thu thuần", ("ky", "don_vi"), _S, "thuần; chưa VAT; dồn tích"),
    Metric("doanh_thu_theo_khach_hang", "Doanh thu theo khách hàng", ("ky", "don_vi"), _S),
    Metric("doanh_thu_theo_san_pham", "Doanh thu theo mặt hàng", ("ky", "don_vi"), _S),
    Metric("doanh_thu_cung_ky_truoc", "Doanh thu cùng kỳ năm trước", ("ky", "don_vi"), _S),
    # Công nợ
    Metric("cong_no_phai_thu", "Tổng phải thu khách hàng", ("ky", "don_vi"), _S, "số dư TK 131"),
    Metric("cong_no_qua_han", "Phải thu quá hạn", ("ky", "don_vi"), _S),
    Metric("cong_no_theo_khach_hang", "Công nợ theo khách hàng", ("ky", "don_vi"), _S),
    Metric("cong_no_phai_tra", "Tổng phải trả nhà cung cấp", ("ky", "don_vi"), _S, "số dư TK 331"),
    # Chi phí & lợi nhuận
    Metric("chi_phi_theo_khoan_muc", "Chi phí theo khoản mục", ("ky", "don_vi"), _S),
    Metric("gia_von_hang_ban", "Giá vốn hàng bán", ("ky", "don_vi"), _S, "TK 632"),
    Metric("loi_nhuan_gop", "Lợi nhuận gộp", ("ky", "don_vi"), _S, "DT thuần − GVHB"),
    Metric("loi_nhuan_truoc_thue", "Lợi nhuận trước thuế", ("ky", "don_vi"), _S),
    Metric("loi_nhuan_sau_thue", "Lợi nhuận sau thuế", ("ky", "don_vi"), _S),
    # Tồn kho
    Metric("ton_kho_cuoi_ky", "Giá trị tồn kho cuối kỳ", ("ky", "kho"), _SK, "TK 15x"),
    Metric("ton_kho_cham_luan_chuyen", "Hàng tồn chậm luân chuyển", ("ky", "kho"), _SK),
    # Dòng tiền & thuế
    Metric("so_du_tien", "Số dư tiền (mặt + gửi NH)", ("ky", "don_vi"), _S, "TK 111 + 112"),
    Metric("dong_tien_thuan", "Dòng tiền thuần trong kỳ", ("ky", "don_vi"), _S),
    Metric("thue_gtgt_phai_nop", "Thuế GTGT phải nộp", ("ky", "don_vi"), _S, "TK 3331"),
    # HR — NHẠY (chỉ phòng Nhân sự/giám đốc; ghim local). Demo RLS điểm nhấn.
    Metric("quy_luong_thang", "Tổng quỹ lương tháng", ("ky", "don_vi"), _S, "nhạy: HR"),
]


def register_catalog() -> None:
    for m in _CATALOG:
        REGISTRY.register(m)


register_catalog()
