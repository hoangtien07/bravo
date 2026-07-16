# Consultant Intelligence implementation status

**Updated:** 2026-07-15  
**Deployment:** local Docker only; `CONSULTANT_ENABLED=true`; external expert is disabled.

This document records implementation evidence separately from gates that require product,
security, and SME approval. It does not promote synthetic fixtures or external-model output to
BRAVO truth.

## Phase 0 — baseline and evaluation

- Implemented: `app/eval/consultant_benchmark.py` and a synthetic, replayable fixture with
  30 trajectories / 120 declared structural variants in
  `app/eval/consultant_benchmark.example.yaml`.
- Evidence: structural replay report at `artifacts/consultant-baseline-structural.json`.
- Pending confirmation: 30–50 redacted real conversations, 2-SME calibration, and the TMS
  threshold. Synthetic results are a contract test, not a quality score.
- `app/eval/consultant_replay.py` can run a no-customer-data A/B replay against the local API;
  it stores only task identifiers, typed workflow state, HTTP status and latency—not answer text
  or credentials. Blind SME judgement remains required for TMS.
- Local replay evidence (2026-07-15): 30 synthetic cases / 60 legacy-consultant runs all returned
  HTTP 200; consultant state matched a known workflow in 29 routed cases, while legacy deliberately
  has no typed workflow state; observed p95 end-to-end latency was 7,864 ms. This is an operational
  baseline only, **not** a claim of task quality or a TMS gate pass.
- Local knowledge readiness audit (2026-07-15): PASS with 72 manifest-declared sources, 10
  lifecycle golden items and nine product use cases. It intentionally leaves 12 files under
  `file_system/Data/` outside shared RAG as private-operational data; no customer/demo sample was
  promoted. Two explicit future-corpus gaps remain: verified support tickets/KEDB and approved
  legal-standard sources.
- Implemented a human-only SME review contract in `app/eval/consultant_sme_review.py`. It validates
  the weighted task rubric, makes harmful actions hard failures, and reports reviewer overlap and
  Cohen's kappa without retaining raw responses. The supplied example is synthetic only.

## Phase 1 — domain goal and workflow

- Implemented: typed `GoalFrame`, `TaskState`, `GoalCard`, `WorkflowCard`, node prerequisites,
  risk classes, and a validated catalog of ten workflows in
  `file_system/bravo_consultant_cards.yaml`.
- Core workflows have detailed node/retrieval contracts: financial close/BCTC, AP invoice, and
  report discrepancy. The remaining seven workflows are deliberately thin scaffolds awaiting
  SME authoring; they are not claimed as verified BRAVO procedures.
- Workflow cards now carry an explicit assurance state (`scaffold`, `sme_reviewed`, `verified`).
  A verified card must include evidence references; an SME-reviewed card must name its reviewer.
  The state is included in the prompt/context manifest so a planning scaffold cannot silently
  become an asserted BRAVO procedure. The chat workflow strip also shows this assurance state to
  the caller (`Khung quy trình`, `Đã SME review`, or `Đã xác minh`).

## Phase 2 — context, conversation, and memory

- Implemented: one conversation owner persists typed task state in the existing `memory_blocks`
  store, applies period/version/correction/pause/resume updates deterministically, and supplies
  only a compact workflow contract to the model.
- A true workflow/goal switch now starts a new bounded task epoch and clears prior task facts
  rather than silently mixing accounting and technical state. Explicit negative corrections
  (for example, a step is *not yet* posted/reconciled/closed) rewind the derived milestone;
  correction parsing also preserves a known year when the user corrects only the month. Pause
  detection is limited to explicit stop commands, so ordinary wording such as "đang dùng BRAVO
  10" cannot pause a task.
- Added caller-owned state inspection at `GET /api/consultant/state/{conversation_id}`.
- Implemented an opt-in lifecycle mechanism for the **Consultant task-state block only**. It is
  disabled by default and cannot affect generic chat history, attachments, archival memory,
  evidence, or an active conversation. When a data owner approves a duration, the daily worker
  purges only inactive task-state blocks beyond that duration. The retention duration, backup/
  erasure semantics, and SME review of correction semantics remain pending confirmation.

## Phase 3 — retrieval, tools, and approval

- Implemented: plan-node query hints are appended after the user query, context manifests are
  stored on the durable run checkpoint, and a deterministic critic records/corrects a jump to a
  financial report before the active close prerequisite or a false execution claim for U3/U4.
  U3/U4 requests are draft-only. Existing RLS, read-tool, draft approval, and durable execution
  controls remain the authority for any side effect.
