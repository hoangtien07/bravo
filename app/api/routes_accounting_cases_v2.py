"""Authorized synthetic Bank-case API (WP-04).  Legacy routes remain unchanged."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.config import get_settings
from app.core_v2.demo_config import DemoConfigError, load_synthetic_demo_config
from app.adapters.accounting_case_store import SqlSyntheticBankCaseStore
from app.core_v2.bank_orchestration import CaseAccessError, SyntheticBankCaseService
from app.core_v2.case_state import CaseStateError, IdempotencyConflict, RevisionConflict
from app.core_v2.contracts import CaseActor, CaseType, ReviewDecision
from app.core_v2.wp01_schema import ScopeKey
from app.core_v2.bank_reasoning import SyntheticBankReasoning
from app.core_v2.secondary_case_contracts import (
    DeterministicCheckView,
    PeriodPrerequisiteInput,
    ReconciliationReferenceInput,
    VoucherEvidenceInput,
)
from app.core_v2.secondary_case_orchestration import preview_period_close, preview_voucher_review
from app.security.auth import get_current_identity
from app.security.rls import Identity
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="/v2/accounting-cases")
_service = SyntheticBankCaseService()
_store = SqlSyntheticBankCaseStore()


class CreateCaseIn(BaseModel):
    scope: ScopeKey
    case_type: CaseType = CaseType.BANK_RECONCILIATION
    idempotency_key: str = Field(min_length=1, max_length=128)


class MutationIn(BaseModel):
    expected_revision: int = Field(ge=0)
    idempotency_key: str = Field(min_length=1, max_length=128)


class EvidenceIn(MutationIn):
    replacement_source_type: str | None = Field(
        default=None,
        pattern=(r"^(bank_statement|bravo_bank_ledger|invoice|purchase_order_or_contract|receipt_or_qc|"
                 r"bravo_draft_voucher|duplicate_registry|tax_master_policy|account_dimension_policy|"
                 r"prerequisite_policy|process_status|reconciliation_reference|approval_record)$"),
    )


class ReviewIn(MutationIn):
    decisions: tuple[ReviewDecision, ...]
    payload_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_hash: str = Field(pattern=r"^[a-f0-9]{64}$")


class ExportIn(MutationIn):
    payload_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    review_hash: str = Field(pattern=r"^[a-f0-9]{64}$")


class ConversationIn(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


class PeriodClosePreviewIn(BaseModel):
    prerequisites: tuple[PeriodPrerequisiteInput, ...]
    reconciliations: tuple[ReconciliationReferenceInput, ...]


def _actor(identity: Identity) -> tuple[CaseActor, frozenset[str]]:
    departments = frozenset(str(item) for item in identity.department_ids)
    if identity.is_admin:
        role = "admin"
    elif identity.scope_level("accounting_case", "review") == "all":
        role = "reviewer_all"
    elif identity.scope_level("accounting_case", "review") == "own_dept":
        role = "reviewer"
    elif identity.scope_level("accounting_case", "create") == "all":
        role = "preparer_all"
    else:
        role = "preparer"
    return CaseActor(user_id=str(identity.employee_id), role=role, scope_ref=",".join(sorted(departments)) or "admin"), departments


def _require_capability(identity: Identity, action: str) -> None:
    if identity.is_admin:
        return
    required_action = {"write": "create", "export": "review"}.get(action, action)
    if identity.scope_level("accounting_case", required_action) is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"Missing accounting-case capability: {action}")


def _error(exc: Exception) -> HTTPException:
    if isinstance(exc, HTTPException):
        return exc
    if isinstance(exc, CaseAccessError):
        return HTTPException(status.HTTP_403_FORBIDDEN, str(exc))
    if isinstance(exc, RevisionConflict):
        return HTTPException(status.HTTP_409_CONFLICT, str(exc))
    if isinstance(exc, IdempotencyConflict):
        return HTTPException(status.HTTP_409_CONFLICT, str(exc))
    if isinstance(exc, CaseStateError):
        return HTTPException(status.HTTP_409_CONFLICT, str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc))
    return HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Accounting case operation failed")


def _require_enabled(capability: str = "accounting_case_v2") -> None:
    settings = get_settings()
    if not settings.accounting_case_v2_enabled:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Accounting Case V2 synthetic API is disabled")
    config_path = getattr(settings, "accounting_case_v2_demo_config", "")
    if not config_path:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Accounting Case V2 synthetic API is disabled")
    try:
        config = load_synthetic_demo_config(config_path)
    except (DemoConfigError, OSError):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Accounting Case V2 synthetic API is disabled") from None
    if not config.capability_flags.get(capability, False):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Accounting Case V2 capability is disabled")


def _require_voucher_preview() -> None:
    _require_enabled("voucher_review")


def _require_period_close_preview() -> None:
    _require_enabled("period_close_readiness")


def _require_bank_reasoning() -> None:
    _require_enabled("bank_reasoning")


def _require_functional_case(case_type: CaseType) -> None:
    settings = get_settings()
    config = load_synthetic_demo_config(getattr(settings, "accounting_case_v2_demo_config", ""))
    if case_type not in config.functional_case_types:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Accounting Case V2 functional case is disabled")


@router.get("")
async def list_cases(_: None = Depends(_require_enabled), identity: Identity = Depends(get_current_identity), db: AsyncSession = Depends(get_db)) -> list[dict]:
    _require_capability(identity, "read")
    return await _store.list(db, identity)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_case(body: CreateCaseIn, _: None = Depends(_require_enabled), identity: Identity = Depends(get_current_identity), db: AsyncSession = Depends(get_db)) -> dict:
    _require_capability(identity, "create")
    actor, _ = _actor(identity)
    try:
        _require_functional_case(body.case_type)
        return await _store.create(db, identity, actor, body.scope, body.idempotency_key, body.case_type)
    except Exception as exc:
        raise _error(exc) from None


@router.post("/preview/voucher-review", response_model=list[DeterministicCheckView])
async def preview_voucher(body: VoucherEvidenceInput, _: None = Depends(_require_voucher_preview), identity: Identity = Depends(get_current_identity)) -> tuple[DeterministicCheckView, ...]:
    """Synthetic, read-only deterministic preview; never posts a voucher or touches BRAVO."""
    _require_capability(identity, "read")
    return preview_voucher_review(body)


@router.post("/preview/period-close-readiness")
async def preview_period_close_readiness(body: PeriodClosePreviewIn, _: None = Depends(_require_period_close_preview), identity: Identity = Depends(get_current_identity)) -> dict:
    """Synthetic readiness projection; never runs BRAVO close, calculation, report, or lock."""
    _require_capability(identity, "read")
    return preview_period_close(body.prerequisites, body.reconciliations).model_dump()


@router.get("/{case_id}")
async def get_case(case_id: str, _: None = Depends(_require_enabled), identity: Identity = Depends(get_current_identity), db: AsyncSession = Depends(get_db)) -> dict:
    _require_capability(identity, "read")
    try:
        return await _store.get(db, identity, case_id)
    except Exception as exc:
        raise _error(exc) from None


@router.post("/{case_id}/conversation")
async def conversation(case_id: str, body: ConversationIn, _: None = Depends(_require_bank_reasoning), identity: Identity = Depends(get_current_identity), db: AsyncSession = Depends(get_db)) -> dict:
    """Read-only explanation/clarification surface; no model or case mutation in developer mode."""
    _require_capability(identity, "read")
    try:
        return SyntheticBankReasoning().respond(await _store.get(db, identity, case_id), body.question).model_dump()
    except Exception as exc:
        raise _error(exc) from None


@router.post("/{case_id}/evidence")
async def attach_evidence(case_id: str, body: EvidenceIn, _: None = Depends(_require_enabled), identity: Identity = Depends(get_current_identity), db: AsyncSession = Depends(get_db)) -> dict:
    _require_capability(identity, "write")
    actor, departments = _actor(identity)
    try:
        if body.replacement_source_type:
            return await _store.mutate(db, identity, actor, case_id, "supersede_evidence", body.idempotency_key,
                body.model_dump(mode="json"), lambda service, _: service.supersede_evidence(case_id, actor=actor, department_ids=departments,
                expected_revision=body.expected_revision, idempotency_key=body.idempotency_key, source_type=body.replacement_source_type))
        else:
            return await _store.mutate(db, identity, actor, case_id, "attach_evidence", body.idempotency_key,
                body.model_dump(mode="json"), lambda service, _: service.attach_evidence(case_id, actor=actor, department_ids=departments,
                expected_revision=body.expected_revision, idempotency_key=body.idempotency_key))
    except Exception as exc:
        raise _error(exc) from None


@router.post("/{case_id}/run-checks")
async def run_checks(case_id: str, body: MutationIn, _: None = Depends(_require_enabled), identity: Identity = Depends(get_current_identity), db: AsyncSession = Depends(get_db)) -> dict:
    _require_capability(identity, "write")
    actor, departments = _actor(identity)
    try:
        return await _store.mutate(db, identity, actor, case_id, "run_checks", body.idempotency_key, body.model_dump(mode="json"),
            lambda service, _: service.run_checks(case_id, actor=actor, department_ids=departments, expected_revision=body.expected_revision, idempotency_key=body.idempotency_key))
    except Exception as exc:
        raise _error(exc) from None


@router.post("/{case_id}/review")
async def review(case_id: str, body: ReviewIn, _: None = Depends(_require_enabled), identity: Identity = Depends(get_current_identity), db: AsyncSession = Depends(get_db)) -> dict:
    _require_capability(identity, "review")
    actor, departments = _actor(identity)
    try:
        return await _store.mutate(db, identity, actor, case_id, "review", body.idempotency_key, body.model_dump(mode="json"), lambda service, _: service.review(case_id, actor=actor, department_ids=departments,
                               expected_revision=body.expected_revision, idempotency_key=body.idempotency_key,
                               decisions=body.decisions, payload_hash_value=body.payload_hash,
                               evidence_hash=body.evidence_hash, result_hash=body.result_hash))
    except Exception as exc:
        raise _error(exc) from None


@router.post("/{case_id}/export")
async def export(case_id: str, body: ExportIn, _: None = Depends(_require_enabled), identity: Identity = Depends(get_current_identity), db: AsyncSession = Depends(get_db)) -> dict:
    _require_capability(identity, "export")
    actor, departments = _actor(identity)
    try:
        return await _store.mutate(db, identity, actor, case_id, "export", body.idempotency_key, body.model_dump(mode="json"), lambda service, _: service.export(case_id, actor=actor, department_ids=departments,
                                         expected_revision=body.expected_revision, idempotency_key=body.idempotency_key,
                                         payload_hash_value=body.payload_hash, evidence_hash=body.evidence_hash,
                                         review_hash=body.review_hash))
    except Exception as exc:
        raise _error(exc) from None
