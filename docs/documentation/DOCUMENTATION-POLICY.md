# Documentation policy

Status: `ACTIVE`  
Owner: project owner  
Last verified: 2026-07-16

## Purpose

Keep repository documentation useful to people and AI without treating historical plans,
research, or raw evidence as current implementation truth.

## Source precedence

When documents conflict, use this order:

1. current code, migrations, configuration, and reproducible test/runtime evidence;
2. `docs/PROJECT-STATE.md` for the current project snapshot;
3. accepted ADRs for architectural decisions;
4. active contracts/plans explicitly linked by `PROJECT-STATE.md`;
5. stable security/runbook/reference documentation;
6. historical reviews, research, work packages, and benchmark evidence.

A newer date alone does not override an accepted ADR or verified runtime evidence.

## Document roles

| Role | Meaning | Default AI context |
|---|---|---|
| `entrypoint` | Repository orientation or agent instruction | Yes |
| `current_state` | Current verified snapshot and open gates | Yes |
| `canonical` | Current contract/architecture for one topic | Yes, when relevant |
| `decision` | ADR or recorded owner decision | On demand |
| `active_plan` | Approved/in-progress work with exit gates | When reviewing that work |
| `runbook` | Operational/security procedure | When relevant |
| `reference` | Useful background that does not own current status | On demand |
| `evidence` | Research, review, raw benchmark, remediation history | No; open to verify claims |
| `domain_data` | Knowledge/corpus Markdown consumed as data | Never as project-status context |
| `superseded` | Replaced by another named document | No |
| `generated` | Prompt/upload/report derivative | No |

## Lifecycle vocabulary

- `proposed`: no owner acceptance yet;
- `accepted`: decision approved, implementation may still be absent;
- `in_progress`: implementation or evaluation is underway;
- `implemented`: code exists but required verification is incomplete;
- `verified`: named evidence proves the declared scope;
- `superseded`: another document owns the topic;
- `archived`: retained only for history.

Do not use `complete` without qualifying the scope, such as `research complete`,
`implementation complete`, or `verified complete`.

## Merge and deletion rules

Merge only when one canonical document can preserve all unique current information. Keep raw
evidence separate. Before deleting a Markdown file, all conditions must hold:

1. it is not an accepted ADR, security invariant, runbook, domain data, or raw evidence;
2. it contains no unique information needed to reproduce a decision;
3. replacement content and inbound links are verified;
4. code/scripts/tests do not reference it;
5. untracked content has a snapshot or explicit owner approval;
6. the approved cleanup manifest names the file and reason.

Prefer an in-place `superseded` banner when a file has inbound links. Prefer archive over delete
for reviews/research. Generated research inputs with no unique result may be deleted after owner
approval.

Files under any `archive/` directory are excluded from default AI context. They may be opened
only when a canonical/current document names a specific historical claim that needs provenance.

## Required metadata

Only current/canonical documents require a small status block: `Status`, `Owner`, and
`Last verified`. Evidence collections are classified centrally by path and do not need mass
header edits.

## Automated audit

Run:

```powershell
python scripts/audit_markdown_docs.py
```

The generated `MARKDOWN-INVENTORY.md` reports roles, conservative action signals, exact
duplicates, inbound links, and broken relative links. It never moves or deletes files.

## Review gate

Documentation is AI-review ready when:

- `PROJECT-STATE.md` matches the current Git/runtime/test evidence;
- `AI-REVIEW-MANIFEST.md` names a bounded default read set;
- active plans do not claim superseded readiness;
- broken actionable relative links are zero;
- delete/archive candidates are approved as explicit batches;
- the final inventory and Git diff are reviewed.
