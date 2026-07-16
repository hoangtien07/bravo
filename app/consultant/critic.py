"""Deterministic response critic for workflow prerequisites and risky actions."""
from __future__ import annotations

from dataclasses import dataclass

from app.consultant.service import PreparedConsultantTurn, _fold


@dataclass(frozen=True)
class CriticResult:
    answer: str
    tags: tuple[str, ...] = ()


def review(answer: str, turn: PreparedConsultantTurn | None) -> CriticResult:
    """Add a bounded corrective guard; it never treats an LLM answer as a policy override."""
    if turn is None:
        return CriticResult(answer)
    text = answer or ""
    folded = _fold(text)
    tags: list[str] = []
    prefix: list[str] = []
    if (turn.frame.goal_type == "financial_statements_ready"
            and turn.state.current_node != "report_validated"
            and any(token in folded for token in ("mo bao cao", "vao bao cao", "in bao cao"))):
        tags.append("prerequisite_guard")
        prefix.append(
            "Lưu ý: trước khi mở/lập báo cáo, cần hoàn tất bước "
            f"'{turn.state.current_node or 'xác định kỳ và dữ liệu'}' trong quy trình khóa sổ."
        )
    if turn.frame.risk in {"U3", "U4"} and any(
            token in folded for token in ("da chay", "toi da sua", "toi da thuc thi", "execute thanh cong")):
        tags.append("execution_claim_guard")
        prefix.append(
            "Tác vụ cấu hình/DB chỉ được trình bày dưới dạng bản nháp; chưa có thay đổi nào được thực thi."
        )
    return CriticResult("\n\n".join([*prefix, text]) if prefix else text, tuple(tags))
