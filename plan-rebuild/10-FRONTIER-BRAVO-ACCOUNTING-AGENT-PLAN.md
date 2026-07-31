# Frontier BRAVO Accounting Agent — product and execution plan

Status: `READY FOR DEV AFTER CONTAINMENT + BASELINE FREEZE — three-case scope accepted`
Owner: project owner
Last verified: 2026-07-31
Supersedes in product scope: Financial Close as the identity or final objective of `Công việc AI`
ADR authority: ADR-0032 selects the primary case; ADR-0033 accepts the three-case owner package

## 1. Decision summary

The target is a standalone product provisionally named **BRAVO Accounting Intelligence**, not a
Financial Close product and not a second ERP.

It has two separately governed product modules in one shell:

1. **Knowledge Chat** — BRAVO helpdesk, self-service and operating guidance.
2. **Accounting Operations Hub (`Công việc AI`)** — controlled accounting cases that assemble
   evidence, run deterministic checks, investigate exceptions and prepare reviewable actions.

They may share identity, source registry, evidence rendering and audit infrastructure, but they
must not be forced into one buyer, contract, entitlement, liability model or success score.
`PKG-A` remains a commercial hypothesis until customer discovery and a paid design-partner pilot
validate it.

The primary business object of `Công việc AI` is an `AccountingCase`, not a chat thread, bot
persona, generic task or BRAVO transaction. Financial Close becomes one optional case template
under periodic accounting. It remains useful as benchmark coverage, but benchmark coverage does
not decide product scope.

Owner decision 2026-07-31: **Reconciliation & Exception Investigator** is the first deep V2
demonstrator. [ADR-0032](../docs/adr/0032-first-v2-demonstrator-reconciliation-exception.md)
records the decision and supersedes the earlier AP/Close demonstrator conflict without selecting a
paid pilot.

The owner subsequently confirmed OD-01 through OD-10 and amended OD-08 to add two functional
cases. [ADR-0033](../docs/adr/0033-three-case-demo-and-owner-package.md) locks the three-case demo,
pilot target architecture and release/promotion guardrails.

## 2. Corrections to the previous direction

| Previous assumption | Corrected position |
|---|---|
| Financial Close Advisor is the first and final product objective | It is one candidate workflow pack and benchmark family |
| One `PKG-A` add-on covers Chat and Agent Work | Treat it only as a packaging hypothesis; validate the two businesses separately |
| A standalone application is inherently safer | It creates a controllable boundary; safety still requires identity, authorization, egress, connector, recovery and audit proof |
| API integration is automatically safe | Use API-first with coverage audit and supported, versioned export fallback |
| An immutable `EvidenceBundle` is permanent truth | Use immutable-in-place, versioned `EvidenceSnapshot`s that may be superseded |
| Trace means deterministic replay | Promise a reconstructable, inspectable trace; external systems and models prevent perfect replay |
| Approval UI is sufficient control | Bind approval to the exact payload and enforce maker-checker, policy and invalidation outside the model |
| AI critic is an independent reviewer | It is a supplemental quality check, never an accounting or authorization control |
| Keycloak-free Compose is production-like | It is synthetic single-tenant demo topology only; it makes no production identity claim |
| Governance Console should be built early | Demo uses configuration-as-code; Console stops at BA specification and FE mock |

## 3. Evidence basis

### 3.1 BRAVO 10 capabilities reviewed

The council reviewed the BRAVO 10 corpus manifest, AI use-case catalogue, connector catalogue,
consultant cards, lifecycle playbooks, all relevant mindmaps, and visually inspected the
Accounting, System and Task user-guide PDFs.

BRAVO 10 already owns:

- accounting vouchers, posting logic, taxes, offsets and document states;
- cash/bank and e-banking, AP/AR, inventory, assets, cost allocation and costing;
- depreciation, FX, COGS, closing entries, period lock, financial and tax reports;
- purchase, sale, inventory, production, QC and HR workflows;
- multi-level approval, digital signing, audit logs, RBAC, locks, backup and scheduling;
- personal/project task management, WBS, recurring work, Kanban, Gantt and reporting;
- operational dashboards and standard financial analysis.

