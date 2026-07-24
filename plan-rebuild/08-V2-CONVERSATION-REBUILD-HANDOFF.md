# BRAVO V2 Conversation Rebuild — handoff plan

Status: `ACTIVE — P0 containment implementation verified; baseline freeze and Core V2 vertical slice not started`
Decision date: 2026-07-16  
Primary objective: produce conversations that are materially more useful, trustworthy, and
outcome-oriented than the current BRAVO implementation—not a cosmetic prompt/UI revision.

## 1. Why V2 is necessary

The current product has substantial platform machinery, but its conversation output is not useful
enough for the project owner. Consultant Intelligence adds workflow cards, state, retrieval hints,
and a critic, yet the final answer is still largely produced by the legacy free-text loop. Current
tests prove many structural contracts; they do not prove that users complete BRAVO work better or
that the answers outperform BravoGen on a controlled benchmark.

Verified continuation snapshot (2026-07-24):

- clean code baseline: `9cc4c91a45a56476428b2e7cddacccea9e0f355d` on
  `codex/v2-financial-close-core`; Alembic head: `0017_native_rls_backstop`;
- Python suite: 404 passed, 41 skipped; the focused P0 containment/evaluation contracts: 17
  passed, 5 skipped. These are code-level checks and do not replace real PostgreSQL/operator
  proofs;
- P0 owner authorization, answer-guard parity, state CAS/recovery, worker/credential checks and
  a ready-to-arm native-RLS backstop are implemented. Native RLS is still OFF and only covers the
  `chunks` read surface;
- A/B replay, C0 comparison and blind-SME/release-gate tooling exist, but no immutable matched
  A/B answer/trace artifact or full A/B/C/D evaluation has been captured;
- the clean framework-independent Conversation Core V2 package and Financial Close Advisor
  vertical slice have not been implemented. Existing Consultant cards and UI prototypes are not
  substitutes;
- frontend test/typecheck/build, effective production Compose, credential rotation, isolated
  restore and offline/egress proofs remain unverified.

V2 therefore starts from a product-quality failure statement: **the current conversation path is
not the implementation to keep extending**. Existing auth, RLS, evidence, audit, approval, draft,
artifact, and deployment services may be retained only behind explicit ports after verification.

### Phase-demo topology decision (2026-07-24)

Keycloak/OIDC is excluded from the conversation-quality demo and its production-like Compose
topology. Do not combine `deploy/docker-compose.keycloak.yml` with this phase's deployment and do
not publish an OIDC/Keycloak ingress. The existing application identity and RLS shell is sufficient
for the bounded demo; complete SSO/OIDC productization is deferred until the conversation-quality
gate passes.

This decision reduces demo scope only. It does not weaken authorization, database isolation,
draft/approval, audit, offline/egress, credential, or network-ingress gates.

## 2. Product target and non-negotiable boundaries

V2 is a clean conversation core inside the existing trusted platform shell. It must be visibly
different in behavior:

1. Understand the user's real outcome before choosing a workflow or composing an answer.
2. Model business/technical prerequisites explicitly; do not reduce them to prompt instructions.
3. Plan evidence and distinguish supplied, inferred, verified, conflicting, and missing facts.
4. Give a natural answer organized around the next useful action, verification, uncertainty, and
   one high-information clarification when necessary.
5. Preserve corrections, cancellation, task switches, and environment/version scope across turns.
6. Fail closed on exact schema, version, financial, execution, and approval claims.
7. Demonstrate improvement with blind user/SME evidence, not architecture diagrams or synthetic
   route tests.

The four project invariants remain: database-enforced authorization, non-invasive/draft-first
actions, no unsupported financial numbers, and an offline-capable path with controlled cloud
egress. V2 does not authorize automatic SQL/config execution, a full platform rewrite,
multi-agent production orchestration, Graphiti/Temporal/ZenML in the online path, or an IDE
extension before the headless core works.

## 3. Immediate blockers before V2 implementation

### Security and operations containment

- Revoke and rotate the provider credential exposed through local Compose rendering; never copy
  its value into this repository or another conversation.
- Fix effective phase-demo Compose so only 80/443 are published. Exclude the Keycloak/OIDC
  overlay, remove default Postgres credentials, authenticate Redis, and keep
  observability/admin ports internal.
- Add Conversation owner authorization to the legacy `/api/agent/ask` path before any memory read,
  state mutation, or model call.
- Do not use real/private customer data with the current cloud-only configuration without explicit
  data-owner/DPA approval. Align API and worker boot/egress policy.
- Extend backup/restore to private operational data and prove recovery with an isolated drill.

### Correctness containment

- Route sync, SSE, and alternate runtime answers through one final-answer safety/grounding guard.
  The current SSE path can bypass the Consultant critic.
- Make conversation/task-state updates atomic with expected revision/CAS or row locking. Perform
  idempotency detection before reconciliation or side effects.
- Treat corrupt persisted state as an explicit failure/recovery event, not a silent empty task.
- Define atomic, audited state transitions for candidate, schema, and KEDB review records.
- Verify native database isolation/RLS with separate runtime roles and negative probes across HTTP,
  MCP, and worker paths.

No new product feature or broad Consultant workflow expansion starts until these blockers have
tests and runtime evidence.

## 4. V2 implementation sequence

