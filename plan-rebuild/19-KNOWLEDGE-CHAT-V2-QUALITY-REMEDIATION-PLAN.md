# BRAVO Knowledge Chat V2 quality remediation plan

**Status:** Proposed implementation plan; no production-readiness claim

**Date:** 2026-08-18

**Standalone product amendment (2026-08-19):** Plan 20 and ADR-0035 retain this plan's
Conversation V2 intelligence contracts but supersede its residual `draft proposal`, write-tool and
future ERP-mutation wording for the current product. Active V2 outputs are read-only analysis,
review requests and artifacts over uploaded/governed evidence only.

**Baseline commit inspected:** `c7afe01d4a4fcfa7785e5e8d021449e5be6ac35c`

**Scope:** Knowledge Chat and its shared Conversation Core V2 contracts. Accounting Operations Hub
remains separately governed by ADR-0032/0033 and the three-case backlog.

**Depends on:** `08-V2-CONVERSATION-REBUILD-HANDOFF.md`,
`10-FRONTIER-BRAVO-ACCOUNTING-AGENT-PLAN.md`, ADR-0032 and ADR-0033.

**Decision rule:** contain critical legacy defects, but place substantive intelligence in a new,
framework-independent Conversation Core V2. Do not continue broad feature patching in
`app/agent/loop.py`.

## 1. Outcome

Build a Knowledge Chat path that is demonstrably more useful and more correct than both the frozen
legacy path and BravoGen on matched BRAVO tasks. The target is not a longer answer or a newer model.
It is a typed, evidence-aware conversation pipeline that:

1. preserves every user task and material fact;
2. retrieves the right BRAVO evidence without silently excluding relevant manuals;
3. performs accounting derivations in deterministic read-only code;
4. binds exact claims and citations to approved, version-compatible evidence;
5. validates tools, calculations and final output before release;
6. produces a reconstructable, privacy-safe trace; and
7. passes a frozen A/B/C/D evaluation and blind SME review.

The ten-transaction prompt that exposed the current problem becomes the first mandatory golden
anchor. It is not, by itself, enough to claim general conversational quality.

## 2. What the review established

### 2.1 Observed code/runtime defects

| Severity | Finding | Evidence in current repository/runtime | Consequence |
|---|---|---|---|
| P0 | Vietnamese `bằng` is folded to `bang`; substring `"bang "` is treated as a database-table signal | `app/rag/bravo_intent.py:26-36,70-84` | Ordinary accounting wording such as “bằng tiền mặt” can become `technical_design`. |
| P0 | The mistaken intent becomes a hard SQL metadata scope | `app/rag/knowledge_router.py:30-35,42-79`; `app/rag/retriever.py:71-84` | Relevant `documents`/user-guide evidence can be excluded even when already ingested. |
| P0 | Long prompts are intentionally rewritten without detailed numbers and then split into at most three retrieval queries | `app/agent/loop.py:909-960` | A ten-item task can lose amounts, subtransactions and evidence coverage before synthesis. |
| P0 | The decision contract has a free-text `answer` and generic `args` | `app/agent/loop.py:151-172` | There is no typed representation of task units, postings, calculations, claims, evidence or missing inputs. |
| P0 | Cloud “structured output” is JSON mode, not strict schema enforcement | `app/llm/router.py:164-182` | Syntactically valid but structurally wrong decisions remain possible; retry/parsing is compensating logic. |
| P0 | The number guard checks provenance of literal numbers but does not calculate | `app/rag/number_integrity.py` and final guard in `app/agent/loop.py:1698-1746` | Correct derived amounts such as 200/20/120 million are either model-owned or can be masked. |
| P0 | Frontier SDK canary streams final prose and only prunes citations | `app/agent/loop.py:1428-1511` | It bypasses the shared final critic/number/claim guard and cannot safely replace the legacy path. |
| P1 | Read-tool arguments are not validated against each tool's `json_schema` before invocation | `app/agent/tools.py:105-180` | Malformed or surplus arguments reach tool functions; failure is late and tool-specific. |
| P1 | Every permission-allowed tool is exposed to the model | `app/agent/loop.py:1142-1146` | Tool selection is noisier than a capability-scoped inventory and prompt size grows with the registry. |
| P1 | Context management only compresses history; it does not compile the complete prompt to a model-specific budget | `app/agent/memory.py:137-178`; `app/agent/context.py` | Retrieved evidence, attachments, tools, system blocks and output reserve are not governed as one context budget. |
| P1 | Consultant selects one workflow from substring counts; ties depend on catalog order | `app/consultant/catalog.py:35-43` | A multi-workflow accounting exercise can be labelled as an unrelated single workflow. |
| P1 | Durable run events are operational progress, not an end-to-end reasoning/evidence trace | `app/agent/runs.py:58-90` | A failure cannot be localized cleanly to decomposition, routing, retrieval, calculation, synthesis or verification. |
| P1 | Existing frozen A/B artifact does not prove Consultant behavior | `evidence/v2/ab/wp00-20260731/baseline.json` | All 30 System-B records have a null workflow id; 11 A/B answers are identical. The label alone is not evidence that B was active. |
| P2 | Normal chat still enters the legacy `AgentSession`; Core V2 is a separate accounting-case API | `app/api/routes_conversations.py` and `app/core_v2` | The completed case-core work does not automatically improve ordinary Knowledge Chat. |

