# WP-01 SME review attestation — template

One completed copy is required for each reviewer. This template stores no credential, raw
customer data, model response, or hidden held-out answer.

```yaml
schema_version: bravo-accounting-case-wp01-sme-attestation/v1
attestation_id: <immutable-id>
reviewer_id: <pseudonymous-or-governed-reviewer-id>
reviewer_role: <accounting_reconciliation_sme|bravo_erp_sme>
reviewed_at: <ISO-8601 timestamp>
fixture_pack_id: bravo-accounting-intelligence-wp01/v1.0.0
public_manifest_sha256: <SHA256 of tests/fixtures/core_v2/wp01/manifest.json>
policy_sha256: <SHA256 of bank_policy.yaml>
golden_pack_sha256: <SHA256 of bank_golden.yaml>
held_out_pack_sha256: <sealed evaluator-pack SHA256, not its contents>
decision: <accepted|changes_requested>
approved_policy_version: <bank-reconciliation/v1.x.x or null>
approved_golden_truth: <true|false>
approved_held_out_truth: <true|false>
conflict_of_interest: <none|declared description>
findings: <redacted rationale and required changes>
```

Acceptance requires two `accepted` attestations, one for each required role, that name the same
policy/golden/held-out hashes. A disagreement on a hard failure is escalated to the designated
adjudicator; it never becomes an implicit approval.

Validate completed records before recording a gate receipt:

```powershell
.venv\Scripts\python.exe -c "from app.core_v2.wp01_review import validate_attestations; print(validate_attestations('tests/fixtures/core_v2/wp01/manifest.json', ['<accounting-review>.yaml', '<bravo-review>.yaml']).as_dict())"
```
