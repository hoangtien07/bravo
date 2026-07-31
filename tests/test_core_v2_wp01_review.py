import hashlib
import json
from pathlib import Path

import pytest
import yaml

from app.core_v2.wp01_review import ReviewGateError, validate_attestations


_ROOT = Path(__file__).parent / "fixtures" / "core_v2" / "wp01"


def _attestation(role: str, reviewer: str, *, policy_hash: str | None = None) -> dict:
    manifest = json.loads((_ROOT / "manifest.json").read_text(encoding="utf-8"))
    artifact_hashes = {item["path"]: item["sha256"] for item in manifest["artifacts"]}
    held_out = json.loads((_ROOT / "held_out_manifest.json").read_text(encoding="utf-8"))
    policy = yaml.safe_load((_ROOT / "bank_policy.yaml").read_text(encoding="utf-8"))
    return {
        "schema_version": "bravo-accounting-case-wp01-sme-attestation/v1",
        "attestation_id": f"attestation-{role}",
        "reviewer_id": reviewer,
        "reviewer_role": role,
        "reviewed_at": "2026-07-31T09:00:00+07:00",
        "fixture_pack_id": manifest["fixture_pack_id"],
        "public_manifest_sha256": hashlib.sha256((_ROOT / "manifest.json").read_bytes()).hexdigest(),
        "policy_sha256": policy_hash or artifact_hashes["bank_policy.yaml"],
        "golden_pack_sha256": artifact_hashes["bank_golden.yaml"],
        "held_out_pack_sha256": held_out["sealed_pack_sha256"],
        "decision": "accepted",
        "approved_policy_version": policy["policy_id"],
        "approved_golden_truth": True,
        "approved_held_out_truth": True,
        "conflict_of_interest": "none",
        "findings": "Synthetic policy and frozen hashes reviewed.",
    }


def _write(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_two_matching_required_role_attestations_open_the_gate(tmp_path):
    accounting = tmp_path / "accounting.yaml"
    bravo = tmp_path / "bravo.yaml"
    _write(accounting, _attestation("accounting_reconciliation_sme", "acct-sme"))
    _write(bravo, _attestation("bravo_erp_sme", "bravo-sme"))

    receipt = validate_attestations(_ROOT / "manifest.json", [accounting, bravo])

    assert receipt.approved is True
    assert receipt.reviewer_roles == ("accounting_reconciliation_sme", "bravo_erp_sme")
    assert receipt.as_dict()["human_only"] is True


def test_stale_or_duplicate_reviews_fail_closed(tmp_path):
    first = tmp_path / "first.yaml"
    second = tmp_path / "second.yaml"
    _write(first, _attestation("accounting_reconciliation_sme", "same-reviewer", policy_hash="stale"))
    _write(second, _attestation("bravo_erp_sme", "same-reviewer"))

    with pytest.raises(ReviewGateError, match="does not match frozen evidence"):
        validate_attestations(_ROOT / "manifest.json", [first, second])


def test_review_requires_both_roles_and_timezone_aware_timestamp(tmp_path):
    first = tmp_path / "first.yaml"
    second = tmp_path / "second.yaml"
    _write(first, _attestation("accounting_reconciliation_sme", "acct-sme"))
    invalid = _attestation("bravo_erp_sme", "bravo-sme")
    invalid["reviewed_at"] = "2026-07-31T09:00:00"
    _write(second, invalid)

    with pytest.raises(ReviewGateError, match="timezone"):
        validate_attestations(_ROOT / "manifest.json", [first, second])