The router defect was reproduced read-only with the full prompt: the knowledge turn was scoped to
`qa_testcase`/technical sources and modules that omitted `documents`. The runtime source inventory
reported Chapter 04 Documents as ready. This is therefore a routing failure, not proof of a missing
manual.

### 2.2 Repository-state caveats

The inspected worktree was already dirty: documentation, migration, corpus manifest, seed/test files
were modified; all `file_system/Mindmaps/*.md` files were deleted; and `tmp/` was untracked. These are
treated as user-owned changes. This plan does not infer that deleted files are absent from the
deployed database and does not restore, overwrite or commit them.

`pytest` could not be executed from the default interpreter because that interpreter does not have
pytest installed. The baseline Alembic head was not independently executed from this review.
Implementation WP-00 must resolve the intended environment and record both facts before changing
runtime behavior.

### 2.3 Accounting answer key for the first anchor

The SME-approved fixture must encode at least the following, using `Decimal` values and a declared
chart-of-accounts policy:

| Item | Deterministic result expected from the work-product engine |
|---|---|
| 1 | Nợ 111 / Có 112: 80,000,000 |
| 2 | If the bank lends and pays the vendor directly: Nợ 331 / Có loan account: 60,000,000. Use 3411 under the repository's TT99 policy; expose the legacy-311 ambiguity when a different curriculum is selected. |
| 3 | Nợ 111 / Có 131: 40,000,000 |
| 4 | Nợ loan account / Có 111: 15,000,000 |
| 5 | Nợ 156: 100,000,000; Nợ 1331: 10,000,000; Có 331: 110,000,000 |
| 6 | Nợ 331 / Có 112: 50,000,000 |
| 7 | Purchase: Nợ 156: 200,000,000; Nợ 1331: 20,000,000; Có 331: 220,000,000. Payment: Nợ 331 / Có 111: 100,000,000. Remaining payable: 120,000,000. |
| 8 | Nợ 211 / Có 4111: 500,000,000, plus the bounded BRAVO fixed-asset registration requirement when supported by the approved guide. |
| 9 | If salary payable was already recognized: Nợ 334 / Có 111: 10,000,000; otherwise name the missing accrual assumption. |
| 10 | Nợ 112 / Có 131: 35,000,000 |

BRAVO-specific navigation must use approved manual terminology. The current evidence supports
`Phiếu nhập mua`; it does not support presenting a generic `Hóa đơn mua hàng` screen or claiming
that a partial-payment field automatically creates the remaining payable without configuration
evidence.

## 3. Root-cause decision

The primary causes are code/logic and representation, followed by evaluation and corpus governance.
The frontend is not the primary cause. The model may affect fluency, but a model upgrade cannot
repair dropped task units, hard-excluded sources, absent arithmetic, generic tool arguments or a
bypassed final guard.

| Layer | Contribution | Decision |
|---|---|---|
| Routing/decomposition | Critical and reproduced | Fix immediately, then replace with typed V2 stages. |
| Domain/accounting logic | Critical | Add a bounded deterministic read-only engine and SME fixtures. |
| Retrieval/evidence policy | High | Replace irreversible keyword scopes with auditable evidence plans and recovery. |
| Synthesis/verification | High | Generate typed claims/work products, verify, then render prose. |
| Eval/observability | High | Freeze real arms and persist stage traces before optimization. |
| Corpus | Material but not the direct cause in this case | Govern version/approval/coverage; do not use corpus work to hide router defects. |
| Model/runtime | Unproven lever | Evaluate as an adapter/ablation after core correctness gates. |
| Frontend | Presentation only for this defect | Do not schedule a UI rewrite as remediation. |

