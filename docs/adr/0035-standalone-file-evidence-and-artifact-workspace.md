# 0035. FigmaMake-only standalone product, file evidence and bounded Artifact Workspace

- **Status:** **Accepted** (2026-08-19) — owner directed Plan 20 consolidation and dev readiness.
- **Date:** 2026-08-19
- **Decision owner:** Project owner.
- **Authority:**
  [Plan 20](../../plan-rebuild/20-FIGMAMAKE-STANDALONE-ACCOUNTING-INTELLIGENCE-COMPLETION-PLAN.md)
  and the owner request to align Office work with frontier enterprise-agent patterns while making
  only high-impact changes.
- **Amends:** ADR-0033 for the current product integration roadmap and ADR-0034 for residual
  draft/write vocabulary.
- **Preserves:** ADR-0032/0033 three-case order and deterministic boundaries; ADR-0034 Conversation
  V2 contract boundary; RLS/database backstop, exact-claim evidence, offline path, audit and
  non-destructive retention invariants.

## Context

Plan 19 freezes a useful Conversation V2 intelligence kernel, and WP19-00 has frozen a matched
synthetic A/B baseline. It does not prove a quality win or complete Core V2. Plan 20 changes the
shipped product boundary: the product receives user-supplied files/evidence and performs analysis,
review and reporting without connecting to or mutating BRAVO.

Current code has not yet reached that boundary. It still builds `frontend-react`, registers
connector/invoice/draft routes and exposes journal-draft/export tools. The decision therefore needs
a containment backlog and negative evidence, not only revised product copy.

The Office proposal also needs a narrower decision. Enterprise productivity platforms show useful
patterns — permission-scoped sources, editable native files, plan/preview, human control,
version/audit and centrally governed brand templates — but no repository claim establishes that a
particular Office engine preserves BRAVO templates, formulas, masters or print/layout fidelity.

## Decision

1. `FigmaMake_UI` is the sole production frontend target. `frontend-react` remains a rollback asset
   until parity/retention evidence allows archival or deletion.
2. BRAVO Accounting Intelligence is a standalone file-in/evidence-in analysis and review product.
   BRAVO is an external system of record, not a connected runtime dependency.
3. The current product has no BRAVO API/DB/browser connector, ERP write tool, journal import output,
   posting, closing, lock or master-data mutation. Reaching those capabilities later requires a new
   owner ADR; ADR-0033's API-first read-only pilot target is no longer an authorized current-roadmap
   implementation item.
4. Plan 19 remains the authority for lossless task decomposition, evidence planning,
   deterministic read-only work products, claims, verification, rendering and evaluation.
   `draft proposal`, `draft action` and write-tool terms in active V2 work are interpreted as
   read-only analysis proposals, review requests and artifact plans.
5. Bank Reconciliation remains the first deep vertical slice. Voucher Evidence Review follows as a
   functional bounded slice; Period Close Readiness remains last. Transaction Analysis is a
   mandatory Knowledge Chat quality anchor, not a separately validated product flagship.
6. Office capability is delivered as a bounded **Artifact Workspace** after a verified analysis
   result. V1 generates or template-safely edits only product-generated artifacts and explicitly
   approved templates. It is not a separate Office Agent and does not accept arbitrary Office-file
   editing.
7. Artifact semantic truth is immutable across rendering. A provider-neutral `ArtifactEnginePort`
   receives a branded spec bound to verified result/evidence hashes; structural, semantic-diff,
   visual/native compatibility and policy validation run before release.
8. Office engine selection is format-specific and benchmark-first. OfficeCLI, Open XML SDK,
   ONLYOFFICE and commercial engines are candidates with different roles; none is selected by this
   ADR. The relevant sanitized fidelity corpus and licensing/offline/support gate must pass before a
   format ships.
9. Removing reachability does not authorize destructive deletion. Historical draft/journal rows,
   user artifacts and the legacy frontend are retained read-only until a separately reviewed
   retention/rollback decision.

## Consequences

### Positive

- Plan 19 and Plan 20 now form one dependency chain instead of two competing architectures.
- The product cannot imply that analysis changed BRAVO.
- Office output becomes a natural, governed last mile for accounting work while accounting truth
  remains outside the renderer/model.
- Bank provides an end-to-end proof of import, evidence, deterministic checks, findings, review,
  audit and governed XLSX output before additional breadth.

### Cost and limits

- FigmaMake cutover and legacy API/tool containment precede feature expansion.
- Independent SME truth remains required before the Plan 19 accounting engine starts.
- Each Office format needs representative templates, native compatibility checks and operational
  ownership; one engine may not satisfy all formats.
- Removing the connector path may defer a future design-partner integration. That trade-off is
  intentional until a new ADR supplies buyer, data, security and support evidence.

## Not decided

- final commercial packaging, buyer or flagship capability;
- an Office engine or embedded browser editor;
- arbitrary Office-file editing;
- customer-data authority or a production/on-prem topology claim;
- a future BRAVO read connector or write-back;
- deletion of historical data or legacy frontend code.

## Implementation gate

Commit this ADR and Plan 20, record a clean baseline and Alembic source head, freeze the
keep/rename/remove/defer inventory and retention disposition, then execute WP20-01/02 with negative
tests. The accepted decision does not convert the current runtime into compliant evidence.
