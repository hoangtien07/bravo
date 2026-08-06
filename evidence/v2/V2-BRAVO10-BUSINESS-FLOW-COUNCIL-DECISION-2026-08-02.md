# V2 BRAVO 10 business-flow council decision

Status: `DECIDED - BACKEND/AI REMEDIATION REQUIRED BEFORE FIGMAMAKE PRODUCTIZATION`

Date: 2026-08-02

Subsequent disposition: Plan 16 BF-00 through BF-05 automated exits were later accepted on the
same date. See the separate
[`FE ADMISSION OPEN` decision](V2-BRAVO10-FE-ADMISSION-COUNCIL-DECISION-2026-08-02.md).
This document remains the historical record of the defects and remediation selection.

## Question reviewed

Is the current Backend and AI path sufficiently faithful to the BRAVO 10 accounting workflows in
`file_system/` to freeze the contracts and begin a new integrated `FigmaMake_UI` frontend?

The review distinguishes a structurally green developer scaffold from a business-correct
AccountingCase. It does not require V2 to rebuild BRAVO voucher entry, e-banking, posting, tax,
costing, closing, reporting, approval, data lock, or audit functions.

## Sources and code reviewed

- BRAVO 10 User Guide chapters: Accounting pages 10-15 and 88-92/110; Documents pages 3, 7, 8,
  10; Purchases pages 23-27; Managements pages 35-45; System pages 8-10 and 33-34.
- Relevant Accounting, Documents, Managements, Purchase, Inventory, System and Task mindmaps.
- `bravo_ai_use_cases.yaml`, `bravo_lifecycle_playbooks.yaml`, `bravo_consultant_cards.yaml`, the
  corpus manifest, WP-01 schemas/policies/golden fixtures and Core V2 code/tests.
- Independent council tracks: accounting/domain, API/implementation and security/control.

The BRAVO guides themselves warn that the shipped product/configuration may differ from the guide;
therefore exact runtime behavior still needs version/config evidence and cannot be inferred from a
generic guide alone.

## Reproduced blocking evidence

All reproductions used only tracked synthetic fixtures/code. No secret, customer data, external
system or `.tmp-pytest/` content was accessed.

### Period Close false positive

```text
assess_period_close((), ())
=> ready=True, blocker_ids=(), reason_codes=()
```

The caller supplies the prerequisite list and reconciliation statuses. There is no authoritative
prerequisite policy, ScopeKey, evidence snapshot, approval record or server lookup. An empty or
curated subset can therefore be declared ready, contradicting the frozen must-not claim.

### Voucher false positive

```text
invoice_total=110, invoice_tax=10, invoice_net=100,
po_amount=110, received=true, bravo_document_id="fabricated"
=> document_total=pass, duplicate_candidate=pass,
   three_way_evidence=pass, lineage=pass
```

A non-empty caller string is treated as a linked BRAVO draft; an empty caller-provided duplicate
list is treated as proof of no duplicate; a scalar PO amount and receipt boolean are treated as a
three-way match. None is server-verified evidence.

### Bank competing-candidate false settlement

With two same-date/same-amount Bank rows competing for one BRAVO ledger row, the sorted first row
is classified `EXACT_MATCH` and consumes the ledger row; the second becomes `BANK_ONLY`. The
result should remain a conflict/duplicate candidate until deterministic tie-breaking or reviewer
resolution. Candidate, duplicate and ambiguous ledger rows are also consumed today.

### Bank misleading exact reason

A ledger row with a deliberately different reference still returns:

```text
EXACT_MATCH EXACT_REFERENCE_AMOUNT_DATE
```

The exact rule compares amount/date but does not compare the reference named by the reason code.

## Severity findings

### P0 - business verdict can be wrong

1. Period Close can return `ready=true` with no evidence or an incomplete caller-curated set.
2. Voucher can return pass/lineage claims from caller assertions rather than immutable evidence.
3. Bank greedily consumes unresolved candidates and can settle the wrong row while hiding a later
   valid conflict.

### P1 - BRAVO control semantics are missing or misleading

1. Bank exact matching does not enforce its stated reference rule. It does not make the selected
   date basis explicit and the row contract lacks source document lifecycle status.
2. The Bank engine checks only account/currency at row level. Legal entity, ledger, cutoff,
   eligible BRAVO document status and statement control totals are not engine inputs.
3. Voucher lacks the frozen line-level invoice/PO-or-contract/receipt-QC/BRAVO-draft evidence,
   tax/master/account/dimension checks and document state needed by its own WP-01 schema.
4. Period Close lacks an approved complete prerequisite/dependency policy, process-status lineage,
   freshness, reconciliation disposition and maker-checker evidence required by its WP-01 schema.
5. Voucher and Period are stateless previews, not the three functional AccountingCases accepted
   by ADR-0033.
6. `SyntheticBankReasoning` is deterministic canned text, not the owner-pinned bounded model path
   or an evaluated accounting assistant.

### P1/P2 - platform and knowledge controls

1. Secondary previews accept caller policy/status facts and bypass ScopeKey, evidence snapshots,
   CAS/idempotency, durable audit, maker-checker, approval invalidation and export controls.
2. `accounting_case_commands_v2` stores case outcomes but has no case-scope RLS policy; V2 audit
   immutability is an application convention, not a database-enforced property.
3. Native RLS is still off by default and has no non-owner HTTP/MCP/worker cutover evidence.
4. `bank_reasoning` is present in the manifest but the conversation route only checks the top-level
   V2 capability.
5. The corpus manifest applies default `B10R1`/`approved` metadata to KQPT sources including names
   that explicitly contain `B8R4`. Exact BRAVO/version claims therefore need source-specific
   governance before Knowledge Chat can be called business-correct.

## Options considered

| Option | Decision | Reason |
|---|---|---|
| Start integrated FigmaMake development now | Rejected | It would freeze false-positive and incomplete business contracts into the UI. |
| Keep secondary previews enabled and rely on labels | Rejected as the functional-demo path | A label does not make `ready/pass/lineage` from caller assertions correct. |
| Remediate source authority, Bank conflict logic, and both secondary evidence/lifecycle contracts before FE | **Selected** | Smallest path that preserves the shared Core and BRAVO non-duplication boundary. |

## Decision boundary

- The current Bank durable shell remains a reusable engineering asset, but its original golden-set
  pass is not sufficient business-flow acceptance.
- Voucher and Period Close remain non-authoritative developer scaffolds. They cannot be presented
  as functional cases or used to conclude readiness.
- New FigmaMake productization is paused until the automated FE admission gate in Plan 16 passes.
- Independent SME, real-user timing, model-owner and operator gates remain deferred; they are not
  simulated by this decision.
- `.tmp-pytest/` remains an unrelated untracked ACL-owned artifact and was not touched.

## Selected follow-up

Execute `plan-rebuild/16-BRAVO10-BUSINESS-FLOW-REMEDIATION-PLAN.md`. After its automated contract
and local runtime gates pass, issue a new council decision explicitly opening FigmaMake design and
local integrated development.