## 4. Target architecture

Create `app/conversation_v2/` as a framework-independent application/domain package. It may call the
existing secure platform shell and `app/core_v2` through explicit ports; it must not import FastAPI,
an LLM SDK, SQLAlchemy models or SSE types into its domain contracts.

```text
API/SSE shell
    -> Turn intake + authorization context
    -> Task decomposition (lossless TaskUnit list)
    -> Capability/evidence planner
    -> Retrieval ports + source authority checks
    -> Deterministic accounting/read-only tool ports
    -> Typed answer plan and claim graph
    -> Claim/calculation/citation verifier
    -> Renderer
    -> Durable, redacted execution trace
```

Minimum contracts:

- `TurnEnvelope`: raw user input, attachment references, identity/scope references, locale and
  conversation revision. Raw current input is immutable for the turn.
- `TaskUnit`: stable id, ordinal, task type, original span, entities, amounts, assumptions,
  requested output and status. No top-level item may disappear silently.
- `EvidencePlan`: queries, required source classes/modules, authority/version requirements, fallback
  policy and expected coverage.
- `EvidenceRef`: source/chunk id, locator, version, approval/effective status, tenant scope, retrieval
  score and supported claim types.
- `AccountingWorkProduct`: postings, tax decomposition, settlement split, balances, assumptions and
  deterministic rule/calculation ids.
- `Claim`: exact text/value, claim type, supporting evidence/calculation ids, confidence class and
  unsupported reason. A numeric confidence score must never substitute for evidence.
- `AnswerPlan`: ordered task results, missing inputs, warnings, proposed read-only next actions or
  artifact requests and citations.
- `VerificationResult`: schema, coverage, debit/credit balance, exact-number provenance,
  claim-to-evidence entailment, version fit, permission and must-not-claim checks.
- `ExecutionTrace`: stage inputs represented by hashes/references, outputs, route alternatives,
  timings, model/runtime ids, token/cost data, tool outcomes and verifier decisions. Do not persist
  raw sensitive prompts solely for traceability.

Postgres remains the authoritative conversation/task state. Provider-managed response state may be
used only as an optional optimization with explicit retention/egress policy; it is never the source
of truth and must have a `store=false`/offline-equivalent path.

## 5. Retrieval and decomposition policy

### 5.1 Lossless decomposition

1. Parse explicit numbering, bullets, paragraphs and conjunctions into candidate `TaskUnit`s.
2. Preserve original spans, amounts and entities. Rephrased queries are derived retrieval views,
   never replacements for the user's request.
3. For large batches, retrieve per task family and merge evidence; do not cap coverage by keeping
   only the first three clauses.
4. Record `covered`, `missing_evidence`, `unsupported` or `needs_input` for every unit.
5. Ask one discriminating question only when it materially changes the result; otherwise state the
   bounded assumption per unit.

### 5.2 Accent-safe, reversible routing

- Keep both original Vietnamese and a folded search form.
- Use token/phrase boundaries and qualified concepts. `bảng B30BizDoc`, `bảng dữ liệu`, `table` and
  stored-procedure terms may indicate technical design; bare `bang` produced from `bằng` may not.
- Route output is a typed hypothesis with matched spans and reasons, not an opaque label.
- Use scoped search as a precision pass, not an irreversible truth. When required source classes or
  task coverage are missing, run a controlled broader recovery search under the same RLS.
- Multi-domain tasks may request a union such as Documents + Purchases + Accounting. Do not force a
  single lifecycle playbook to own the whole turn.
- Lifecycle/approval/version checks remain mandatory after retrieval. Broad fallback never weakens
  RLS or exact-claim authority.

## 6. Accounting and tool policy

### 6.1 Deterministic read-only accounting engine

Add a bounded engine for accounting exercise/work-product tasks. It is not an ERP posting engine.
It must:

- use `Decimal`, declared currency scale and explicit inclusive/exclusive VAT rules;
- calculate tax, net amount, paid amount and remaining payable;
- validate total debits equal total credits for every posting group;
- carry chart-of-accounts policy/version and surface unresolved account-policy differences;
- separate accounting truth from BRAVO navigation evidence;
- return calculation lineage and rule ids for every derived number;
- refuse or mark missing facts instead of guessing configuration-dependent BRAVO behavior; and
- expose read-only results only. A future connector or mutation is outside this product plan and
  requires a new owner ADR; it is not a dormant branch of Conversation V2.

