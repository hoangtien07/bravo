# BRAVO Accounting Intelligence — three-case demo dev backlog

Status: `READY FOR DEV AFTER WP-00 CONTAINMENT + BASELINE FREEZE`
Owner: project owner
Prepared: 2026-07-31
Authority: ADR-0032, ADR-0033 and accepted owner packet 11
Primary case: Bank statement ↔ sổ tiền gửi BRAVO
Secondary cases: Voucher Evidence & Accounting Review; Period Close Readiness

Current-roadmap amendment (2026-08-19): this backlog remains evidence for the shared core,
deterministic case policies and three-case order. Plan 20/ADR-0035 replace optional BRAVO connector,
`DraftAction`/`ApprovalEnvelope` and ERP-directed export semantics with uploaded file evidence,
`AnalysisArtifactPlan`/`ReviewEnvelope` and governed human-readable artifacts. Plan 20 owns the
active implementation order.

## 1. Outcome

Deliver a synthetic, single-tenant BRAVO Accounting Intelligence demo with:

- separately navigable Knowledge Chat and Accounting Operations Hub;
- one Accounting Work inbox;
- one framework-independent Conversation/AccountingCase Core V2;
- three functional accounting cases sharing scope, evidence, finding, review and trace contracts;
- deterministic accounting results and bounded LLM assistance;
- blind evidence that the new conversation/case path is materially more useful than the current
  Consultant path.

This backlog is implementation authority only after WP-00 passes. It does not authorize real
customer data, production deployment, direct BRAVO database access or accounting mutation.

## 2. Locked boundaries

### BRAVO remains system of record

Do not rebuild:

- bank/cash vouchers, journal posting or ledger;
- incoming e-invoice ingestion and standard BRAVO voucher mapping;
- depreciation, allocation, costing, FX, closing entries or period lock;
- financial/tax report formulas;
- Task/Kanban/Gantt, approval engine, RBAC, audit store, scheduler or notification center.

### Deterministic services own

- scope and source completeness;
- normalization, exact financial values and every calculation;
- matching, aggregation, tolerance policy and reason codes;
- duplicate rules, dependency checks and state transitions;
- maker-checker, payload hashes, approval invalidation and idempotency;
- export schemas and audit records.

### LLM may only

- ask high-information questions for missing context;
- explain evidence and deterministic findings;
- suggest ambiguous mapping candidates with confidence and alternatives;
- group semantically similar exceptions;
- draft investigation notes, review narrative and safe next actions;
- help retrieve approved BRAVO/SOP guidance.

The LLM cannot calculate authoritative numbers, set tolerance/materiality, approve/waive, post,
pay, lock a period, file tax or execute SQL/config.

## 3. Delivery order

```text
WP-00 containment + baseline freeze
  -> WP-01 schemas, glossary, fixtures and SME truth
  -> WP-02 shared AccountingCase Core V2
  -> WP-03 Bank deterministic engine
  -> WP-04 Bank case orchestration/API/export
  -> WP-05 bounded conversation + Bank evaluation
  -> WP-06 Accounting Work frontend + Bank UX
  -> WP-07 Voucher Evidence Review
  -> WP-08 Period Close Readiness
  -> WP-09 config-as-code + Governance/Integration mock
  -> WP-10 integrated A/B/C/D, security and demo release evidence
```

WP-07 and WP-08 do not begin until WP-03/04 deterministic tests pass. They may prepare fixture
specifications in parallel, but must not introduce a second core, case state machine or evidence
model.

## 4. Shared domain model

Implement in a new clean package such as `app/core_v2/`; exact filenames may follow repository
conventions. Domain code must not import FastAPI, SQLAlchemy, Postgres clients, vector stores,
browser objects or a live model SDK.

### 4.1 Required value objects

| Contract | Minimum fields |
|---|---|
| `AccountingCaseId` | stable opaque ID |
| `CaseType` | `bank_reconciliation`, `voucher_evidence_review`, `period_close_readiness` |
| `ScopeKey` | tenant, legal entity, book/ledger, period, cutoff, currency, environment, BRAVO/config version |
| `CaseActor` | user ID, role, department/scope reference |
| `EvidenceRequest` | source type, required fields, coverage rule, allowed version |
| `EvidenceSnapshot` | snapshot ID, source/version, cutoff, captured-at, hash, `supersedes`, completeness |
| `DeterministicCheckResult` | check/rule version, typed inputs, typed result, reason code, lineage |
| `Finding` | type, severity, status, evidence/result references, reviewer disposition |
| `RecommendationDraft` | recommendation type, evidence, alternatives, confidence, assumptions |
| `DraftAction` | typed payload, target capability, source snapshot IDs, payload hash |
| `ApprovalEnvelope` | maker, checker, payload hash, policy version, approved-at, invalidation reason |
| `CaseTransition` | from/to, actor, preconditions, revision, idempotency key |
| `ReconstructableTrace` | contract/rule/model/prompt versions, source/result IDs, tool calls, decisions |
| `CapabilityManifest` | reads, draft actions, roles, limits, egress and abstention policy |

