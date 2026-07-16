# BRAVO AI Copilot — current project state

Status: `IN_PROGRESS — documentation cleanup verified; architecture review preparation`  
Owner: project owner  
As of: 2026-07-16  
Verified against Git: branch `research-14-7`, HEAD `50fa877`, dirty worktree

## Executive state

The repository contains an existing BRAVO platform plus uncommitted Consultant Intelligence
work. The current direction is **not** a full platform rewrite and is **not** approval to keep
patching the legacy loop indefinitely.

Two independently evaluated strangler tracks are proposed:

1. **Conversation Intelligence Core v2** — improve outcome understanding, prerequisite reasoning,
   evidence planning, synthesis, and multi-turn correction; benchmark separately against BravoGen.
2. **Engineering Workbench** — process technical requirements into canonical cases, isolated
   diffs, validators, build/test evidence, and developer handover.

The tracks may share BRAVO identity/RLS, environment, evidence, artifacts, approval, and trace
services. A passing engineering artifact does not prove conversational quality, and a helpful
answer does not prove a technical change is correct.

## Evidence-backed milestones

| Item | Current state | Evidence strength |
|---|---|---|
| Markdown documentation cleanup | Verified complete for the 2026-07-16 pass | Generated inventory: 0 broken relative links, 0 exact duplicates; owner-approved archive batch executed |
| BravoGen R0 black-box collection | Research complete | Strong for observed behavior; no claim about hidden implementation |
| Current platform services | Existing code for API, RLS, retrieval, tools, drafts, approval, audit, and checkpoints | Code exists; this cleanup did not re-run full tests |
| Consultant Intelligence additions | Large uncommitted implementation/eval slice exists | Implementation snapshot; production quality and TMS gates remain open |
| Conversation Core v2 | Proposed design; clean matched-model benchmark not executed | Decision pending |
| Engineering Workbench | Proposed contract; headless runner/IDE adapter not implemented | Decision pending |
| Production rollout | Not approved | SME, data, canary, SLO, and ownership gates remain open |

## Verification limitations at this snapshot

- The worktree contains modified and untracked source, migrations, tests, documentation, and
  `plan-rebuild/`; a clean baseline has not been committed.
- Docker Desktop/daemon was unavailable during the 2026-07-16 documentation audit.
- The host Python installation has no `pytest` package; Consultant tests were not re-run during
  this cleanup.
- Claims in historical implementation/review documents are evidence snapshots, not automatically
  revalidated current facts.

## Current decisions and contracts

- Current rebuild boundary and repository council: `plan-rebuild/04-WORKSPACE-REPO-COUNCIL-DECISION.md`.
- Engineering pipeline contract: `plan-rebuild/05-BRAVO-ENGINEERING-WORKBENCH-CONTRACT.md`.
- Two-track execution sequence: `plan-rebuild/06-RESEARCH-AND-IMPLEMENTATION-ROUNDS.md`.
- Conversation architecture and BravoGen benchmark: `plan-rebuild/07-CONVERSATION-INTELLIGENCE-BRAVOGEN-BENCHMARK.md`.
- OSS runtime prototype choice: `plan-rebuild/03-OSS-CORE-DECISION-PYDANTIC-LANGGRAPH-ZENML-KITARU.md`.

These documents are proposed decision inputs. Accepted ADRs remain authoritative for existing
platform invariants until explicitly superseded.

## Invariants retained during the decision

- RLS/authorization remains outside the model/runtime framework.
- Exact financial calculations remain deterministic.
- Writes remain draft/approval gated; no generated SQL/config is executed automatically.
- BravoGen is a behavioral comparator, not an oracle or knowledge-promotion source.
- One online orchestration owner and one business-state owner are preferred until evidence
  justifies additional infrastructure.

## Immediate sequence

1. Review the dirty codebase using `AI-REVIEW-MANIFEST.md` and the two-track contracts before
   changing more features.
2. Establish an immutable A/B conversational baseline and evidence fixtures.
3. Run the contract-to-code feasibility spike before an IDE extension or repository migration.

## Not current truth by default

The following are retained as evidence/reference and must not override this file without fresh
verification:

- `docs/research/**`, `docs/reviews/**`, and `docs/work-packages/**`;
- `docs/research/frontier-conversation-architecture-v2/**`;
- `plan-rebuild/bravogen-p0/**` raw/derived research;
- legacy top-level plans and dated council reviews;
- corpus/data Markdown under `file_system/**`;
- Deep Research prompt/upload derivatives;
- `docs/archive/**` and `plan-rebuild/archive/**`.
