"""Build-time (OFFLINE) — đọc `Danh mục TK TT99.xlsx` -> freeze YAML versioned.

Chạy MỘT LẦN ở máy dev khi danh mục TK đổi; KHÔNG chạy lúc runtime (loader đọc YAML).
Dùng stdlib (zipfile + xml.etree) — không kéo openpyxl/torch (anti-over-engineering).

  python scripts/build_coa_from_xlsx.py --dump            # in cấu trúc sheet để soát
  python scripts/build_coa_from_xlsx.py                   # sinh app/accounting/data/*.yaml
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_REL_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def _col_index(cell_ref: str) -> int:
    """A1 -> 0, B1 -> 1, ... (chỉ phần chữ)."""
    letters = re.match(r"[A-Z]+", cell_ref).group()
    idx = 0
    for ch in letters:
        idx = idx * 26 + (ord(ch) - ord("A") + 1)
    return idx - 1


def read_xlsx(path: str) -> dict[str, list[list[str]]]:
    """Trả {sheet_name: rows}, mỗi row là list ô (string, '' nếu trống)."""
    z = zipfile.ZipFile(path)
    # shared strings
    shared: list[str] = []
    if "xl/sharedStrings.xml" in z.namelist():
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
        for si in root.findall(f"{_NS}si"):
            shared.append("".join(t.text or "" for t in si.iter(f"{_NS}t")))
    # map rId -> sheet file
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rid_to_target = {r.get("Id"): r.get("Target") for r in rels}
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    out: dict[str, list[list[str]]] = {}
    for sh in wb.find(f"{_NS}sheets"):
        name = sh.get("name")
        rid = sh.get(f"{_REL_NS}id")
        target = rid_to_target[rid]
        target = target if target.startswith("xl/") else "xl/" + target
        sheet = ET.fromstring(z.read(target))
        rows: list[list[str]] = []
        for row in sheet.iter(f"{_NS}row"):
            cells: list[str] = []
            for c in row.findall(f"{_NS}c"):
                ci = _col_index(c.get("r"))
                while len(cells) <= ci:
                    cells.append("")
                v = c.find(f"{_NS}v")
                if v is None or v.text is None:
                    val = ""
                elif c.get("t") == "s":
                    val = shared[int(v.text)]
                else:
                    val = v.text
                cells[ci] = (val or "").strip()
            rows.append(cells)
        out[name] = rows
    return out


def _dump(sheets: dict[str, list[list[str]]]) -> None:
    for name, rows in sheets.items():
        print(f"\n===== SHEET: {name!r} ({len(rows)} rows) =====")
        for i, r in enumerate(rows[:30]):
            print(f"[{i}]", " | ".join(c[:28] for c in r))


_LOAI_MAP = {
    "TÀI SẢN": "tai_san", "NỢ PHẢI TRẢ": "no_phai_tra", "VỐN CHỦ SỞ HỮU": "von_chu_so_huu",
    "DOANH THU": "doanh_thu", "CHI PHÍ": "chi_phi", "XÁC ĐỊNH KẾT QUẢ": "xac_dinh_kqkd",
}


def _norm_loai(text: str) -> str:
    t = text.replace("LOẠI TÀI KHOẢN", "").strip().upper()
    for key, slug in _LOAI_MAP.items():
        if key in t:
            return slug
    return t.lower().replace(" ", "_")


def _get(row: list[str], i: int) -> str:
    return row[i].strip() if i < len(row) else ""


def build_coa(rows: list[list[str]]) -> list[dict]:
    """Sheet 'HTTK theo TT99' -> list account. col1=Cấp1(3 số), col2=Cấp2(4 số), col3=Tên."""
    accounts: list[dict] = []
    loai: str | None = None
    for row in rows:
        c1, c2, c3 = _get(row, 1), _get(row, 2), _get(row, 3)
        if not c1 and not c2 and c3.startswith("LOẠI TÀI KHOẢN"):
            loai = _norm_loai(c3)
            continue
        if re.fullmatch(r"\d{3}", c1):
            accounts.append({"code": c1, "level": 1, "parent": None, "name": c3, "loai": loai})
        elif re.fullmatch(r"\d{4}", c2):
            accounts.append({"code": c2, "level": 2, "parent": c2[:3], "name": c3, "loai": loai})
    # is_postable: cấp-2 luôn postable; cấp-1 postable CHỈ KHI không có con cấp-2.
    has_child = {a["parent"] for a in accounts if a["level"] == 2}
    for a in accounts:
        a["is_postable"] = a["level"] == 2 or a["code"] not in has_child
    return accounts


def _classify_change(name_tt200: str, name_tt99: str, note: str) -> tuple[str, bool]:
    t200, t99, n = name_tt200.strip(), name_tt99.strip(), note.lower()
    if t200 == "--" or "thêm" in n or "bổ sung" in n:
        return "THEM", True
    if t99 == "--" or n.startswith("bỏ") or "bỏ tk" in n:
        return "BO", True
    if "đổi tên" in n:
        return "DOI_TEN", False
    if "không đổi" in n or "giữ nguyên" in n:
        return "KHONG_DOI", False
    if "điều chỉnh" in n or "khác" in n:
        return "KHAC", True
    return "KHONG_DOI", False


def build_crosswalk(rows: list[list[str]]) -> list[dict]:
    """Sheet 'Sự khác biệt' -> crosswalk. col1/col2=mã, col4=tên TT200, col5=tên TT99, col6=note."""
    out: list[dict] = []
    for row in rows:
        c1, c2, c3 = _get(row, 1), _get(row, 2), _get(row, 3)
        if c3.startswith("LOẠI TÀI KHOẢN"):
            continue
        code = c2 if re.fullmatch(r"\d{4}", c2) else (c1 if re.fullmatch(r"\d{3}", c1) else None)
        if not code:
            continue
        name200, name99, note = _get(row, 4), _get(row, 5), _get(row, 6)
        change, needs_confirm = _classify_change(name200, name99, note)
        out.append({"code": code, "name_tt200": name200 if name200 != "--" else None,
                    "name_tt99": name99 if name99 != "--" else None, "change": change,
                    "note": note, "needs_confirm": needs_confirm})
    return out


def _emit_yaml(path: Path, header: dict, key: str, items: list[dict]) -> None:
    import yaml

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(header, f, allow_unicode=True, sort_keys=False)
        f.write("\n")
        yaml.safe_dump({key: items}, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    print(f"  wrote {path}  ({len(items)} {key})")


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    xlsx = root / "file_system" / "Danh mục TK TT99.xlsx"
    sheets = read_xlsx(str(xlsx))
    if "--dump" in sys.argv:
        _dump(sheets)
        sys.exit(0)

    coa = build_coa(sheets["HTTK theo TT99"])
    crosswalk = build_crosswalk(sheets["Sự khác biệt"])
    n1 = sum(1 for a in coa if a["level"] == 1)
    n2 = sum(1 for a in coa if a["level"] == 2)
    print(f"CoA: {len(coa)} accounts ({n1} cấp-1, {n2} cấp-2); crosswalk: {len(crosswalk)} entries")

    out_dir = root / "app" / "accounting" / "data"
    _emit_yaml(out_dir / "coa_tt99_v2025.yaml",
               {"version": "TT99/2025", "effective_from": "2026-01-01",
                "source": "file_system/Danh mục TK TT99.xlsx · sheet 'HTTK theo TT99'",
                "note": "Sinh tự động bởi scripts/build_coa_from_xlsx.py — KHÔNG sửa tay."},
               "accounts", coa)
    _emit_yaml(out_dir / "crosswalk_tt200_tt99_v2025.yaml",
               {"version": "TT200->TT99/2025", "effective_from": "2026-01-01",
                "source": "file_system/Danh mục TK TT99.xlsx · sheet 'Sự khác biệt'",
                "note": "Sinh tự động — needs_confirm=True (THEM/BO/KHAC) cần kế toán xác nhận."},
               "entries", crosswalk)