### 4.2 Case state machine

Minimum states:

```text
NEW
  -> SCOPE_LOCKED
  -> EVIDENCE_PENDING
  -> EVIDENCE_READY
  -> CHECKED
  -> NEEDS_REVIEW
  -> REVIEWED
  -> EXPORTED
  -> CLOSED
```

Terminal/side states: `ABSTAINED`, `FAILED`, `CANCELLED`, `SUPERSEDED`.

Rules:

- no check before scope lock and required evidence coverage;
- any evidence supersession returns the case to `EVIDENCE_PENDING` or `EVIDENCE_READY`;
- any payload change invalidates the previous approval;
- `EXPORTED` means an artifact was produced, never that BRAVO executed it;
- transitions require expected revision/CAS and an idempotency key;
- invalid/corrupt persisted state is explicit failure, not an empty case.

### 4.3 Ports

- `EvidenceSourcePort`
- `CaseRepositoryPort`
- `DeterministicEnginePort`
- `ReasoningPort`
- `AuthorizationPort`
- `AuditPort`
- `ArtifactExportPort`
- `ClockPort`
- optional future `BravoReadConnectorPort`
- optional future `BravoDraftConnectorPort`

Adapters remain outside domain truth. Synthetic file adapters are implemented first.

## 5. Case 1 — Bank Reconciliation

### 5.1 Scope

One case is limited to:

- one tenant and legal entity;
- one bank account;
- one book/ledger;
- one currency; first fixture pack is VND;
- one period and explicit cutoff;
- one bank-statement snapshot and one BRAVO bank-ledger snapshot;
- one approved tolerance policy version.

Cross-currency, multi-entity and live-bank connectivity are out of scope.

### 5.2 Input schemas

`BankStatementRow`:

- stable source row ID;
- account reference;
- transaction date and value date;
- amount and direction;
- currency;
- bank reference;
- description/counterparty text;
- source file/snapshot/line reference.

`BravoBankLedgerRow`:

- stable BRAVO/export row ID;
- legal entity, account and book;
- posting/document date;
- debit, credit and signed amount;
- currency;
- document/voucher/reference IDs;
- description/counterparty text;
- source export/snapshot/line reference.

Money uses decimal semantics. Timezone, date parsing and sign normalization are explicit. Rows
with invalid required fields are rejected or quarantined with a reason; they are not silently
coerced.

### 5.3 Deterministic classification

Minimum result classes:

- `EXACT_MATCH`
- `TOLERANCE_MATCH`
- `AGGREGATED_CANDIDATE`
- `DUPLICATE_CANDIDATE`
- `BANK_ONLY`
- `BRAVO_ONLY`
- `AMBIGUOUS`
- `INVALID_INPUT`

The SME-approved fixture policy defines date window, amount tolerance, aggregation constraints and
tie-breaking. The model cannot invent these values.

Each result stores:

- contributing source row IDs;
- rule and policy version;
- calculation/match features;
- result amount/difference;
- reason code;
- confidence only where ranking is probabilistic;
- evidence lineage.

### 5.4 Bounded LLM slots

After deterministic checks:

- ask for missing remittance/business context;
- explain unmatched/ambiguous results without changing classification;
- propose mapping candidates for reviewer selection;
- draft investigation note and next check;
- abstain when evidence is insufficient.

### 5.5 Output

- reconciliation summary;
- reviewed exception list;
- source-linked finding detail;
- reviewer dispositions;
- investigation narrative;
- exportable reconciliation packet;
- no journal-entry execution.

## 6. Case 2 — Voucher Evidence & Accounting Review

### 6.1 Scope

Synthetic VND evidence set:

- invoice XML/PDF-derived normalized data;
- PO or contract reference when applicable;
- receipt and QC reference when applicable;
- BRAVO draft-voucher snapshot;
- approved customer policy fixture.