- Pending confirmation: schema snapshot tool, KEDB corpus, and action-map evidence for exact
  BRAVO navigation. The assistant must label those facts as version/configuration dependent.
- Implemented foundation: `/api/consultant/schema-snapshots` accepts metadata-only snapshots and
  `/schema-lookup` returns only verified records; `/kedb` candidate entries require explicit
  verification before `/kedb/search` can return a resolution. Empty evidence produces a typed
  gap (`missing_schema`/`missing_kedb`), not a guessed fact.

## Phase 4 — external expert and autonomous jobs

- Implemented: privacy-minimised gap records, migrations `0013`/`0014`, an admin-only gap
  dashboard, and a curation job that creates `review_required` candidates only. An admin can
  approve/reject a candidate with an audit note, but approval does **not** activate/index it.
- Autonomous curation now routes typed gaps to the correct review artifact: workflow card,
  schema-snapshot request, diagnostic/KEDB card, environment-profile request, or action map.
- Added an opt-in hourly ARQ curation job. Its default is disabled; when enabled it clusters only
  privacy-minimised internal gaps into `review_required` candidates. It has no external-provider
  path and cannot activate/index knowledge, so promotion remains a human evidence gate. Open gap
  rows are claimed with `FOR UPDATE SKIP LOCKED`, preventing duplicate candidates if the manual
  admin action overlaps the scheduler.
- `ExternalExpertGateway` is intentionally disabled. No hidden BravoGen fallback, account/token
  rotation, raw-response publishing, or production knowledge promotion exists.
- Pending confirmation: official provider authorization/ToS, DLP scope, cost/quota, redaction
  tests, shadow lift, and knowledge-owner approval. Only then may a provider adapter be enabled.

## Phase 5 — integration and operations

- Implemented: feature flag (`CONSULTANT_ENABLED`), stable per-conversation percentage rollout
  (`CONSULTANT_ROLLOUT_PERCENT`), config-versioned durable checkpoint manifest, Docker migration,
  health/OpenAPI smoke checks, and component-level fallback: a consultant-state failure falls back
  to the existing safe chat path. Both chat UI variants show a caller-scoped "Lộ trình đang xử
  lý" strip with the selected workflow, active node, and the first blocking clarification when
  applicable; it is observational and cannot alter tools, RLS, or approval.
- The chat composer exposes three usable policy profiles: `Tự động`, `Hướng dẫn BRAVO`, and
  `Triển khai & kỹ thuật`. A selection scopes retrieval before search and changes the consultant
  answer contract; it is not a model switch and cannot bypass the global kill switch, RLS, tool
  policy, egress, or approval. The ISMS profile remains hidden because no approved ISMS corpus
  exists; the API exposes it as unavailable rather than pretending it knows policy.
- Rollback: set `CONSULTANT_ENABLED=false` and restart `api`/`worker`; this does not affect the
  existing knowledge, RLS, approval, or legacy chat path. External gateway remains independently
  off.
- Dogfood users can flag a routed workflow as `wrong_goal` or `wrong_step` from the workflow
  strip. The endpoint writes only the typed workflow/node/task-epoch signal to the governed gap
  queue; it neither duplicates transcript/answer text nor changes active knowledge. Curation,
  when explicitly enabled, can only make a review-required candidate.
- Pending confirmation: shadow/dogfood sample size, SLO budget, on-call owners, and canary TMS
  acceptance gate. Do not declare production-default rollout before those gates are evidenced.
- Added a fail-closed, human-owned release-gate artifact and evaluator
  (`app/eval/consultant_release_gates.py`). A gate marked `passed` needs a named owner and an
  evidence reference; the provided example intentionally leaves all production-critical gates
  pending. The tool does not convert a green CI run, a synthetic replay, or an external answer
  into approval.

## Commands

```powershell
.venv\Scripts\python.exe -m app.eval.consultant_benchmark --out artifacts\consultant-baseline-structural.json
.venv\Scripts\python.exe -m app.eval.consultant_sme_review app\eval\consultant_sme_review.example.yaml
.venv\Scripts\python.exe -m app.eval.consultant_release_gates app\eval\consultant_release_gates.example.yaml --require-ready
docker compose exec -T api alembic upgrade head
docker compose ps
```
