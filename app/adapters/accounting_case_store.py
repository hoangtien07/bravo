"""SQL shell adapter for the synthetic WP-04 Bank case.

The domain state machine remains pure.  This adapter hydrates it under a row lock, applies one
command, then persists privacy-minimised state and an immutable idempotency/audit record in the
same database transaction.
"""
from __future__ import annotations

from typing import Any, Callable
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core_v2.bank_orchestration import SyntheticBankCaseService
from app.core_v2.voucher_orchestration import SyntheticVoucherCaseService
from app.core_v2.period_close_orchestration import SyntheticPeriodCloseCaseService
from app.core_v2.case_state import AccountingCase, IdempotencyConflict
from app.core_v2.contracts import (
    AccountingCaseId, ApprovalEnvelope, CaseActor, CaseState, CaseType, DeterministicCheckResult,
    DraftAction, EvidenceSnapshot, Finding, ReviewDecision,
)
from app.core_v2.wp01_schema import ScopeKey
from app.database.models import AccountingCaseAudit, AccountingCaseCommand, AccountingCaseRecord, AuditLog
from app.security.rls import Identity, accounting_case_scope_filter


class SqlSyntheticBankCaseStore:
    """Transactional adapter; source rows are reread only from frozen synthetic fixtures."""

    async def create(self, db: AsyncSession, identity: Identity, actor: CaseActor, scope: ScopeKey,
                     key: str, case_type: CaseType = CaseType.BANK_RECONCILIATION) -> dict[str, Any]:
        subject = f"actor:{identity.employee_id}"
        request = {"scope": scope.model_dump(mode="json"), "case_type": case_type.value}
        replay = await self._replay(db, subject, "create", key, request)
        if replay:
            return dict(replay.outcome)
        service = self._new_service(case_type)
        case = service.create(actor=actor, scope=scope, department_ids=frozenset(str(x) for x in identity.department_ids),
                              idempotency_key=key)
        record = self._record_from(service, case, identity)
        db.add(record)
        outcome = service.view(case)
        await self._record_command(db, subject, "create", key, request, case.case_id.value, identity.employee_id,
                                   list(identity.department_ids), outcome)
        await db.commit()
        return outcome

    async def get(self, db: AsyncSession, identity: Identity, case_id: str) -> dict[str, Any]:
        record = await self._scoped_record(db, identity, case_id, "read")
        return self._view_record(record)

    async def list(self, db: AsyncSession, identity: Identity) -> list[dict[str, Any]]:
        rows = (await db.execute(select(AccountingCaseRecord).where(
            accounting_case_scope_filter(identity, "read")).order_by(AccountingCaseRecord.created_at))).scalars().all()
        return [self._view_record(row) for row in rows]

    async def mutate(self, db: AsyncSession, identity: Identity, actor: CaseActor, case_id: str, operation: str,
                     key: str, request: dict[str, Any], apply: Callable[[SyntheticBankCaseService, AccountingCase], Any]) -> Any:
        record = await self._scoped_record(db, identity, case_id, self._permission_for(operation), lock=True)
        replay = await self._replay(db, case_id, operation, key, request)
        if replay:
            return dict(replay.outcome)
        service = self._service_from(record)
        case = self._case_from(record)
        result = apply(service, case)
        output_case = result[0] if isinstance(result, tuple) else result
        self._update_record(record, service, output_case)
        outcome = {"case": service.view(output_case), "artifact": result[1]} if isinstance(result, tuple) else service.view(output_case)
        await self._record_command(db, case_id, operation, key, request, output_case.case_id.value, identity.employee_id,
                                   list(record.department_ids), outcome)
        audit_detail = {
            "case_id": case_id, "revision": output_case.revision, "state": output_case.state.value,
            "request_hash": service._hash(request), "raw_evidence_retained": False,
        }
        db.add(AccountingCaseAudit(case_id=case_id, department_ids=list(record.department_ids),
                                   actor_id=identity.employee_id, action=operation, detail=audit_detail))
        db.add(AuditLog(actor_id=identity.employee_id, action=f"accounting_case.{operation}", detail=audit_detail))
        await db.commit()
        return outcome

    async def _scoped_record(self, db: AsyncSession, identity: Identity, case_id: str, action: str, *, lock: bool = False) -> AccountingCaseRecord:
        stmt = select(AccountingCaseRecord).where(AccountingCaseRecord.case_id == case_id,
                                                   accounting_case_scope_filter(identity, action))
        if lock:
            stmt = stmt.with_for_update()
        record = (await db.execute(stmt)).scalar_one_or_none()
        if record is None:
            raise PermissionError("accounting case does not exist or is outside scope")
        return record

    async def _replay(self, db: AsyncSession, subject: str, operation: str, key: str, request: dict[str, Any]) -> AccountingCaseCommand | None:
        existing = (await db.execute(select(AccountingCaseCommand).where(
            AccountingCaseCommand.subject == subject, AccountingCaseCommand.idempotency_key == key))).scalar_one_or_none()
        if existing is None:
            return None
        digest = SyntheticBankCaseService._hash(request)
        if existing.operation == operation and existing.request_hash == digest:
            return existing
        raise IdempotencyConflict("idempotency key was already used for another command or request")

    async def _record_command(self, db: AsyncSession, subject: str, operation: str, key: str,
                              request: dict[str, Any], outcome_case_id: str, actor_id: uuid.UUID,
                              department_ids: list[uuid.UUID], outcome: dict[str, Any]) -> None:
        db.add(AccountingCaseCommand(subject=subject, operation=operation, idempotency_key=key,
                                     request_hash=SyntheticBankCaseService._hash(request), outcome_case_id=outcome_case_id,
                                     department_ids=department_ids, outcome=outcome))
        db.add(AuditLog(actor_id=actor_id, action="accounting_case.command", detail={
            "subject": subject, "operation": operation, "outcome_case_id": outcome_case_id,
            "request_hash": SyntheticBankCaseService._hash(request), "raw_evidence_retained": False,
        }))
        db.add(AccountingCaseAudit(case_id=outcome_case_id, department_ids=department_ids, actor_id=actor_id,
                                   action=f"command:{operation}", detail={
            "subject": subject, "request_hash": SyntheticBankCaseService._hash(request),
            "raw_evidence_retained": False,
        }))
        await db.flush()

    @staticmethod
    def _permission_for(operation: str) -> str:
        return "review" if operation in {"review", "export"} else "create"

    @staticmethod
    def _case_from(row: AccountingCaseRecord) -> AccountingCase:
        case_type = CaseType(row.case_type)
        required_sources = {
            CaseType.BANK_RECONCILIATION: frozenset({"bank_statement", "bravo_bank_ledger"}),
            CaseType.VOUCHER_EVIDENCE_REVIEW: SyntheticVoucherCaseService().evidence.required_sources,
            CaseType.PERIOD_CLOSE_READINESS: SyntheticPeriodCloseCaseService().evidence.required_sources,
        }.get(case_type, frozenset())
        return AccountingCase(AccountingCaseId(value=row.case_id), CaseType(row.case_type), ScopeKey.model_validate(row.scope),
                              state=CaseState(row.state), revision=row.revision,
                              required_evidence_sources=required_sources,
                              evidence=tuple(EvidenceSnapshot.model_validate(item) for item in row.evidence),
                              draft_action=DraftAction.model_validate(row.draft_action) if row.draft_action else None,
                              approval=ApprovalEnvelope.model_validate(row.approval) if row.approval else None)

    @classmethod
    def _service_from(cls, row: AccountingCaseRecord) -> SyntheticBankCaseService:
        service = cls._new_service(CaseType(row.case_type))
        case = cls._case_from(row)
        service.repo.create(case)
        # Restore only typed/hashes-based runtime state; raw source rows remain in frozen adapter.
        from app.core_v2.bank_orchestration import _RuntimeCase
        service._runtime[case.case_id.value] = _RuntimeCase(str(row.owner_id), frozenset(str(x) for x in row.department_ids),
            results=tuple(DeterministicCheckResult.model_validate(item) for item in row.results),
            findings=tuple(Finding.model_validate(item) for item in row.findings),
            review_decisions=tuple(ReviewDecision.model_validate(item) for item in (row.review_dispositions or [])))
        return service

    @staticmethod
    def _new_service(case_type: CaseType) -> SyntheticBankCaseService:
        if case_type is CaseType.BANK_RECONCILIATION:
            return SyntheticBankCaseService()
        if case_type is CaseType.VOUCHER_EVIDENCE_REVIEW:
            return SyntheticVoucherCaseService()
        if case_type is CaseType.PERIOD_CLOSE_READINESS:
            return SyntheticPeriodCloseCaseService()
        raise ValueError("functional service is not available for this AccountingCase type")

    @classmethod
    def _record_from(cls, service: SyntheticBankCaseService, case: AccountingCase, identity: Identity) -> AccountingCaseRecord:
        runtime = service._runtime[case.case_id.value]
        return AccountingCaseRecord(case_id=case.case_id.value, case_type=case.case_type.value, owner_id=identity.employee_id,
            department_ids=list(identity.department_ids), scope=case.scope.model_dump(mode="json"), state=case.state.value,
            revision=case.revision, evidence=[x.model_dump(mode="json") for x in case.evidence],
            results=[x.model_dump(mode="json") for x in runtime.results], findings=[x.model_dump(mode="json") for x in runtime.findings],
            review_dispositions=[item.model_dump(mode="json") for item in runtime.review_decisions], draft_action=case.draft_action.model_dump(mode="json") if case.draft_action else None,
            approval=case.approval.model_dump(mode="json") if case.approval else None)

    @classmethod
    def _view_record(cls, row: AccountingCaseRecord) -> dict[str, Any]:
        return cls._service_from(row).view(cls._case_from(row))

    @classmethod
    def _update_record(cls, row: AccountingCaseRecord, service: SyntheticBankCaseService, case: AccountingCase) -> None:
        fresh = cls._record_from(service, case, Identity(employee_id=row.owner_id, department_ids=list(row.department_ids)))
        for field in ("case_type", "scope", "state", "revision", "evidence", "results", "findings", "review_dispositions", "draft_action", "approval"):
            setattr(row, field, getattr(fresh, field))
