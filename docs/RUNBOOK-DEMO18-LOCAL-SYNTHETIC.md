# Plan 18 local synthetic internal-demo runbook

Status: `LOCAL SYNTHETIC INTERNAL DEMO ONLY`

## Start

From the repository root, run:

```powershell
./scripts/demo18-launch.ps1
```

The launcher starts Postgres, Redis and API through `docker-compose.demo18.yml`, waits for
`/health`, shows the applied Alembic revision, and idempotently seeds the demo identities. It then
starts the FigmaMake Vite candidate on `http://127.0.0.1:8443` unless a frontend already responds
there. It defaults the isolated local Postgres host port to `55432`; set
`BRAVO_POSTGRES_HOST_PORT` before launching only when another explicit local port is required.

The overlay explicitly sets only:

```text
ACCOUNTING_CASE_V2_ENABLED=true
ACCOUNTING_CASE_V2_DEMO_CONFIG=file_system/core_v2_synthetic_demo.yaml
```

It does not enable production data, ERP mutations, a pilot, or cloud egress.

## Reset and stop

`./scripts/demo18-reset.ps1` re-runs the idempotent synthetic identity/permission seed. It never
deletes conversations, cases, uploads, volumes, or unrelated local/customer data. Start with a
fresh isolated local stack if a completely blank dataset is required; do not use a volume delete as
an ordinary rehearsal step.

To stop services without deleting data:

```powershell
docker compose -f docker-compose.yml -f docker-compose.override.yml -f docker-compose.demo18.yml stop api redis postgres
```

The launcher prints the PID only when it started Vite; stop that process separately if necessary.

## Health checklist

1. `http://127.0.0.1:8000/health` returns `status: ok`.
2. The launch output shows `0020_case_v2_audit (head)`.
3. The seed output lists maker with AccountingCase read/create and reviewer with read/review; it
   never prints a credential value or token.
4. Normal UI navigation shows Knowledge Chat and authorized Accounting Work only. `?qa=1` remains
   the explicit fixture route.
5. Accounting export text says artifact produced, not posted, executed, or closed in BRAVO.

## Demonstration boundary and rollback

Show only synthetic local data. Do not claim conversation-quality superiority, blind SME approval,
customer-data authorization, pilot eligibility, production readiness, or ERP execution.

The rollback comparator is the read-only `frontend-react/` application. To return to the prior
candidate, stop the FigmaMake Vite process and run the documented comparator build; do not copy
state or source code between the two frontends. Bundle hashes and exact build commands are recorded
in the Plan 18 evidence packet when packaging verification is complete.
