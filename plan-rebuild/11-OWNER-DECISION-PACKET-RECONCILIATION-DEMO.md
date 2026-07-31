# Owner decision packet — BRAVO Reconciliation demonstrator

Status: `ACCEPTED — OD-01..OD-10 confirmed; OD-08 amended to three functional cases`
Owner: project owner
Prepared: 2026-07-31
Applies to: BRAVO Accounting Intelligence demo and dev-ready scope
Confirmed: 2026-07-31 — owner response `CONFIRM ALL. OD-08 thêm 2 case nữa`
Authority: ADR-0032 plus ADR-0033 and this accepted decision packet

## 1. Purpose

Collect every remaining product, data, topology, integration, packaging and acceptance decision
needed to turn the current design into a dev-ready plan. The owner can approve the recommended
package once instead of answering decisions across multiple implementation rounds.

## 2. Decisions already locked

These are recorded for context and are not reopened by this packet:

| ID | Locked decision |
|---|---|
| L-01 | Independent BRAVO Accounting Intelligence product; not embedded in BRAVO 10 |
| L-02 | One product shell with separately governed Knowledge Chat and Accounting Operations Hub |
| L-03 | `Công việc AI` complements BRAVO; it does not rebuild vouchers, ledger, close engine, Task, approval, reporting, scheduler, RBAC or audit |
| L-04 | Reconciliation & Exception Investigator is the first deep V2 demonstrator |
| L-05 | First subtype is Bank statement ↔ sổ tiền gửi BRAVO |
| L-06 | Financial Close is benchmark/template coverage, not the product objective |
| L-07 | Deterministic services own numbers, matching, policy, state and approval; LLM has bounded language/ambiguity roles |
| L-08 | Demo omits Keycloak/OIDC and is synthetic single-tenant only, not production topology |
| L-09 | Governance & Integration is BA specification + FE mock; runtime uses configuration-as-code |
| L-10 | `PKG-A` is a hypothesis; no billing UI, marketplace, Agent Catalog or general model-management platform |

## 3. Confirmed one-time decisions

OD-01 through OD-10 are Accepted with the OD-08 amendment below. The phrase **Confirmed default**
replaces the earlier recommendation status.

### OD-01 — Target user, reviewer and economic buyer

**Confirmed default**

- preparer: bank/accounting reconciliation accountant;
- checker: chief accountant or designated reconciliation reviewer;
- economic buyer hypothesis: chief accountant/controller;
- CFO is sponsor/escalation stakeholder, not the default daily user.

Why: gives dev a concrete role model and maker-checker path without claiming buyer/WTP is already
validated.

Alternative impact: choosing CFO as the primary user would shift the product toward management
narrative and away from transaction-level investigation.

### OD-02 — Demo data and evidence policy

**Confirmed default**

- synthetic, versioned fixtures only;
- no customer, employee, vendor or bank data;
- two frozen input schemas: normalized bank statement and BRAVO bank-ledger export;
- every run records snapshot ID, source version, cutoff, hash and `supersedes`;
- fixtures include exact, tolerance, aggregation, duplicate, bank-only, BRAVO-only and ambiguous
  cases.

Alternative impact: using real/redacted customer data now would add legal, egress, access and
retention gates before conversation-quality work can start.

### OD-03 — Demo model and identity topology

**Confirmed default**

- use one pinned frontier cloud model/version for the synthetic demo and A/B/C comparison;
- model/provider changes require a new benchmark run;
- keep the current trusted application auth/RLS shell;
- no Keycloak/OIDC in the demo;
- do not market this as production, on-prem or offline readiness.

Alternative impact: requiring a local model for the synthetic demo increases setup work and
confounds whether quality problems come from the product or model strength.

### OD-04 — Pilot reference deployment

**Confirmed default**

- customer-managed, single-tenant data plane inside the customer's private network;
- on-prem deployment is the first reference profile;
- application, deterministic engine, raw evidence, audit and backup remain customer-side;
- vendor control plane, if later introduced, receives license/capability and coarse health only;
- remote support is disabled by default and must be time-bound, approved and audited.

Alternative impact: a vendor-hosted SaaS pilot reduces deployment work but increases data,
identity, contractual and trust barriers for sensitive accounting evidence.

### OD-05 — Real-data model and egress policy

**Confirmed default**

- raw accounting evidence and deterministic reconciliation never leave the customer data plane;
- cloud LLM receives only policy-approved, minimized/redacted exception context;
- egress is allowlisted, purpose-bound, auditable and requires customer/DPA approval;
- raw prompts, documents, full transactions and detailed traces are not sent to a vendor control
  plane;
- if the customer disallows cloud egress, use a private/local model profile, but make no
  quality-equivalence claim until it passes the same benchmark.

Consequence: this requires a future ADR that supersedes/amends cloud-only ADR-0019 and
audit-without-blocking ADR-0022 before real data.

Alternative impact: full raw-data cloud egress may improve model context but is not the default
for this product's sensitivity and trust position.

### OD-06 — BRAVO integration and mutation boundary

**Confirmed default**

- demo: versioned file fixtures, no live BRAVO dependency;
- pilot: API-first, read-only connector with a field/coverage audit;
- fallback: supported, versioned BRAVO export when API coverage is absent;
- connector is scoped, allowlisted, bounded, version-aware and cannot execute arbitrary SQL;
- no direct database access;
- future write integration is limited to a typed, payload-bound draft after maker-checker;
- no autonomous posting, payment, lock/reopen period or master-data mutation.

