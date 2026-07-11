# T9 — Evidence Consolidation & Reproduction

T9 is a mechanical consolidation of T1–T8. It does not change provisional severity, reject a finding, make an architecture decision, or modify production files. All tests below were read from the artifacts and repository; none was executed because T0 records Python/pytest and npm as unavailable.

## Executive counts

| Count | Result |
|---|---:|
| Finding occurrences in T1–T8 | 53 |
| Canonical IDs after retaining repeated IDs | 40 |
| Occurrences by source task | T1: 6; T2: 5; T3: 6; T4: 4; T5: 6; T6: 12; T7: 7; T8: 7 |
| Occurrences by provisional severity | High (including conditional): 20; Medium: 29; Low: 4 |
| Occurrences by evidence state | VERIFIED: 50; INFERRED: 3; NEED FILE/CONTEXT: 0 |
| Canonical rows by evidence quality | Strong: 18; Adequate: 21; Weak: 1; Insufficient: 0 |
| T10 candidates | 28 |
| Findings explicitly marked NEED FILE/CONTEXT | 0; missing runtime corroboration is recorded separately |

## Canonical evidence index

`Status` preserves the first ID and records later task coverage; repeated IDs are not silently dropped.

| Canonical ID | Source task | Provisional severity | Evidence state | File:symbol | Failure path | Affected boundary | Test evidence | Needs Sol review | Evidence quality | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| BRV-API-001 | T1 | Medium | VERIFIED | `app/security/rls.py:Identity.scope_level`; `app/api/routes_admin.py:ASSIGNABLE_PERMISSIONS` | Bare assignable permissions do not satisfy scoped route dependencies. | Auth/API; Agent/tool authority | No direct auth matrix executed; `tests/test_admin.py` read only. | No | Adequate | CANONICAL |
| BRV-API-002 | T1,T2,T3,T8 | High (conditional) / High | INFERRED → VERIFIED | `routes_sources.upload_source`; `SourceDepartment`; `ingest_source`; `retriever.*_search`; frontend source uploads | Caller/frontend department scope reaches source rows, chunks, and retrieval; omitted frontend scope becomes global. | Tenant/RLS; Private/shared data; RAG/ingestion; Frontend/API contract | RLS, memory, ingestion, and draft probes read only; no live cross-department run. | Yes | Strong | CANONICAL; T2/T3/T8 extend the same ID |
| BRV-API-003 | T1,T6 | Medium | VERIFIED | `app/ratelimit.py:limiter`; route decorators; compose rate-limit config | Only streaming chat is limited; ask/agent/scan paths lack endpoint limits. | Auth/API; Deployment/operations | No HTTP 429 test executed. | No | Adequate | CANONICAL; T6 confirms deployment path |
| BRV-API-004 | T1,T6 | Medium | VERIFIED | `app/main.py:readyz`; `deploy/Caddyfile` | Public readiness response includes raw DB exception text and proxy forwards it. | Auth/API; Deployment/operations | No deployed readiness probe executed. | No | Adequate | CANONICAL; T6 confirms proxy |
| BRV-API-005 | T1,T6 | Low | VERIFIED | `app/observability.py:setup`; `deploy/Caddyfile` | Unauthenticated metrics route is exposed through the supplied proxy. | Deployment/operations | No network exposure test executed. | No | Adequate | CANONICAL; T6 confirms proxy |
| BRV-API-006 | T1,T6,T8 | Low / Medium | VERIFIED | upload/invoice/SSE exception paths; frontend `api/sse.ts` | Raw exception/detail text is serialized by backend and rendered by frontend. | Auth/API; Deployment/operations; Frontend/API contract | No failure-response test executed. | No | Strong | CANONICAL; T6/T8 extend consumer path |
| BRV-DATA-001 | T2 | High | VERIFIED | `alembic/versions/0004_db_roles.py:upgrade`; database session factory | No native RLS policy/backstop is created; base-table ORM session has no role context switch. | Database; Tenant/RLS | `tests/test_rls.py` is application predicate-only and was not executed; live role/grant evidence missing. | Yes | Adequate | CANONICAL |
| BRV-DATA-002 | T2,T4 | High | INFERRED | `routes_agent.agent_ask`; `AgentSession`; `MemoryStore.recall_recent` | Caller-supplied session UUID is read without owner check; prompt disclosure is not demonstrated. | Memory; Tenant/RLS; Private/shared data; Agent/tool authority | `tests/test_chat.py` covers the owner-checked SSE route; no `/agent/ask` ownership test executed. | Yes | Weak | CANONICAL; T4 traces downstream prompt path |
| BRV-DATA-003 | T2,T4 | High | VERIFIED | `MemoryStore.history_for_prompt`; `AgentSession._summarize` | Raw older turns enter summarization, then persisted summary is emitted as a system message. | Memory; Agent/tool authority | Memory framing tests read only; no compaction/adversarial next-turn test executed. | Yes | Strong | CANONICAL; T4 confirms agent consumer |
| BRV-DATA-004 | T2 | Medium | VERIFIED | `MemoryBlock`; `ArchivalPassage`; `MemoryStore` | Memory schema and service have no retention timestamp/policy or archival deletion path. | Memory; Database; Private/shared data | No retention/erase test executed. | No | Adequate | CANONICAL |
| BRV-RAG-001 | T3,T8 | High (conditional) | VERIFIED | `routes_sources.upload_source`; `ingest_source`; `sensitivity.ingest_sensitive`; `DocumentsPage` | User-controlled knowledge type and scope influence sensitivity before cloud embedding. | Private/shared data; RAG/ingestion; Egress/secrets; Frontend/API contract | Embedding guard and manifest tests read only; no adversarial upload e2e. | Yes | Strong | CANONICAL; T8 adds UI consumer |
| BRV-RAG-002 | T3 | High (conditional) | VERIFIED | `scripts/ingest_userguide.py:_select_files`, `main` | Explicit unmanifested import can omit department and create global corpus data. | Private/shared data; RAG/ingestion | Ingestion/data-audit tests read only; no CLI reproduction executed. | Yes | Strong | CANONICAL |
| BRV-RAG-003 | T3 | Medium | VERIFIED | `ingest_userguide.main`; `ingest_source`; `Source`, `Chunk` | Filename-based replacement deletes old rows before successful replacement; no version/tombstone identity. | RAG/ingestion; Database | No collision/failed-reindex test executed. | No | Adequate | CANONICAL |
| BRV-RAG-004 | T3,T8 | Medium | VERIFIED | `Chunk.heading_path`; `Retrieved.citation`; frontend `SseEvent` | Stored heading/hash/version is not carried into retrieval, SSE, or citation UI. | RAG/ingestion; Frontend/API contract | Parser/citation tests read only; no end-to-end citation provenance test. | No | Strong | CANONICAL; T8 confirms consumer loss |
| BRV-PLAT-001 | T3,T6 | High (conditional) | VERIFIED | `retriever.retrieve`; `rerank.llm_rerank`; router call | Retrieved private text is sent to LLM rerank with explicit `sensitive=False` and cloud allowed. | Egress/secrets; RAG/ingestion | Egress component tests read only; no sensitive rerank runtime test. | Yes | Strong | CANONICAL; T6 confirms egress configuration |
| BRV-AGENT-001 | T4 | Medium | VERIFIED | `AgentSession._llm_decide`; budget tracker | Malformed-output retry dispatches a second LLM call before another budget check. | Agent/tool authority; Evaluation | Agent loop/budget tests read only; no retry-budget test executed. | No | Adequate | CANONICAL |
| BRV-AGENT-002 | T4 | Medium | VERIFIED | `AgentSession._open_run`, `_close_run`, `_audit`; `_audit_attempt` | Agent-run/tool audit failures are swallowed while the turn/draft path continues. | Agent/tool authority; Voucher/approval; Deployment/operations | Agent-run tests are DB-conditional and were not executed; no audit-failure injection test. | No | Adequate | CANONICAL |
| BRV-BIZ-001 | T5 | High | VERIFIED | `routes_drafts.propose`; `ap_service.create_invoice_draft`; `draft_scope_filter` | Generic and ambiguous AP creators can create NULL/global financial drafts. | Tenant/RLS; Accounting/financial state; Voucher/approval | AP happy path and pure scope tests read only; no zero/multi-department route test. | Yes | Strong | CANONICAL |
| BRV-BIZ-002 | T5 | High | VERIFIED | `routes_drafts.approve/reject`; `draft_queue.approve_draft/reject_draft` | Own-department permission is checked at the route, but service fetches draft by ID without scope predicate. | Tenant/RLS; Accounting/financial state; Voucher/approval | Draft leak test covers list predicate only; no foreign approve/reject test. | Yes | Strong | CANONICAL |
| BRV-BIZ-003 | T5 | High | VERIFIED | `routes_drafts.DraftIn`; `create_draft`; `journal_export` | Generic JSON draft bypasses journal schema/number gate and can be approved/exported. | Accounting/financial state; Voucher/approval; Number integrity | AP/journal validator tests read only; no generic payload route test. | Yes | Strong | CANONICAL |
| BRV-BIZ-004 | T5 | Medium | VERIFIED | `Invoice.key`; `ap_service.create_invoice_draft`; `Draft` constraint | AP derives invoice key/hash but does not deduplicate; idempotency only covers non-null agent runs. | Accounting/financial state; Voucher/approval | AP happy path only; no repeat-upload test. | Yes | Adequate | CANONICAL |
| BRV-BIZ-005 | T5 | Medium | VERIFIED | `routes_agents`; `TaxFlag/Flag.to_payload` | Mock tax/anomaly results enter shared pending/approved Draft state with `is_demo=True`. | Accounting/financial state; Voucher/approval; Evaluation | Tax/anomaly engine tests read only; no route approval/provenance test. | No | Strong | CANONICAL |
| BRV-BIZ-006 | T5 | Medium | VERIFIED | `as_of_from_iso`; `rules_governance._pick_period`; `build_journal_entry` | Missing/invalid invoice date silently selects latest/earliest statutory period without setting review. | Accounting/financial state; Number integrity | Valid-date accounting tests read only; no date-boundary test. | No | Adequate | CANONICAL |
| BRV-PLAT-002 | T6 | Medium | VERIFIED | `docker-compose*.yml:postgres`; `.env.example` | Supplied compose retains known database password/default credentials. | Egress/secrets; Deployment/operations | No secret/preflight command executed. | No | Adequate | CANONICAL |
| BRV-PLAT-003 | T6 | Medium | VERIFIED | compose private-data volumes; `scripts/backup.sh` | Private operational volume is mounted but not included in backup; no executable restore path observed. | Private/shared data; Deployment/operations | No backup/restore execution. | No | Adequate | CANONICAL |
| BRV-PLAT-004 | T6 | Medium | VERIFIED | `config.data_policy_variables`; `routes_sources._DATA_DIR` | Configured upload root is ignored by source file consumer, which uses fixed relative path. | Private/shared data; Deployment/operations | No non-default upload-root test. | No | Adequate | CANONICAL |
| BRV-PLAT-005 | T6 | Medium | VERIFIED | `validate_data_runtime_policy`; `ensure_runtime_policy_paths` | Boot-created directories can mask missing runtime volumes. | Deployment/operations; Private/shared data | No missing-volume/container test. | No | Adequate | CANONICAL |
| BRV-PLAT-006 | T6 | Medium | VERIFIED | `main.lifespan`; `config.validate_boot`; `alembic/env.py` | Startup does not gate DB connectivity, migration head, or vector dimension. | Deployment/operations; Database; RAG/ingestion | No boot/migration/vector preflight executed. | No | Adequate | CANONICAL |
| BRV-PLAT-007 | T6 | Medium | VERIFIED | `deploy/docker-compose.keycloak.yml:keycloak` | Optional IdP overlay uses `admin`/`admin` and `start-dev`. | Egress/secrets; Deployment/operations; Auth/API | No Keycloak deployment test. | No | Adequate | CANONICAL |
| BRV-PLAT-008 | T6 | Low | VERIFIED | `Dockerfile`; compose services | Image/compose do not establish non-root user or capability/filesystem hardening. | Deployment/operations | No container runtime test. | No | Adequate | CANONICAL |
| BRV-EVAL-001 | T7 | High | VERIFIED | CI pass^k step; `app.eval.run:passk_main`; `MockLoop` | CI hard gate runs scripted mock, not real AgentSession. | Evaluation; Agent/tool authority | `test_eval_passk.py` reads only; CI command not executed. | No | Strong | CANONICAL |
| BRV-EVAL-002 | T7 | High | VERIFIED | `passk.run_trajectory`; `hard_fails` | Only final turn is scored; earlier-turn leaks/tool activity can escape the gate. | Evaluation; Agent/tool authority | Multi-turn harness tests read only; no early-turn hard-fail test. | No | Strong | CANONICAL |
| BRV-EVAL-003 | T7 | High | VERIFIED | `probes.probe_draft_leak`; `tests/test_draft_leak_probe.py`; `approve_draft` | Evaluation checks scoped listing/predicate, not service approval/rejection scope. | Evaluation; Tenant/RLS; Voucher/approval | Pure probe tests read only; no service-level reproduction. | No | Strong | CANONICAL |
| BRV-EVAL-004 | T7 | Medium | VERIFIED | `passk.detect_prompt_injection`; mock loop; `history_for_prompt` | Injection detection is final-output substring matching and does not exercise real retrieval/summary. | Evaluation; Memory; Agent/tool authority | Mock fault tests and memory framing tests read only. | No | Strong | CANONICAL |
| BRV-EVAL-005 | T7 | Medium | VERIFIED | `passk._outcome_correct`; `bravo_lifecycle.score_item` | Any nonempty citation passes; lifecycle expected behavior is not generated/checked. | Evaluation; RAG/ingestion; Frontend/API contract | Lifecycle/passk tests read only; no answer provenance test. | No | Strong | CANONICAL |
| BRV-EVAL-006 | T7 | Medium | VERIFIED | CI workflow; `bravo_readiness.audit_readiness`; lifecycle main | Actual checked-out readiness/lifecycle audit is not release-gated. | Evaluation; Deployment/operations; RAG/ingestion | Temporary-fixture tests read only; commands not executed. | No | Strong | CANONICAL |
| BRV-EVAL-007 | T7 | Medium | VERIFIED | `faithfulness.score`; CI workflow | Optional local faithfulness judge has no consumed threshold/job. | Evaluation; Egress/secrets | No ragas/local-judge command executed. | No | Adequate | CANONICAL |
| BRV-FE-001 | T8 | High | VERIFIED | `DraftCard`; queue/money pages; `routes_drafts:export_*` | UI and backend allow export of pending/rejected journal drafts. | Frontend/API contract; Accounting/financial state; Voucher/approval | No browser/API status-gate test; frontend build unavailable. | Yes | Strong | CANONICAL |
| BRV-FE-002 | T8 | Medium | VERIFIED | `api/sse.ts:streamChat`; `store/chat.send/stop`; `routes_conversations.chat_stream` | EOF/abort has no synthesized terminal event; cancelled assistant can remain streaming. | Frontend/API contract | No frontend SSE test or browser run. | No | Adequate | CANONICAL |
| BRV-FE-003 | T8 | Medium | VERIFIED | `api.client.api`; direct frontend `fetch`/`downloadFile` consumers | Only wrapper API handles 401 reset; stream/upload/export/file consumers bypass it. | Frontend/API contract; Auth/API | No browser expiry test; frontend build unavailable. | No | Adequate | CANONICAL |

