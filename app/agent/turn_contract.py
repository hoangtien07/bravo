"""Turn-level product contract for knowledge QA versus work-product generation.

The original chat runtime treated every request as an internal-document lookup.  That is safe
for factual BRAVO guidance, but it makes attachment-led tasks (analyse this screenshot, design a
table, draft SQL/XML, list the missing reference files) collapse into a generic RAG abstention.
This module keeps the distinction deterministic, auditable and independent of model choice.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal


TurnMode = Literal["knowledge_qa", "work_product"]


def _fold(text: str) -> str:
    value = unicodedata.normalize("NFD", text or "")
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    return value.replace("đ", "d").replace("Đ", "D").lower()


_WORK_PRODUCT_PATTERNS = tuple(re.compile(pattern) for pattern in (
    r"\bxac dinh (?:ro )?bai toan\b",
    r"\bphan tich (?:de bai|yeu cau|anh|tai lieu|nghiep vu)\b",
    r"\b(?:tao|viet|soan|sinh|generate|thiet ke|xay dung)\b.{0,45}"
    r"\b(?:db|database|sql|ddl|table|bang|view|layout|datasource|template|xml|script|code|schema)\b",
    r"\b(?:db|database|sql|ddl|table|bang|view|layout|datasource|template|xml|script|code|schema)"
    r"\b.{0,35}\b(?:tao|viet|soan|sinh|generate|thiet ke|xay dung)\b",
    r"\bcan (?:nhung |cac )?(?:file|tep|mau|tai lieu) (?:mau )?(?:gi|nao)\b",
    r"\btrien khai (?:chuc nang|module|man hinh|danh muc)\b",
))


@dataclass(frozen=True)
class TurnContract:
    mode: TurnMode
    has_attachments: bool

    @property
    def is_work_product(self) -> bool:
        return self.mode == "work_product"


def classify_turn(question: str, attachments: list[dict] | None = None) -> TurnContract:
    """Classify only the behavioral contract; corpus routing remains a separate concern."""
    normalized = _fold(question)
    mode: TurnMode = (
        "work_product" if any(pattern.search(normalized) for pattern in _WORK_PRODUCT_PATTERNS)
        else "knowledge_qa"
    )
    return TurnContract(mode=mode, has_attachments=bool(attachments))


def render_turn_contract(contract: TurnContract) -> str:
    """A model-facing policy appended after the global safety contract."""
    evidence = (
        "Các khối [N] có thể là tài liệu nội bộ HOẶC tệp/ảnh do người dùng cung cấp. "
        "Ảnh/tệp người dùng là bằng chứng hợp lệ cho nội dung nhìn thấy trong chính tệp đó; "
        "hãy đọc kỹ và trích [N] khi sử dụng."
        if contract.has_attachments else
        "Các khối [N] là bằng chứng nội bộ được phép truy cập."
    )
    if contract.is_work_product:
        behavior = (
            "Đây là yêu cầu PHÂN TÍCH/TẠO WORK PRODUCT, không phải chỉ là tra cứu tài liệu. "
            "Hãy (1) xác định bài toán và phạm vi từ bằng chứng người dùng đã cung cấp; "
            "(2) tạo phần có thể tạo ngay; (3) nêu rõ giả định; (4) nếu thiếu chuẩn kỹ thuật, "
            "yêu cầu ĐÚNG tên file/bảng/mẫu cần bổ sung và giải thích mục đích từng mẫu. "
            "KHÔNG được trả câu abstain chung chỉ vì RAG không có chunk. Được phép SOẠN DDL/SQL/"
            "XML/code dưới dạng bản nháp để người dùng rà soát; không được tự thực thi hoặc tuyên "
            "bố đã ghi vào ERP/production. Không tự bịa kiểu dữ liệu, constraint hay quy ước BRAVO: "
            "chỗ chưa có căn cứ phải đánh dấu TODO/giả định hoặc hỏi mẫu tương ứng."
        )
    else:
        behavior = (
            "Đây là yêu cầu HỎI ĐÁP TRI THỨC. Nếu tệp/ảnh hoặc lịch sử đã chứa câu trả lời thì "
            "phải dùng chúng để trả lời; chỉ abstain khi không có bằng chứng nào đủ cho một khẳng "
            "định nội bộ cụ thể."
        )
    return f"CHẾ ĐỘ LƯỢT: {contract.mode.upper()}\n- {evidence}\n- {behavior}"