The case reviews evidence around a draft. It does not ingest into BRAVO, recreate the e-invoice
connector or post a voucher.

### 6.2 Deterministic checks

- document totals and line totals;
- tax arithmetic and approved tax-code eligibility;
- duplicate source/document/reference candidates;
- PO/contract, receipt and invoice quantity/value comparison;
- vendor/customer/master reference consistency;
- account/dimension eligibility against an approved fixture;
- required evidence coverage and lineage;
- payload hash for any recommendation/export.

No legal/tax conclusion is generated without an approved effective-dated rule/policy and reviewer.

### 6.3 Bounded LLM slots

- classify unclear document text;
- ask for missing receipt/contract/business purpose;
- propose account/dimension mappings with alternatives;
- explain deterministic mismatches;
- draft a review memo.

### 6.4 Output

- evidence completeness result;
- findings and severity;
- proposed mapping/treatment alternatives;
- reviewer disposition;
- exportable review packet or typed recommendation;
- no BRAVO mutation.

## 7. Case 3 — Period Close Readiness

### 7.1 Scope

Synthetic single-entity, single-period pack:

- approved close prerequisite definition;
- status/evidence snapshots from applicable BRAVO functions;
- references to completed/open reconciliation cases;
- evidence gaps and owner/status metadata;
- report/readiness assertions.

Financial Close is a case template, not the product identity.

### 7.2 Deterministic checks

- required/applicable prerequisite coverage;
- dependency ordering;
- evidence freshness, cutoff and version;
- unresolved reconciliation/material exception references;
- maker/checker and required approval presence;
- readiness result with explicit blockers.

The case never calculates depreciation, allocation, costing, FX, closing entries or reports, and
never locks/reopens a period.

### 7.3 Bounded LLM slots

- ask which processes are applicable when scope is incomplete;
- explain blockers and evidence gaps;
- summarize completed/open prerequisites;
- draft a close-status handoff or management narrative;
- retrieve approved SOP guidance.

### 7.4 Output

- readiness summary with deterministic blocker list;
- prerequisite/evidence matrix;
- linked reconciliation exceptions;
- next-action narrative;
- review/handoff packet;
- no claim that BRAVO close was executed.

## 8. Work packages

### WP-00 — containment and immutable baseline

Tasks:

- record current clean baseline commit and Alembic head;
- rotate previously exposed provider credential without reading/copying its value;
- verify effective demo Compose: no Keycloak/OIDC, approved ingress only, non-default DB
  credentials, authenticated Redis, internal admin/observability ports;
- provision non-owner runtime roles and pass HTTP/MCP/worker isolation probes;
- run clean migration, downgrade/upgrade and security-critical DB tests without skips;
- perform isolated backup/restore;
- run frontend typecheck/test/build;
- freeze A/B outputs, traces, prompt/model/version, inputs and evidence snapshots.

Exit:

- controlled evidence artifact exists;
- every failed runtime proof is explicitly blocked;
- no prompt/routing/retrieval/synthesis change has occurred before baseline freeze.

### WP-01 — glossary, schemas, fixtures and SME truth

Tasks:

- freeze `ScopeKey`, bank and BRAVO row schemas;
- define approved match/tolerance/aggregation policy;
- create deterministic golden fixture pack with all Bank result classes;
- create critical held-out cases, including plausible false-negative traps;
- create Voucher and Period Close fixture schemas and must-not claims;
- obtain two SME reviewers and answer keys;
- version/hash all fixtures and manifests.

Tests:

- schema validation and reject/quarantine behavior;
- decimal/date/sign normalization;
- fixture manifest integrity;
- no customer or secret data;
- golden answers independently reviewed.

Exit: no engine/prompt implementation starts without frozen truth.

### WP-02 — framework-independent Core V2

Tasks:

- implement contracts in section 4;
- implement state-machine transition validation;
- implement evidence supersession and stale-approval invalidation;
- implement revision/CAS and idempotency contracts;
- define ports and in-memory test adapters;
- implement privacy-minimized reconstructable trace.

Tests:

- domain package imports no prohibited framework/runtime;
- state-transition table coverage;
- corrupt state, stale revision, duplicate idempotency and superseded evidence tests;
- payload change invalidates approval;
- scope cannot widen through model or UI input.

Exit: all domain tests run without DB, web framework, vector store or live LLM.

### WP-03 — Bank deterministic engine

