# DEMO18-09 packaging and rollback evidence

Status: `RUNTIME PASS — local synthetic internal-demo packaging only`

Date: 2026-08-03

## Launcher and reset

- [demo18-launch.ps1](../../scripts/demo18-launch.ps1) starts the explicit synthetic overlay,
  waits for API health, prints the applied Alembic revision, and re-seeds the least-privilege demo
  identities without logging secret values.
- [demo18-reset.ps1](../../scripts/demo18-reset.ps1) is deliberately non-destructive: it only
  idempotently re-seeds identities/capabilities. It does not delete conversations, cases, uploads,
  volumes, or unrelated local/customer data.
- [RUNBOOK-DEMO18-LOCAL-SYNTHETIC.md](../../docs/RUNBOOK-DEMO18-LOCAL-SYNTHETIC.md) records start,
  stop, health, boundary and rollback instructions.

## Build identities

Both artifacts were built from the current workspace on 2026-08-03. A bundle tree hash is SHA-256
of newline-joined, sorted `relative-path SHA-256(file)` rows.

| Artifact | Build gate | Bundle tree SHA-256 | Lockfile SHA-256 |
|---|---|---|---|
| FigmaMake candidate | `pnpm run typecheck`, `test`, `test:a11y`, `build` | `3fe11615ee477bc8ef285eed16459bb953c0ea31dbda272e344b23695fdad648` | `d659c65eabb6e9da7f523ead0ffdce2c367aaa06428d04fcef488181b8c3fb03` |
| Read-only classic comparator | `npm run typecheck`, `test`, `build` | `9ba471537adfa747a76f4e1be625b25f20d9a29c0dfb02af2ce427256e64c1fa` | `b06ea86f13e3903d1262f21c1a9150fc643efb3efd747dc633e2ad361ac53030` |

Candidate Vitest result: `22 passed` across `7` files. Candidate axe gate: `1 passed`.
Comparator result: `13 passed` across `6` files. Its build emits known large-chunk warnings and
React Router future-flag warnings; neither was changed in this work.

## Rollback selection

The classic comparator remains read-only. To roll back the local presenter, stop the FigmaMake
Vite process and run the comparator's existing development/build command. Do not copy session,
fixture, or source state between frontends. Production cutover remains disabled.

## Technical rehearsal and final visual evidence

The credential-isolated browser rehearsal in [DEMO18-08-LIVE-BROWSER-2026-08-03.md](DEMO18-08-LIVE-BROWSER-2026-08-03.md)
completed in `24.7s`: live Chat POST-SSE/durable reload/attachment/citation/share plus all three
maker → independent reviewer → non-executing export lifecycles. It also generated the final 4×2
responsive light/dark visual matrix. This is a repeatable technical rehearsal, not an owner
acceptance. Owner evaluation remains pending.

The bounded completion packet is [DEMO18-FINAL-PACKET-2026-08-03.md](DEMO18-FINAL-PACKET-2026-08-03.md).
