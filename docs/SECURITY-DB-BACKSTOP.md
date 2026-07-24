# Native RLS backstop — operator cutover (P0.6)

Status: `READY-TO-ARM — OFF by default`
Last updated: 2026-07-19

## What this is

Defense-in-depth (layer #2) for invariant #1. The enforced path today is layer #1: the
application-composed `WHERE` clauses in [app/security/rls.py](../app/security/rls.py), applied in
every retrieval query and covered by tests. This backstop adds **native Postgres row-level-security
policies** so that a future forgotten `.where()` still cannot leak cross-department chunks.

- Policy: migration [0017_native_rls_backstop](../alembic/versions/0017_native_rls_backstop.py),
  on `chunks`, mirroring `chunk_scope_filter`. Created **inert** (RLS not enabled).
- Per-request GUCs: [app/security/native_rls.py](../app/security/native_rls.py), stamped in
  `get_current_identity` when `native_rls_enabled=true`.
- Proof it works when armed: [tests/test_native_rls_backstop.py](../tests/test_native_rls_backstop.py).

## Why it is OFF by default (the load-bearing caveat)

The runtime currently connects as the Postgres **owner/superuser** (`bravo`). A superuser
**bypasses RLS entirely — even `FORCE ROW LEVEL SECURITY`.** So arming RLS without first moving the
runtime to a dedicated **non-owner, NOSUPERUSER, non-BYPASSRLS** login role is a no-op. Arming it
while the app is NOT setting the GUCs (or is still the owner) risks either no protection or, once a
non-owner role is used, denying every row. That cutover needs a maintenance window and verification,
so it is a deliberate operator step, not a default.

## Cutover procedure (run with a maintenance window)

1. Create a dedicated login role and grant least privilege (adjust table list to the armed set):
   ```sql
   CREATE ROLE bravo_app LOGIN PASSWORD '<strong-secret>' NOSUPERUSER NOBYPASSRLS;
   GRANT CONNECT ON DATABASE bravo TO bravo_app;
   GRANT USAGE ON SCHEMA public TO bravo_app;
   GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO bravo_app;
   GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO bravo_app;
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO bravo_app;
   ```
2. Point `DATABASE_URL` at `bravo_app` (not the owner). Keep migrations running as the owner.
3. Set `NATIVE_RLS_ENABLED=true` so each request stamps `bravo.employee_id / bravo.dept_ids /
   bravo.doc_read_level`.
4. Arm RLS on the policy's table(s):
   ```sql
   ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;
   ALTER TABLE chunks FORCE ROW LEVEL SECURITY;
   ```
5. Verify with a two-department negative probe (HTTP + MCP + worker) that a user cannot retrieve
   another department's chunk, and that normal retrieval still returns own-dept + global rows.
6. Rollback if needed: `ALTER TABLE chunks NO FORCE / DISABLE ROW LEVEL SECURITY;` and
   `NATIVE_RLS_ENABLED=false`; repoint `DATABASE_URL` to the owner.

## Cutover preflight

Run this command with the **non-owner runtime** `DATABASE_URL` after enabling the policy and
before admitting traffic. It reads PostgreSQL catalogs only and exits non-zero if the runtime is a
superuser, has `BYPASSRLS`, owns `chunks`, lacks `FORCE ROW LEVEL SECURITY`, lacks the policy, or
has not enabled the application GUC stamping:

```bash
NATIVE_RLS_ENABLED=true python scripts/verify_native_rls_cutover.py
```

The ingestion worker needs a separately reviewed write role before native RLS is armed: migration
0017 supplies a `SELECT` policy for `chunks`, not a blanket writer bypass. Do not reuse the
owner/migrator role for API, MCP, or worker processes.

## Follow-up (not in 0017)

Extend the backstop to `sources` (join table `source_departments`), `conversations`
(owner-scoped), and `memory_blocks` (session-scoped) with their own policies. Layer #1 covers these
today; add them before relying on native RLS as the sole control anywhere.