Tasks:

- normalize both source schemas;
- implement exact and tolerance matching;
- implement bounded aggregation candidate generation;
- implement duplicate, unmatched and ambiguous classifications;
- produce typed result/lineage/reason codes;
- add complexity and input-size limits.

Tests:

- 100% golden monetary/match exactness;
- zero critical false negatives on held-out critical cases;
- permutation/determinism tests;
- decimal precision, duplicate and aggregation edge cases;
- malformed/oversized input fails explicitly;
- engine output is identical with LLM disabled.

Exit: deterministic gate passes before WP-05 or secondary case implementation.

### WP-04 — Bank case orchestration, API and export

Tasks:

- implement synthetic file evidence adapter;
- compose scope → snapshot → checks → findings → review transitions;
- add authorized V2 case endpoints behind the trusted shell;
- implement review dispositions and payload-bound export;
- write audit/trace references without raw-data overcollection;
- keep existing legacy API unchanged as baseline/fallback.

Tests:

- owner/role/scope authorization;
- two-user/two-department negative probes;
- retry/idempotency and concurrent revision conflict;
- evidence supersession forces recheck;
- exported artifact cannot be mistaken for ERP execution;
- fixture IDs cannot mutate live resources.

Exit: headless Bank case completes without LLM and without BRAVO API.

### WP-05 — bounded conversation and Bank evaluation

Tasks:

- implement `ReasoningPort` adapter with pinned model/version;
- define typed prompts/outputs for missing-context question, explanation, mapping candidate and
  narrative;
- apply exact-claim/evidence guard to sync/SSE outputs;
- add correction/cancel/task-switch handling;
- add Bank matched A/B/C anchors and ablations.

Tests:

- model cannot change deterministic classification/amount;
- unsupported exact claim is blocked or labelled;
- one high-information clarification when required;
- correction fidelity ≥95%;
- prerequisite/scope recall ≥90%;
- blind non-tied C-vs-B win rate ≥60%;
- no unsafe execution claim.

Exit: Bank primary case passes OD-09 quality and safety gate.

### WP-06 — Accounting Work frontend and Bank UX

Tasks:

- rebase the approved Figma visual system onto real typed contracts;
- add top-level Chat and `Công việc AI` modes;
- build Accounting Work inbox states;
- build reusable case page tabs;
- implement Bank summary/findings/evidence/recommendation/review/export views;
- label live, synthetic, inferred, missing, stale and superseded data;
- remove Financial Close as navigation/product root.

Tests:

- no UI-only authorization;
- synthetic/live boundary and fixture-ID rejection;
- keyboard, screen-reader, 200% zoom and responsive matrix;
- loading/empty/error/abstained/stale/superseded states;
- no recommendation appears as executed.

Exit: Bank case is usable end-to-end through the candidate frontend.

### WP-07 — Voucher Evidence & Accounting Review

Tasks:

- implement Voucher fixture adapters and deterministic checks;
- reuse shared case/evidence/review contracts;
- implement bounded mapping/explanation slots;
- add case-specific UI;
- export review packet.

Tests:

- totals/tax/duplicate/3-way checks match golden truth;
- missing evidence fails or abstains explicitly;
- no voucher posting or parallel ledger path exists;
- account/dimension suggestions are reviewable candidates;
- exact claim lineage and payload-bound review.

Exit: functional bounded case passes its deterministic/safety tests without new core abstraction.

### WP-08 — Period Close Readiness

Tasks:

- implement prerequisite/dependency policy as approved data/config;
- read synthetic status/evidence and reconciliation references;
- compute deterministic readiness/blockers;
- implement bounded missing-context/explanation/narrative slots;
- add case-specific UI and handoff export.

Tests:

- readiness cannot pass with a required blocker;
- non-applicable prerequisites require explicit policy/scope;
- stale/missing evidence prevents unsupported readiness;
- no close calculation, report formula or period lock implementation;
- no claim that BRAVO executed close.

Exit: functional bounded case passes its deterministic/safety tests and keeps Financial Close as
a template rather than product root.

### WP-09 — config-as-code and Governance/Integration mock

Tasks:

- define one demo tenant, roles and capability flags;
- version source packs and model/egress policy;
- define audit export;
- write BA specs for customer identity, connector coverage, egress, retention, support and
  update/rollback;
- implement explicitly non-functional Governance & Integration FE mock.

Tests:

