# WP-01 — glossary, schemas, fixtures and SME truth status

Status: `OWNER-ACCEPTED — WP-02/03 DEVELOPMENT GATE OPEN`
Recorded: 2026-07-31
Baseline commit observed: `aeb72641f26df53e2e2483fa3183f18c13439526` (`complete wp00`)
Alembic head observed: `0017_native_rls_backstop`

## Delivered preparation

- Frozen, framework-independent schema validation for `ScopeKey`, Bank statement rows and BRAVO
  bank-ledger rows at `app/core_v2/wp01_schema.py`.
- Synthetic VND golden pack covering every locked Bank result class and invalid-row quarantine.
  The four critical false-negative traps are now sealed outside the implementation worktree; only
  their count and sealed SHA-256 remain in the public manifest.
- Versioned deterministic policy proposal, glossary, Voucher/Period Close fixture schemas and
  hard must-not claims in `tests/fixtures/core_v2/wp01/`.
- Fixture manifest plus `SHA256SUMS`; the test suite verifies every declared artifact hash and
  the manifest checksum.
- Fail-closed attestation validator: two distinct SME roles must accept the same frozen hashes,
  with timezone-aware timestamps and no declared conflict, before it emits a human-only receipt.

## Evidence

- Fixture manifest: `tests/fixtures/core_v2/wp01/manifest.json`
- Checksums: `tests/fixtures/core_v2/wp01/SHA256SUMS`
- Reviewer template: `evidence/v2/WP-01-SME-REVIEW-ATTESTATION-TEMPLATE.md`
- Verification: `.venv\\Scripts\\python.exe -m pytest -q -p no:cacheprovider tests/test_core_v2_wp01_schema.py tests/test_core_v2_wp01_review.py`
  — `14 passed` (2026-07-31)
- Static check: `.venv\\Scripts\\python.exe -m ruff check app/core_v2/wp01_schema.py app/core_v2/wp01_review.py tests/test_core_v2_wp01_schema.py tests/test_core_v2_wp01_review.py`
  — passed (2026-07-31)

## Owner acceptance and remaining evidence limit

The project owner accepted the frozen synthetic policy, golden truth and development gate on
2026-07-31. `manifest.json` now opens WP-02/03. This is an owner acceptance for synthetic
development, not a claim that two independent SMEs reviewed the evidence or that an external
quality gate has passed. The evaluator-held-out payload must not return to this worktree or
implementation CI logs.

## Worktree note

The user committed WP-00 while initial WP-01 schema/test files were already present in the shared
worktree. Commit `aeb7264` consequently includes those two files. Because the branch has no
configured upstream, this work does not rewrite the commit; a follow-up hygiene commit should
remove the tracked pytest temporary artifact and add the directory to `.gitignore`.

## Next dependency gate

Begin WP-02. Retain independent SME attestations for the later blind-evaluation/release evidence;
they are no longer a prerequisite to the synthetic Core V2 implementation.
