# WP-04 Bank orchestration — new-chat development prompt

Copy the prompt below into a new Codex chat in `D:\VsCode\Workspace\bravo-v2`.

```text
Continue BRAVO Accounting Intelligence from WP-04 (Bank case orchestration, authorized API and
payload-bound export). Do not restart or redesign WP-00–03.

Read in this exact order:
1. docs/PROJECT-STATE.md
2. docs/AI-REVIEW-MANIFEST.md
3. plan-rebuild/10-FRONTIER-BRAVO-ACCOUNTING-AGENT-PLAN.md
4. plan-rebuild/11-OWNER-DECISION-PACKET-RECONCILIATION-DEMO.md
5. docs/adr/0032-first-v2-demonstrator-reconciliation-exception.md
6. docs/adr/0033-three-case-demo-and-owner-package.md
7. plan-rebuild/12-THREE-CASE-DEMO-DEV-BACKLOG.md
8. plan-rebuild/13-WP-04-BANK-ORCHESTRATION-HANDOFF-PROMPT.md
9. plan-rebuild/08-V2-CONVERSATION-REBUILD-HANDOFF.md
10. plan-rebuild/04-WORKSPACE-REPO-COUNCIL-DECISION.md
11. plan-rebuild/07-CONVERSATION-INTELLIGENCE-BRAVOGEN-BENCHMARK.md

Baseline: branch codex/v2-financial-close-core; commit
33421684541663e199d397d2f7db12388ccb170a; Alembic head 0017_native_rls_backstop. Confirm a clean
worktree before edits. Do not read or print .env/secret values.

Completed evidence:
- WP-00 PASS: frozen 30-case A/B artifact at evidence/v2/ab/wp00-20260731/.
- WP-01 owner-accepted synthetic fixture truth:
  tests/fixtures/core_v2/wp01/ and evidence/v2/WP-01-OWNER-ACCEPTANCE.md.
- WP-02 Core V2: app/core_v2/contracts.py and app/core_v2/case_state.py; status at
  evidence/v2/WP-02-CORE-STATUS.md.
- WP-03 deterministic Bank engine: app/core_v2/bank_engine.py; status at
  evidence/v2/WP-03-BANK-ENGINE-STATUS.md. The sealed held-out result is owner-attested external
  evidence, not a payload to copy into the worktree.
- Focused verification before WP-04: 24 passed; Ruff passed.

Implement WP-04 only:
1. Add a synthetic file EvidenceSource adapter outside app/core_v2 domain truth.
2. Compose scope -> evidence snapshot -> deterministic checks -> findings -> review transitions.
3. Add the provisional authorized V2 Bank-case endpoints behind the trusted platform shell:
   GET/POST /api/v2/accounting-cases, GET case, and evidence/run-checks/review/export mutations.
4. Every mutation must enforce backend authorization, expected revision and idempotency key.
   Scope may never widen through UI/request/model input.
5. Export must bind the exact payload/evidence hash and state “artifact produced; BRAVO did not
   execute anything.” Keep legacy APIs unchanged.
6. Store privacy-minimized audit/trace references only. No raw evidence overcollection.

Required tests: owner/role/scope authorization; two-user/two-department negative probes;
retry/idempotency and revision conflict; evidence supersession requires recheck; export cannot be
mistaken for ERP execution; fixture IDs cannot mutate a live resource; headless case completes
without LLM or BRAVO API.

Hard boundaries: synthetic data only; no direct BRAVO DB or arbitrary SQL; no autonomous posting,
payment, period lock, approval bypass, or LLM-authoritative number/policy/classification. Domain
code remains framework/database/model-runtime free. Do not start WP-05, frontend, Voucher or
Period Close work.

Run focused tests and Ruff, record a WP-04 evidence status document, preserve unrelated changes,
and commit only scoped files. Report tests, evidence paths, remaining limits and the next gate.
```
