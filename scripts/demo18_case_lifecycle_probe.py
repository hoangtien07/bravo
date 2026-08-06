"""Redacted, local HTTP proof for the three synthetic AccountingCase lifecycles.

This intentionally emits only aggregate status.  It neither prints credentials/tokens nor raw
fixture/case data.  Run inside the API container with ``PYTHONPATH=.``.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
import uuid

from app.core_v2.bank_orchestration import SyntheticBankCaseService
from app.core_v2.contracts import CaseType, ReviewDecision
from app.core_v2.period_close_orchestration import SyntheticPeriodCloseCaseService
from app.core_v2.voucher_orchestration import SyntheticVoucherCaseService
from seed_demo import PASSWORD

BASE = "http://127.0.0.1:8000/api"


def login(email: str) -> tuple[str, str]:
    request = urllib.request.Request(
        f"{BASE}/auth/login",
        data=urllib.parse.urlencode({"username": email, "password": PASSWORD}).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = json.load(urllib.request.urlopen(request, timeout=15))["access_token"]
    identity = request_json("/me", token)
    return token, str(identity["id"])


def request_json(path: str, token: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        f"{BASE}{path}", data=data,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def status(path: str, token: str, body: dict) -> int:
    data = json.dumps(body).encode()
    request = urllib.request.Request(
        f"{BASE}{path}", data=data,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code


def key(case_type: CaseType, operation: str) -> str:
    return f"demo18-{case_type.value}-{operation}-{uuid.uuid4().hex}"


def bank_decisions(view: dict, reviewer_id: str) -> list[dict]:
    service = SyntheticBankCaseService()
    decisions: list[dict] = []
    for finding in view.get("findings", []):
        draft = ReviewDecision(
            finding_id=finding["finding_id"], disposition="investigate",
            reviewer_id=reviewer_id, reason_code="REVIEW_PENDING", decision_hash="0" * 64,
        )
        decisions.append(draft.model_copy(update={"decision_hash": service.review_decision_hash(draft)}).model_dump(mode="json"))
    return decisions


def complete(case_type: CaseType, service: object, maker_token: str, reviewer_token: str, reviewer_id: str) -> dict[str, object]:
    scope = service.evidence.scope.model_dump(mode="json")
    created = request_json("/v2/accounting-cases", maker_token, {"case_type": case_type.value, "scope": scope, "idempotency_key": key(case_type, "create")})
    case_id = created["case_id"]
    evidence = request_json(f"/v2/accounting-cases/{case_id}/evidence", maker_token, {"expected_revision": created["revision"], "idempotency_key": key(case_type, "evidence")})
    stale_status = status(f"/v2/accounting-cases/{case_id}/run-checks", maker_token, {"expected_revision": evidence["revision"] - 1, "idempotency_key": key(case_type, "stale")})
    checked = request_json(f"/v2/accounting-cases/{case_id}/run-checks", maker_token, {"expected_revision": evidence["revision"], "idempotency_key": key(case_type, "checks")})
    decisions = bank_decisions(checked, reviewer_id) if case_type is CaseType.BANK_RECONCILIATION else []
    review_body = {"expected_revision": checked["revision"], "idempotency_key": key(case_type, "review"), "decisions": decisions, "payload_hash": checked["draft_payload_hash"], "evidence_hash": checked["evidence_hash"], "result_hash": checked["result_hash"]}
    maker_review_status = status(f"/v2/accounting-cases/{case_id}/review", maker_token, review_body)
    reviewed = request_json(f"/v2/accounting-cases/{case_id}/review", reviewer_token, review_body)
    exported = request_json(f"/v2/accounting-cases/{case_id}/export", reviewer_token, {"expected_revision": reviewed["revision"], "idempotency_key": key(case_type, "export"), "payload_hash": reviewed["draft_payload_hash"], "evidence_hash": reviewed["evidence_hash"], "review_hash": reviewed["approval"]["review_hash"]})
    return {"state_after_checks": checked["state"], "state_after_export": exported["case"]["state"], "stale_rejected": stale_status == 409, "maker_review_rejected": maker_review_status == 403, "artifact_non_executing": "did not" in str(exported["artifact"].get("execution", ""))}


if __name__ == "__main__":
    maker_token, _ = login("ketoan@bravo.vn")
    reviewer_token, reviewer_id = login("ketoantruong@bravo.vn")
    print(json.dumps({
        "bank_reconciliation": complete(CaseType.BANK_RECONCILIATION, SyntheticBankCaseService(), maker_token, reviewer_token, reviewer_id),
        "voucher_evidence_review": complete(CaseType.VOUCHER_EVIDENCE_REVIEW, SyntheticVoucherCaseService(), maker_token, reviewer_token, reviewer_id),
        "period_close_readiness": complete(CaseType.PERIOD_CLOSE_READINESS, SyntheticPeriodCloseCaseService(), maker_token, reviewer_token, reviewer_id),
    }, sort_keys=True))
