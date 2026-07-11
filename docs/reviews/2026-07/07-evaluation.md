# T7 — Evaluation, Probes & Readiness Claims

Scope read: T1–T6 artifacts; `app/eval/**`, `tests/eval/**`, focused eval/readiness/probe/golden tests, direct grounding/RLS/memory/egress/RAG test evidence, and `.github/workflows/ci.yml`. No command was executed: the baseline records no usable host Python/pytest toolchain.

## Claim → enforcement → evaluation coverage

| Claim | Enforcement evidence | Eval/test | Coverage | Gap | Priority |
|---|---|---|---|---|---|
| Department retrieval isolation (BRV-DATA-001, BRV-API-002) | T2/T3 trace application-side scope predicates and source→chunk propagation. | `tests/test_rls.py` predicate tests; `probes:probe_leak`; pass^k RLS trajectories. | Unit and an available DB probe; CI pass^k uses a mock answer only. | No CI execution of the live retrieval probe against seeded cross-department data; no database-policy verification. | High |
| Agent-session isolation (BRV-DATA-002) | T4 traces `/agent/ask` caller-controlled session ID into memory loading. | `tests/test_chat.py` covers the different conversation-owner route; memory tests cover session lookup. | Partial. | No `/agent/ask` cross-user session request/eval or output-leak probe. | High |
| Memory-summary trust boundary (BRV-DATA-003) | T2/T4 trace raw history → LLM summary → system message. | `tests/test_memory_rls.py` frames untrusted recall rows. | Partial structural unit coverage. | No compaction test with adversarial historical content followed by a real next agent turn. | High |
| Private/shared ingest classification (BRV-RAG-001, BRV-RAG-002) | T3 traces caller/CLI metadata into scope and sensitivity. | `test_bravo_data_audit.py`, manifest tests, `test_egress_embedding.py`. | Static policy/parser checks. | No authenticated upload/CLI e2e proving private content cannot be misclassified and egressed. | High |
| Rerank egress (BRV-PLAT-001) | T6/T3 trace retrieved content into LLM rerank. | Router/embedding unit tests; pass^k synthetic egress detector. | Component/synthetic. | No retrieval+rering runtime test with sensitive chunk and cloud provider enabled. | High |
| Financial draft scope/approval/payload integrity (BRV-BIZ-001–003) | T5 traces generic creation, service approval, and export. | `test_draft_queue.py`, `test_draft_leak_probe.py`, AP/journal tests. | Helper and normal-path coverage. | No generic-draft global-scope, foreign-department approve/reject, or malformed journal approval/export probe. | High |
| Duplicate AP proposal (BRV-BIZ-004) | T5 traces invoice key/hash with no AP uniqueness boundary. | AP service happy-path test. | Normal creation only. | No repeat-upload or same-invoice different-file lifecycle test. | Medium |
| Demo tax/anomaly workflow (BRV-BIZ-005) | T5 verifies routes use `MockDataSource` and `is_demo` payload. | `test_tax.py`, `test_anomaly.py` exercise engine output. | Deterministic engine only. | No route/approval test distinguishes demo drafts from operational records. | Medium |
| Effective-date mapping (BRV-BIZ-006) | T5 traces missing date → latest statutory period. | Accounting tests cover valid dates and thresholds. | Valid-date fixtures. | No missing, malformed, or out-of-range invoice-date test. | Medium |
| Number integrity / wrong unit | `JournalEntryPayload` and `verify_numbers`; agent verify gate in T4. | `test_grounding.py`, AP gate/golden tests, pass^k wrong-unit/fabrication detector. | Strong unit coverage; CI gate uses scripted mock. | Generic draft API bypass from T5 is not represented in the number/approval evaluation. | High |
| Citation and correct-source routing | T3 retrieval citation contract; lifecycle scoring reads `Chunk.extra`. | `test_bravo_lifecycle_eval.py`; pass^k citation-rate gate. | Metadata-score and nonempty-citation check. | No answer-to-source/page/heading/version citation validation. | Medium |
| Deployment/data readiness | T6 boot/config controls; static corpus/policy artifacts. | `bravo_readiness.audit_readiness`, `bravo_data_audit`, temporary-fixture tests. | Static validation logic. | CI does not invoke readiness/data audit against the checked-out corpus/runtime layout. | Medium |

## Findings