### 6.2 Tool safety and relevance

- Validate model-produced arguments against the selected tool's strict schema before any tool
  function or artifact builder is invoked; reject unknown fields and invalid types.
- Define typed tool results and error categories. A caught Python exception is not a business
  validation contract.
- Compile a task-relevant tool set after authorization filtering; both filters are required.
- Preserve the current permission re-check, database RLS backstop and audit-attempt invariants.
  Compile only read-only tools for V2; Plan 20 WP20-02 removes legacy ERP/draft tools from the active
  product inventory.
- Add idempotency, timeout and retry policies per tool, with no unsafe retry for non-idempotent
  review or artifact transitions.

## 7. Synthesis, verification and streaming

The model produces an `AnswerPlan`/claim structure, not final unrestricted prose. Rendering occurs
only after deterministic verification.

Verification order:

1. schema and task-unit coverage;
2. authorization and source-scope checks;
3. accounting calculation and debit/credit checks;
4. exact-number lineage;
5. BRAVO version/configuration authority;
6. claim-to-evidence and citation binding;
7. must-not-claim and abstention checks;
8. rendering and citation numbering.

The same verifier must be called by sync, SSE, local/offline and frontier adapters. Financial and
exact-claim sections are buffered until verified. Streaming may emit progress and already-verified
sections; it must not emit irreversible unverified prose and append a warning later.

Replace the monolithic prompt with a prompt compiler that includes only the task contract,
authorized relevant tools, selected evidence, unresolved assumptions and required output schema.
System policy remains stable and short; domain knowledge lives in governed evidence/rules.

## 8. Frontier gap assessment

The current official OpenAI model guidance is used as a contemporary architecture signal, not as a
release claim: <https://developers.openai.com/api/docs/guides/latest-model>.

| Frontier pattern | Current state | Planned response |
|---|---|---|
| Current frontier/balanced model lanes with explicit reasoning effort | Model ids exist in config, but normal chat remains legacy and no matched quality result proves a better lane | Add evaluated provider adapters; pin model snapshot, reasoning effort, prompt/schema and token budget per run. Do not switch production on model age alone. |
| Responses-style unified reasoning/tool loop | Legacy uses Chat Completions and custom JSON ReAct; SDK canary is text-only | Add an adapter after core contracts/guards exist. Keep the provider outside the domain core and preserve the offline adapter. |
| Strict Structured Outputs/function schemas | Cloud path only requests JSON mode | Use strict JSON Schema for task/answer/tool contracts where supported; validate again locally in all cases. |
| Relevant tools and programmatic computation | All authorized tools are exposed; derived accounting values are model-owned | Add capability-scoped tools and deterministic accounting computation. |
| Lean, task-specific instructions | Current prompt combines persona, retrieval, citation, tool and safety behavior in one large block | Compile a small stage-specific prompt from typed policy and evidence. |
| Trace grading and representative evals | Operational events and several eval utilities exist, but there is no unified stage trace/quality gate for this failure | Persist redacted stage traces and grade route, retrieval, calculation, claims, citations and outcome separately. |
| Durable conversation state | Postgres memory exists and is the correct base; summaries are model-generated derived text | Keep canonical facts/corrections/assumptions typed in Postgres; treat summaries as non-authoritative derived context. |

Migration to a frontier provider is P2 until strict schema, guard parity, traceability, offline parity
and matched evals pass. The architecture must still work with a capable local model; degraded model
quality must fail visibly, not weaken financial, authorization or approval invariants.

## 9. Work packages and dependencies

### WP19-00 — Containment, baseline and environment freeze (P0)

**Actions**

- Resolve the intended worktree state with the owner; preserve all unrelated changes.
- Record clean implementation baseline commit, actual Alembic head, sanitized runtime feature flags,
  model/version ids and corpus snapshot hashes. Never record secret values.
- Freeze System A and an actually enabled System B answer plus stage/runtime evidence for the
  ten-transaction anchor before changing prompt, routing, retrieval or synthesis.
- Add the smallest legacy containment fix for the `bằng`/`bang` false positive and a boundary test.
- Keep Consultant/frontier rollout disabled for any arm whose active configuration is not proven.

**Exit gate**

- Reproducible baseline bundle exists; `bằng tiền mặt` is not technical design; true `bảng B30...`
  cases still route technical; no unrelated file was changed.

### WP19-01 — Freeze contracts, taxonomy and SME fixtures (P0)

**Actions**

