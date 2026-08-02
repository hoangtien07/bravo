# BRAVO 10 business-flow remediation plan before FigmaMake

Status: `COUNCIL SELECTED - FE ADMISSION CLOSED UNTIL AUTOMATED GATES PASS`

Date: 2026-08-02

Authority: BRAVO 10 business-flow council decision dated 2026-08-02; preserves ADR-0032/0033 and
the accepted three-case scope while correcting the implementation's business adequacy.

## 1. Outcome

Produce three synthetic AccountingCases whose positive results can only come from immutable,
scope-locked, policy-authoritative evidence:

1. Bank Reconciliation remains primary/deep.
2. Voucher Evidence & Accounting Review becomes functional/bounded.
3. Period Close Readiness becomes functional/bounded.

Only after those backend contracts and automated local flows pass may `FigmaMake_UI` be
productized as the integrated frontend. Human/SME evaluation is deliberately deferred during the
developer sequence, but its absence remains visible and blocks quality/release claims.

## 2. Non-duplication boundary

BRAVO 10 continues to own:

- bank connection, transfer commands and transaction status;
- voucher entry, invoice integration, posting, tax and ledger;
- inventory cost, depreciation, allocation, costing, FX and closing entries;
- financial reports, approval/signature, data lock, RBAC, task and audit functions.

V2 may read approved synthetic snapshots, run independent checks, investigate exceptions, explain
verified findings, collect reviewer decisions and export a reviewed packet. It never performs the
BRAVO operations above.

## 3. Immediate containment

Before further UI work:

1. Separate `developer_preview` capability flags from `functional_case` flags.
2. Disable the current Voucher/Period functional claim in the runnable demo manifest. If the
   arbitrary-body preview endpoints are retained temporarily, rename/label them
   `developer_non_authoritative` and never return authoritative `pass`, `ready`, or BRAVO-lineage
   claims without server-resolved evidence.
3. Make empty/missing policy or evidence return `abstain`/`not_ready`, never a positive verdict.
4. Enforce the `bank_reasoning` manifest flag on the Bank conversation route.

Exit: the current scaffold cannot be mistaken for a functional accounting verdict.

## 4. BF-00 - source authority and traceability freeze

### Tasks

- Create a traceability matrix for every required decision:
  `persona -> input/evidence -> BRAVO object/status -> deterministic check -> exception -> reviewer -> artifact`.
- Treat B10 User Guides as general product guidance with their documented configuration/runtime
  caveat; do not use them alone for an exact deployed-version claim.
- Add source-specific `doc_version`, owner, approval status, effective date and customer-specific
  scope to the corpus manifest. B8R4/customer KQPT material must not inherit B10R1/approved truth.
- For exact/versioned answers, fail closed unless an approved matching source exists; lifecycle
  demotion alone is insufficient when the only retrieved source is stale or customer-specific.
- Freeze revised schemas, policies, fixture manifests, hashes and must-not claims before engine
  changes.

### Automated exit

- A manifest audit rejects conflicting filename/version metadata and missing source authority.
- Exact-claim retrieval tests reject a mismatched BRAVO version/status.
- Every field/check in the three case schemas maps to a named BRAVO source or an explicit synthetic
  policy decision.

Independent accounting/BRAVO SMEs approve the final truth later; developer fixtures remain labelled
`pending_independent_sme_review` until then.

## 5. BF-01 - correct the Bank reconciliation contract and engine

### Evidence contract

Add immutable statement/extract headers and controls:

- tenant, legal entity, bank account, ledger/book, currency, from/to dates and cutoff;
- source/version/hash, captured-at, row count and signed control total;
- opening/closing balance where the source provides them;
- BRAVO extraction rule and eligible document states (`Đã hoàn thiện`/`Đã khóa` or an approved
  version-specific equivalent); cancelled/incomplete rows are rejected or quarantined;
- explicit policy for bank transaction date versus value date and BRAVO posting versus document
  date.

### Matching correction

