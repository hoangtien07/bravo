"""Synthetic-file evidence adapter for the WP-04 Bank demonstrator.

This adapter deliberately lives outside the Core V2 domain contracts.  It only accepts the
frozen fixture identifiers and never treats an arbitrary path or a BRAVO resource identifier as
an input.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from typing import Literal

import yaml

from app.core_v2.bank_engine import BankReconciliationEngine, BankReconciliationPolicy
from app.core_v2.contracts import EvidenceSnapshot
from app.core_v2.wp01_schema import BankStatementRow, BravoBankLedgerRow, ScopeKey, validate_rows


EvidenceKind = Literal["bank_statement", "bravo_bank_ledger"]
_ROOT = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "core_v2" / "wp01"


class SyntheticBankEvidenceSource:
    """Loads only the owner-accepted WP-01 fixture pack for the synthetic demo."""

    def __init__(self, root: Path = _ROOT) -> None:
        self._raw = yaml.safe_load((root / "bank_golden.yaml").read_text(encoding="utf-8"))
        self._policy = yaml.safe_load((root / "bank_policy.yaml").read_text(encoding="utf-8"))
        self._scope = ScopeKey.model_validate(self._raw["scope"])

    @property
    def scope(self) -> ScopeKey:
        return self._scope

    def capture(self, kind: EvidenceKind, scope: ScopeKey, *, reissued: bool = False) -> EvidenceSnapshot:
        if scope != self._scope:
            raise ValueError("synthetic fixture scope does not match the locked case scope")
        rows = self._rows(kind)
        source_version = "bank-reconciliation-golden/v1.0.0-reissued" if reissued else "bank-reconciliation-golden/v1.0.0"
        canonical = json.dumps({"source_version": source_version, "rows": rows}, ensure_ascii=False,
                               sort_keys=True, separators=(",", ":"))
        base_id = "BANK-SNAPSHOT-001" if kind == "bank_statement" else "BRAVO-SNAPSHOT-001"
        snapshot_id = f"{base_id}-R1" if reissued else base_id
        cutoff = datetime.combine(scope.cutoff, datetime.max.time(), tzinfo=timezone.utc)
        return EvidenceSnapshot(
            snapshot_id=snapshot_id,
            source_type=kind,
            source_version=source_version,
            cutoff=cutoff,
            captured_at=cutoff,
            content_hash=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            supersedes=base_id if reissued else None,
            complete=True,
            scope=scope,
        )

    def bank_rows(self) -> tuple[BankStatementRow, ...]:
        batch = validate_rows(BankStatementRow, self._raw["bank_statement_rows"])
        if batch.quarantined:
            raise ValueError("frozen bank fixture unexpectedly contains invalid runnable rows")
        return batch.valid

    def ledger_rows(self) -> tuple[BravoBankLedgerRow, ...]:
        batch = validate_rows(BravoBankLedgerRow, self._raw["bravo_bank_ledger_rows"])
        if batch.quarantined:
            raise ValueError("frozen BRAVO fixture unexpectedly contains invalid runnable rows")
        return batch.valid

    def engine(self) -> BankReconciliationEngine:
        matching = self._policy["matching"]
        limits = self._policy["scope"]
        return BankReconciliationEngine(BankReconciliationPolicy(
            policy_id=self._policy["policy_id"],
            maximum_statement_rows=limits["maximum_statement_rows"],
            maximum_ledger_rows=limits["maximum_ledger_rows"],
            tolerance_amount_vnd=Decimal(matching["tolerance"]["amount_difference_vnd"]),
            tolerance_date_window_days=matching["tolerance"]["date_window_days"],
            aggregation_maximum_rows=matching["aggregation"]["maximum_contributing_ledger_rows"],
            aggregation_amount_difference_vnd=Decimal(matching["aggregation"]["amount_difference_vnd"]),
            aggregation_date_window_days=matching["aggregation"]["date_window_days"],
        ))

    def _rows(self, kind: EvidenceKind) -> list[dict]:
        return self._raw["bank_statement_rows"] if kind == "bank_statement" else self._raw["bravo_bank_ledger_rows"]