- ADR the package boundary and freeze the contracts in section 4.
- Freeze task types: knowledge lookup, BRAVO navigation, multi-item accounting work product,
  read-only investigation, clarification and analysis proposal.
- Encode the section 2.3 answer key, assumptions, source requirements and must-not claims.
- Add adversarial variants: `bằng` vs `bảng`; VAT inclusive/exclusive; direct bank payment vs cash;
  salary accrued/not accrued; TT99 vs legacy account policy; missing/superseded guide.

**Exit gate**

- Fixture hashes and SME review are recorded before implementation of the engine.

### WP19-02 — Lossless task decomposition and route hypotheses (P0)

**Actions**

- Implement pure decomposition and accent-safe routing functions in Conversation Core V2.
- Emit matched spans/reasons and unit-level coverage status.
- Support multi-domain/multi-workflow evidence plans; remove arbitrary single-workflow ownership
  from the V2 path.

**Exit gate**

- The ten-item anchor produces exactly ten top-level units and all material amounts/entities are
  preserved. Boundary and property tests show zero known `bằng` false positives.

### WP19-03 — Evidence planner, retrieval recovery and authority (P0)

**Actions**

- Convert each task unit to required source classes and queries.
- Execute scoped retrieval followed by controlled recovery when coverage is inadequate.
- Bind source version, approval, effective date and scope to evidence refs.
- Create a corpus coverage report for Documents, Purchases, Accounting and Banking-related flows.

**Exit gate**

- The anchor retrieves supporting Chapter 04/08/17 evidence where applicable, or returns a precise
  source gap. No hard filter silently removes a required class; RLS tests remain green.

### WP19-04 — Deterministic accounting work-product engine (P0)

**Actions**

- Implement the policy in section 6.1 behind a read-only port.
- Add typed postings, VAT/settlement calculations, assumption handling and calculation lineage.
- Reuse shared money/accounting primitives where contracts match; do not duplicate BRAVO posting,
  period close or report execution.

**Exit gate**

- 100% exact match on the frozen accounting fixture; all posting groups balance; every derived
  number has rule/calculation lineage; no mutation path exists.

### WP19-05 — Structured synthesis, verification and rendering (P0)

**Actions**

- Implement strict `AnswerPlan`, `Claim` and `VerificationResult` validation.
- Add claim/citation binding, exact-claim authority checks and must-not-claim policy.
- Render a useful response per task unit: BRAVO document/screen when evidenced, debit/credit entry,
  amount split, assumption and missing evidence.
- Make one verifier mandatory for sync/SSE/local/frontier paths.

**Exit gate**

- No answer can be released with a missing task unit, unbalanced posting, unsupported derived number
  or exact BRAVO navigation claim without matching evidence.

### WP19-06 — Tool, context and conversation-state hardening (P1)

**Actions**

- Add strict argument/result validation and task-relevant tool compilation.
- Build a context compiler with budgets for policy, current raw task, canonical state, evidence,
  tool schemas and output reserve.
- Store typed user corrections, assumptions and open questions. Summary text remains derived and
  cannot override canonical state.

**Exit gate**

- Malformed tool calls are rejected before invocation; compiled prompts stay within the selected
  model budget; correction/memory tests demonstrate that newer explicit user facts win.

### WP19-07 — Redacted stage traces and unified evaluation (P1)

**Actions**

- Persist stage decisions as references/hashes plus safe metadata.
- Extend replay to reconstruct task units, route, evidence ids, calculations, claims, verifier
  decisions, model/runtime ids, latency and usage.
- Add graders for each stage and outcome; separate Knowledge Chat and Accounting Work scorecards.

**Exit gate**

- Every failed golden run receives one or more actionable labels such as decomposition loss,
  wrong route, retrieval miss, corpus gap, calculation error, unsupported claim, citation mismatch,
  unsafe tool or renderer defect.

### WP19-08 — Frontier and offline adapters (P2)

**Actions**

- Implement provider-neutral ports first, then a Responses/strict-schema frontier adapter and a
  controlled offline adapter.
- Pin model snapshot/reasoning effort and use identical core contracts/verifiers.
- Run model, reasoning-effort, retrieval, planner, critic and state ablations. Attribute gains; do
  not bundle them into an unexplained “frontier” result.

**Exit gate**

- Guard parity, trace parity and feature parity pass. Frontier egress is policy-approved and
  auditable; offline mode remains functional and fail-closed.

### WP19-09 — Frozen A/B/C/D, blind review and canary decision (P0 release gate)