Sources:

- [Accounting mindmap](../file_system/Mindmaps/Mindmap_Accounting.md)
- [Documents mindmap](../file_system/Mindmaps/Mindmap_Documents.md)
- [Management mindmap](../file_system/Mindmaps/Mindmap_Managements.md)
- [System mindmap](../file_system/Mindmaps/Mindmap_System.md)
- [Task mindmap](../file_system/Mindmaps/Mindmap_Task.md)
- [Purchase mindmap](../file_system/Mindmaps/Mindmap_Purchase.md)
- [BRAVO AI use cases](../file_system/bravo_ai_use_cases.yaml)
- [BRAVO connector catalogue](../file_system/bravo_connectors.yaml)

Therefore `Công việc AI` must not rebuild BRAVO forms, ledgers, calculations, close engine,
approval engine, task manager, report formulas, scheduler, authorization or audit store.

### 3.2 Frontier product signals

These are design signals, not proof of product accuracy or market success:

- Microsoft Account Reconciliation separates scheduled deterministic reconciliation and
  exceptions from AI-generated analysis and suggested action; users confirm settings and can
  review or undo an addressed exception.
- Microsoft Finance Reconciliation uses structured tables, templates and mapping keys; AI assists
  mapping and explains unmatched or potentially matched results.
- Microsoft Business Central Expense and Payables agents create drafts for human review rather
  than posting permanent financial changes.
- QuickBooks Accounting AI asks for missing context, makes accounting suggestions and groups
  high-confidence work for review.
- Other frontier vendors present bounded finance agents by job, not a single unrestricted
  super-agent.

Primary references:

