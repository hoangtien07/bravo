# Secondary-case synthetic API examples

Status: `DEVELOPER EXAMPLES — NOT SME TRUTH OR PRODUCTION DATA`

These typed examples are the design input for the bounded secondary cases. They contain no live
BRAVO identifiers, no customer data, and authorize no mutation.

## Voucher Evidence Review input

```json
{
  "invoice_total": "1100000",
  "invoice_tax": "100000",
  "invoice_net": "1000000",
  "po_amount": "1100000",
  "received": true,
  "bravo_document_id": "synthetic-draft-voucher-001",
  "duplicate_document_ids": []
}
```

The deterministic result is a list of `{check_id, status, reason_code}`. Status is `pass`,
`fail`, or `abstain`; missing PO/receipt and missing BRAVO draft produce `abstain`. No result
posts a voucher, writes a ledger, or approves an accounting action.

## Period Close Readiness input

```json
{
  "prerequisites": [
    {"prerequisite_id": "bank-reconciliation", "required": true, "status": "complete", "evidence_fresh": true}
  ],
  "reconciliations": [
    {"case_id": "case_12345678", "status": "reviewed", "material": true}
  ]
}
```

The view exposes `{ready, blocker_ids, reason_codes, execution}`. A required pending/stale item or
material unresolved/missing reconciliation makes `ready=false`. The execution label is always:
`readiness artifact produced; BRAVO did not execute close, calculations, reports, or period lock.`

## Design states

| State | Required UI behavior |
|---|---|
| `pass` / `ready=true` | Explain evidence and rule references; do not display “executed”. |
| `fail` / `ready=false` | Render every blocker and reason; no completion shortcut. |
| `abstain` | Name the missing evidence and safe next action. |
| missing/stale/superseded | Block unsupported recommendation and request refresh/review. |