### Phase A — freeze an auditable baseline

1. **Complete:** named code baseline is clean at `9cc4c91`; do not add prompt/routing/retrieval or
   synthesis changes before answer capture.
2. **Open:** record dependency-lock hashes, redacted config, corpus manifest version and effective
   Compose output in a controlled evidence artifact. Never render or copy secret values.
3. **Open:** run `0012 -> head` migration tests on a clean database, downgrade/upgrade verification,
   all security-critical DB integration tests without skip, and frontend test/typecheck/build.
4. **Open:** freeze legacy System A and current Consultant System B outputs before changing prompts,
   retrieval, routing, or synthesis.

### Phase B — build the clean Conversation Core v2

Create a framework-independent domain package with these minimum contracts:

- `TaskBrief`: outcome, task/profile, environment, constraints, risk, known/missing facts;
- `PrerequisitePlan`: required business/technical nodes, alternatives, completion evidence;
- `EvidencePlan` and `EvidenceBundle`: claims to ground, source scope, version/environment, gaps;
- `ConversationState`: task epoch, correction/cancellation state, bounded facts, expected revision;
- `AnswerDraft` and `CriticReport`: claims, next actions, uncertainty, unsupported/risky findings;
- `StateDelta`: validated transition proposed for atomic persistence.

The domain package must run without FastAPI, SQLAlchemy, Postgres, vector DB, browser, or a live
LLM. Runtime, retrieval, state, tools, audit, and approval connect through narrow ports. Framework
objects and opaque checkpoints must not become domain truth.

Implement only one deep vertical slice: **Financial Close Advisor**. It must cover goal discovery,
period/environment scope, posting/reconciliation/closing prerequisites, evidence gaps, safe report
readiness, corrections, pause/cancel, and handoff. Other Consultant workflows remain frozen.

### Phase C — rebuild evidence and evaluation

1. Audit corpus owner, BRAVO version, approval status, and effective date per source. B8R4 material
   must not inherit B10R1-approved status by default.
2. Assemble a Financial Close evidence pack with reviewed workflow nodes, exact-claim sources,
   known gaps, and must-not claims.
3. Freeze six development anchors and the 24-trajectory/66-turn manifest, then add 30–50 redacted
   real-pattern conversations plus an SME-held-out set not visible during implementation.
4. Run A/B/C/D blind evaluation: legacy, current Consultant, Core v2, and BravoGen. A/B/C use the
   same model/version, token budget, prompt input, environment facts, and frozen EvidenceBundle.
5. Run ablations for model strength, retrieval/evidence, prerequisite planner, critic, and
   multi-turn state so the source of improvement is identifiable.

### Phase D — decision and rollout

Adopt Core v2 behind the existing API/security shell only when the complete gate below passes.
Route a small, stable canary cohort to V2 while preserving rollback to the frozen baseline. Use one
canonical chat surface for the wedge; hide/defer graph, anomaly, tax, and unrelated feature entry
points during dogfood. Engineering Workbench remains a separately gated headless experiment and
must not be used as proof of conversation quality.

## 5. Acceptance and stop gates

### Conversation quality gate

- at least two calibrated SMEs and blind randomized outputs;
- Core v2 wins at least 60% of non-tied C-vs-BravoGen comparisons, with the lower confidence bound
  above 50% before any external “better” claim;
- critical prerequisite recall at least 90%;
- multi-turn correction fidelity at least 95%;
- zero unsafe execution claims and zero fabricated exact schema/version facts;
- no major regression in any evaluated family;
- held-out real-pattern task success and time-to-correct-next-action materially improve over B.

### Platform/release gate

- effective production network publishes only approved ingress;
- no default/exposed credentials and the exposed provider credential has been rotated;
- owner isolation and two-user/two-department RLS probes pass through HTTP, MCP, and worker;
- clean migrations, backend integration tests, frontend CI, and rollback pass from one immutable
  baseline;
- backup includes DB, uploads, and private operational data; isolated restore evidence exists;
- cold-host, zero-egress air-gap smoke succeeds before claiming on-prem readiness;
- release-gate evidence references are machine-checked for existence and measured thresholds.

If C improves only with a stronger model, choose a model upgrade. If only oracle evidence improves
quality, fix corpus/retrieval. If planner/critic/state ablations cause the improvement to disappear,
the V2 architecture is causal. If C does not clear the complete gate, keep B as fallback, document
the failure clusters, and do not expand V2 by adding frameworks or features.

## 6. Handoff instructions for the next conversation

Read in this order:

1. `docs/PROJECT-STATE.md` and `docs/AI-REVIEW-MANIFEST.md`;
2. this document;
3. `plan-rebuild/04-WORKSPACE-REPO-COUNCIL-DECISION.md`;
4. `plan-rebuild/07-CONVERSATION-INTELLIGENCE-BRAVOGEN-BENCHMARK.md`;
5. `plan-rebuild/05-BRAVO-ENGINEERING-WORKBENCH-CONTRACT.md` and
   `plan-rebuild/06-RESEARCH-AND-IMPLEMENTATION-ROUNDS.md` only for shared contracts and gates.

The next conversation should begin with the open operational containment proofs and immutable A/B
baseline capture, not prompt tuning or feature implementation. It must preserve unrelated user
changes and must not repeat or display any local secret.