| ID | Severity tạm thời | Evidence state | File:symbol | Evidence ngắn | Consumer/impact | Next action | Needs Sol review |
|---|---|---|---|---|---|---|---|
| BRV-EVAL-001 | High | VERIFIED | `.github/workflows/ci.yml:Eval pass^k gate`; `app/eval/run.py:passk_main`; `app/eval/passk.py:MockLoop` | CI runs `python -m app.eval.run --passk --mock --k=8`; the passing path uses scripted `MockLoop`, not `AgentSession`. The real branch exists but is not selected in CI. | A green hard gate proves detector/harness behavior against scripted output, not the deployed agent’s retrieval, tools, memory, routing, or verifier controls. | Add a seeded, non-network real-loop integration gate or mark the existing job harness-only; retain deterministic mock tests. | No |
| BRV-EVAL-002 | High | VERIFIED | `app/eval/passk.py:run_trajectory`, `hard_fails` | For every multi-turn run, `last` is overwritten on each turn; hard-fail detection and outcome/tool scoring run only against the final `TurnResult`. | A prior-turn RLS disclosure, cloud egress, injection response, or unsafe tool activity can be absent from the final answer and escape the pass^k gate. | Preserve and evaluate every turn/event, with hard-fail aggregation across the full trajectory. | No |
| BRV-EVAL-003 | High | VERIFIED | `app/eval/probes.py:probe_draft_leak`; `tests/test_draft_leak_probe.py`; `app/erp/draft_queue.py:approve_draft` | Draft probe calls only `list_drafts`, which applies `draft_scope_filter`; tests exercise its pure predicate. T5 shows `approve_draft`/`reject_draft` fetch by ID without that predicate. | The available draft “leak” evaluation can pass while an own-department approver changes a foreign draft’s state (BRV-BIZ-002). | Add service/route probes for foreign approve and reject, plus generic global-draft creation; gate them in CI. | No |
| BRV-EVAL-004 | Medium | VERIFIED | `app/eval/passk.py:detect_prompt_injection`; `tests/eval/mock_loop.py`; `app/agent/memory.py:history_for_prompt` | Injection detection is a forbidden-substring check on final mock output. Memory tests frame recall rows, but do not invoke long-history summarization or the next agent turn. | T4’s summary-to-system failure path and a real retrieved-chunk instruction path are not evaluated end-to-end. | Seed adversarial document/history fixtures and run retrieval→agent→compaction→next-turn probes. | No |
| BRV-EVAL-005 | Medium | VERIFIED | `app/eval/passk.py:_outcome_correct`, `run_passk`; `app/eval/bravo_lifecycle.py:score_item` | Citation gate accepts any nonempty `citations` list. Lifecycle eval scores metadata hits only and `expected_behavior` is reported but not generated/checked. | A green result does not prove that an answer’s citation identifies the supporting source/page/heading/version or that routing produced the expected response behavior. | Add answer-level citation provenance assertions and couple lifecycle retrieval to response behavior. | No |
| BRV-EVAL-006 | Medium | VERIFIED | `.github/workflows/ci.yml`; `app/eval/bravo_readiness.py:audit_readiness`; `app/eval/bravo_lifecycle.py:main` | CI runs `pytest -q` and mock pass^k only. Readiness/lifecycle commands exist, while their tests construct temporary fixtures or mock chunks. | Repository-specific manifest/playbook/use-case/golden consistency and live lifecycle retrieval are not release-gated. | Invoke static readiness/data audit on the checked-out layout in CI; run seeded lifecycle retrieval separately where DB/corpus is available. | No |
| BRV-EVAL-007 | Medium | VERIFIED | `app/eval/faithfulness.py:score`; `.github/workflows/ci.yml` | Faithfulness scoring requires optional `ragas` plus an explicit local judge; no CI workflow or threshold consumes its score. | There is no operational faithfulness measurement beyond deterministic output detectors. | Define an optional-but-reported local-judge job, fixture set, and threshold ownership before presenting a faithfulness metric. | No |

## Gate and fixture evidence

| Area | VERIFIED evidence | Limitation |
|---|---|---|
| Deterministic pass^k | `DEFAULT_K=8`; gate fails any detected RLS/fabrication/wrong-unit/egress/injection, number pass^k < 0.95, or citation rate < 0.95. `test_eval_passk.py` injects faulty mock scripts to prove detector failure. | The CI invocation is mock-only; it cannot establish real model/provider/retriever behavior. |
| Legacy retrieval gate | `eval.run:main` retrieves as configured identities and calls `assert_no_leak` for named employees when present. | It is not invoked by CI and depends on seeded users/corpus/database. |
| Lifecycle retrieval gate | `bravo_lifecycle.run_items` retrieves as each golden actor and `main` fails below 0.95 source-type/module/label pass rate. | Not invoked by CI; it does not generate/check an answer or citations. |
| Static readiness | `audit_readiness` validates manifest files/types, data policy/audit output, playbooks, use cases, and lifecycle golden items. | Tests use temporary artifacts; current repository result is `NEED FILE/CONTEXT` because command was not run. |
| Faithfulness judge | `faithfulness.score` refuses absent ragas/judge and takes an explicit judge. | Local-judge identity, dataset, score, and release threshold are `NEED FILE/CONTEXT`. |

## Commands and execution state

| Purpose | Command | Source | Executed | Notes |
|---|---|---|---|---|
| Unit/integration suite | `pytest -q` | `.github/workflows/ci.yml` | No | CI declares it; host Python/pytest unavailable. |
| Deterministic harness | `python -m app.eval.run --passk --mock --k=8` | `.github/workflows/ci.yml` | No | Mock-only coverage (BRV-EVAL-001). |
| Static readiness | `python -m app.eval.bravo_readiness` | `app/eval/bravo_readiness.py:main` | No | Not wired in the observed CI workflow. |
| Lifecycle retrieval | `python -m app.eval.bravo_lifecycle` | `app/eval/bravo_lifecycle.py:main` | No | Requires database, seeded identities, and ingested corpus. |
| Legacy retrieval/ACL | `python -m app.eval.run` | `app/eval/run.py:main` | No | Requires database and seeded identities. |

## T7 exit check

- Every provisional Critical/High finding from T2–T6 has test/eval evidence or an explicit gap in the claim table.
- Unit, integration-capable probe, mock golden, static readiness, and runtime-eval evidence are distinguished.
- No documentation/YAML claim is treated as proof of implementation; no target evaluation architecture or production change is proposed.
