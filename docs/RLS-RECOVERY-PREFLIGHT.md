# RLS and recovery preflight

This checklist is an implementation aid, not production sign-off. It intentionally contains no
credentials and all included verification commands are read-only.

## Native RLS cutover

1. Use separate roles for runtime API/MCP, worker, migrator, backup, and break-glass operations.
   API and MCP must not connect as the table owner, superuser, or a `BYPASSRLS` role.
2. Enable `NATIVE_RLS_ENABLED=true`, then enable and force the `chunks` policy during an approved
   maintenance window.
3. With the runtime role's `DATABASE_URL`, run:

   ```bash
   NATIVE_RLS_ENABLED=true python scripts/verify_native_rls_cutover.py
   ```

4. Execute two-department negative probes through HTTP and MCP. Verify own-department and global
   reads still work. The worker needs its own reviewed write policy before native RLS is armed;
   migration 0017 currently protects the chunk read surface only.

## Recovery readiness

For a backup timestamp `<ts>`, verify the dump, uploads archive, and private operational-data
archive before the isolated restore drill:

```bash
bash scripts/verify_backup_artifact.sh /var/backups/bravo <ts>
```

The drill remains an operator action: restore only to an isolated target, measure the RTO, then
verify the restored policy/grant catalog and representative draft, audit, conversation, upload,
and private-data records. Keep the target offline if any check fails.
