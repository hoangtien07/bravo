# T5 — Accounting, AP & Tax Business Workflow

Scope read: T0/T2/T4 artifacts; `app/accounting/**`, `app/agent/tax.py`, `app/agent/anomaly.py`, `app/erp/**`, invoice/draft/agent routes, `app/ingestion/invoice_parser.py` as a direct dependency, accounting data, and focused accounting/draft tests. No test was run because the baseline records no usable host Python/pytest toolchain.

## Current state transitions

| Flow | VERIFIED implementation trace | Current enforcement / endpoint |
|---|---|---|
| Invoice XML proposal | `routes_invoices:invoice_to_draft` reads upload bytes → `ap_service:create_invoice_draft` → `parse_invoice_xml` → `build_journal_entry` → `draft_queue.create_draft(status="pending")`. | Route requires `draft:create`. Parser and journal builder are deterministic; no LLM call occurs in this path. |
| Agent journal proposal | `agent.loop:_build_journal_payload` builds `JournalEntryPayload`; `tools:call_tool` creates a pending draft instead of invoking the write function. | T4 confirms per-tool permission, payload builder, and non-admin department fail-closed behavior for this path. |
| Generic proposal | `routes_drafts:propose` accepts `DraftIn(kind, payload)` and calls `create_draft` directly. | Requires `draft:create`; no type-specific payload validation or department resolution is performed here. |
| Review / disposition | `routes_drafts:approve` / `reject` call `draft_queue:approve_draft` / `reject_draft`. `approve_draft` serializes by advisory lock, checks maker ≠ approver subject to config, checks unchanged payload hash, then changes status. | The service fetches by draft ID without `draft_scope_filter` (BRV-BIZ-002). |
| Accounting output | `routes_drafts:export_draft` allows an approver-scoped `journal_entry` draft to be rendered by `journal_export` as CSV/XLSX. | `journal_export` formats payload fields; it does not revalidate `JournalEntryPayload`. No executable ERP write client was found: `app/erp/client.py` has no client implementation. |
| Tax / anomaly proposal | `routes_agents:reconcile_tax` / `scan_anomaly` use `MockDataSource`, create `tax_adjustment` / `anomaly_flag` pending drafts, and mark payloads `is_demo=True`. | Routes do resolve a department and fail closed for non-admin identities with ambiguous scope. The results are fixture-derived, not ERP reads. |

## Invariant and lineage map

| Invariant / lineage element | Code enforcement | Scope / limitation |
|---|---|---|
| Double-entry balance and one-sided lines | `JournalEntryPayload._enforce_number_integrity` rejects empty, dual-sided, unbalanced, and inconsistent totals. | Enforced in invoice/agent payload builders, not on generic `POST /drafts` or before export/approval. |
| Source numbers and invoice provenance | Parser produces Decimal amounts and a source hash; `build_journal_entry` stores source hash, invoice metadata, source refs, invoice lines, and derived engine values in the journal payload. | The AP service does not persist the raw XML or a relational invoice/source record; `raw_xml_path` is not carried into `InvoiceMeta`. |
| Mapping / statutory rules | `map_invoice` maps by governed rules and marks fallback/TSCĐ cases for review; `build_journal_entry` selects statutory thresholds using `Invoice.ngay_lap`. | An absent or unparseable date falls back to the latest rule period (BRV-BIZ-006). |
| VAT / semantic checks | Invoice validation flags malformed tax/totals; mapping flags uncertain TSCĐ and non-cash VAT conditions. | Flags make `needs_review=True`; the approval service does not inspect `needs_review` or require an override record. Whether a flag must block approval is `NEED FILE/CONTEXT`. |
| Duplicate invoice | `Invoice.key()` and `source_hash` are derived in memory. | Neither is queried or constrained in the AP draft flow; `create_draft` idempotence applies only when an `agent_run_id` is supplied (BRV-BIZ-004). |
| PO / receipt / QC / payment lineage | `Invoice`, `JournalEntryPayload`, and the scoped accounting/ERP routes contain invoice/journal fields only; a scoped code search found no PO, receipt, QC, payment, or liability record relation. | No implementation evidence was found for a three-way-match or payment lineage in this task scope. Whether such controls exist upstream/external is `NEED FILE/CONTEXT`. |

## Findings