- Build a global candidate/compatibility graph before final classification.
- Consume only an unambiguous match that satisfies the approved policy.
- Never consume aggregated, duplicate or ambiguous candidates before a reviewer selection.
- Detect competition/duplicates on both Bank and BRAVO sides.
- Make reason codes truthful. If both references exist, the approved exact-reference policy must
  compare them; otherwise use a candidate/tolerant classification, not
  `EXACT_REFERENCE_AMOUNT_DATE`.
- Enforce entity, ledger, account, currency, cutoff, date basis and eligible document status before
  matching.
- Surface quarantined rows and statement/extract control-total failures as explicit findings.

### Review contract

Replace the string disposition map with typed immutable decisions containing disposition, reviewer,
reason, note/evidence references and decision hash. `resolved` requires resolution evidence;
`accepted_exception` requires an approved reason/policy; `investigate`/`escalate` remain open. The
export states unresolved totals and cannot imply that BRAVO was adjusted.

### Automated exit

- Two Bank rows competing for one ledger row remain a conflict; no arbitrary exact match occurs.
- An aggregation/duplicate candidate cannot make a later valid row disappear.
- Wrong reference/entity/ledger/cutoff/status/date-basis rows cannot exact-match.
- Missing row coverage or failed opening/closing/control totals prevents a reconciled conclusion.
- Changed-content supersession invalidates checks, review and export.
- Golden, held-out and property/permutation tests remain deterministic with the LLM disabled.

## 6. BF-02 - functional Voucher Evidence Review

### Frozen subtype

Start with one domestic VND purchase case. Evidence is loaded by an approved immutable synthetic
scenario/fixture ID, never accepted as truth from caller scalar fields.

Required versioned evidence:

- invoice identity, supplier/tax identity, dates, currency, lines, UOM, quantity, net, discount,
  tax code/rate/amount and gross total;
- PO or contract lines, approved price/quantity/terms and source lineage;
- receipt and QC acceptance lines/status where applicable;
- BRAVO draft-voucher snapshot with document type/status, account/dimension candidates and lineage;
- effective-dated tax/master/account/dimension policy fixtures.

Deterministic checks implement the full WP-01 list: document total, tax arithmetic/policy eligibility,
duplicate detection from an authoritative registry, line-level PO/receipt/invoice comparison,
supplier/master consistency, account/dimension eligibility and evidence coverage.

Missing or inapplicable evidence is decided by policy. A client cannot claim `received`, provide its
own duplicate result or turn an arbitrary BRAVO ID into lineage.

Reuse the shared AccountingCase lifecycle, evidence supersession, CAS/idempotency, findings,
typed review, hash-bound approval, audit and export packet. Never post or create a parallel ledger.

### Automated exit

- Fabricated ID, empty duplicate list or caller `received=true` cannot produce a pass.
- Missing policy/evidence abstains; foreign scope/version and stale/superseded evidence fail closed.
- Partial receipt, UOM, quantity, price, discount, tax, supplier, account and dimension mismatches
  have golden cases and exact lineage.
- Full durable create/evidence/check/review/export flow passes local HTTP/DB tests.

## 7. BF-03 - functional Period Close Readiness

### Policy and evidence

The server loads an approved prerequisite policy for the locked entity/period. It defines the
complete required/applicable set, dependencies, freshness windows, materiality source and approval
requirements. The client cannot omit a prerequisite or mark it non-applicable.

Synthetic evidence references BRAVO-owned outcomes/statuses only, including as applicable:

- posting/data-integrity checks and document approval state;
- Bank/other reconciliation case outcomes and unresolved material exceptions;
- depreciation, CCDC allocation, payroll, recurring entries, FX, inventory cost and costing status;
- closing-entry status, report validation status and data-lock status;
- maker-checker approval records and evidence freshness/cutoff.

V2 verifies completeness/dependencies and explains blockers; it never runs any process or locks the
period.

### Automated exit

