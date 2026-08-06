"""Server-authoritative synthetic evidence for the bounded Voucher case."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Literal

import yaml

from app.core_v2.contracts import EvidenceSnapshot
from app.core_v2.wp01_schema import ScopeKey


EvidenceKind = Literal[
    "invoice", "purchase_order_or_contract", "receipt_or_qc", "bravo_draft_voucher",
    "duplicate_registry", "tax_master_policy", "account_dimension_policy",
]
_ROOT = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "core_v2" / "wp01"


class SyntheticVoucherEvidenceSource:
    required_sources = frozenset(EvidenceKind.__args__)

    def __init__(self, root: Path = _ROOT) -> None:
        self._raw = yaml.safe_load((root / "voucher_golden.yaml").read_text(encoding="utf-8"))
        self._scope = ScopeKey.model_validate(self._raw["scope"])

    @property
    def scope(self) -> ScopeKey:
        return self._scope

    def capture(self, kind: EvidenceKind, scope: ScopeKey, *, reissued: bool = False) -> EvidenceSnapshot:
        if scope != self._scope:
            raise ValueError("synthetic voucher fixture scope does not match the locked case scope")
        payload = self._raw["evidence"][kind]
        version = "voucher-evidence-review-golden/v1.0.0" + ("-reissued" if reissued else "")
        canonical = json.dumps({"source_version": version, "kind": kind, "payload": payload},
                               ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        source_id = str(payload["source_id"])
        snapshot_id = f"{source_id}-R1" if reissued else source_id
        cutoff = datetime.combine(scope.cutoff, datetime.max.time(), tzinfo=timezone.utc)
        return EvidenceSnapshot(snapshot_id=snapshot_id, source_type=kind, source_version=version,
                                cutoff=cutoff, captured_at=cutoff,
                                content_hash=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
                                supersedes=source_id if reissued else None, complete=True, scope=scope)

    def payload(self, kind: EvidenceKind) -> dict:
        return dict(self._raw["evidence"][kind])
