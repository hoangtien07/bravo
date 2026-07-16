# BRAVO V2 workspace instructions

This repository is preparing a clean Conversation Core V2 because the current conversation path
does not produce sufficiently useful results. Do not continue broad feature patching in the legacy
agent loop.

## Required read order

1. `docs/PROJECT-STATE.md`
2. `docs/AI-REVIEW-MANIFEST.md`
3. `plan-rebuild/08-V2-CONVERSATION-REBUILD-HANDOFF.md`
4. `plan-rebuild/04-WORKSPACE-REPO-COUNCIL-DECISION.md`
5. `plan-rebuild/07-CONVERSATION-INTELLIGENCE-BRAVOGEN-BENCHMARK.md`

Treat code, current tests, migrations, and runtime evidence as stronger than historical progress
claims. Historical council/research documents are evidence inputs, not current truth.

## Current objective

- Build a framework-independent Conversation Core V2 behind the existing trusted platform shell.
- Start with the Financial Close Advisor vertical slice.
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
