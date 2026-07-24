# WP-00 baseline evidence

Status: `BASELINE RECORDED — containment remains a release gate`
Recorded: `2026-07-20T16:01:33+07:00`
Agent: Codex

## Repository baseline

- Branch: `feat/v2-p0-containment`
- Commit: `f17d31c079f8de71f0ffc303495f3176eef59d23`
- User-owned/untracked content preserved:
  - `FigmaMake_UI/`
  - `docs/reviews/FIGMA-MAKE-FRONTIER-PRODUCT-AUDIT-2026-07-20.md`
  - `plan-rebuild/09-FRONTEND-FIGMA-MAKE-CUTOVER-EXECUTION-PLAN.md`
- Source had no tracked diff before this evidence record was added.
- No `.env`, credential value, token, or customer payload was read or emitted while collecting
  this evidence.

## Runtime and migration baseline

- Host Node: `v24.16.0`
- npm: `11.13.0`
- pnpm: `11.15.1`
- Project virtual-environment Python: `3.12.13`
- Command: `.\\.venv\\Scripts\\alembic.exe heads`
- Result: `0017_native_rls_backstop (head)`

## Frontend baseline

Working directory: `frontend-react/`

| Command | Result |
|---|---|
| `npm.cmd run typecheck` | PASS |
| `npm.cmd test -- --run` | PASS — 3 files, 7 tests |
| `npm.cmd run build` | PASS — Vite 5.4.21, 4,860 modules |

Recorded build comparison points:

- eager CSS: `48.13 kB`, gzip `12.83 kB`;
- main application chunk: `131.61 kB`, gzip `37.17 kB`;
- React chunk: `162.61 kB`, gzip `53.07 kB`;
- assistant-ui chunk: `176.09 kB`, gzip `50.44 kB`;
- build warns about multiple chunks above `500 kB`, including Mermaid/Markdown/Cynefin;
- Vite reports an empty `katex` chunk.

These values are comparison evidence only. They are not a statement that the future WP-09 route
budget has passed.

## Prototype baseline

Working directory: `FigmaMake_UI/`

| Command | Result |
|---|---|
| `.\\node_modules\\.bin\\tsc.cmd --noEmit` | PASS |
| `pnpm.cmd run build` | PASS — Vite 8.0.3 |

Prototype build comparison points:

- CSS: `10.11 kB`, gzip `2.83 kB`;
- JS: `324.36 kB`, gzip `88.85 kB`.

The successful prototype build does not qualify `FigmaMake_UI` for production use.

## Frozen behavior diff guard

The guard is the Git tree listing at the baseline commit for:

- `app/agent/loop.py`
- `app/agent/bravo_playbooks.py`
- `app/agent/bravo_use_cases.py`
- `app/agent/turn_contract.py`
- `app/consultant/`
- `app/rag/knowledge_router.py`
- `app/rag/retriever.py`
- `app/rag/grounded_answer.py`
- `app/api/routes_agent.py`
- `app/api/routes_conversations.py`
- `file_system/bravo_consultant_cards.yaml`

Combined tree-list hash: `bcb4e4f9baebf875ad27602b68ea0560b4c4ea9f`.

Reproduction command:

```powershell
$guardPaths = @(
  'app/agent/loop.py',
  'app/agent/bravo_playbooks.py',
  'app/agent/bravo_use_cases.py',
  'app/agent/turn_contract.py',
  'app/consultant',
  'app/rag/knowledge_router.py',
  'app/rag/retriever.py',
  'app/rag/grounded_answer.py',
  'app/api/routes_agent.py',
  'app/api/routes_conversations.py',
  'file_system/bravo_consultant_cards.yaml'
)
git ls-tree -r f17d31c079f8de71f0ffc303495f3176eef59d23 -- $guardPaths |
  git hash-object --stdin
```

## Owner decision update — 2026-07-21

The project owner authorized local productization work in `FigmaMake_UI` while the frozen A/B
manifest and containment evidence remain open. This supersedes the earlier local-development stop,
but does not authorize staging, production traffic, cutover or release claims.

The candidate implementation target is now `FigmaMake_UI`. `frontend-react` was restored to the
recorded Git baseline and is retained unchanged as the classic comparator and rollback source.

## Open release evidence

The release evidence cannot be marked complete because the controlled frozen System A/B output locations, run
metadata, benchmark input checksums, and artifact checksums were not available in the workspace.
Creating `ab-baseline-manifest.json` without those values would fabricate evidence.

The required runtime/operator evidence directory and signed containment ledger are absent. Per the
updated execution plan, these items block staging, production and cutover, not local candidate FE
development.

## Next exact action

Begin FM-01 in `FigmaMake_UI` using the updated execution plan. In parallel, the project owner or
benchmark operator must provide the redacted controlled-artifact metadata/checksums and complete
the containment ledger before any staging or production cutover.
