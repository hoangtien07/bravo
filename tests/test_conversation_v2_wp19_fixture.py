"""Integrity checks for the frozen, synthetic Knowledge Chat V2 anchor fixture.

This is fixture governance only.  It must not become a deterministic accounting engine or a
runtime implementation of Conversation Core V2 before the owner/SME review gate is recorded.
"""
from __future__ import annotations

from decimal import Decimal
import hashlib
import json
from pathlib import Path


_ROOT = Path(__file__).parent / "fixtures" / "conversation_v2" / "wp19"


def _load(name: str) -> dict:
    return json.loads((_ROOT / name).read_text(encoding="utf-8"))


def test_ten_transaction_anchor_is_complete_synthetic_and_engine_gated():
    fixture = _load("ten_transaction_golden.json")

    assert fixture["schema_version"] == "bravo-knowledge-chat-v2-ten-transaction/v1"
    assert fixture["synthetic_only"] is True
    assert fixture["customer_data_permitted"] is False
    assert fixture["review_status"] == "owner_accepted_pending_independent_sme_review"
    assert fixture["implementation_gate"]["deterministic_engine_allowed"] is False
    assert [item["ordinal"] for item in fixture["task_units"]] == list(range(1, 11))


def test_every_frozen_posting_group_balances_with_decimal_strings_and_lineage():
    fixture = _load("ten_transaction_golden.json")

    for unit in fixture["task_units"]:
        assert unit["deterministic_rule_ids"], unit["ordinal"]
        for posting in unit["expected_work_product"]["posting_groups"]:
            debit = sum((Decimal(line["amount_vnd"]) for line in posting["debits"]), Decimal())
            credit = sum((Decimal(line["amount_vnd"]) for line in posting["credits"]), Decimal())
            assert debit == credit, (unit["ordinal"], posting["group_id"])
            assert all(isinstance(line["amount_vnd"], str)
                       for line in [*posting["debits"], *posting["credits"]])


def test_fixture_manifest_hashes_all_reviewable_artifacts():
    manifest = _load("manifest.json")

    assert manifest["schema_version"] == "bravo-knowledge-chat-v2-wp19-fixture-manifest/v1"
    assert manifest["review_status"] == "owner_accepted_pending_independent_sme_review"
    for artifact in manifest["artifacts"]:
        digest = hashlib.sha256((_ROOT / artifact["path"]).read_bytes()).hexdigest()
        assert digest == artifact["sha256"]


def test_checksum_file_covers_the_manifest_and_frozen_inputs():
    checksums = dict(
        line.split("  ", 1)
        for line in (_ROOT / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
        if line
    )

    assert set(checksums.values()) == {
        "ten_transaction_schema.json", "ten_transaction_golden.json", "must_not_claims.md",
        "manifest.json",
    }
    for expected, name in checksums.items():
        assert hashlib.sha256((_ROOT / name).read_bytes()).hexdigest() == expected
