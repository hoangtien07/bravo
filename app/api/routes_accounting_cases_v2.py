"""Authorized synthetic Bank-case API (WP-04).  Legacy routes remain unchanged."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core_v2.bank_orchestration import CaseAccessError, SyntheticBankCaseService
from app.core_v2.case_state import CaseStateError, IdempotencyConflict, RevisionConflict
from app.core_v2.contracts import CaseActor
from app.core_v2.wp01_schema import ScopeKey
from app.security.auth import get_current_identity
from app.security.rls import Identity


router = APIRouter(prefix="/v2/accounting-cases")
_service = SyntheticBankCaseService()


class CreateCaseIn(BaseModel):
    scope: ScopeKey
    idempotency_key: str = Field(min_length=1, max_length=128)


class MutationIn(BaseModel):
    expected_revision: int = Field(ge=0)
    idempotency_key: str = Field(min_length=1, max_length=128)


class ReviewIn(MutationIn):
    dispositions: dict[str, str]


def _actor(identity: Identity) -> tuple[CaseActor, frozenset[str]]:
    departments = frozenset(str(item) for item in identity.department_ids)
    if identity.is_admin:
        role = "admin"
    elif "draft:approve" in identity.permissions or "accounting_case:review" in identity.permissions:
        role = "reviewer"
    else:
        role = "preparer"
    return CaseActor(user_id=str(identity.employee_id), role=role, scope_ref=",".join(sorted(departments)) or "admin"), departments


def _require_capability(identity: Identity, action: str) -> None:
    if identity.is_admin:
        return
    accepted = {
        "create": {"accounting_case:create", "draft:create"},
        "write": {"accounting_case:create", "draft:create"},
        "review": {"accounting_case:review", "draft:approve"},
        "export": {"accounting_case:review", "draft:approve"},
    }[action]
    if not (accepted & identity.permissions):
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"Missing accounting-case capability: {action}")


def _error(exc: Exception) -> HTTPException:
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


@router.get("")
async def list_cases(identity: Identity = Depends(get_current_identity)) -> list[dict]:
    actor, departments = _actor(identity)
    return [_service.view(case) for case in _service.list_accessible(actor=actor, department_ids=departments)]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_case(body: CreateCaseIn, identity: Identity = Depends(get_current_identity)) -> dict:
    _require_capability(identity, "create")
    actor, departments = _actor(identity)
    try:
        case = _service.create(actor=actor, scope=body.scope, department_ids=departments, idempotency_key=body.idempotency_key)
        return _service.view(case)
    except Exception as exc:
        raise _error(exc) from None


@router.get("/{case_id}")
async def get_case(case_id: str, identity: Identity = Depends(get_current_identity)) -> dict:
    actor, departments = _actor(identity)
    try:
        return _service.view(_service.get(case_id, actor=actor, department_ids=departments))
    except Exception as exc:
        raise _error(exc) from None


@router.post("/{case_id}/evidence")
async def attach_evidence(case_id: str, body: MutationIn, identity: Identity = Depends(get_current_identity)) -> dict:
    _require_capability(identity, "write")
    actor, departments = _actor(identity)
    try:
        case = _service.attach_evidence(case_id, actor=actor, department_ids=departments,
                                        expected_revision=body.expected_revision, idempotency_key=body.idempotency_key)
        return _service.view(case)
    except Exception as exc:
        raise _error(exc) from None


@router.post("/{case_id}/run-checks")
async def run_checks(case_id: str, body: MutationIn, identity: Identity = Depends(get_current_identity)) -> dict:
    _require_capability(identity, "write")
    actor, departments = _actor(identity)
    try:
        case = _service.run_checks(case_id, actor=actor, department_ids=departments,
                                   expected_revision=body.expected_revision, idempotency_key=body.idempotency_key)
        return _service.view(case)
    except Exception as exc:
        raise _error(exc) from None


@router.post("/{case_id}/review")
async def review(case_id: str, body: ReviewIn, identity: Identity = Depends(get_current_identity)) -> dict:
    _require_capability(identity, "review")
    actor, departments = _actor(identity)
    try:
        case = _service.review(case_id, actor=actor, department_ids=departments,
                               expected_revision=body.expected_revision, idempotency_key=body.idempotency_key,
                               dispositions=body.dispositions)
        return _service.view(case)
    except Exception as exc:
        raise _error(exc) from None


@router.post("/{case_id}/export")
async def export(case_id: str, body: MutationIn, identity: Identity = Depends(get_current_identity)) -> dict:
    _require_capability(identity, "export")
    actor, departments = _actor(identity)
    try:
        case, artifact = _service.export(case_id, actor=actor, department_ids=departments,
                                         expected_revision=body.expected_revision, idempotency_key=body.idempotency_key)
        return {"case": _service.view(case), "artifact": artifact}
    except Exception as exc:
        raise _error(exc) from None
