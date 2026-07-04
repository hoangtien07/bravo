"""Xuất bút toán nháp ra file để kế toán NHẬP TAY vào ERP (ADR-0016).

Không phụ thuộc ERP write API: cổng ghi cuối cùng là con người (non-invasive, invariant #2).
CSV mặc định (không cần thư viện ngoài, giữ air-gap; BOM UTF-8 để Excel đọc tiếng Việt đúng).
XLSX chỉ khi có openpyxl (tùy chọn). Mọi số lấy nguyên từ payload bút toán (không tính lại).
"""
from __future__ import annotations

import csv
import io


def journal_to_rows(payload: dict) -> list[list[str]]:
    """Bút toán (JournalEntryPayload dạng dict) -> ma trận ô để ghi CSV/XLSX."""
    inv = payload.get("invoice") or {}
    rows: list[list[str]] = [
        ["Hoá đơn", str(inv.get("so_hoa_don") or ""), "Ký hiệu", str(inv.get("ky_hieu") or "")],
        ["Bên bán", str(inv.get("ten_ban") or ""), "MST", str(inv.get("mst_ban") or "")],
        ["Ngày lập", str(inv.get("ngay_lap") or ""), "", ""],
        [],
        ["TK", "Nợ", "Có", "Diễn giải", "Nguồn (truy vết)"],
    ]
    for ln in payload.get("lines", []):
        rows.append([
            str(ln.get("account", "")),
            str(ln.get("debit", "") or ""),
            str(ln.get("credit", "") or ""),
            str(ln.get("memo", "") or ""),
            str(ln.get("source_ref", "") or ""),
        ])
    rows.append([])
    rows.append(["Tổng", str(payload.get("total_debit", "")), str(payload.get("total_credit", "")), "", ""])
    flags = payload.get("validation_flags") or []
    if flags:
        rows.append([])
        rows.append(["Cảnh báo — kế toán xác nhận trước khi nhập ERP:"])
        rows.extend([[str(f)] for f in flags])
    return rows


def to_csv(payload: dict) -> bytes:
    """CSV + BOM UTF-8 (Excel mở đúng dấu tiếng Việt). Không phụ thuộc thư viện ngoài."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    for row in journal_to_rows(payload):
        writer.writerow(row)
    return ("﻿" + buf.getvalue()).encode("utf-8")


def batch_to_csv(payloads: list[dict]) -> bytes:
    """Xuất GỘP nhiều bút toán vào 1 CSV (mỗi bút toán cách nhau 1 dòng trống) — nhập tay theo lô."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    for i, p in enumerate(payloads):
        if i > 0:
            writer.writerow([])
            writer.writerow([])
        for row in journal_to_rows(p):
            writer.writerow(row)
    return ("﻿" + buf.getvalue()).encode("utf-8")


def to_xlsx(payload: dict) -> bytes:
    """XLSX — chỉ khả dụng nếu cài openpyxl (tùy chọn, không bắt buộc cho air-gap)."""
    from openpyxl import Workbook  # optional dep -> ImportError nếu chưa cài

    wb = Workbook()
    ws = wb.active
    ws.title = "ButToan"
    for row in journal_to_rows(payload):
        ws.append(row)
    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()
