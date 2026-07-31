"""Fail-closed validation of the human WP-01 fixture-review gate.

This module validates the reviewers' attested hashes and decisions.  It does not infer SME
approval, inspect the sealed held-out answers, or change the fixture manifest.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


ATTESTATION_SCHEMA_VERSION = "bravo-accounting-case-wp01-sme-attestation/v1"
REQUIRED_ROLES = frozenset({"accounting_reconciliation_sme", "bravo_erp_sme"})
_REQUIRED_FIELDS = frozenset({
    "schema_version", "attestation_id", "reviewer_id", "reviewer_role", "reviewed_at",
    "fixture_pack_id", "public_manifest_sha256", "policy_sha256", "golden_pack_sha256",
    "held_out_pack_sha256", "decision", "approved_policy_version", "approved_golden_truth",
    "approved_held_out_truth", "conflict_of_interest", "findings",
})


class ReviewGateError(ValueError):
    """Raised when submitted review evidence is incomplete, stale, or inconsistent."""


@dataclass(frozen=True)
class ReviewGateReceipt:
    fixture_pack_id: str
    public_manifest_sha256: str
    reviewer_ids: tuple[str, ...]
    reviewer_roles: tuple[str, ...]
    approved: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "fixture_pack_id": self.fixture_pack_id,
            "public_manifest_sha256": self.public_manifest_sha256,
            "reviewer_ids": list(self.reviewer_ids),
            "reviewer_roles": list(self.reviewer_roles),
            "approved": self.approved,
            "human_only": True,
        }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_mapping(path: Path) -> dict[str, Any]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ReviewGateError(f"cannot read attestation: {path}") from exc
    if not isinstance(raw, dict):
        raise ReviewGateError(f"attestation must be a mapping: {path}")
    unknown = set(raw) - _REQUIRED_FIELDS
    missing = _REQUIRED_FIELDS - set(raw)
    if unknown or missing:
        detail = ", ".join(sorted(unknown or missing))
        raise ReviewGateError(f"attestation has invalid fields: {detail}")
    return raw


def _required_string(raw: dict[str, Any], name: str, path: Path) -> str:
    value = raw.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ReviewGateError(f"{path}: {name} is required")
    return value.strip()


def _manifest_artifact_hash(manifest: dict[str, Any], path: str) -> str:
    for artifact in manifest.get("artifacts", []):
        if isinstance(artifact, dict) and artifact.get("path") == path:
            value = artifact.get("sha256")
            if isinstance(value, str) and value:
                return value
    raise ReviewGateError(f"manifest does not hash required artifact: {path}")


def validate_attestations(manifest_path: str | Path, attestation_paths: list[str | Path]) -> ReviewGateReceipt:
    """Return an approval receipt only for two matching, accepted human attestations."""
    manifest_file = Path(manifest_path)
    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReviewGateError("public fixture manifest is unreadable") from exc
    if manifest.get("schema_version") != "bravo-accounting-case-wp01-manifest/v1":
        raise ReviewGateError("unexpected public fixture manifest schema")
    if manifest.get("review_status") not in {
        "pending_independent_sme_review", "owner_accepted_synthetic_fixture_truth",
    }:
        raise ReviewGateError("fixture manifest is not eligible for independent SME review")
    if len(attestation_paths) != len(REQUIRED_ROLES):
        raise ReviewGateError("exactly two attestations are required")

    root = manifest_file.parent
    expected_manifest_hash = _sha256(manifest_file)
    expected_policy_hash = _manifest_artifact_hash(manifest, "bank_policy.yaml")
    expected_golden_hash = _manifest_artifact_hash(manifest, "bank_golden.yaml")
    held_out_file = root / "held_out_manifest.json"
    try:
        held_out = json.loads(held_out_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReviewGateError("sealed held-out manifest is unreadable") from exc
    expected_held_out_hash = held_out.get("sealed_pack_sha256")
    if not isinstance(expected_held_out_hash, str) or len(expected_held_out_hash) != 64:
        raise ReviewGateError("sealed held-out pack hash is invalid")

    policy_path = root / "bank_policy.yaml"
    policy = yaml.safe_load(policy_path.read_text(encoding="utf-8")) or {}
    expected_policy_version = policy.get("policy_id")
    if not isinstance(expected_policy_version, str):
        raise ReviewGateError("bank policy ID is invalid")

    reviewer_ids: set[str] = set()
    reviewer_roles: set[str] = set()
    attestation_ids: set[str] = set()
    for item_path in map(Path, attestation_paths):
        raw = _load_mapping(item_path)
        if _required_string(raw, "schema_version", item_path) != ATTESTATION_SCHEMA_VERSION:
            raise ReviewGateError(f"{item_path}: unexpected schema_version")
        attestation_id = _required_string(raw, "attestation_id", item_path)
        reviewer_id = _required_string(raw, "reviewer_id", item_path)
        role = _required_string(raw, "reviewer_role", item_path)
        if attestation_id in attestation_ids or reviewer_id in reviewer_ids or role in reviewer_roles:
            raise ReviewGateError(f"{item_path}: duplicate attestation, reviewer, or role")
        attestation_ids.add(attestation_id)
        reviewer_ids.add(reviewer_id)
        reviewer_roles.add(role)
        reviewed_at = _required_string(raw, "reviewed_at", item_path)
        try:
            parsed_at = datetime.fromisoformat(reviewed_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ReviewGateError(f"{item_path}: reviewed_at must be ISO-8601") from exc
        if parsed_at.tzinfo is None:
            raise ReviewGateError(f"{item_path}: reviewed_at must include a timezone")
        expected_values = {
            "fixture_pack_id": manifest.get("fixture_pack_id"),
            "public_manifest_sha256": expected_manifest_hash,
            "policy_sha256": expected_policy_hash,
            "golden_pack_sha256": expected_golden_hash,
            "held_out_pack_sha256": expected_held_out_hash,
            "approved_policy_version": expected_policy_version,
            "decision": "accepted",
            "conflict_of_interest": "none",
        }
        for field, expected in expected_values.items():
            if raw.get(field) != expected:
                raise ReviewGateError(f"{item_path}: {field} does not match frozen evidence")
        if raw.get("approved_golden_truth") is not True or raw.get("approved_held_out_truth") is not True:
            raise ReviewGateError(f"{item_path}: golden and held-out truth must both be approved")
        _required_string(raw, "findings", item_path)
    if reviewer_roles != REQUIRED_ROLES:
        raise ReviewGateError("attestations must cover both required reviewer roles")
    return ReviewGateReceipt(
        fixture_pack_id=manifest["fixture_pack_id"],
        public_manifest_sha256=expected_manifest_hash,
        reviewer_ids=tuple(sorted(reviewer_ids)),
        reviewer_roles=tuple(sorted(reviewer_roles)),
    )