## Duplicate and relationship map

| Canonical ID | Related IDs / tasks | Relationship | Reason | Merge decision |
|---|---|---|---|---|
| BRV-API-002 | T1→T2→T3→T8 | SAME ROOT CAUSE / EXTENDS | Source write scope is first observed at API, confirmed in DB predicate, propagated to chunk retrieval, and consumed by frontend uploads. | Keep one ID; retain all enforcement-layer evidence. |
| BRV-API-003 | T1,T6 | SAME ROOT CAUSE | Same missing route limiter; T6 only confirms deployment configuration. | Consolidated under existing ID. |
| BRV-API-004 | T1,T6 | SAME ROOT CAUSE | Same raw readiness response; proxy does not redact it. | Consolidated under existing ID. |
| BRV-API-005 | T1,T6 | SAME ROOT CAUSE | Same public metrics exposure; proxy confirms reachability path. | Consolidated under existing ID. |
| BRV-API-006 | T1,T6,T8 | EXTENDS | Backend raw exceptions, deployment forwarding, and frontend rendering are one error-disclosure path with distinct consumers. | Keep one ID and preserve consumer evidence. |
| BRV-DATA-002 | T2,T4 | EXTENDS | T2 establishes context read; T4 traces agent prompt consumer. | Keep one ID; response disclosure remains INFERRED. |
| BRV-DATA-003 | T2,T4 | EXTENDS | T2 identifies raw summarization; T4 confirms system-message use. | Keep one ID. |
| BRV-PLAT-001 | T3,T6 | EXTENDS | T3 identifies sensitive retrieval content; T6 confirms router call configuration. | Keep one ID. |
| BRV-RAG-001 | T3,T8 | EXTENDS | T8 is the UI input consumer of T3’s caller-controlled classification. | Keep one ID. |
| BRV-RAG-004 | T3,T8 | EXTENDS | T3 identifies missing retrieval provenance; T8 identifies SSE/UI loss. | Keep one ID; do not merge with generic citation eval gap. |
| BRV-BIZ-001 | BRV-API-002 | RELATED / SAME SYMPTOM | Both can create global state, but one affects Sources and one affects Drafts; assets and service layers differ. | Do not merge. |
| BRV-BIZ-002 | BRV-EVAL-003 | RELATED / SAME SYMPTOM | Approval scope bypass is implementation; eval probe omission is evaluation enforcement. | Do not merge. |
| BRV-BIZ-003 | BRV-FE-001 | RELATED | Generic payload validation and export state gate are separate enforcement layers. | Do not merge. |
| BRV-DATA-003 | BRV-EVAL-004 | RELATED | Memory poisoning path and missing adversarial evaluation are distinct findings. | Do not merge. |
| BRV-BIZ-004 | BRV-RAG-003 | POSSIBLE DUPLICATE | Both concern duplicate/replacement identity, but AP invoice identity and corpus source identity differ. | Keep both; no shared remediation assumed. |
| BRV-EVAL-001 | BRV-EVAL-006 | RELATED | Mock CI gate and readiness command omission both affect release evidence, but different evaluators. | Keep both. |

