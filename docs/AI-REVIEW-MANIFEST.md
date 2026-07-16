# AI review manifest

Status: `ACTIVE — review entrypoint`  
Last verified: 2026-07-16

## Purpose

Provide a small, ordered context set for reviewing the current project without loading historical
research, raw conversations, or obsolete progress as current truth.

## Required read order

### Tier 0 — always read

1. `docs/PROJECT-STATE.md` — current state, verification limits, and precedence.
2. `CLAUDE.md` — existing product/security invariants (applies as project context even when the
   reviewing tool is not Claude).
3. `README.md` — current repository surface and local run orientation.

### Tier 1 — architecture decision review

4. `plan-rebuild/04-WORKSPACE-REPO-COUNCIL-DECISION.md`.
5. `plan-rebuild/07-CONVERSATION-INTELLIGENCE-BRAVOGEN-BENCHMARK.md`.
6. `plan-rebuild/05-BRAVO-ENGINEERING-WORKBENCH-CONTRACT.md`.
7. `plan-rebuild/06-RESEARCH-AND-IMPLEMENTATION-ROUNDS.md`.
8. `plan-rebuild/02-R1-DECISION-BENCHMARK-PLAN.md`.

### Tier 2 — open only for a specific claim

- `docs/adr/README.md` and the relevant accepted ADR;
- `docs/ARCHITECTURE.md` for the legacy/current platform shape, checking its stale-status warning;
- `docs/SECURITY-RLS.md`, `docs/SECURITY-AGENT-DB-ROLE.md`, and `docs/TOOL-INVENTORY.md`;
- `docs/CONSULTANT-INTELLIGENCE-IMPLEMENTATION.md` for the uncommitted implementation snapshot;
- code, migrations, tests, configuration, and generated runtime evidence.

## Excluded from default context

Do not preload:

- `docs/research/**`;
- `docs/reviews/**`;
- `docs/work-packages/**`;
- `docs/reference/**`;
- `plan-rebuild/bravogen-p0/**`;
- `file_system/**` Markdown data/corpus;
- `research-paper/**`;
- generated Deep Research prompt/upload packs;
- `docs/archive/**` and `plan-rebuild/archive/**`;
- archived or superseded plans.

Open an excluded file only to verify a named claim. Summarize the minimum evidence and return to
the canonical document; do not recursively load an evidence tree.

## Conflict rules

1. Reproducible code/test/runtime evidence overrides prose implementation claims.
2. `PROJECT-STATE.md` owns the current snapshot.
3. Accepted ADRs own existing architectural invariants.
4. `plan-rebuild/04–07` own the current proposed two-track decision design.
5. Historical research and council reports do not become current merely because they are detailed.
6. A structural/synthetic green test does not prove conversational task quality.

## Review questions

The next project review should answer:

1. Which current platform modules are safe, cohesive assets to retain behind ports?
2. Where does the legacy/Consultant path collapse typed workflow state back into prompt-only
   guidance or free-text synthesis?
3. Can Conversation Core v2 be isolated without duplicating auth, state, retrieval, or approval?
4. Can the Engineering Workbench run headlessly and fail closed before any IDE/browser adapter?
5. Which existing tests prove the required behavior, and which only prove structure?
6. What must be fixed before freezing the matched A/B baseline?

## Required review output

- findings ordered by severity with exact code/evidence locations;
- a retain/wrap/replace/remove map;
- contradictions between code, tests, ADRs, and current plans;
- missing verification explicitly labelled, not inferred as pass;
- the smallest next experiment that resolves the architecture decision.
