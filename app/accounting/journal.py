"""Dựng bút toán kép từ hoá đơn + NUMBER-INTEGRITY GATE (deterministic, ADR-0014).

Bút toán AP chuẩn: Nợ <chi phí/hàng> + Nợ 1331 (VAT) / Có 331 (phải trả NCC).
Mọi SỐ lấy TỪ HOÁ ĐƠN (Decimal) — LLM không sinh (invariant #3).

⚠️ PHẠM VI CỦA GATE — đọc kỹ: "cân Nợ=Có" là **Number-Integrity Gate**, chỉ bảo đảm hai
điều: (1) không bịa số (mọi số truy được về engine_values) và (2) số học cân (Σ Nợ == Σ Có,
dung sai 0 đồng). Nó **KHÔNG** bảo đảm định khoản ĐÚNG NGỮ NGHĨA (đúng loại tài khoản, đủ
điều kiện TSCĐ/khấu trừ VAT). Một bút toán có thể CÂN nhưng SAI tài khoản. Tính đúng ngữ
nghĩa thuộc về kế toán xác nhận ở HITL (maker-checker) — các điều kiện cần xác nhận được
ghi vào `validation_flags` + `needs_review` (xem account_mapper TT45 và VAT TT219 bên dưới).

`JournalEntryPayload` là schema CHẶT cho Draft.payload (giải gap "draft JSONB tự do").
Thiết kế cân-bằng-by-construction: Có 331 = Σ Nợ (chi phí+VAT) -> luôn cân. Nếu Σ này lệch
TỔNG THANH TOÁN của hoá đơn -> ghi CỜ (needs_review) chứ không vỡ (kế toán xử ở HITL).
"""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

# TT219/2013 Đ.15: hoá đơn mua vào từng lần ≥ 20 triệu phải có chứng từ thanh toán KHÔNG dùng
# tiền mặt mới được khấu trừ VAT đầu vào. Lằn ranh này kiểm được; phương thức thanh toán thật
# KHÔNG suy ra được từ hoá đơn -> cờ chờ kế toán (non-invasive).
VAT_NONCASH_THRESHOLD = Decimal("20000000")

from app.accounting.account_mapper import map_invoice
from app.accounting.coa import CoaCatalog, load_coa
from app.data_layer import money
from app.ingestion.invoice_parser import Invoice, validate_invoice


class JournalLine(BaseModel):
    account: str
    debit: Decimal = Decimal(0)
    credit: Decimal = Decimal(0)
    memo: str = ""
    source_ref: str | None = None     # provenance tới dòng hoá đơn / thẻ tổng


class InvoiceMeta(BaseModel):
    mst_ban: str | None = None
    ten_ban: str | None = None
    so_hoa_don: str | None = None
    ky_hieu: str | None = None
    mau_so: str | None = None
    ngay_lap: str | None = None
    source_hash: str | None = None


class JournalEntryPayload(BaseModel):
    """Schema CHẶT cho Draft.payload khi kind='journal_entry'."""

    doc_type: str = "AP_invoice"
    invoice: InvoiceMeta
    lines: list[JournalLine]
    total_debit: Decimal
    total_credit: Decimal
    needs_review: bool = False
    validation_flags: list[str] = Field(default_factory=list)
    engine_values: list[str] = Field(default_factory=list)  # số nguồn+dẫn-xuất (str cho JSON/verify-gate)
    invoice_lines: list[dict] = Field(default_factory=list)  # dòng hàng GỐC (xem lại — không dùng tính toán)

    @model_validator(mode="after")
    def _enforce_number_integrity(self):
        # Number-Integrity Gate (ADR-0014): chỉ chặn BỊA SỐ + LỆCH SỐ HỌC. KHÔNG kiểm đúng-ngữ-nghĩa.
        if not self.lines:
            raise ValueError("Bút toán không có dòng nào")
        for ln in self.lines:
            d, c = money.D(ln.debit), money.D(ln.credit)
            if (d > 0) == (c > 0):  # cả hai > 0, hoặc cả hai = 0
                raise ValueError(f"Dòng TK {ln.account}: phải là Nợ HOẶC Có (không cả hai/không gì)")
        sum_d = money.money_sum([ln.debit for ln in self.lines])
        sum_c = money.money_sum([ln.credit for ln in self.lines])
        if sum_d != sum_c:
            raise ValueError(f"Bút toán KHÔNG cân: Σ Nợ {sum_d} ≠ Σ Có {sum_c} (ADR-0014)")
        if money.D(self.total_debit) != sum_d or money.D(self.total_credit) != sum_c:
            raise ValueError("total_debit/total_credit không khớp Σ dòng")
        return self