- [Microsoft Account Reconciliation](https://learn.microsoft.com/en-us/dynamics365/finance/general-ledger/account-reconciliation)
- [Microsoft Account Reconciliation Agent](https://learn.microsoft.com/en-us/dynamics365/finance/general-ledger/acct-rec-agent)
- [Microsoft Financial Reconciliation](https://learn.microsoft.com/en-us/copilot/finance/reconcile/reconcile-data)
- [Microsoft Expense Agent safety](https://learn.microsoft.com/en-us/dynamics365/business-central/expense-management/faqs-expense-agent)
- [Microsoft Payables Agent](https://learn.microsoft.com/en-us/dynamics365/business-central/faqs-payables-agent)
- [QuickBooks Intuit AI overview](https://quickbooks.intuit.com/learn-support/en-us/help-article/accounting-bookkeeping/overview-agents-quickbooks-online/L9irCAtK4_US_en_US)

## 4. Product structure

```text
BRAVO Accounting Intelligence (independent product shell)
|
|-- Knowledge Chat
|   |-- BRAVO operating guidance
|   |-- cited SOP/manual answers
|   |-- troubleshooting and self-service
|   `-- handoff to support or a governed accounting case
|
|-- Accounting Operations Hub ("Công việc AI")
|   |-- My Accounting Work
|   |-- bounded job templates
|   |-- AccountingCase workspace
|   |-- evidence, findings, recommendations and draft actions
|   `-- review, approval handoff and reconstructable trace
|
`-- Minimal shared platform
    |-- identity and entitlement
    |-- source/evidence registry
    |-- capability flags
    |-- model/egress policy
    `-- audit export
```

This is one application shell with two distinct operating modes, not necessarily two deployments
or codebases. Separate navigation and entitlement are justified because Chat optimizes answer
quality while Accounting Work carries workflow state, sensitive data, control liability and
review obligations.

## 5. Product and buyer separation

| Dimension | Knowledge Chat | Accounting Operations Hub |
|---|---|---|
| Primary users | BRAVO end users, key users, helpdesk, implementation/support staff | Accountants, reviewers, chief accountants, controllers, internal control, CFO |
| Economic buyer hypothesis | ERP owner, IT/support or implementation leadership | Chief accountant, controller, CFO, shared-services or internal-control leader |
| Job | Find a correct BRAVO answer and next step | Resolve a governed accounting case with evidence and review |
| Data | Manuals, approved SOP and limited user context | Transactions, ledgers, reports, documents, policies and external source evidence |
| Liability | Incorrect operational guidance | Missed material exception, wrong treatment, privacy breach or unauthorized action |
| Success | Cited correctness, self-service rate, resolution time, escalation quality | Exactness, exception recall/precision, review time, no-edit acceptance, cycle time, zero unsafe action |
| Support model | Corpus/version/content operations | Connector, accounting policy, rule, mapping, evidence and control operations |
| Commercial hypothesis | Bundled/site/seat or support-value component | Separately purchased capability packs plus implementation/support |

No billing implementation or final SKU decision is authorized by this plan.

## 6. `AccountingCase` domain contract

Every `Công việc AI` capability uses the same governed lifecycle:

```text
Trigger / request
    -> ScopeLock
    -> VersionedEvidenceSnapshot
    -> DeterministicChecks
    -> Findings and Exceptions
    -> Recommendation / DraftAction
    -> Human Review
    -> approved export or supported API draft
    -> ReconstructableTrace
```

Minimum contracts:

| Contract | Required content |
|---|---|
| `AccountingCase` | case type, state, owner, eligible reviewers, risk, timestamps |
| `ScopeKey` | tenant, legal entity, book/ledger, basis, period/cutoff, currency, BRAVO/config version |
| `EvidenceRequest` | required sources, fields, lineage and completeness rule |
| `EvidenceSnapshot` | snapshot ID, source versions/cutoff, captured-at, hash, supersedes, missing/conflicting facts |
| `DeterministicCheckResult` | rule/engine version, inputs, calculation/match result, tolerance policy, lineage |
| `Finding` / `Exception` | severity, reason code, evidence links, status and reviewer disposition |
| `RecommendationDraft` | bounded recommendation, alternatives, confidence, unsupported assumptions |
| `DraftAction` | exact typed payload for export or supported downstream draft API |
| `ApprovalEnvelope` | payload hash, maker, checker, policy version, approval time, invalidation rule |
| `StateTransition` | allowed from/to state, actor, preconditions, idempotency key |
| `ReconstructableTrace` | source/snapshot IDs, rule/model/prompt versions, tool calls, outputs and decisions |
| `CapabilityManifest` | allowed reads, draft actions, roles, sources, limits and abstention conditions |

Snapshots are not overwritten. A newer snapshot can supersede an older one; any changed payload or
source snapshot invalidates the previous approval.

## 7. Deterministic, hybrid and LLM boundaries

### 7.1 Deterministic services own

- scope, authorization, RLS and source coverage;
- debit/credit equality and every exact financial calculation;
- reconciliation matching, aggregation, tolerance and materiality policy;
- duplicate rules, aging, completeness and cutoff logic;
- workflow state, queue, due date and SLA;
- approval policy, maker-checker, payload hash and idempotency;
- API allowlists, query bounds, action bounds and audit persistence;
- report, export and accounting artifact templates.

### 7.2 Hybrid services with deterministic verification

- fuzzy entity resolution and candidate matching;
- anomaly and duplicate candidate ranking;
- semantic account, dimension or mapping suggestions;
- document classification and extraction where rules cannot resolve ambiguity.

Every hybrid output is a candidate with confidence, alternatives and evidence. It does not become
a ledger fact until deterministic validation and the required human review pass.

### 7.3 LLM may

- ask high-information questions for missing context;
- retrieve and explain approved BRAVO guidance or customer SOP;
- explain evidence and deterministic findings in user language;
- classify genuinely ambiguous exceptions;
- propose mappings or accounting-treatment options with evidence and uncertainty;
- draft investigation notes, management narrative and communications.

### 7.4 LLM must never

- set materiality or tolerance policy;
- calculate or silently alter authoritative financial numbers;
- approve, waive or override an exception;
- post a journal, issue an invoice, initiate payment or change master data;
- close, lock or reopen a period;
- file tax or assert an audit opinion;
- execute arbitrary SQL, query or configuration;
- act with a blanket ERP credential.

## 8. Accounting capability portfolio

Capability priority remains provisional until section 14 is decided.

### P1 — candidates for the first demonstrator and commercial validation

#### A. Reconciliation & Exception Investigator — council recommendation

- Jobs: bank-to-cashbook, AP/AR-to-GL, inventory-to-GL, asset-to-GL, WIP/cost-to-GL and
  report-to-report.
- Deterministic core: normalization, matching, aggregation, tolerance, completeness, cutoff,
  reason codes and lineage.
- LLM role: suggest ambiguous mapping keys, ask for missing business context, explain unmatched
  items and draft the investigation pack.
- Output: versioned reconciliation result, ranked exception cases and a reviewed next action.
- Why it complements BRAVO: it joins BRAVO with approved external/source-system evidence and
  investigates differences; it does not replace posting or close.

#### B. Voucher Evidence & Accounting Review

- Inputs: BRAVO draft voucher, invoice/XML/PDF, PO, receipt, QC record, contract and policy.
- Deterministic core: totals, tax, duplicate, 3/4-way match, account/dimension eligibility and
  lineage.
- LLM role: resolve document ambiguity, propose mapping alternatives and explain review findings.
- Output: evidence-linked review packet or draft recommendation only.
- Boundary: do not recreate BRAVO voucher entry, incoming e-invoice mapping or ledger.

#### C. Management Variance Investigator

- Inputs: approved BRAVO reports, budgets, dimensions and source lineage.
- Deterministic core: variance, driver tree and drill-down calculations.
- LLM role: explain verified drivers, ask contextual questions and draft management commentary.
- Output: evidence-linked analysis; no new report formula or unverified causal claim.

### P2 — after read-only integration and evidence contracts are proven

#### D. Continuous Controls & Audit Evidence

Monitor configured assertions, find missing evidence, assemble samples and prepare PBC/control-test
packets. It must not claim that AI performed an audit or that absence of a finding proves control
effectiveness.

#### E. AR Collection Preparation

Use deterministic aging and approved prioritization policy; summarize account history and draft
communications. A human selects the recipient and sends the message. The agent cannot promise,
waive, settle or change credit terms.

#### F. Accounting Policy & Mapping Assistant

Gather facts, retrieve approved internal policy/SOP and propose account/dimension or treatment
options. Current tax/legal conclusions require authoritative current sources and qualified review.

#### G. Period Close & Periodic Accounting

Coordinate evidence, dependencies, reconciliation cases and handoff across a period. BRAVO still
calculates depreciation, cost, FX, closing entries, reports and locks. `Financial Close Readiness`
is one template in this capability, not the product identity.

### P3 — only after trust, data and integration maturity

- AP anomaly/duplicate/fraud-candidate triage;
- cost, margin, inventory and production variance investigation;
- treasury and working-capital scenarios;
- tax/IFRS/statutory disclosure and audit packs;
- cross-entity and consolidation support;
- contract-obligation, accrual and deferral assistance.

Explicitly excluded for this phase: autonomous posting/payment/close/tax filing, generic task
management, agent marketplace, general agent builder, unrestricted planner and free-form SQL.

## 9. UX and information architecture

### 9.1 Top-level navigation

```text
Chat
  Conversations
  Knowledge sources

Công việc AI
  My Accounting Work
  Start a job
  Reviews
  Completed cases

Administration (authorized only)
  Demo configuration summary
  Audit export
  Governance & Integration preview
```

`Chat` and `Công việc AI` are distinct modes because the latter has durable typed state and
control obligations. A case may contain a side chat, but conversation is not the state machine.

### 9.2 My Accounting Work

Use an accounting inbox, not a replacement Kanban/Gantt:

- Needs my attention;
- Waiting for evidence;
- Waiting for review;
- Monitoring;
- Completed.

If a BRAVO Task is needed, create a reviewed task draft through a supported API/export. Do not
duplicate BRAVO's project/task module.

### 9.3 Case page

Required tabs:

1. Scope
2. Findings
3. Evidence and lineage
4. Recommendations
5. Draft actions
6. Review and audit

Each exact claim links to its deterministic result or evidence snapshot. The UI labels live,
synthetic, inferred, missing, superseded and stale data. It never implies execution from a
recommendation.

### 9.4 Job templates, not Agent Marketplace

Templates are a curated product navigation and configuration concept. They are not user-authored
agents, a skill DSL or a marketplace. Each template must satisfy the capability contract in
section 6 before appearing as enabled.

## 10. Demo scope

### 10.1 Demo purpose

The demo proves that the new product can produce materially better, evidence-backed conversations
and one controlled accounting outcome. It does not prove a production deployment, commercial
packaging or all accounting capabilities.

### 10.2 Recommended demonstrator shape

- one independent BRAVO Accounting Intelligence shell;
- two modes: Knowledge Chat and `Công việc AI`;
- one shared Accounting Work inbox;
- three synthetic, functional case templates:
  Bank Reconciliation, Voucher Evidence & Accounting Review and Period Close Readiness;
- Bank Reconciliation is the primary/deep case; the two added cases are bounded and sequential,
  but must be functional rather than visual previews;
- Knowledge Chat and the selected Accounting Work case evaluated separately;
- no Keycloak/OIDC, real customer data, autonomous mutation or production claim.

Reconciliation & Exception Investigator is the owner-selected deep demonstrator because it has the
clearest deterministic/LLM split, a measurable outcome and strong frontier precedent. The exact
subtype is **Bank statement ↔ sổ tiền gửi BRAVO**. First paid pilot, production topology and
real-data policy remain separate decisions.

### 10.3 Minimal runtime configuration

Configuration-as-code only:

- one synthetic demo tenant;
- demo roles and capability flags;
- source pack and version;
- model and egress policy;
- audit export policy;
- enabled job templates.

Do not build Agent Catalog, billing UI, marketplace, model-management platform or general
Governance Console.

### 10.4 Governance & Integration Console

For this phase:

- complete BA requirements, data-flow and permission specifications;
- produce an FE mock with explicit non-functional labels;
- do not connect it to production control APIs;
- do not claim multi-tenant administration or customer deployment readiness.

## 11. Integration and deployment boundaries

### 11.1 Integration contract

Use **API-first with coverage audit and supported-export fallback**:

1. inventory required objects, fields, lineage and actions for the selected capability;
2. verify which BRAVO API contracts exist and their supported versions;
3. record missing coverage instead of inferring it;
4. use a supported, versioned export when an API is absent;
5. start read-only; add only payload-bound draft write endpoints after separate approval.

The customer-side connector must be outbound-only where feasible, scoped, allowlisted, bounded and
version-aware. Require scoped credentials, rotation/revocation, transport authentication,
cutoff/cursor semantics, rate/query limits and signed release packages. No direct database access
or arbitrary SQL is authorized.

### 11.2 Deployment claims

| Stage | Allowed claim |
|---|---|
| Current demo | Synthetic, single tenant, Keycloak/OIDC omitted, not production topology |
| Design-partner pilot | One selected reference deployment after identity, egress, connector, recovery and support proof |
| Production | Only after tested customer identity, authorization, backup/RTO/RPO, update/rollback, egress, audit and support controls |

The recommended pilot hypothesis is a customer-managed single-tenant data plane with a supported
read-only BRAVO connector and explicit model-egress policy. It conflicts with current cloud-only
and audit-without-blocking ADRs until the owner chooses a real-data policy and a superseding ADR is
accepted.

The vendor control plane, if introduced later, should receive license/capability manifest and
coarse health/usage by default, not raw prompts, evidence, accounting outputs or detailed traces.

## 12. Evaluation model

### 12.1 Separate scorecards

Knowledge Chat:

- cited answer correctness;
- procedure/version scope correctness;
- self-service/containment rate;
- time to correct next step;
- escalation packet quality;
- unsafe or unsupported claim rate.

Accounting Work:

- deterministic exactness;
- critical exception recall and precision;
- false-negative rate by severity/materiality;
- evidence completeness and lineage coverage;
- review time and time to resolution;
- approval without material edit;
- unsafe-action, cross-scope leakage and approval-bypass rate;
- abstention quality when scope or evidence is incomplete.

Do not average the two scorecards into one product-quality number.

### 12.2 Frozen A/B/C/D design

- Freeze matched System A/B outputs, traces, model/version, prompts, input scope and versioned
  evidence snapshots before changing prompt, routing, retrieval or synthesis.
- Keep existing Financial Close questions as one benchmark family.
- Add matched anchors for the selected first Accounting Work capability.
- Compare A legacy, B current Consultant, C Core V2 and D BravoGen with matched inputs where
  technically possible.
- Run blind SME review and task-outcome evaluation.
- Treat a frontier reference as an architecture signal, not a success baseline.

### 12.3 Stop gates

Stop or narrow the capability when:

- exact deterministic checks are not independently testable;
- required source coverage or lineage is missing;
- a critical false negative cannot be bounded acceptably;
- reviewer workload exceeds the manual baseline;
- API/export support requires unsupported direct DB access;
- the result depends on the LLM owning calculations, workflow or approval;
- real-data egress, identity or recovery policy is unresolved;
- the user/buyer does not validate the problem or willingness to pay.

## 13. Execution plan

The implementation-level dependency graph, schemas, work packages and test matrix are frozen in
`12-THREE-CASE-DEMO-DEV-BACKLOG.md`. This section remains the product-stage view.

### Phase 0 — canonical correction and decision preparation

- [x] Read BRAVO functional sources and map non-duplication boundaries.
- [x] Review the attached critique.
- [x] Run accounting/control/product/security council.
- [x] Redefine Financial Close as a capability/template, not the product objective.
- [x] Obtain the one-time owner confirmation in packet 11 and record ADR-0033.
- [x] Record ADR-0032 for the selected first demonstrator and its relationship to ADR-0016/0031.

Exit: no canonical document silently treats AP or Financial Close as the selected frontier
product.

### Phase 1 — runtime containment and frozen evidence

- [ ] Complete RLS runtime roles and HTTP/MCP/worker negative probes.
- [ ] Complete clean migration, downgrade/upgrade and unskipped DB checks.
- [ ] Complete backup/restore, Compose, credentials and effective ingress evidence.
- [ ] Label the Keycloak-free topology synthetic demo-only.
- [ ] Freeze the matched A/B answer and trace baseline before quality changes.
- [ ] Freeze source/version manifests and evidence snapshots for Chat plus the chosen capability.

Exit: runtime containment evidence exists and the baseline is immutable.

### Phase 2 — capability selection and discovery

- [ ] Interview at least three target users and two economic buyers for each shortlisted job.
- [ ] Score value, frequency, data availability, deterministic testability, liability,
  integration readiness, support burden and willingness to pay.
- [ ] Audit BRAVO API/export coverage for the top candidate.
- [ ] Obtain representative redacted/synthetic case patterns and SME answer keys.
- [x] Select Reconciliation & Exception Investigator as the deep demonstrator.
- [x] Select Bank statement ↔ sổ tiền gửi BRAVO as the bounded reconciliation subtype.
- [x] Add Voucher Evidence & Accounting Review and Period Close Readiness as functional, bounded
  cases under the same core.

Exit: signed decision record names one user, buyer, job, data contract and measurable outcome.

### Phase 3 — shared Core V2 contracts

- [ ] Implement framework-independent `AccountingCase`, scope, evidence snapshot, finding,
  recommendation, action, approval and trace contracts.
- [ ] Define narrow ports for source retrieval, deterministic engines, model, state, audit and
  downstream draft/export.
- [ ] Keep authorization, calculation, workflow and approval outside the model.
- [ ] Add contract tests for superseded evidence, stale approvals, idempotency and abstention.

Exit: the core runs in tests without FastAPI, SQLAlchemy, Postgres, vector DB or a live model.

### Phase 4 — three-case Accounting Work demonstrator

- [ ] Implement the shared case state machine, evidence/review contracts and Accounting Work
  inbox.
- [ ] Implement Bank Reconciliation first and pass its deterministic gate.
- [ ] Add bounded LLM slots only where section 7 permits.
- [ ] Add Voucher Evidence & Accounting Review using deterministic total/tax/duplicate/lineage and
  3-way evidence checks; never post a voucher.
- [ ] Add Period Close Readiness using deterministic dependency/completeness checks; never
  duplicate BRAVO period calculations or lock.
- [ ] Build one reusable case page contract with case-specific views and policies.
- [ ] Integrate synthetic/versioned files first; then approved read-only API/export.
- [ ] Generate reviewed output; do not execute accounting mutations.

Exit: Bank Reconciliation passes the complete exactness/quality gate; Voucher Review and Period
Close Readiness pass their case-specific deterministic, safety, evidence and functional gates.

### Phase 5 — Knowledge Chat quality rebuild

- [ ] Keep Chat evaluation independent from Accounting Work.
- [ ] Freeze and improve retrieval/source/version behavior against the matched baseline.
- [ ] Preserve natural conversation, correction and task switching.
- [ ] Add a governed handoff from Chat to a typed AccountingCase when appropriate.

Exit: Chat improves its own blind scorecard without borrowing Accounting Work success.

### Phase 6 — demo hardening

- [ ] Configure one synthetic tenant, roles, source pack, model/egress policy, audit export and
  capability flags as code.
- [ ] Complete Governance & Integration BA specification and FE mock only.
- [ ] Run backend, frontend, accessibility, isolation, egress and rollback checks.
- [ ] Produce an evidence index that separates test, synthetic demo and production claims.
- [ ] Run the owner demo and blind SME review.

Exit: the demo is useful, labelled accurately and has no hidden production claim.

### Phase 7 — paid design-partner pilot evidence gate

- [ ] Validate buyer, willingness to pay, liability tolerance and support effort.
- [ ] Prove the ADR-0033 customer-managed single-tenant on-prem reference profile.
- [ ] Accept and implement the real-data ADR for minimized/redacted cloud egress or private/local
  fallback.
- [ ] Prove identity federation, read-only connector, DPA/egress, recovery and remote support.
- [ ] Supersede/amend conflicting cloud/offline/egress ADRs before real data.
- [ ] Define pilot contract, service boundaries and success/stop thresholds.

Exit: a pilot proceeds only with an accountable buyer, approved data path and measurable job.

## 14. Owner decision gates

The one-time confirmation surface is
`11-OWNER-DECISION-PACKET-RECONCILIATION-DEMO.md`. Its OD-01 through OD-10 defaults consolidate
the product, data, topology, model, integration, packaging, dev-scope and release-gate choices.
The owner confirmed all ten decisions and amended OD-08 to three functional cases; ADR-0033
records that confirmation.

ADR-0033 locks the plan values below. `TARGET` means an accepted architecture for future pilot
work, not evidence that the production control has been implemented or passed:

| Gate | Status | Decision / recommendation | Consequence |
|---|---|---|---|
| DG-01 First user/buyer/problem | `DECIDED TARGET — ADR-0033` | Reconciliation accountant/reviewer; chief accountant/controller; unresolved discrepancies | Discovery must still validate WTP |
| DG-02 First deep demonstrator | `DECIDED — ADR-0032` | Reconciliation & Exception Investigator | Resolves the AP-versus-Close demonstrator conflict |
| DG-03 Pilot reference deployment | `DECIDED TARGET — ADR-0033` | Customer-managed single-tenant on-prem data plane | Requires future identity, update, recovery and support proof |
| DG-04 Real-data model policy | `DECIDED TARGET — ADR-0033` | Raw data local; only approved minimized/redacted context may egress; private/local fallback | Requires future ADR superseding/amending ADR-0019/0022 |
| DG-05 Integration level | `DECIDED BOUNDARY — ADR-0033` | Demo files; pilot API-first read-only plus supported-export fallback; future typed draft only | No direct DB, arbitrary SQL or autonomous mutation |
| DG-06 ADR-0016 disposition | `DECIDED — ADR-0032` | Superseded for V2 demonstrator selection; non-invasive controls preserved | Removes conflicting first-demonstrator truth |
| DG-07 Packaging hypothesis | `DECIDED AS HYPOTHESIS — ADR-0033` | Validate Chat and Accounting Work separately; no final SKU | No billing implementation yet |
| DG-08 Governance scope | `DECIDED` | Config-as-code plus BA/FE mock only | Prevents premature platform work |
| DG-09 First reconciliation subtype | `DECIDED — ADR-0032` | Bank statement ↔ sổ tiền gửi BRAVO | Fixes the first fixture/schema and deterministic engine boundary |
| DG-10 Additional demo cases | `DECIDED — ADR-0033` | Voucher Evidence Review + Period Close Readiness | Functional/bounded, built after Bank Reconciliation |

Implementation is authorized only after runtime containment and A/B baseline freeze. ADR-0033
defines pilot targets but does not prove production readiness, grant customer-data permission or
validate final pricing/WTP.

## 15. Canonical synchronization

- [x] `docs/PROJECT-STATE.md`: make Accounting Operations Hub the north star; record ADR-0032/0033 and fix
  demo topology wording.
- [x] `docs/AI-REVIEW-MANIFEST.md`: add this plan to the required read order and expose the ADR
  conflict.
- [x] `plan-rebuild/08-V2-CONVERSATION-REBUILD-HANDOFF.md`: replace the hard-coded Financial Close
  vertical with a selected bounded Accounting Work capability; update evidence and critic
  semantics.
- [x] `plan-rebuild/02-R1-DECISION-BENCHMARK-PLAN.md` and
  `plan-rebuild/07-CONVERSATION-INTELLIGENCE-BRAVOGEN-BENCHMARK.md`: state that Financial Close
  benchmark coverage does not decide product scope.
- [x] `plan-rebuild/06-RESEARCH-AND-IMPLEMENTATION-ROUNDS.md`: replace the unsupported claim that
  Financial Close is the most important gap with the capability-selection scorecard.
- [x] `plan-rebuild/09-FRONTEND-FIGMA-MAKE-CUTOVER-EXECUTION-PLAN.md`: treat existing Financial Close
  screens as non-authoritative synthetic references; do not productize them as the product root.
- [x] Add accepted owner packet 11, ADR-0033 and implementation backlog 12.

## 16. Definition of “frontier” for this project

The project may call `Công việc AI` a frontier accounting agent only when it demonstrates:

- job-specific accounting depth, not a generic chat wrapper;
- authoritative deterministic numbers and controls;
- evidence-linked reasoning and explicit scope;
- useful ambiguity handling and missing-context questions;
- human control over every consequential action;
- bounded, inspectable integration with BRAVO as system of record;
- measurable improvement over the current system and strong-model document baseline;
- deployable privacy, identity, recovery and audit controls for the selected customer topology.

Feature count, an Agent Catalog, autonomous language, a multi-agent diagram or a frontier model
alone does not satisfy this definition.
