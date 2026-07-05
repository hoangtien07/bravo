"""Parser hoá đơn điện tử VN (NĐ123/2020 + TT78/2021, QĐ 1450/TCT) — DETERMINISTIC.

Hoá đơn điện tử VN là XML CÓ CẤU TRÚC: trích xuất số liệu là parse thuần, KHÔNG để LLM
bịa số (khớp invariant #3). Đọc theo TÊN TAG (namespace-agnostic) để bám được biến thể
nhà cung cấp; thiếu field -> để None + cờ (không đoán). Mọi số tiền là Decimal.

XML hoá đơn là nội dung KHÔNG tin cậy -> ưu tiên defusedxml (chống XXE/billion-laughs);
fallback stdlib nếu chưa cài (cài `defusedxml` cho production).

Cấu trúc chuẩn: HDon/DLHDon/NDHDon: TTChung(SHDon·KHHDon·KHMSHDon·NLap·DVTTe),
NBan/NMua(Ten·MST), DSHHDVu/HHDVu(THHDVu·DVTinh·SLuong·DGia·ThTien·TSuat·TThue),
TToan(TgTCThue·TgTThue·TgTTTBSo).
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

try:  # XXE-safe cho XML không tin cậy
    from defusedxml.ElementTree import fromstring as _fromstring
except ImportError:  # pragma: no cover - fallback khi chưa cài defusedxml
    from xml.etree.ElementTree import fromstring as _fromstring

VALID_TAX_RATES = frozenset({"0", "5", "8", "10", "KCT", "KKKNT"})  # KCT=không chịu, KKKNT=không kê khai


# --------------------------------------------------------------------------------------
# XML helpers — tìm theo TÊN TAG cục bộ, bỏ namespace.
# --------------------------------------------------------------------------------------
def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _find(el, name: str):
    for e in el.iter():
        if _local(e.tag) == name:
            return e
    return None


def _findall(el, name: str) -> list:
    return [e for e in el.iter() if _local(e.tag) == name]


def _text(el, name: str) -> str | None:
    if el is None:
        return None
    e = _find(el, name)
    return e.text.strip() if (e is not None and e.text and e.text.strip()) else None


def _dec(s: str | None) -> Decimal | None:
    if s is None or s == "":
        return None
    t = s.strip().replace(" ", "")
    if "," in t and "." in t:        # 1.234.567,89 -> 1234567.89 (VN)
        t = t.replace(".", "").replace(",", ".")
    elif "," in t:                    # 1234567,89 -> 1234567.89
        t = t.replace(",", ".")
    try:
        return Decimal(t)
    except InvalidOperation:
        return None


def _parse_rate(s: str | None) -> str | None:
    """'10%' -> '10'; 'KCT'/'KKKNT' giữ nguyên; None -> None."""
    if not s:
        return None
    t = s.strip().upper().replace("%", "").strip()
    if t in {"KCT", "KKKNT"}:
        return t
    t = t.replace(",", ".")
    try:
        return str(int(Decimal(t)))   # '10.0' -> '10'
    except InvalidOperation:
        return t


# --------------------------------------------------------------------------------------
# MST checksum (Tổng cục Thuế) — 10 số (DN) hoặc 13 số (đơn vị phụ thuộc).
# --------------------------------------------------------------------------------------
_MST_WEIGHTS = [31, 29, 23, 19, 17, 13, 7, 5, 3]


def valid_mst(mst: str | None) -> bool:
    s = re.sub(r"\D", "", mst or "")
    if len(s) not in (10, 13):
        return False
    total = sum(int(s[i]) * _MST_WEIGHTS[i] for i in range(9))
    chk = 10 - (total % 11)
    return chk <= 9 and int(s[9]) == chk


# --------------------------------------------------------------------------------------
# Value-objects.
# --------------------------------------------------------------------------------------
@dataclass(frozen=True)
class InvoiceLine:
    stt: int | None
    ten_hang: str | None
    dvt: str | None
    so_luong: Decimal | None
    don_gia: Decimal | None
    thanh_tien: Decimal | None       # tiền hàng chưa thuế
    thue_suat: str | None            # '0'|'5'|'8'|'10'|'KCT'|'KKKNT'
    tien_thue: Decimal | None
    source_ref: str                  # provenance, vd "HHDVu[1]"


@dataclass(frozen=True)
class Invoice:
    mau_so: str | None
    ky_hieu: str | None
    so_hoa_don: str | None
    ngay_lap: str | None
    currency: str
    mst_ban: str | None
    ten_ban: str | None
    mst_mua: str | None
    ten_mua: str | None
    lines: list[InvoiceLine]
    tong_tien_hang: Decimal | None   # TgTCThue
    tong_tien_thue: Decimal | None   # TgTThue
    tong_thanh_toan: Decimal | None  # TgTTTBSo
    source_hash: str
    raw_xml_path: str | None = None

    def key(self) -> str:
        """Khoá trùng hoá đơn (mst_ban + ký hiệu + số)."""
        return f"{self.mst_ban}|{self.ky_hieu}|{self.so_hoa_don}"

    def source_numbers(self) -> list[Decimal]:
        """Mọi số NGUỒN từ hoá đơn — làm engine base values cho verify-gate (invariant #3)."""
        nums: list[Decimal] = []
        for ln in self.lines:
            nums += [x for x in (ln.so_luong, ln.don_gia, ln.thanh_tien, ln.tien_thue) if x is not None]
        nums += [x for x in (self.tong_tien_hang, self.tong_tien_thue, self.tong_thanh_toan)
                 if x is not None]
        return nums


# --------------------------------------------------------------------------------------
# Parse.
# --------------------------------------------------------------------------------------
def parse_invoice_xml(xml_bytes: bytes | str, *, raw_xml_path: str | None = None) -> Invoice:
    data = xml_bytes.encode("utf-8") if isinstance(xml_bytes, str) else xml_bytes
    root = _fromstring(data)
    source_hash = hashlib.sha256(data).hexdigest()[:16]

    nban = _find(root, "NBan")
    nmua = _find(root, "NMua")
    lines: list[InvoiceLine] = []
    for i, hh in enumerate(_findall(root, "HHDVu"), start=1):
        stt = _text(hh, "STT")
        lines.append(InvoiceLine(
            stt=int(stt) if stt and stt.isdigit() else i,
            ten_hang=_text(hh, "THHDVu") or _text(hh, "TenHang"),
            dvt=_text(hh, "DVTinh"),
            so_luong=_dec(_text(hh, "SLuong")),
            don_gia=_dec(_text(hh, "DGia")),
            thanh_tien=_dec(_text(hh, "ThTien")),
            thue_suat=_parse_rate(_text(hh, "TSuat")),
            tien_thue=_dec(_text(hh, "TThue")),
            source_ref=f"HHDVu[{i}]",
        ))

    ttoan = _find(root, "TToan")
    return Invoice(
        mau_so=_text(root, "KHMSHDon"),
        ky_hieu=_text(root, "KHHDon"),
        so_hoa_don=_text(root, "SHDon"),
        ngay_lap=_text(root, "NLap"),
        currency=_text(root, "DVTTe") or "VND",
        mst_ban=_text(nban, "MST") if nban is not None else None,
        ten_ban=_text(nban, "Ten") if nban is not None else None,
        mst_mua=_text(nmua, "MST") if nmua is not None else None,
        ten_mua=_text(nmua, "Ten") if nmua is not None else None,
        lines=lines,
        tong_tien_hang=_dec(_text(ttoan, "TgTCThue")) if ttoan is not None else None,
        tong_tien_thue=_dec(_text(ttoan, "TgTThue")) if ttoan is not None else None,
        tong_thanh_toan=_dec(_text(ttoan, "TgTTTBSo")) if ttoan is not None else None,
        source_hash=source_hash,
        raw_xml_path=raw_xml_path,
    )


# --------------------------------------------------------------------------------------
# Validate (deterministic) — trả danh sách CỜ; rỗng = sạch. KHÔNG raise (caller quyết HITL).
# --------------------------------------------------------------------------------------
def validate_invoice(inv: Invoice, *, rounding_tol: Decimal = Decimal("1")) -> list[str]:
    from app.data_layer import money

    flags: list[str] = []
    if not valid_mst(inv.mst_ban):
        flags.append(f"MST bên bán không hợp lệ: {inv.mst_ban}")
    if inv.mst_mua and not valid_mst(inv.mst_mua):
        flags.append(f"MST bên mua không hợp lệ: {inv.mst_mua}")
    if not inv.lines:
        flags.append("Hoá đơn không có dòng hàng nào")

    for ln in inv.lines:
        if ln.thue_suat is not None and ln.thue_suat not in VALID_TAX_RATES:
            flags.append(f"Thuế suất lạ ở {ln.source_ref}: {ln.thue_suat}")
        # tiền thuế dòng ≈ thành tiền × suất (dung sai làm tròn)
        if (ln.tien_thue is not None and ln.thanh_tien is not None
                and ln.thue_suat and ln.thue_suat.isdigit()):
            expected = (ln.thanh_tien * Decimal(ln.thue_suat) / Decimal(100))
            if abs(money.D(ln.tien_thue) - money.quantize(expected)) > rounding_tol:
                flags.append(f"Tiền thuế lệch ở {ln.source_ref}: {ln.tien_thue} ≠ {expected:.0f}")

    # Σ thành tiền dòng == tổng tiền hàng
    line_amounts = [ln.thanh_tien for ln in inv.lines if ln.thanh_tien is not None]
    if inv.tong_tien_hang is not None and line_amounts:
        if not money.reconcile(inv.tong_tien_hang, line_amounts, tol=rounding_tol):
            flags.append(f"Σ thành tiền dòng ≠ tổng tiền hàng ({inv.tong_tien_hang})")
    # tổng hàng + tổng thuế == tổng thanh toán
    if None not in (inv.tong_tien_hang, inv.tong_tien_thue, inv.tong_thanh_toan):
        if abs((inv.tong_tien_hang + inv.tong_tien_thue) - inv.tong_thanh_toan) > rounding_tol:
            flags.append("Tổng tiền hàng + thuế ≠ tổng thanh toán")
    return flags
