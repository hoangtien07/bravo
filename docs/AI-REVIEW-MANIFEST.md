# AI review manifest

Status: `ACTIVE — review entrypoint`  
Last consolidated: 2026-08-19 (runtime evidence dates remain explicit per source)

## Purpose

Provide a small, ordered context set for reviewing the current project without loading historical
research, raw conversations, or obsolete progress as current truth.

## Required read order

### Tier 0 — always read

1. `docs/PROJECT-STATE.md` — current verified state, gates, and precedence.
2. `CLAUDE.md` — existing product/security invariants (applies as project context even when the
   reviewing tool is not Claude).
3. `README.md` — current repository surface and local run orientation.

### Tier 1 — architecture decision review

4. `plan-rebuild/10-FRONTIER-BRAVO-ACCOUNTING-AGENT-PLAN.md` — current product target,
   non-duplication boundary, capability portfolio and owner decision gates.
5. `plan-rebuild/11-OWNER-DECISION-PACKET-RECONCILIATION-DEMO.md` — accepted OD-01..OD-10
   package, including the owner amendment to three functional cases.
6. `docs/adr/0032-first-v2-demonstrator-reconciliation-exception.md` — accepted first
   demonstrator decision and its explicit non-decisions.
7. `docs/adr/0033-three-case-demo-and-owner-package.md` — accepted three-case scope and
   demo-to-pilot guardrails.
8. `plan-rebuild/12-THREE-CASE-DEMO-DEV-BACKLOG.md` — implementation dependency order,
   contracts, schemas, work packages and acceptance tests.
9. `plan-rebuild/13-WP-04-BANK-ORCHESTRATION-HANDOFF-PROMPT.md` — current clean baseline,
   completed WP-01–03 evidence and the exact WP-04 handoff boundary.
10. `plan-rebuild/08-V2-CONVERSATION-REBUILD-HANDOFF.md` — current execution boundary.
11. `plan-rebuild/04-WORKSPACE-REPO-COUNCIL-DECISION.md`.
12. `plan-rebuild/07-CONVERSATION-INTELLIGENCE-BRAVOGEN-BENCHMARK.md`.
13. `plan-rebuild/02-R1-DECISION-BENCHMARK-PLAN.md`.
14. `plan-rebuild/05-BRAVO-ENGINEERING-WORKBENCH-CONTRACT.md` and
   `plan-rebuild/06-RESEARCH-AND-IMPLEMENTATION-ROUNDS.md` only when the independent track or
   shared contract is in scope.
15. `plan-rebuild/15-V2-EXTERNAL-GATE-EXECUTION-PACKET.md` when assessing completion, runtime
    cutover, model/evaluation, SME or user-baseline evidence.
16. `evidence/v2/V2-BRAVO10-BUSINESS-FLOW-COUNCIL-DECISION-2026-08-02.md` and
    `plan-rebuild/16-BRAVO10-BUSINESS-FLOW-REMEDIATION-PLAN.md` before assessing backend business
    adequacy, secondary-case functionality, FigmaMake admission or local-demo readiness.
17. `evidence/v2/V2-BRAVO10-FE-ADMISSION-REVIEW-PACKET-2026-08-02.md`,
    `evidence/v2/V2-BRAVO10-FE-ADMISSION-COUNCIL-DECISION-2026-08-02.md` and
    `plan-rebuild/17-FIGMAMAKE-UI-THREE-CASE-FE-IMPLEMENTATION-PLAN.md` before implementing or
    reviewing the admitted FigmaMake three-case frontend.
18. `plan-rebuild/18-FIGMAMAKE-UI-INTERNAL-DEMO-COMPLETION-PLAN.md` before changing normal
    FigmaMake routes, live Knowledge Chat, the final two-module shell, demo identities or the
    Plan 17 local-demo handoff claim.
19. `plan-rebuild/19-KNOWLEDGE-CHAT-V2-QUALITY-REMEDIATION-PLAN.md` and
    `docs/adr/0034-conversation-v2-contract-boundary.md` before implementing Conversation V2,
    Transaction Analysis, retrieval/routing/synthesis changes or judging the WP19 baseline.
20. `plan-rebuild/20-FIGMAMAKE-STANDALONE-ACCOUNTING-INTELLIGENCE-COMPLETION-PLAN.md` and
    `docs/adr/0035-standalone-file-evidence-and-artifact-workspace.md` before changing the shipped
    frontend, product route/API/tool inventory, file evidence path, ERP-connectivity boundary or
    Artifact Workspace.

