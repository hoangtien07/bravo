"""Từ điển viết tắt nghiệp vụ kế toán/ERP Việt Nam — query expansion tất định.

Helpdesk/kế toán gõ viết tắt là chuẩn giao tiếp hằng ngày ("khai báo CCDC", "lên CĐPS")
nhưng tài liệu viết cụm đầy đủ -> lexical trượt, dense phập phù (council 2026-07-12 #6).
Mở rộng dạng "CCDC (công cụ dụng cụ)" TRƯỚC khi retrieve: giữ nguyên từ gốc (mã/số vẫn
khớp lexical), thêm cụm đầy đủ cho cả hai nhánh. Tất định, audit được — không LLM.

CHỈ đưa vào đây viết tắt KHÔNG nhập nhằng (bỏ: HĐ hóa đơn/hợp đồng, KH khách hàng/kế
hoạch, TK tài khoản/tồn kho...).
"""
from __future__ import annotations

import re

# viết tắt (không phân biệt hoa thường, match cả bản không dấu) -> cụm đầy đủ
_ABBREVIATIONS: dict[str, str] = {
    "nvl": "nguyên vật liệu",
    "ccdc": "công cụ dụng cụ",
    "tscđ": "tài sản cố định",
    "tscd": "tài sản cố định",
    "gtgt": "giá trị gia tăng",
    "bctc": "báo cáo tài chính",
    "cđps": "cân đối phát sinh",
    "cdps": "cân đối phát sinh",
    "ncc": "nhà cung cấp",
    "pnk": "phiếu nhập kho",
    "pxk": "phiếu xuất kho",
    "đntt": "đề nghị thanh toán",
    "dntt": "đề nghị thanh toán",
    "unc": "ủy nhiệm chi",
    "bhxh": "bảo hiểm xã hội",
    "tncn": "thu nhập cá nhân",
    "tndn": "thu nhập doanh nghiệp",
    "xnt": "xuất nhập tồn",
    "kqkd": "kết quả kinh doanh",
    "sxkd": "sản xuất kinh doanh",
    "htk": "hàng tồn kho",
    "cltg": "chênh lệch tỷ giá",
    "hđđt": "hóa đơn điện tử",
    "hddt": "hóa đơn điện tử",
}

_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(a) for a in sorted(_ABBREVIATIONS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE | re.UNICODE,
)


def expand_abbreviations(query: str) -> str:
    """'khai báo CCDC' -> 'khai báo CCDC (công cụ dụng cụ)'. Không đổi gì nếu cụm đầy đủ
    đã có sẵn trong câu (tránh lặp); mỗi viết tắt chỉ mở rộng lần xuất hiện đầu."""
    if not query:
        return query
    lowered = query.lower()
    expanded: set[str] = set()

    def _sub(m: re.Match) -> str:
        abbr = m.group(0)
        full = _ABBREVIATIONS.get(abbr.lower(), "")
        if not full or full in lowered or abbr.lower() in expanded:
            return abbr
        expanded.add(abbr.lower())
        return f"{abbr} ({full})"

    return _PATTERN.sub(_sub, query)
