# AccountingCase V2 API contract freeze — FEV2-01

Status: `FROZEN FOR LOCAL SYNTHETIC FIGMAMAKE INTEGRATION`

Date: 2026-08-02  
Scope: Plan 17 FEV2-01; local synthetic three-case demo only.

## Authority and boundary

This freeze reflects the existing FastAPI route implementation in
`app/api/routes_accounting_cases_v2.py` and the Core V2 contracts. It adds no backend endpoint,
does not enable a capability and does not authorize a live BRAVO, bank, posting, payment, close,
lock or report operation.

The browser renders server-owned scope, evidence, findings, revision and hashes. It never computes
an accounting verdict or sends `fixture:` identifiers to this API.

## Endpoints

| Method | Path | Request | Success response |
|---|---|---|---|
| `GET` | `/api/v2/accounting-cases` | — | `AccountingCaseView[]` |
| `POST` | `/api/v2/accounting-cases` | `CreateCaseInput` | `AccountingCaseView` (`201`) |
| `GET` | `/api/v2/accounting-cases/{case_id}` | — | `AccountingCaseView` |
| `POST` | `.../{case_id}/evidence` | `EvidenceInput` | `AccountingCaseView` |
| `POST` | `.../{case_id}/run-checks` | `MutationInput` | `AccountingCaseView` |
| `POST` | `.../{case_id}/review` | `ReviewInput` | `AccountingCaseView` |
| `POST` | `.../{case_id}/export` | `ExportInput` | `{ case: AccountingCaseView, artifact: object }` |
| `POST` | `.../{case_id}/conversation` | `{ question }` | read-only Bank explanation |

Voucher/Period preview routes are deliberately absent from the functional contract.

## Invariants carried in every mutation

- `expected_revision` comes from the last server response.
- One user intent owns one `idempotency_key`; a transport retry uses the exact same body/key.
- `review` carries current `draft_payload_hash`, `evidence_hash` and `result_hash` unchanged.
- `export` carries the server-approved `payload_hash`, `evidence_hash` and `review_hash` unchanged.
- A `409` stops the mutation, refetches the server state and requires a deliberate re-apply.
- A `403` is a permission boundary; a `404` may mean disabled capability; a `422` is invalid
  input/contract; none is a successful/empty case.

## Review decision hash vector

Canonical JSON must exactly equal:

```json
{"disposition":"resolved","evidence_snapshot_ids":["snapshot-1","snapshot-2"],"finding_id":"finding-001","note":"Evidence reviewed.","reason_code":"EVIDENCE_CONFIRMED","reviewer_id":"reviewer-42"}
```

UTF-8 SHA-256: `9af456f98d59e4e73a22d9e4f994bf0a13510f223ddf00f7fddce009446679e6`

`src/api/reviewDecisionHash.ts` and `src/test/accountingCases.test.ts` enforce this vector. A
different serializer, whitespace, key order or value changes the hash and the server rejects the
review decision.

## Runtime validation

`src/api/accountingCases.ts` rejects a successful HTTP response if required V2 fields, known case
types/states, evidence/result/finding shapes or the non-mutating conversation constraint do not
match this freeze. Unknown values are not silently styled as success.