### Tier 2 — open only for a specific claim

- `docs/adr/README.md` and the relevant accepted ADR;
- `docs/ARCHITECTURE.md` for the legacy/current platform shape, checking its stale-status warning;
- `docs/SECURITY-RLS.md`, `docs/SECURITY-AGENT-DB-ROLE.md`, and `docs/TOOL-INVENTORY.md`;
- `docs/CONSULTANT-INTELLIGENCE-IMPLEMENTATION.md` for the legacy/Consultant implementation
  snapshot; it is not evidence that the clean Core V2 is built;
- `docs/SECURITY-DB-BACKSTOP.md` and `docs/RLS-RECOVERY-PREFLIGHT.md` for native-RLS and recovery
  operator actions;
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
4. `plan-rebuild/04–12` own the product/decision design and original dev backlog; Plan 16 owns the
   backend business-flow remediation/FE admission gate, Plan 17 owns the admitted FigmaMake
   three-case frontend execution, and Plan 18 owns completion of the two-module local internal-demo
   shell, including live Knowledge Chat and the Plan 17 handoff exit.
   ADR-0032 now selects Reconciliation & Exception Investigator as the first deep V2 demonstrator
   and supersedes the earlier AP/Close demonstrator conflict. ADR-0033 accepts the three-case
   scope and target pilot guardrails. Plan 12 owns implementation sequencing. Target architecture
   is not runtime/production evidence.
   Plan 19/ADR-0034 own the new Conversation V2 intelligence contracts. Plan 20/ADR-0035 own the
   current shipped-product boundary: FigmaMake-only, user-supplied file evidence, no live BRAVO
   connector/mutation, and a bounded benchmark-first Artifact Workspace. They amend residual
   draft/write and pilot-connector semantics for the current roadmap without rewriting historical
   ADR evidence.
5. Historical research and council reports do not become current merely because they are detailed.
6. A structural/synthetic green test does not prove conversational task quality.

## Plan 18 local-demo status

Plan 18 is `TECHNICAL DEMO-COMPLETE — READY FOR OWNER EVALUATION` as recorded in
[`DEMO18-FINAL-PACKET-2026-08-03.md`](../evidence/v2/DEMO18-FINAL-PACKET-2026-08-03.md). This only
closes the local synthetic UI handoff: it does not close blind SME review, A/B/C/D conversation
quality, customer-data authority, pilot, recovery/deployment or production gates.

## Plan 19/20 dev-handoff status

WP19-00 has a frozen synthetic 30-pair A/B baseline, and the owner accepted the synthetic
ten-transaction fixture plus ADR-0034. This does not prove System B quality, Core V2 quality or SME
truth; independent accounting/BRAVO SME review remains open. Plan 20/ADR-0035 are ready for dev
handoff only in the sense that the product boundary, dependency order and first slice are explicit.
Current code still ships legacy surfaces, so implementation must begin with WP20-00 inventory,
FigmaMake cutover and reversible API/tool containment rather than feature expansion or an Office
engine choice.

## Review questions

The next project review should answer:

1. Which current platform modules are safe, cohesive assets to retain behind ports?
2. Where does the legacy/Consultant path collapse typed workflow state back into prompt-only
   guidance or free-text synthesis?
3. Can Conversation Core v2 be isolated without duplicating auth, state, retrieval, or approval?
4. Can the Engineering Workbench run headlessly and fail closed before any IDE/browser adapter?
5. Which existing tests prove the required behavior, and which only prove structure?
6. Which containment gates are code-tested only, and which have real runtime evidence?
7. What must be fixed before freezing the matched A/B baseline?
8. Does a proposed `Công việc AI` capability complement BRAVO 10, or duplicate an existing
   transaction, calculation, approval, task, reporting or system function?
9. Which user, buyer, liability, data contract and success metric support the first Accounting
   Work capability, independently of Knowledge Chat?
10. Can any positive accounting verdict be produced from caller-asserted status, completeness,
    policy, lineage or materiality rather than a server-resolved immutable evidence snapshot?

## Required review output

- findings ordered by severity with exact code/evidence locations;
- a retain/wrap/replace/remove map;
- contradictions between code, tests, ADRs, and current plans;
- missing verification explicitly labelled, not inferred as pass;
- the smallest next experiment that resolves the architecture decision.
