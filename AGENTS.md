# BRAVO V2 workspace instructions

This repository is preparing a clean Conversation Core V2 because the current conversation path
does not produce sufficiently useful results. Do not continue broad feature patching in the legacy
agent loop.

## Required read order

1. `docs/PROJECT-STATE.md`
2. `docs/AI-REVIEW-MANIFEST.md`
3. `plan-rebuild/10-FRONTIER-BRAVO-ACCOUNTING-AGENT-PLAN.md`
4. `plan-rebuild/11-OWNER-DECISION-PACKET-RECONCILIATION-DEMO.md`
5. `docs/adr/0032-first-v2-demonstrator-reconciliation-exception.md`
6. `docs/adr/0033-three-case-demo-and-owner-package.md`
7. `plan-rebuild/12-THREE-CASE-DEMO-DEV-BACKLOG.md`
8. `plan-rebuild/08-V2-CONVERSATION-REBUILD-HANDOFF.md`
9. `plan-rebuild/04-WORKSPACE-REPO-COUNCIL-DECISION.md`
10. `plan-rebuild/07-CONVERSATION-INTELLIGENCE-BRAVOGEN-BENCHMARK.md`

Treat code, current tests, migrations, and runtime evidence as stronger than historical progress
claims. Historical council/research documents are evidence inputs, not current truth.

## Current objective

- Build a framework-independent Conversation and AccountingCase Core V2 behind the existing
  trusted platform shell.
- Target a standalone BRAVO Accounting Intelligence product with separately governed Knowledge
  Chat and Accounting Operations Hub modules.
- Treat Financial Close as one benchmark family and optional case template, not the product
  objective.
- ADR-0032 selects Reconciliation & Exception Investigator as the first deep V2 demonstrator.
  Its first subtype is Bank statement ↔ sổ tiền gửi BRAVO. Freeze the scope/schema, deterministic
  policy, golden fixtures and SME answer key before implementation. ADR-0032 alone does not infer
  a paid pilot, production topology or real-data policy.
- ADR-0033 adds two functional/bounded cases after Bank Reconciliation: Voucher Evidence &
  Accounting Review, then Period Close Readiness. Reuse the shared core; do not rebuild BRAVO
  voucher posting, closing calculations, reports or period lock. ADR-0033 selects target pilot
  guardrails, not production-readiness evidence or customer-data permission.
- Demonstrate a materially better outcome through frozen A/B/C/D evidence and blind SME review.
- Keep Engineering Workbench independent from the conversation-quality verdict.

## Before implementation

- Confirm the worktree is clean and record the baseline commit and Alembic head.
- Complete the security/correctness containment gates in the V2 handoff plan.
- Freeze System A/B outputs before changing prompts, routing, retrieval, or synthesis.
- Never print, copy, commit, or infer values from `.env` or other secret stores.

## Non-negotiable invariants

- Authorization/RLS is enforced outside the model and must have a database backstop.
- Exact financial, schema, version, and execution claims require matching evidence.
- Mutations remain draft/approval gated; generated SQL/config is never executed automatically.
- The product retains a verified offline-capable path with controlled cloud egress.
- Preserve unrelated user changes and do not edit reference repositories outside this workspace.