def build_journal_entry(inv: Invoice, *, coa: CoaCatalog | None = None,
                        version: str = "v1") -> JournalEntryPayload:
    """Hoá đơn -> bút toán nháp (cân Nợ=Có by-construction). Số từ hoá đơn (Decimal)."""
    coa = coa or load_coa()
    proposal = map_invoice(inv, coa=coa, version=version)
    flags: list[str] = list(validate_invoice(inv)) + list(proposal.notes)

    # Nợ: gộp thành tiền theo tài khoản đích.
    by_acct: dict[str, Decimal] = {}
    refs: dict[str, list[str]] = {}
    for m in proposal.line_mappings:
        amt = money.quantize(m.line.thanh_tien or Decimal(0))
        by_acct[m.debit_account] = by_acct.get(m.debit_account, Decimal(0)) + amt
        refs.setdefault(m.debit_account, []).append(m.line.source_ref)

    lines: list[JournalLine] = []
    for acct, amt in by_acct.items():
        a = coa.lookup(acct)
        lines.append(JournalLine(account=acct, debit=amt,
                                 memo=(a.name if a else acct), source_ref=",".join(refs[acct])))
    # Nợ VAT 1331/1332 (nếu có thuế). Khấu trừ KHÔNG mặc nhiên — xem cờ điều kiện bên dưới.
    vat = money.quantize(inv.tong_tien_thue or Decimal(0))
    if vat > 0:
        lines.append(JournalLine(account=proposal.vat_account, debit=vat,
                                 memo="Thuế GTGT đầu vào (khấu trừ CHỜ điều kiện)", source_ref="TgTThue"))
        # TT219/2013 Đ.15: khấu trừ VAT đầu vào cần (i) hoá đơn GTGT hợp lệ, (ii) hoá đơn ≥20tr có
        # chứng từ thanh toán KHÔNG dùng tiền mặt, (iii) phục vụ SXKD chịu thuế. (ii) là lằn ranh
        # kiểm được; phương thức thanh toán & mục đích KHÔNG suy ra được từ hoá đơn -> cờ HITL.
        pay = inv.tong_thanh_toan
        if pay is not None and money.quantize(pay) >= VAT_NONCASH_THRESHOLD:
            flags.append(
                f"Hoá đơn ≥20tr ({money.quantize(pay):.0f}đ): khấu trừ VAT {vat:.0f}đ yêu cầu chứng từ "
                f"thanh toán KHÔNG dùng tiền mặt (không xác minh được từ hoá đơn) — kế toán xác nhận"
            )

    # Có 331 = Σ Nợ (chi phí + VAT) -> luôn cân.
    total_debit = money.money_sum([ln.debit for ln in lines])
    lines.append(JournalLine(account=proposal.credit_account, credit=total_debit,
                             memo=f"Phải trả người bán {inv.ten_ban or ''}".strip(),
                             source_ref="TgTTTBSo"))

    # Cờ lệch tổng hoá đơn (cân nội bộ vẫn đúng; lệch với hoá đơn -> kế toán xem).
    needs_review = proposal.needs_review
    if inv.tong_thanh_toan is not None and money.quantize(inv.tong_thanh_toan) != total_debit:
        flags.append(f"Tổng bút toán {total_debit} ≠ tổng thanh toán hoá đơn {inv.tong_thanh_toan}")
        needs_review = True
    if flags:
        needs_review = True

    # engine_values: số NGUỒN từ hoá đơn + số DẪN XUẤT (gộp Nợ, tổng Có) — đều tính
    # deterministic bằng money.py, KHÔNG do LLM -> verify-gate (W3.4) dùng làm base values.
    engine = {money.quantize(x) for x in inv.source_numbers()}
    engine |= {money.D(ln.debit) for ln in lines if ln.debit > 0}
    engine |= {money.D(ln.credit) for ln in lines if ln.credit > 0}

    inv_lines = [
        {"stt": ln.stt, "ten_hang": ln.ten_hang, "dvt": ln.dvt,
         "so_luong": str(ln.so_luong) if ln.so_luong is not None else None,
         "don_gia": str(ln.don_gia) if ln.don_gia is not None else None,
         "thanh_tien": str(ln.thanh_tien) if ln.thanh_tien is not None else None,
         "thue_suat": ln.thue_suat,
         "tien_thue": str(ln.tien_thue) if ln.tien_thue is not None else None}
        for ln in inv.lines
    ]
    return JournalEntryPayload(
        invoice=InvoiceMeta(mst_ban=inv.mst_ban, ten_ban=inv.ten_ban, so_hoa_don=inv.so_hoa_don,
                            ky_hieu=inv.ky_hieu, mau_so=inv.mau_so, ngay_lap=inv.ngay_lap,
                            source_hash=inv.source_hash),
        lines=lines, total_debit=total_debit, total_credit=total_debit,
        needs_review=needs_review, validation_flags=flags,
        engine_values=sorted(str(x) for x in engine), invoice_lines=inv_lines,
    )