## Test reproduction results

| Finding ID | Command | Executed | Result | Exit code | Evidence added |
|---|---|---|---|---:|---|
| BRV-DATA-001, BRV-API-002, BRV-DATA-002, BRV-DATA-003 | `pytest -q tests/test_rls.py tests/test_memory_rls.py tests/test_sensitivity.py tests/test_router_egress.py` | No | Python/pytest unavailable per T0 | — | None; evidence remains as recorded. |
| BRV-DATA-002, BRV-DATA-003, BRV-AGENT-001, BRV-AGENT-002 | `pytest -q tests/test_agent_loop.py tests/test_agent_runs.py tests/test_chat.py tests/test_mcp_server.py` | No | Python/pytest unavailable | — | None. |
| BRV-API-002, BRV-RAG-001–004, BRV-PLAT-001 | `pytest -q tests/test_grounding.py tests/test_ingestion_wpa.py tests/test_mock_source.py tests/test_egress_embedding.py` | No | Python/pytest unavailable | — | None. |
| BRV-BIZ-001–006 | `pytest -q tests/test_accounting_rules.py tests/test_ap_*.py tests/test_coa.py tests/test_journal*.py tests/test_tax.py` | No | Python/pytest unavailable | — | None. |
| BRV-EVAL-001–007 | `pytest -q tests/test_eval_passk.py tests/test_bravo_*.py` | No | Python/pytest unavailable | — | None. |
| BRV-EVAL-001, BRV-EVAL-002 | `python -m app.eval.run --passk --mock --k=8` | No | Python unavailable | — | None; mock result not represented as runtime evidence. |
| BRV-FE-001–003, BRV-RAG-004 | `cd frontend-react && npm run build` | No | npm unavailable; no frontend test script observed | — | None. |
| BRV-API-003–006, BRV-PLAT-002–008 | `ruff check app` | No | ruff unavailable | — | None. |
| BRV-DATA-001, BRV-PLAT-006 | `alembic upgrade head` | No | alembic/PostgreSQL unavailable | — | None. |
| All relevant findings | `pytest -q` | No | Full suite intentionally not run; Python/pytest unavailable | — | None. |

