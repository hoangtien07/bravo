# DEMO18-05/06 live three-AccountingCase lifecycle evidence

Status: `RUNTIME PASS — local synthetic demo only`

Date: 2026-08-03

## Runtime profile

The API was rebuilt and started through the explicit synthetic-only overlay:

```powershell
$env:BRAVO_POSTGRES_HOST_PORT='55432'
docker compose -f docker-compose.yml -f docker-compose.override.yml -f docker-compose.demo18.yml up -d api
```

The overlay enables `ACCOUNTING_CASE_V2_ENABLED` only with the versioned synthetic manifest `file_system/core_v2_synthetic_demo.yaml`. It does not enable a production or real-data route. The API reached `Application startup complete`; the idempotent demo seed was run in the container.

## Authoritative probe

`PYTHONPATH=. python scripts/demo18_case_lifecycle_probe.py` ran inside the live API container. It authenticated the non-admin maker and reviewer without logging a credential or token. For each case it performed maker create → attach frozen evidence → checks; a different reviewer performed review → non-executing export. The probe also attempted a stale check and self-review.

```json
{"bank_reconciliation":{"state_after_checks":"NEEDS_REVIEW","state_after_export":"EXPORTED","stale_rejected":true,"maker_review_rejected":true,"artifact_non_executing":true},"voucher_evidence_review":{"state_after_checks":"NEEDS_REVIEW","state_after_export":"EXPORTED","stale_rejected":true,"maker_review_rejected":true,"artifact_non_executing":true},"period_close_readiness":{"state_after_checks":"NEEDS_REVIEW","state_after_export":"EXPORTED","stale_rejected":true,"maker_review_rejected":true,"artifact_non_executing":true}}
```

This is direct local API evidence for three durable synthetic lifecycles, revision and maker-checker controls, and artifact non-execution. It does **not** prove a browser walkthrough, pilot readiness, customer-data authorization, SME correctness, production readiness, or ERP execution.