- configuration schema validation and fail-closed boot;
- capability flags cannot widen authorization;
- mock makes no live-control or production claim;
- no billing, marketplace, model-management or agent-builder backend.

Exit: demo configuration is reproducible without a premature governance platform.

### WP-10 — integrated evaluation and release evidence

Tasks:

- run full backend/frontend/security suite;
- run A/B/C/D and blind SME evaluation;
- measure manual reviewer baseline and OD-09 time/edit metrics;
- run model/retrieval/planner/critic/state ablations;
- produce evidence index and release-gate result;
- document failure clusters and rollback.

Exit:

- OD-09 gates pass for Bank;
- secondary cases pass their exactness/safety/evidence gates;
- no production/pilot claim is made from synthetic evidence;
- paid pilot remains blocked until OD-10 evidence exists.

## 9. API and UI target

Provisional routes; freeze exact API grammar in WP-02/04 contract review:

```text
GET  /api/v2/accounting-cases
POST /api/v2/accounting-cases
GET  /api/v2/accounting-cases/{case_id}
POST /api/v2/accounting-cases/{case_id}/evidence
POST /api/v2/accounting-cases/{case_id}/run-checks
POST /api/v2/accounting-cases/{case_id}/review
POST /api/v2/accounting-cases/{case_id}/export
POST /api/v2/accounting-cases/{case_id}/conversation
```

Every mutating request carries expected revision and idempotency key. Review/export carries the
exact payload/evidence hash. Backend authorization remains authoritative.

Frontend routes:

```text
/                         Knowledge Chat
/work                     Accounting Work inbox
/work/new/:caseType       Start case from enabled template
/work/cases/:caseId       Typed case page
/admin/governance-preview Non-functional authorized preview
```

Do not expose `/financial-close` as the product root.

## 10. Acceptance matrix

| Gate | Bank | Voucher | Period Close | Shared platform |
|---|---|---|---|---|
| Golden deterministic exactness | 100% | 100% applicable checks | 100% prerequisite/readiness checks | N/A |
| Critical false negatives | 0 | 0 | 0 readiness blockers missed | N/A |
| Exact-claim lineage | Required | Required | Required | Required |
| Cross-scope leakage | 0 | 0 | 0 | 0 across HTTP/MCP/worker |
| Unsafe mutation/approval bypass | 0 | 0 | 0 | 0 |
| LLM disabled path | Full deterministic result | Full deterministic checks | Full deterministic readiness | Core/state works |
| Correction fidelity | ≥95% | ≥95% | ≥95% | Shared |
| Prerequisite/scope recall | ≥90% | ≥90% | ≥90% | Shared |
| Functional UI | Required | Required | Required | Inbox/case shell required |
| Reviewer time/edit target | Primary OD-09 measurement | Observational until baseline | Observational until baseline | Report separately |

The 30% reviewer-time improvement and 80% no-material-edit targets are release gates for the
primary Bank case once a frozen manual baseline exists. Secondary case metrics are collected but
do not block Bank architecture evaluation unless they expose a safety regression.

## 11. Required artifacts

- controlled baseline/run manifest;
- effective Compose evidence without secret values;
- migration/RLS/backup-restore proof;
- frozen A/B outputs and traces;
- three fixture/schema manifests;
- Bank golden and held-out SME truth sets;
- case-specific must-not claims;
- contract and transition tables;
- deterministic engine test reports;
- blind SME packets and results;
- ablation/root-cause report;
- frontend accessibility/visual/contract evidence;
- release-gate result and rollback instructions.

## 12. Stop conditions

Stop implementation or narrow scope if:

- WP-00 cannot produce real runtime evidence;
- source truth or SME answer key is not available;
- deterministic matching/checks cannot be independently tested;
- the LLM is required to calculate, set policy or own workflow state;
- a secondary case requires duplicating BRAVO functionality;
- direct DB/arbitrary SQL becomes necessary;
- critical false negatives, scope leakage or unsafe action cannot be driven to zero;
- frontend work begins inventing APIs from mock screens;
- adding cases causes a second core/state/evidence implementation.

## 13. Handoff rule

The first dev task is WP-00, not prompt tuning or case UI. After WP-00 passes, freeze WP-01 truth
before implementing WP-02/03. Every work package handoff records:

- baseline commit and worktree state;
- inputs/outputs and changed contracts;
- tests run and skipped;
- evidence artifact paths;
- remaining blockers;
- whether the next dependency gate is actually open.