No test was executed, so no finding is upgraded from INFERRED to VERIFIED and no product conclusion is drawn from a missing toolchain.

## T10 candidate package

Candidates are selected mechanically from provisional High, `Needs Sol review: Yes`, cross-subsystem/private-data/financial boundaries, or a Medium path that can become High when its call chain is combined. “Sol needed” below is not a final severity or architecture decision.

| ID | Provisional severity | Why Sol is needed / candidate basis | Evidence files | Key symbols | Test evidence | Decision required |
|---|---|---|---|---|---|---|
| BRV-API-002 | High | Tenant/private boundary; source→chunk→frontend cross-subsystem | T1,T2,T3,T8 artifacts | `upload_source`, `SourceDepartment`, `ingest_source`, `retriever` | Not run | Verify trusted scope authority. |
| BRV-API-003 | Medium | API + operations capacity path | T1,T6 | limiter decorators; route consumers | Not run | Define endpoint classes/limits. |
| BRV-DATA-001 | High | Database/RLS backstop | T2 | migration roles; session factory | Not run | Verify deployed roles/policies. |
| BRV-DATA-002 | High | Cross-user memory/private boundary | T2,T4 | `agent_ask`, `AgentSession`, `MemoryStore` | Not run | Confirm ownership invariant. |
| BRV-DATA-003 | High | Memory→agent instruction boundary | T2,T4 | `history_for_prompt`, `_summarize` | Not run | Define trusted-summary boundary. |
| BRV-DATA-004 | Medium | Private memory lifecycle may intersect backup/deletion | T2,T6 | `MemoryBlock`, `ArchivalPassage` | Not run | Confirm retention/erase obligations. |
| BRV-RAG-001 | High (conditional) | Private/shared data→cloud egress | T3,T8 | `upload_source`, `ingest_sensitive` | Not run | Decide trusted classification source. |
| BRV-RAG-002 | High (conditional) | Operator import→global corpus boundary | T3 | `_select_files`, CLI `main` | Not run | Decide unmanifested import policy. |
| BRV-RAG-003 | Medium | RAG/database replacement identity and evidence loss | T3 | `ingest_source`, `Source.filename` | Not run | Confirm version/tombstone requirement. |
| BRV-RAG-004 | Medium | RAG→SSE/frontend provenance contract | T3,T8 | `Retrieved.citation`, `SseEvent` | Not run | Define citation evidence contract. |
| BRV-PLAT-001 | High (conditional) | Sensitive RAG content→cloud rerank | T3,T6 | `llm_rerank`, router call | Not run | Decide rerank egress policy. |
| BRV-PLAT-002 | Medium | Secret exposure in deployment boundary | T6 | compose Postgres env | Not run | Verify provisioning/default rejection. |
| BRV-PLAT-003 | Medium | Private operational data recovery boundary | T6 | compose volumes, `backup.sh` | Not run | Confirm backup/restore scope. |
| BRV-PLAT-006 | Medium | Deployment→DB/migration/vector readiness | T6 | `lifespan`, `validate_boot` | Not run | Define startup gate requirements. |
| BRV-PLAT-007 | Medium | IdP secret/deployment boundary | T6 | Keycloak compose overlay | Not run | Confirm production IdP provisioning. |
| BRV-AGENT-002 | Medium | Agent audit→draft/financial reconciliation | T4 | `_audit`, `_audit_attempt`, `create_draft` | Not run | Decide transactional audit requirement. |
| BRV-BIZ-001 | High | Tenant/RLS + financial draft state | T5 | `propose`, `create_invoice_draft`, `draft_scope_filter` | Not run | Verify mandatory draft scope. |
| BRV-BIZ-002 | High | Voucher approval + tenant boundary | T5 | `approve_draft`, `reject_draft` | Not run | Verify service-level scope. |
| BRV-BIZ-003 | High | Financial payload/number/approval boundary | T5 | `DraftIn`, `create_draft`, `journal_to_rows` | Not run | Decide shared validation boundary. |
| BRV-BIZ-004 | Medium | Duplicate financial proposal can become posting risk | T5 | `Invoice.key`, `Draft` constraint | Not run | Confirm duplicate identity/lifecycle. |
| BRV-BIZ-005 | Medium | Demo result enters shared financial workflow | T5 | `routes_agents`, `MockDataSource` | Not run | Decide demo/operational separation. |
| BRV-EVAL-001 | High | Release gate does not exercise real agent | T7 | CI; `passk_main`, `MockLoop` | Not run | Decide runtime evaluation evidence. |
| BRV-EVAL-002 | High | Multi-turn agent safety events can be dropped | T7 | `run_trajectory`, `hard_fails` | Not run | Define full-trajectory scoring. |
| BRV-EVAL-003 | High | Evaluation misses approval/RLS service bypass | T7 | `probe_draft_leak`, `approve_draft` | Not run | Add service-level probe gate. |
| BRV-EVAL-004 | Medium | Memory/agent prompt injection cross-subsystem gap | T7 | `detect_prompt_injection`, `history_for_prompt` | Not run | Add real adversarial trajectory. |
| BRV-EVAL-005 | Medium | RAG citation/response evidence gap | T7 | `_outcome_correct`, `score_item` | Not run | Define answer-level provenance checks. |
| BRV-EVAL-006 | Medium | Evaluation→deployment readiness gap | T7 | CI; `audit_readiness` | Not run | Decide release readiness invocation. |
| BRV-FE-001 | High | Frontend exposes financial export before approval | T8,T5 | `DraftCard`, `export_*` routes | Not run | Enforce approved-state export. |

