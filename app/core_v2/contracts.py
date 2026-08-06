"""Framework-independent AccountingCase Core V2 contracts (WP-02)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core_v2.wp01_schema import ScopeKey


def _nonblank(value: str) -> str:
    if not value:
        raise ValueError("must not be blank")
    return value


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class CaseType(StrEnum):
    BANK_RECONCILIATION = "bank_reconciliation"
    VOUCHER_EVIDENCE_REVIEW = "voucher_evidence_review"
    PERIOD_CLOSE_READINESS = "period_close_readiness"


class CaseState(StrEnum):
    NEW = "NEW"
    SCOPE_LOCKED = "SCOPE_LOCKED"
    EVIDENCE_PENDING = "EVIDENCE_PENDING"
    EVIDENCE_READY = "EVIDENCE_READY"
    CHECKED = "CHECKED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    REVIEWED = "REVIEWED"
    EXPORTED = "EXPORTED"
    CLOSED = "CLOSED"
    ABSTAINED = "ABSTAINED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    SUPERSEDED = "SUPERSEDED"


class FindingSeverity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReviewDisposition(StrEnum):
    INVESTIGATE = "investigate"
    RESOLVED = "resolved"
    ACCEPTED_EXCEPTION = "accepted_exception"
    ESCALATE = "escalate"


class AccountingCaseId(ContractModel):
    value: str = Field(pattern=r"^case_[A-Za-z0-9_-]{8,128}$")


class CaseActor(ContractModel):
    user_id: str
    role: str
    scope_ref: str

    _required = field_validator("user_id", "role", "scope_ref")(_nonblank)


class EvidenceRequest(ContractModel):
    source_type: str
    required_fields: tuple[str, ...]
    coverage_rule: str
    allowed_version: str

    _required = field_validator("source_type", "coverage_rule", "allowed_version")(_nonblank)


class EvidenceSnapshot(ContractModel):
    snapshot_id: str
    source_type: str
    source_version: str
    cutoff: datetime
    captured_at: datetime
    content_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    supersedes: str | None = None
    complete: bool
    scope: ScopeKey

    _required = field_validator("snapshot_id", "source_type", "source_version")(_nonblank)

    @model_validator(mode="after")
    def chronological_capture(self) -> "EvidenceSnapshot":
        if self.captured_at < self.cutoff:
            raise ValueError("captured_at cannot precede cutoff")
        return self


class DeterministicCheckResult(ContractModel):
    check_id: str
    rule_version: str
    inputs: dict[str, Any]
    result: dict[str, Any]
    reason_code: str
    lineage_snapshot_ids: tuple[str, ...]

    _required = field_validator("check_id", "rule_version", "reason_code")(_nonblank)


class Finding(ContractModel):
    finding_id: str
    finding_type: str
    severity: FindingSeverity
    status: str
    evidence_snapshot_ids: tuple[str, ...]
    check_result_ids: tuple[str, ...]
    reviewer_disposition: str | None = None

    _required = field_validator("finding_id", "finding_type", "status")(_nonblank)


class ReviewDecision(ContractModel):
    """Immutable reviewer decision bound to evidence and the reviewing identity."""

    finding_id: str
    disposition: ReviewDisposition
    reviewer_id: str
    reason_code: str
    note: str | None = None
    evidence_snapshot_ids: tuple[str, ...] = ()
    decision_hash: str = Field(pattern=r"^[a-f0-9]{64}$")

    _required = field_validator("finding_id", "reviewer_id", "reason_code")(_nonblank)

    @model_validator(mode="after")
    def disposition_evidence_requirements(self) -> "ReviewDecision":
        if self.disposition is ReviewDisposition.RESOLVED and not self.evidence_snapshot_ids:
            raise ValueError("resolved decision requires resolution evidence")
        return self


class RecommendationDraft(ContractModel):
    recommendation_type: str
    evidence_snapshot_ids: tuple[str, ...]
    alternatives: tuple[str, ...]
    confidence: Decimal | None = Field(default=None, ge=Decimal("0"), le=Decimal("1"))
    assumptions: tuple[str, ...]

    _required = field_validator("recommendation_type")(_nonblank)


class DraftAction(ContractModel):
    action_type: str
    target_capability: str
    payload: dict[str, Any]
    source_snapshot_ids: tuple[str, ...]
    payload_hash: str = Field(pattern=r"^[a-f0-9]{64}$")

    _required = field_validator("action_type", "target_capability")(_nonblank)


class ApprovalEnvelope(ContractModel):
    maker_id: str
    checker_id: str
    payload_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    policy_version: str
    approved_at: datetime
    # WP-04: the checker approves one immutable export payload together with the exact
    # evidence/result/review-decision hashes used to produce it.  Optional preserves WP-02
    # contract fixtures; the Bank orchestration requires all three values.
    evidence_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    result_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    review_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    invalidation_reason: str | None = None

    _required = field_validator("maker_id", "checker_id", "policy_version")(_nonblank)

    @model_validator(mode="after")
    def maker_checker_separation(self) -> "ApprovalEnvelope":
        if self.maker_id == self.checker_id:
            raise ValueError("maker and checker must differ")
        return self


class CaseTransition(ContractModel):
    from_state: CaseState
    to_state: CaseState
    actor: CaseActor
    preconditions: tuple[str, ...]
    expected_revision: int = Field(ge=0)
    idempotency_key: str

    _required = field_validator("idempotency_key")(_nonblank)


class TraceToolCall(ContractModel):
    tool_name: str
    outcome: Literal["allowed", "denied", "abstained"]
    reference_id: str | None = None

    _required = field_validator("tool_name")(_nonblank)


class ReconstructableTrace(ContractModel):
    contract_version: str
    rule_versions: tuple[str, ...]
    model_version: str | None = None
    prompt_version: str | None = None
    source_snapshot_ids: tuple[str, ...]
    result_ids: tuple[str, ...]
    tool_calls: tuple[TraceToolCall, ...]
    decision_ids: tuple[str, ...]

    _required = field_validator("contract_version")(_nonblank)


class CapabilityManifest(ContractModel):
    reads: tuple[str, ...]
    draft_actions: tuple[str, ...]
    roles: tuple[str, ...]
    limits: dict[str, int]
    egress_policy: str
    abstention_policy: str

    _required = field_validator("egress_policy", "abstention_policy")(_nonblank)


class EvidenceSourcePort(Protocol):
    def capture(self, request: EvidenceRequest, scope: ScopeKey) -> EvidenceSnapshot: ...


class CaseRepositoryPort(Protocol):
    def get(self, case_id: AccountingCaseId) -> Any: ...


class DeterministicEnginePort(Protocol):
    def run(self, case_type: CaseType, evidence: tuple[EvidenceSnapshot, ...]) -> tuple[DeterministicCheckResult, ...]: ...


class ReasoningPort(Protocol):
    def explain(self, trace: ReconstructableTrace) -> RecommendationDraft: ...


class AuthorizationPort(Protocol):
    def can_access(self, actor: CaseActor, scope: ScopeKey, capability: str) -> bool: ...


class AuditPort(Protocol):
    def record(self, trace: ReconstructableTrace) -> None: ...


class ArtifactExportPort(Protocol):
    def export(self, action: DraftAction) -> str: ...


class ClockPort(Protocol):
    def now(self) -> datetime: ...
