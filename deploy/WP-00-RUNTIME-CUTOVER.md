# WP-00 runtime containment cutover

This runbook arms the existing `chunks` native-RLS policy for the API/MCP process. It is a
synthetic-demo containment proof, not production or pilot approval.

## Preconditions

- Worktree and baseline commit are recorded.
- Provider credential rotation is complete in the provider/secret-manager control plane.
- Deployment secrets exist outside Git: strong Postgres and Redis credentials, API and worker
  non-owner DSNs, and any approved provider credentials.
- The database owner/migrator connection is available only to the operator.

Do not copy an existing `.env`, print it, or run `deploy/gen-secrets.sh --force` over it. The
cutover overlay reads `BRAVO_API_DATABASE_URL` and `BRAVO_WORKER_DATABASE_URL` from the deployment
secret source; neither value may be committed or included in command output.

## Procedure

1. Run `deploy/runtime-roles.sql` as the migrator/owner, then create the two LOGIN roles with
   passwords supplied directly from the secret manager. Do not grant either role ownership,
   `SUPERUSER`, or `BYPASSRLS`.
2. Use an isolated/staging database to apply `0012 -> head`, downgrade/upgrade, and run the
   security-critical integration suite. Keep the existing data volume intact unless a separately
   approved backup and reset procedure exists.
3. Validate interpolation without rendering it:

   ```powershell
   docker compose -f docker-compose.yml -f docker-compose.prod.yml `
     -f deploy/docker-compose.rls-cutover.yml --env-file <deployment-secret-file> config --quiet
   ```

4. Start the same three Compose files. The overlay gives API/MCP the non-owner role and enables
   `NATIVE_RLS_ENABLED`; the worker uses its separate role with native RLS disabled until a
   reviewed `chunks` write policy exists.
5. During the approved maintenance window, enable and force native RLS on `chunks`, then run:

   ```powershell
   $env:NATIVE_RLS_ENABLED = 'true'
   .\.venv\Scripts\python.exe scripts/verify_native_rls_cutover.py
   ```

6. Seed only the deterministic synthetic A/B/global rows as the owner, then run all runtime paths
   as their non-owner roles. The output must be copied into a redacted evidence artifact; do not
   print DSNs or credentials.

   ```powershell
   $runId = [guid]::NewGuid().ToString()
   docker compose --project-name bravo-wp00 --env-file .env.wp00 `
     -f docker-compose.yml -f docker-compose.prod.yml run --rm --no-deps api `
     python scripts/wp00_runtime_probes.py --run-id $runId --mode seed --owner-database-env DATABASE_URL
   docker compose --project-name bravo-wp00 --env-file .env.wp00 `
     -f docker-compose.yml -f docker-compose.prod.yml -f deploy/docker-compose.rls-cutover.yml `
     exec -T api python scripts/wp00_runtime_probes.py --run-id $runId --mode api
   docker compose --project-name bravo-wp00 --env-file .env.wp00 `
     -f docker-compose.yml -f docker-compose.prod.yml -f deploy/docker-compose.rls-cutover.yml `
     exec -T worker python scripts/wp00_runtime_probes.py --run-id $runId --mode worker
   ```

7. Run backup integrity and restore only into a distinct project. The runner never deletes the
   source project or backup artifacts; teardown of the restore project is an explicit operation.

   ```powershell
   $backup = Join-Path $env:TEMP 'bravo-wp00-backup'
   python scripts/wp00_backup_restore.py backup --project bravo-wp00 --env-file .env.wp00 --output $backup
   python scripts/wp00_backup_restore.py verify --project bravo-wp00 --env-file .env.wp00 --output $backup --timestamp <timestamp>
   python scripts/wp00_backup_restore.py restore --project bravo-wp00 --target-project bravo-wp00-restore `
     --env-file .env.wp00 --output $backup --timestamp <timestamp> --evidence-out <redacted-json-path>
   ```

## A/B baseline

After runtime containment passes and the rotated credential is available, start the local service with the frozen synthetic fixture and
capture A/B using `app.eval.consultant_replay --persist-answers`. Freeze the captured replay with
`python -m app.eval.frozen_ab_baseline`; its required controls bind the fixture, evidence snapshot,
model/version and prompt hashes. Commit the new evidence directory before any prompt, routing,
retrieval or synthesis change.