## Non-Sol findings

| Group | IDs | Routing |
|---|---|---|
| Terra remediation candidate | `BRV-API-001`, `BRV-AGENT-001`, `BRV-BIZ-006`, `BRV-PLAT-004`, `BRV-PLAT-005`, `BRV-PLAT-008`, `BRV-FE-002` | Scoped implementation/test work with pass/fail criteria; no Sol decision assigned. |
| Luna/mechanical cleanup | `BRV-API-004`, `BRV-API-005`, `BRV-API-006`, `BRV-FE-003` | Stable error/exposure/auth-wrapper cleanup; API-006 remains cross-referenced, not re-severitized. |
| Need more context | `BRV-EVAL-007` | Local judge, dataset, threshold, and runtime provider evidence are absent. |

## Missing evidence

| Finding ID | Missing evidence | Exact file/config/runtime data needed | Blocks T10? |
|---|---|---|---|
| BRV-API-002 | Deployed permission records and source-write behavior | `Employee.permissions`, deployed API request with `department_ids`, resulting `SourceDepartment` rows | Yes |
| BRV-DATA-001 | Runtime role/grant/policy state | PostgreSQL `\du`, `\dp`, `pg_policies`, migration head in deployed DB | Yes |
| BRV-DATA-002 | Cross-user `/agent/ask` response behavior | Two owned sessions, authenticated request traces, returned prompt/output/tool events | Yes |
| BRV-DATA-003 | Model behavior after compaction | Long untrusted history fixture, summary row, next-turn model/tool trace | Yes |
| BRV-RAG-001 | Cloud flags and trusted classification source | deployed rerank/embedding settings, upload record, egress audit | Yes |
| BRV-RAG-002 | Operator invocation and source provisioning | CLI command log, `department` argument, resulting Source/SourceDepartment rows | Yes |
| BRV-PLAT-001 | Real provider/rerank execution | `RERANK_PROVIDER`, cloud enable flags, redacted egress audit and sensitive fixture | Yes |
| BRV-BIZ-001–004 | Production approval/import and duplicate records | Draft rows, approver permissions, export/import runbook or ERP boundary, repeat invoice records | Yes |
| BRV-BIZ-005 | Operational status policy for demo flags | Production route enablement and allowed Draft kinds/status transitions | Yes |
| BRV-EVAL-001–003 | CI artifacts and seeded runtime gate | CI logs, real-loop job configuration, seeded DB/corpus, service-level probe output | Yes |
| BRV-EVAL-004–006 | Runtime evaluation/readiness results | CI job logs, checked-out corpus audit, adversarial trajectory results | Yes |
| BRV-EVAL-007 | Local faithfulness judge and threshold | `ragas` availability, judge provider config, sample dataset, threshold owner | Yes |
| BRV-FE-001 | Browser/API status behavior | Frontend build, browser export attempts for pending/rejected states, API responses | Yes |
| BRV-FE-002–003 | Browser stream/auth behavior | Built SPA, abort/EOF/401 traces, browser network logs | No |

## Integrity checks

- All 53 T1–T8 finding occurrences are represented by 40 canonical IDs; repeated IDs are explained in the relationship map.
- No provisional severity was changed or converted into a final severity; conditional labels remain conditional.
- No finding was removed because evidence was weak; `BRV-DATA-002` remains INFERRED and has Weak quality.
- No finding is marked `NEED FILE/CONTEXT` as its evidence state; missing runtime corroboration is explicitly listed instead.
- No production code, configuration, migration, or test was modified; no test command was executed.
- No T10/T11 architecture decision, KG decision, planner/executor/verifier decision, or target architecture is made here.

## Exit criteria

1. All T1–T8 finding rows are in the canonical index or represented by an explained repeated ID.
2. Evidence state, quality, file/symbol, failure path, boundary, test state, and provisional severity are present for every canonical row.
3. Relationship decisions distinguish consolidation from related/extended paths and preserve enforcement-layer evidence.
4. T10 candidates have a bounded evidence package and an explicit decision-required statement without deciding it.
5. Reproduction commands and not-run reasons are recorded with exit-code status.
6. No production code was changed and no final severity or architecture decision was made.