| ID | Severity tạm thời | Evidence state | File:symbol | Evidence ngắn | Consumer/impact | Next action | Needs Sol review |
|---|---|---|---|---|---|---|---|
| BRV-BIZ-001 | High | VERIFIED | `app/api/routes_drafts.py:propose`; `app/accounting/ap_service.py:create_invoice_draft`; `app/erp/draft_queue.py:draft_scope_filter` | Generic `POST /drafts` passes no `department_id`, so created drafts are NULL/global. AP resolves a department but still calls `create_draft` with `None` when a non-admin has zero or multiple departments. The scope filter includes NULL/global drafts for an `own_dept` approver. | A draft creator can create globally visible financial workflow state; ambiguous AP identities also receive a global draft instead of the fail-closed behavior applied by the agent path. | Centralize mandatory department resolution in `create_draft` (or a typed creator) and test generic/AP zero- and multi-department identities. | Yes |
| BRV-BIZ-002 | High | VERIFIED | `app/api/routes_drafts.py:approve`, `reject`; `app/erp/draft_queue.py:approve_draft`, `reject_draft`; `app/security/auth.py:require_permission` | `require_permission("draft:approve")` admits `draft:approve:own_dept`, but approval/rejection then uses `db.get(Draft, draft_id)` and never applies `draft_scope_filter`. | An own-department approver who knows a foreign draft UUID can change its financial workflow state; list/get/export use a scope filter but approve/reject do not. | Enforce the scoped predicate inside service-level approve/reject and add cross-department approve/reject integration probes. | Yes |
| BRV-BIZ-003 | High | VERIFIED | `app/api/routes_drafts.py:DraftIn`, `propose`; `app/erp/draft_queue.py:create_draft`, `approve_draft`; `app/accounting/journal_export.py:journal_to_rows` | Generic input is unrestricted `kind: str, payload: dict`; create stores JSONB unchanged, approval checks only its hash, and export renders fields without `JournalEntryPayload` validation. | A `draft:create` user can propose a malformed or unbalanced `journal_entry` through a path that bypasses the XML/agent number gate; a second approver can approve/export it. | Restrict draft kinds and validate journal payloads at a shared boundary; decide and record how flagged proposals may be overridden. | Yes |
| BRV-BIZ-004 | Medium | VERIFIED | `app/ingestion/invoice_parser.py:Invoice.key`; `app/accounting/ap_service.py:create_invoice_draft`; `app/erp/draft_queue.py:create_draft`; `app/database/models.py:Draft` | The AP flow derives invoice key/source hash but does not query/store either as a uniqueness key. It passes no `agent_run_id`, while the only unique constraint is `(agent_run_id, payload_hash)`. | Resubmitting the same XML creates independently pending journal drafts, increasing duplicate-review/posting risk. | Define duplicate identity and lifecycle at the AP boundary; add repeat-upload and same-invoice/different-file tests. | Yes |
| BRV-BIZ-005 | Medium | VERIFIED | `app/api/routes_agents.py:scan_anomaly`, `reconcile_tax`; `app/agent/anomaly.py:Flag.to_payload`; `app/agent/tax.py:TaxFlag.to_payload` | Both operational routes instantiate `MockDataSource`; their drafts carry `is_demo=True`, but use the shared Draft state and shared approval route. | Demo-derived anomaly/tax recommendations can enter the same pending/approved workflow records as accounting proposals, despite not being sourced from ERP data. | Keep demo outputs out of an approvable operational queue or make approval/export eligibility kind- and provenance-aware; add route-level tests. | No |
| BRV-BIZ-006 | Medium | VERIFIED | `app/ingestion/invoice_parser.py:parse_invoice_xml`, `validate_invoice`; `app/accounting/rules_governance.py:as_of_from_iso`, `_pick_period`; `app/accounting/journal.py:build_journal_entry` | `ngay_lap` is optional and validation does not flag it. Missing/unparseable values become `None`, for which `_pick_period` selects the latest rule period; an out-of-range early date selects the earliest period. | AP mapping and statutory thresholds can be applied without a verified effective document date, and this condition does not itself set `needs_review`. | Reject or explicitly flag missing/invalid/out-of-coverage invoice dates before statutory mapping; add date-boundary tests. | No |

## Test evidence and gaps

| Evidence | State | Notes |
|---|---|---|
| `tests/test_invoice_parser.py`, `test_journal.py`, `test_ap_gate.py`, `test_ap_golden.py`, and `test_accounting_rules.py` cover Decimal parsing, balance, source-number coverage, account postability, fixtures, and selected VAT/TSCĐ flags. | Read only; not executed | No test covers a missing/malformed effective date in the journal path. |
| `tests/test_ap_service.py` verifies one single-department AP draft and its audit. | Read only; not executed | It does not cover duplicate submission or zero/multiple department scopes. |
| `tests/test_draft_queue.py` and `test_draft_leak_probe.py` exercise helper predicates and scope resolution. | Read only; not executed | They do not call `approve_draft`/`reject_draft` against a foreign department or generic `POST /drafts`. |
| `tests/test_tax.py` and `test_anomaly.py` exercise deterministic fixture engines. | Read only; not executed | No route test proves demo recommendations cannot be approved as operational workflow records. |
| Expected focused command | `pytest -q tests/test_invoice_parser.py tests/test_journal.py tests/test_ap_service.py tests/test_ap_gate.py tests/test_ap_golden.py tests/test_accounting_rules.py tests/test_draft_queue.py tests/test_draft_leak_probe.py tests/test_tax.py tests/test_anomaly.py` | Not run: host Python/pytest unavailable. |

## Missing context and handoff

| Area | State | Required follow-up |
|---|---|---|
| PO/receipt/QC/vendor/payment lineage and support escalation | NEED FILE/CONTEXT | Provide upstream BRAVO ERP/API workflow evidence if it is meant to gate this Copilot’s AP draft flow. |
| Approval policy for `needs_review` / `validation_flags` | NEED FILE/CONTEXT | Confirm whether explicit override evidence is required or maker-checker approval alone is the intended control. |
| Production invoice/draft records and manual ERP import process | NEED FILE/CONTEXT | Needed to quantify duplicate and wrong-scope operational impact; no production access was requested. |
| T7 input | VERIFIED handoff | Test claims and gaps above, plus BRV-BIZ-001 through BRV-BIZ-006, should be mapped to evaluated enforcement layers. |

## T5 exit check

- Invoice, generic draft, agent draft, approval/rejection, export, tax, and anomaly state paths are mapped from code.
- Number, date, duplicate, scope, and provenance enforcement locations are distinguished from unimplemented/external lineage.
- Six evidence-backed findings are recorded; four require Sol review for financial, tenant/RLS, or approval-boundary decisions.
- No production code, configuration, migration, or test was changed.