- Empty input is always blocked/abstained.
- Omission of any policy-required prerequisite, approval or reconciliation blocks readiness.
- A fabricated/reviewed foreign case ID or client-selected materiality is rejected.
- Stale, wrong-period/entity/version or superseded evidence blocks readiness.
- `ready=true` is possible only after complete policy coverage, fresh evidence, resolved material
  blockers and required maker-checker evidence.
- Full durable create/evidence/check/review/handoff-export flow passes local HTTP/DB tests.

## 8. BF-04 - bounded AI/reasoning

- Keep deterministic numbers, classifications, readiness, workflow and approval outside the model.
- Implement one typed `ReasoningPort` adapter for clarification, evidence-linked explanation,
  reviewer-selectable alternatives, investigation memo and abstention.
- Bind model/provider/version, prompt/config hashes and egress policy only after the owner approves
  the model record. Until then the deterministic fallback must say it is synthetic and cannot be
  counted as an AI-quality pass.
- Every exact claim references evidence/rule IDs. The model cannot change or invent a finding,
  disposition, amount, status or BRAVO action.
- Add adversarial tests for prompt attempts to waive, post, pay, close, lock, run SQL, widen scope or
  override a deterministic result.

Automated developer exit: the typed fallback and model-adapter contract pass without a live model.
Model quality, blind comparison and user-time benefit remain external gates.

## 9. BF-05 - authorization, RLS and audit backstops

- Add case scope/RLS coverage for every V2 table containing command outcomes or case-derived audit
  data, not only `accounting_cases_v2`.
- Make runtime audit append-only through grants/role separation and an immutable database control;
  test that the application role cannot update/delete audit history.
- Derive native RLS policy from the action being performed rather than the union of all caller
  capabilities, or create operation-specific policies/GUCs.
- Map out-of-scope records to one deliberate non-enumerating denial response.
- Audit privacy-minimized reads, conversations, denials and mutations.
- Preserve the off-by-default synthetic manifest and separate preview/functional capability flags.

Automated developer exit: application authorization, forced-RLS SQL integration and audit
immutability tests pass. Operator-owned non-owner HTTP/MCP/worker probes remain an external gate.

## 10. BF-06 - FE admission and local integrated demo

`FigmaMake_UI` productization begins only after BF-00 through BF-05 automated exits pass and council
records a new `FE ADMISSION OPEN` decision.

The handoff package must contain for all three cases:

- frozen OpenAPI grammar and typed success/error/abstention examples;
- state machine, role/action matrix, revision/idempotency and approval/hash behavior;
- fixture/policy/evidence hashes and exact must-not claims;
- rendering states for missing, stale, superseded, conflicted, abstained, denied and unresolved;
- proof that no empty/fabricated caller input can produce a positive accounting verdict.

Then convert `FigmaMake_UI` from static fixtures to the same-origin trusted API/auth/RLS shell,
preserving `frontend-react` as rollback until local E2E, typecheck, unit, accessibility, visual and
production build checks pass. The first deliverable is a local synthetic demo, not a public or
production deployment.

## 11. Delivery order and stop rules

```text
Immediate containment
  -> BF-00 source/business truth
  -> BF-01 Bank correction
  -> BF-02 Voucher functional case
  -> BF-03 Period functional case
  -> BF-04 bounded reasoning contract
  -> BF-05 security/audit automated gates
  -> council FE admission
  -> BF-06 FigmaMake + local integrated demo
  -> deferred model/SME/user/operator/release evidence
```

Stop or narrow when:

- positive output still depends on caller-asserted accounting truth;
- a required source/policy cannot be versioned and independently tested;
- deterministic checks require the LLM;
- a case begins recreating BRAVO transaction/calculation/approval/lock behavior;
- a critical false positive, false negative, scope leak or approval bypass remains;
- the frontend has to invent an API or business state.

## 12. Completion claims

Passing BF-00 through BF-06 permits only: **local synthetic three-case developer demo ready for
human evaluation**.

It does not prove model quality, SME acceptance, reviewer-time improvement, non-owner runtime
containment, real-data permission, pilot readiness or production readiness. Those remain governed
by Plan 15 and OD-09/OD-10.
