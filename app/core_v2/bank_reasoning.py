"""Read-only, bounded Bank-case conversation for the synthetic V2 developer track.

This adapter is deliberately deterministic until the separately governed model/evaluation gate is
open.  It can explain only findings already produced by the Bank engine, ask one clarification,
or abstain.  It cannot create or alter accounting state, numbers, classifications or approvals.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class BankConversationReply(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["explanation", "clarification", "abstention"]
    text: str
    finding_ids: tuple[str, ...] = ()
    evidence_snapshot_ids: tuple[str, ...] = ()
    rule_ids: tuple[str, ...] = ()
    mutates_case: Literal[False] = False
    model_provider: str | None = None
    model_version: str | None = None
    prompt_hash: str | None = None
    config_hash: str | None = None
    synthetic_fallback: bool = True


class ReasoningModelRecord(BaseModel):
    """Owner-pinned metadata; a record alone never authorizes live model execution."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: str
    model_version: str
    prompt_hash: str
    config_hash: str
    egress_policy: Literal["deny_until_owner_pins_model", "approved_minimized_egress"]
    owner_approved: bool = False


_FORBIDDEN_REQUESTS = ("bỏ qua", "override", "post", "thanh toán", "pay", "khóa kỳ", "close period", "run sql", "chạy sql", "widen scope", "mở rộng phạm vi")


class BoundedReasoningAdapter:
    """A safe development implementation of the Core V2 ``ReasoningPort`` boundary."""

    def respond(self, case_view: dict, question: str) -> BankConversationReply:
        text = question.strip()
        findings = tuple(case_view.get("findings") or ())
        evidence = tuple(item["snapshot_id"] for item in case_view.get("evidence") or ())
        if any(token in text.lower() for token in _FORBIDDEN_REQUESTS):
            return BankConversationReply(kind="abstention",
                text="Yêu cầu không thể thay đổi kiểm tra, phê duyệt, phạm vi hoặc thực thi BRAVO.",
                evidence_snapshot_ids=evidence)
        if not text:
            return BankConversationReply(kind="clarification",
                text="Hãy nêu mã finding cần giải thích hoặc hỏi về bằng chứng đang thiếu.")
        selected = tuple(item for item in findings if item["finding_id"] in text)
        if not selected and len(findings) == 1:
            selected = findings
        if not selected:
            return BankConversationReply(kind="abstention",
                text="Không có finding đã được kiểm tra phù hợp để trả lời. Hãy chạy kiểm tra hoặc nêu mã finding.",
                evidence_snapshot_ids=evidence)
        item = selected[0]
        result_ids = tuple(item.get("check_result_ids") or ())
        snapshots = tuple(item.get("evidence_snapshot_ids") or ())
        return BankConversationReply(kind="explanation",
            text=(f"Finding {item['finding_id']} được phân loại {item['finding_type']} "
                  f"với mức độ {item['severity']}. Đây là diễn giải của kết quả kiểm tra; "
                  "không thay đổi số tiền, phân loại hay trạng thái phê duyệt."),
            finding_ids=tuple(x["finding_id"] for x in selected), evidence_snapshot_ids=snapshots,
            rule_ids=result_ids)


# No live model is active until an owner-pinned record and evaluation exist.
SyntheticBankReasoning = BoundedReasoningAdapter
