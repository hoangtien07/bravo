# Markdown cleanup action manifest

Status: `VERIFIED COMPLETE — 2026-07-16 PASS`  
As of: 2026-07-16

## Applied non-destructive actions

- Added `docs/PROJECT-STATE.md` as the sole current-status entrypoint.
- Added `docs/AI-REVIEW-MANIFEST.md` with bounded read tiers and exclusions.
- Added `docs/documentation/DOCUMENTATION-POLICY.md`.
- Added repeatable Markdown inventory/link audit tooling.
- Classified research, reviews, work packages, BravoGen raw evidence, corpus, and external papers
  outside default AI context.
- Reconciled high-risk progress markers without removing historical evidence.

## Owner decision and execution

Decision received: **Option 1 — archive all three files**.

- Batch A was moved to `plan-rebuild/archive/research-inputs/`.
- Batch B was moved to `docs/archive/2026-07/`.
- No Markdown content was deleted.
- No Batch C/D file was moved or deleted.

## Findings

- No exact-content duplicate Markdown files were detected.
- Duplication is semantic: several plans/reviews describe different historical project states.
- `file_system/**` Markdown is domain data/corpus and is excluded from documentation deletion.
- Accepted ADRs and raw BravoGen evidence are retained.
- `plan-rebuild/` is currently untracked, so deletion requires explicit owner approval and a
  snapshot/commit decision.
- Two accepted ADR files share historical prefix `0027`. The ADR index now assigns aliases
  `0027a` and `0027b`; no accepted ADR was renamed in this pass.

## Batch A — generated Deep Research inputs

Files:

- `plan-rebuild/DEEP-RESEARCH-OSS-FOUNDATION-PROMPT.md`;
- `plan-rebuild/DEEP-RESEARCH-UPLOAD-PACK.md`.

Evidence: the research outcome is already synthesized into `plan-rebuild/03–07`; the prompt has
no inbound references and the upload pack has only a self/reference link.

Recommended action: archive under `plan-rebuild/archive/research-inputs/`. This preserves the
research provenance while removing generated inputs from the default AI context. Delete only if
the owner explicitly prefers it after confirming the external research session does not need to
be reproduced verbatim.

Proposed destinations:

- `plan-rebuild/archive/research-inputs/DEEP-RESEARCH-OSS-FOUNDATION-PROMPT.md`;
- `plan-rebuild/archive/research-inputs/DEEP-RESEARCH-UPLOAD-PACK.md`.

## Batch B — superseded continuation/progress snapshot

File:

- `docs/BRAVO-AI-CONTINUATION-NOTES.md`.

Evidence: zero inbound links; it records a corpus-cleanup checkpoint and commands, while current
status is now owned by `PROJECT-STATE.md`. Unique corpus facts should remain recoverable from Git.

Recommended action: archive under `docs/archive/2026-07/`, leaving no default-context reference.
Alternative: keep in place with the added superseded banner.

Proposed destination:

- `docs/archive/2026-07/BRAVO-AI-CONTINUATION-NOTES.md`.

## Batch C — legacy top-level plans and dated reviews

Files initially flagged for reconciliation include:

- `docs/PLAN.md`, `docs/ROADMAP.md`, `docs/AGENTIC-PLAN.md`;
- `docs/FIX-REUSE-PLAN.md`, `docs/MONEY-ENGINE-ROADMAP.md`;
- `docs/COUNCIL-REVIEW-2026-07.md`, `docs/COUNCIL-REVIEW-2026-07-12.md`;
- `docs/ADMIN-FLOW-PLAN.md`, `docs/AGENTIC-SPIKE-WS0.md`;
- `docs/ANOMALY-AGENT.md`, `docs/AR-COLLECTIONS-AGENT.md`, `docs/TAX-ASSISTANT-AGENT.md`;
- `docs/METRIC-CATALOG-PROPOSAL.md`.

Recommended action for this pass: keep in place as reference/evidence, exclude from default AI
context, and add superseded/historical banners only where the file can be mistaken for current
overall project state. Do not mass-archive because several have inbound links or remain valid
domain/product references.

## Batch D — historical evidence collections

Paths:

- `docs/research/**`, `docs/reviews/**`, `docs/work-packages/**`, `docs/reference/**`;
- `plan-rebuild/bravogen-p0/**`;
- `research-paper/**`.

Recommended action: retain in place and exclude from default context. Physical moves would create
large link churn without reducing AI context once the review manifest is followed.

## Not eligible for deletion

- accepted ADRs;
- security/tool/RLS/runbook documents;
- raw benchmark observations;
- `file_system/**` domain data;
- code-referenced documentation;
- current two-track decision documents;
- untracked implementation status until the worktree is snapshotted.

## Owner decisions resolved

1. Batch A: **archive selected and executed**.
2. Batch B: **archive selected and executed**.

The current worktree is intentionally not staged or committed by this cleanup. A Git snapshot is
an independent owner action and is not required for the recommended archive operation because no
content is discarded. If deletion is selected, the owner's explicit selection is the approval
required by `DOCUMENTATION-POLICY.md` for these two untracked generated files.

## Rollback

An archive operation is rolled back by moving each file to its original path and rerunning
`python scripts/audit_markdown_docs.py`. No content edits are required. A deletion operation has
no repository rollback for untracked files, which is why archive is the default recommendation.

No Batch C/D files should be deleted in this cleanup pass.

## Final verification

Executed after the owner-approved archive operation:

- `python -m py_compile scripts/audit_markdown_docs.py`: passed;
- `python scripts/audit_markdown_docs.py`: passed;
- Markdown files inventoried: 229 (including two new archive indexes);
- broken relative-link occurrences: 0;
- exact duplicate groups: 0;
- all five archive files (three preserved documents and two archive indexes) classify as
  `archived / exclude_default`;
- `git diff --check` for the documentation cleanup scope: passed;
- 30 ADR Markdown files and 31 `file_system/**` Markdown corpus files remain; none was deleted;
- branch/HEAD still match `PROJECT-STATE.md`: `research-14-7` / `50fa877` with a dirty worktree.

The worktree was not staged or committed. That is intentionally outside this cleanup operation.