Use the already governed arm definitions without renaming them:

- A: legacy;
- B: current Consultant;
- C: Core V2;
- D: BravoGen.

A/B/C use matched model/version, token budget, input, environment facts and versioned evidence where
technically possible. Frontier/local runs are declared ablations of C, not a replacement for D.

**Exit gate**

- Blind SME and outcome gates in section 10 pass; owner signs the evidence packet; canary cohort and
  rollback are specified. Otherwise retain the frozen baseline and continue diagnosis.

## 10. Test matrix and release gates

Thresholds below are proposed and must be frozen by the owner/SME before candidate runs.

| Gate | Required result |
|---|---|
| Hard safety | 0 unauthorized disclosure, direct mutation, approval bypass, unsupported exact financial result or cross-scope source. |
| Route boundary | 0 false `technical_design` results across a frozen Vietnamese `bằng...` boundary suite; 100% of qualified database-table controls remain recognized. |
| Task coverage | 100% of explicit top-level tasks represented; no silent drop. Ten-transaction anchor: 10/10. |
| Accounting exactness | 100% on critical SME golden postings/calculations; debit equals credit; exact Decimal arithmetic. |
| Evidence authority | 100% of exact BRAVO navigation/version/configuration claims have a matching approved evidence ref or are explicitly withheld. |
| Citation correctness | At least 95% claim-level citation entailment on the stratified set and 100% on critical claims; no fabricated source/locator. |
| Abstention/partial answer | Missing evidence produces a precise gap while still returning all independently supported task units. |
| Tool contract | 100% malformed/unauthorized tool calls blocked before invocation; the V2 product inventory contains no ERP mutation/write tool. |
| Multi-turn state | Explicit corrections override older assumptions in 100% of held-out correction cases; summary poisoning does not alter policy or authority. |
| Consistency | Critical set passes `pass^k` with `k >= 8`; one lucky run is not a release pass. |
| Human utility | Recommended: C wins at least 60% and loses no more than 15% against each matched A, B and D comparison, with zero critical SME error. Final threshold is frozen before scoring. |
| Operations | Candidate p95 latency/cost budgets are frozen before run; a quality gain that breaches the agreed budget is a trade-off decision, not an automatic pass. |

Minimum stratification:

- simple knowledge lookup and exact navigation;
- multi-item/accounting work products;
- multi-turn correction and follow-up;
- missing, stale, superseded and conflicting evidence;
- Vietnamese accent/word-boundary adversaries;
- permission/RLS, prompt injection and unsafe mutation requests;
- local/offline and approved cloud paths;
- the existing Financial Close benchmark family and all three governed Accounting Operations cases,
  scored separately from Knowledge Chat.

## 11. Delivery order

```text
WP19-00 baseline/containment
    -> WP19-01 contracts + SME fixtures
        -> WP19-02 decomposition/routing
        -> WP19-03 evidence planning/retrieval
        -> WP19-04 deterministic accounting
            -> WP19-05 synthesis/verifier
                -> WP19-06 tools/context/state
                -> WP19-07 traces/evals
                    -> WP19-08 adapters/ablations
                        -> WP19-09 blind gate/canary
```

WP19-02, WP19-03 and WP19-04 may be developed in parallel only after WP19-01 contracts and fixtures
are frozen. WP19-09 cannot be waived by passing unit tests or a polished browser demo.

## 12. Explicit non-goals

- No broad refactor of the legacy loop beyond P0 containment and baseline instrumentation.
- No direct posting, closing, report execution, period lock, SQL execution or configuration change.
- No inference that a paid pilot, customer-data permission or production topology is approved.
- No frontend rewrite as a substitute for conversation correctness.
- No GraphRAG, larger context, reranker, extra agent or new model unless an ablation demonstrates
  measurable lift without violating security, offline or cost gates.
- No claim that a model's self-reported confidence proves accounting or BRAVO correctness.
- No use of historical progress documents as stronger evidence than current code, migrations,
  runtime traces, frozen fixtures and human review.

## 13. Immediate next implementation slice

The first authorized slice should contain only:

1. WP19-00 baseline evidence capture;
2. one regression test proving `bằng tiền mặt` does not match the database-table intent while
   `Bảng B30BizDoc` still does;
3. the smallest boundary-safe router fix;
4. a frozen schema and SME fixture for the ten transactions; and
5. a design-only ADR for `app/conversation_v2` contracts.

Do not begin prompt/model migration or the deterministic engine until these artifacts are reviewed.
