"""Engine đối chiếu thuế (TẤT ĐỊNH) — hoá đơn GTGT ↔ tờ khai (TAX-ASSISTANT-AGENT.md Lớp 2).

Chỉ KIẾN NGHỊ (draft chờ kế toán duyệt) — KHÔNG tự sửa tờ khai/nộp. Số từ DỮ LIỆU (Decimal),
KHÔNG do LLM (invariant #3). Bắt: (1) tổng thuế đầu ra/vào từ hoá đơn ≠ tờ khai theo kỳ;
(2) thuế suất lạ (ngoài 0/5/8/10). Lớp 1 (tra luật thuế) tái dùng RAG — không ở engine này.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from app.accounting.rules_governance import statutory_field
from app.data_layer import money

# Externalize ra statutory_rules_vn.yaml (tầng LUẬT). Set thuế suất hợp lệ MỚI NHẤT (2022+ gồm
# 8% giảm theo NQ). LƯU Ý: 8% chỉ áp trong kỳ giảm + loại trừ ngành — điều kiện đủ do kế toán
# xác nhận ở HITL (không mở logic ngành ở đây, giữ freeze demo). Đường dated: statutory_field(as_of).
VALID_RATES = frozenset(statutory_field("vat_valid_rates", "rates"))


@dataclass
class TaxFlag:
    ky: str
    loai: str
    mo_ta: str
    so_hd_thuc: str
    so_khai: str
    chenh_lech: str
    muc_do: int
    bang_chung: list[str] = field(default_factory=list)

    def to_payload(self) -> dict:
        return {"ky": self.ky, "loai": self.loai, "mo_ta": self.mo_ta,
                "so_hd_thuc": self.so_hd_thuc, "so_khai": self.so_khai,
                "chenh_lech": self.chenh_lech, "muc_do": self.muc_do,
                "bang_chung": self.bang_chung, "is_demo": True}


def reconcile(invoices: list | None, tax_returns: list | None) -> list[TaxFlag]:
    invoices = invoices or []
    returns = tax_returns or []
    flags: list[TaxFlag] = []

    for ret in returns:
        ky = ret.get("ky")
        out_actual = sum((money.D(i["tien_thue"]) for i in invoices
                          if i.get("loai") == "dau_ra" and i.get("ky") == ky), Decimal(0))
        in_actual = sum((money.D(i["tien_thue"]) for i in invoices
                         if i.get("loai") == "dau_vao" and i.get("ky") == ky), Decimal(0))
        for label, actual, declared, loai in (
            ("đầu ra", out_actual, money.D(ret.get("thue_dau_ra_khai", 0)), "lech_thue_dau_ra"),
            ("đầu vào", in_actual, money.D(ret.get("thue_dau_vao_khai", 0)), "lech_thue_dau_vao"),
        ):
            if actual != declared:
                diff = actual - declared
                flags.append(TaxFlag(
                    ky=str(ky), loai=loai,
                    mo_ta=f"Thuế GTGT {label} từ hoá đơn ({actual:,.0f}đ) ≠ tờ khai ({declared:,.0f}đ)",
                    so_hd_thuc=str(actual), so_khai=str(declared), chenh_lech=str(diff),
                    muc_do=2 if abs(diff) >= 1_000_000 else 1,
                    bang_chung=[f"Tổng hoá đơn {label} kỳ {ky}: {actual:,.0f}đ",
                                f"Tờ khai khai: {declared:,.0f}đ",
                                f"Chênh lệch: {diff:,.0f}đ"],
                ))

    for i in invoices:
        rate = i.get("thue_suat")
        if rate not in VALID_RATES:
            flags.append(TaxFlag(
                ky=str(i.get("ky", "")), loai="thue_suat_la",
                mo_ta=f"Hoá đơn {i.get('id')} có thuế suất LẠ {rate}%",
                so_hd_thuc=str(money.D(i.get("tien_thue", 0))), so_khai="0", chenh_lech="0",
                muc_do=2, bang_chung=[f"Thuế suất {rate}% ngoài khung 0/5/8/10 (GTGT VN)"],
            ))

    flags.sort(key=lambda f: f.muc_do, reverse=True)
    return flags
