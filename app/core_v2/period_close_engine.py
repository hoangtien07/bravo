"""Bounded synthetic Period Close readiness checker; this is not a BRAVO close engine."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ClosePrerequisite:
    prerequisite_id: str
    required: bool
    status: str  # complete | pending | not_applicable
    evidence_fresh: bool


@dataclass(frozen=True)
class ReconciliationReference:
    case_id: str
    status: str  # reviewed | unresolved | missing
    material: bool


@dataclass(frozen=True)
class PeriodCloseReadiness:
    ready: bool
    blocker_ids: tuple[str, ...]
    reason_codes: tuple[str, ...]
    execution: str = "readiness artifact produced; BRAVO did not execute close, calculations, reports, or period lock."


def assess_period_close(prerequisites: tuple[ClosePrerequisite, ...],
                        reconciliations: tuple[ReconciliationReference, ...]) -> PeriodCloseReadiness:
    """Fail closed: a required pending/stale item or material unresolved recon blocks readiness."""
    blockers: list[str] = []
    reasons: list[str] = []
    for item in prerequisites:
        if item.required and item.status != "complete":
            blockers.append(item.prerequisite_id)
            reasons.append("REQUIRED_PREREQUISITE_INCOMPLETE")
        elif item.required and not item.evidence_fresh:
            blockers.append(item.prerequisite_id)
            reasons.append("REQUIRED_EVIDENCE_STALE")
    for item in reconciliations:
        if item.material and item.status != "reviewed":
            blockers.append(item.case_id)
            reasons.append("MATERIAL_RECONCILIATION_UNRESOLVED")
    return PeriodCloseReadiness(not blockers, tuple(blockers), tuple(reasons))