Alternative impact: requiring a live API for the demo reintroduces an external blocker; allowing
direct DB/write access expands the highest-risk surface before value is proven.

### OD-07 — Product entitlement and commercial hypothesis

**Confirmed default**

- Knowledge Chat and Accounting Operations Hub are separately entitled modules in one shell;
- Knowledge Chat may be bundled with support/site licensing;
- Accounting Work is tested as a separately purchased capability pack;
- first design-partner engagement may include implementation/onboarding plus a pilot fee;
- no final price, billing engine or usage marketplace is built in this phase.

Alternative impact: one bundled SKU hides different buyers, support costs, liability and
willingness-to-pay.

### OD-08 — Dev scope for the three-case demonstrator

**Confirmed with owner amendment: add two functional cases**

Build:

- one Accounting Work inbox;
- one shared `AccountingCase` page contract with Scope, Findings, Evidence, Recommendations, Draft
  actions and Review/Audit;
- **Case 1 — Bank Reconciliation (primary/deep):** Bank statement ↔ sổ tiền gửi BRAVO;
  deterministic normalization/matching/classification; bounded LLM questions, explanations and
  investigation narrative; review disposition and exportable reconciliation packet;
- **Case 2 — Voucher Evidence & Accounting Review (functional/bounded):** synthetic invoice,
  PO/contract, receipt/QC where applicable and BRAVO draft-voucher snapshot; deterministic
  total/tax/duplicate/lineage and 3-way evidence checks; LLM handles document ambiguity, mapping
  alternatives and explanation; output is a review packet or typed recommendation, never a posted
  voucher;
- **Case 3 — Period Close Readiness (functional/bounded):** synthetic period scope, prerequisite
  statuses, reconciliation references and evidence gaps; deterministic dependency/completeness
  checks; LLM asks for missing context and explains readiness/next action; BRAVO remains the engine
  for depreciation, costing, FX, closing entries, reports and period lock;
- versioned evidence snapshots and reconstructable trace shared by all three cases;
- config-as-code for tenant, roles, source pack, model/egress policy, audit export and capability
  flags;
- Governance & Integration BA specification and non-functional FE mock.

Depth/order rule:

1. Build the shared Core V2 contracts.
2. Complete Bank Reconciliation and its deterministic/quality gate.
3. Add Voucher Evidence Review by reusing the same case/evidence/review contracts.
4. Add Period Close Readiness last; it may reference reconciliation results but cannot become a
   new close engine.

All three cases must be functional with synthetic fixtures. Case 2 and Case 3 are narrower than
Case 1 and do not independently authorize new platform abstractions.

Do not build:

- automatic journal adjustment or posting;
- live bank connectivity;
- generic task/Kanban/Gantt;
- full Governance Console;
- billing, marketplace, Agent Catalog or agent builder;
- Management Variance or any fourth deep accounting capability;
- voucher posting/e-invoice ingestion already owned by BRAVO;
- depreciation, costing, FX, closing-entry, report-formula or period-lock engines;
- arbitrary SQL or unrestricted multi-agent orchestration.

### OD-09 — Quality and safety release gates

**Confirmed default**

The demonstrator is accepted only when:

- deterministic monetary/match results are 100% correct on the frozen golden set;
- zero critical false negatives on the critical held-out set;
- zero cross-tenant/scope leaks, unsafe mutations or approval bypasses;
- every exact number and classification has source/rule lineage;
- critical prerequisite/scope recall is at least 90%;
- multi-turn correction fidelity is at least 95%;
- Core V2 wins at least 60% of non-tied blind comparisons against the current Consultant path;
- any external “better than BravoGen” claim still requires the existing lower confidence bound
  above 50%;
- median reviewer completion time improves at least 30% against the frozen manual baseline;
- at least 80% of accepted recommendations need no material accounting edit;
- all failed/abstained cases expose a reason instead of silently fabricating completion.

Alternative impact: softer exactness or safety gates are not recommended. Time/edit targets may be
re-estimated once a measured manual baseline exists, but cannot be reported as passed without that
baseline.

### OD-10 — Promotion from demo to paid pilot

**Confirmed default**

Do not automatically promote the demo. A paid pilot requires all of:

- demo quality/safety gates pass;
- at least three target-user interviews and two buyer interviews;
- one accountable design partner and written success/stop criteria;
- verified BRAVO API/export coverage for the agreed subtype;
- accepted identity, egress/DPA, retention, backup/restore, update/rollback and support model;
- a superseding real-data/model-policy ADR;
- no unresolved critical accounting, security or recovery blocker.

If these gates pass, Bank Reconciliation is the default pilot candidate. If they fail, stop or
narrow the capability rather than adding more agents.

## 4. Decisions intentionally deferred beyond dev planning

The following do not block the synthetic demonstrator and are not silently decided:

- final commercial price;
- a fourth accounting case/capability beyond the accepted three-case demo;
- multi-tenant vendor SaaS;
- air-gapped production certification;
- local-model equivalence;
- write-back to BRAVO;
- marketplace/agent builder;
- general-purpose multi-agent orchestration.

## 5. Confirmation record

The owner confirmed all OD-01 through OD-10 and amended OD-08 to add two cases. The plan applies
the amendment as Voucher Evidence & Accounting Review plus Period Close Readiness, matching the
previous council three-template recommendation. Bank Reconciliation remains the primary/deep
case; the two additions are functional, bounded and sequential.

This confirmation authorizes planning and implementation only after the existing containment and
baseline-freeze gates. It does not authorize real customer data, production deployment, direct DB
access, autonomous mutation or bypass of a future real-data/DPA gate.
