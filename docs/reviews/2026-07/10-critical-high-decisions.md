# T10 — Critical/High Verification Gate

## Executive summary

- All 28 T9 candidates received a verdict: 19 Confirmed, 7 Downgraded, 0 Rejected, and 2 Need more evidence.
- No Critical finding is confirmed. Seven findings are confirmed High: `BRV-API-002`, `BRV-RAG-001`, `BRV-PLAT-001`, `BRV-BIZ-001`, `BRV-BIZ-002`, `BRV-BIZ-003`, and `BRV-FE-001`.
- Source-write scope is server-unvalidated: a seeded `doc:create:own_dept` principal can create a global or foreign-department source, and that scope is preserved into chunks and retrieval.
- The workspace configuration makes both cloud embedding and LLM reranking reachable. Caller-influenced ingest classification and the reranker's explicit `sensitive=False` create two distinct outbound-data paths.
- Financial draft scope, object-level approval, payload validation, and export-status checks are separate missing enforcement points. Maker-checker and manual ERP import reduce direct-posting risk but do not close those paths.
- `BRV-DATA-001` is downgraded because no active database-level bypass was demonstrated; the implementation has no native RLS backstop, but the reviewed application read paths use predicates.
- `BRV-DATA-002` and `BRV-DATA-004` need exact runtime/policy evidence. Neither retains a final High severity on the current evidence.
- Evaluation findings do not independently prove a production trust-boundary breach. The three provisional High eval findings are downgraded to Medium and remain regression-gate remediation work.
- No product test was executed: Python/pytest remain unavailable, and the T9 test commands therefore remain not-run evidence. Every confirmed High has a concrete required regression test below.
- Only the database isolation model is forwarded to T11. The confirmed pilot blockers have bounded fixes suitable for direct T12 remediation.

## Decision table

| ID | Original severity | Verdict | Final severity | Blocks pilot | Minimal fix | Required test | Confidence |
|---|---|---|---|---|---|---|---|
| BRV-API-002 | High | Confirmed | High | Yes | Derive allowed source scope server-side; require `doc:create:all` for global/foreign scope | Own-department writer cannot create global/foreign source; authorized global publisher can | High |
| BRV-API-003 | Medium | Confirmed | Medium | No | Apply limits to ask/agent/scan endpoint classes | Authenticated burst receives deterministic 429 without invoking downstream work | High |
| BRV-DATA-001 | High | Downgraded | Medium | Conditional | Restrict DB roles now; decide independent row enforcement in T11 | Migration/grant test plus attempted cross-department base-table read | Medium |
| BRV-DATA-002 | High | Need more evidence | Undetermined (potential High) | Conditional | Add session ownership check before constructing `AgentSession` | User B submits user A's session UUID and receives 404/403 with no memory/model call | Medium |
| BRV-DATA-003 | High | Downgraded | Medium | No | Keep raw history and summaries framed as untrusted data | Adversarial old turn survives compaction without becoming a trusted instruction | High |
| BRV-DATA-004 | Medium | Need more evidence | Undetermined (potential Medium) | No | Define retention/erase obligation before schema change | Policy-driven erase test across core and archival memory | Low |
| BRV-RAG-001 | High (conditional) | Confirmed | High | Yes | Make classification server-authoritative and default uploads to sensitive before embedding | Adversarial multipart metadata cannot trigger cloud embedding of private fixture | High |
| BRV-RAG-002 | High (conditional) | Downgraded | Medium | No | Require explicit department or privileged `--global` acknowledgement for unmanifested import | CLI rejects `--allow-unmanifested` without an explicit valid scope | High |
| BRV-RAG-003 | Medium | Confirmed | Medium | No | Replace by stable source identity and commit replacement only after successful parse/embed | Same-basename collision and failed reindex preserve prior source/version | High |
| BRV-RAG-004 | Medium | Confirmed | Medium | No | Carry heading and stable source version/hash through retrieval/SSE | Citation identifies source, location, and content version end to end | High |
| BRV-PLAT-001 | High (conditional) | Confirmed | High | Yes | Pass actual passage sensitivity to rerank or force sensitive rerank local | Sensitive retrieved chunk never reaches cloud rerank client | High |
| BRV-PLAT-002 | Medium | Confirmed | Medium | Conditional | Provision DB secret externally and reject the known default | Production preflight fails on the supplied default credential | High |
| BRV-PLAT-003 | Medium | Confirmed | Medium | Conditional | Include private-data volume and executable restore verification | Restore drill recovers DB, uploads, and private operational data | High |
| BRV-PLAT-006 | Medium | Confirmed | Medium | Conditional | Gate service readiness on DB, migration head, and vector dimension | Startup/readiness fails for stale migration and dimension mismatch | High |
| BRV-PLAT-007 | Medium | Confirmed | Medium | Conditional | Require external bootstrap secret and production Keycloak mode | Overlay preflight rejects `admin/admin` and `start-dev` | High |
| BRV-AGENT-002 | Medium | Confirmed | Medium | No | Make required run/tool audit writes fail closed or explicitly degraded | Inject audit-write failure and assert defined turn/draft behavior | High |
| BRV-BIZ-001 | High | Confirmed | High | Yes | Centralize mandatory draft department resolution and fail closed on ambiguity | Generic and AP creation reject zero/multi-department ambiguity and never create NULL scope | High |
| BRV-BIZ-002 | High | Confirmed | High | Yes | Apply `draft_scope_filter` inside approve and reject service queries | Own-department approver cannot approve/reject a foreign draft by UUID | High |
| BRV-BIZ-003 | High | Confirmed | High | Yes | Restrict kinds and validate journal schema/number invariants at create, approve, and export | Malformed/unbalanced generic journal cannot be approved or exported | High |
| BRV-BIZ-004 | Medium | Confirmed | Medium | No | Persist a canonical invoice identity and define duplicate lifecycle | Repeat and renamed-file upload produce one reviewable AP proposal | High |
| BRV-BIZ-005 | Medium | Downgraded | Low | No | Keep demo provenance non-exportable or separate from operational queue | Demo draft cannot become an operational/exportable accounting artifact | High |
| BRV-EVAL-001 | High | Downgraded | Medium | No | Label mock gate as harness-only and add a seeded real-loop job | Real `AgentSession` gate exercises retrieval, memory, tools, and routing | High |
| BRV-EVAL-002 | High | Downgraded | Medium | No | Aggregate hard-fails and tool events across every trajectory turn | Early-turn leak fails even when final turn is clean | High |
| BRV-EVAL-003 | High | Downgraded | Medium | No | Add foreign approve/reject probes to the real service path | Eval fails on the pre-fix `BRV-BIZ-002` path and passes after fix | High |
| BRV-EVAL-004 | Medium | Confirmed | Medium | No | Exercise real retrieval and memory compaction, not final-output substrings only | Retrieved/history injection cannot become a privileged next-turn instruction | High |
| BRV-EVAL-005 | Medium | Confirmed | Medium | No | Validate citation provenance and expected response behavior | Wrong source/version citation fails despite a nonempty citation list | High |
| BRV-EVAL-006 | Medium | Confirmed | Medium | No | Run checked-out readiness/data audit in CI and seeded lifecycle separately | CI fails on manifest/policy/golden inconsistency | High |
| BRV-FE-001 | High | Confirmed | High | Yes | Require `approved` status in both backend export queries; align UI | Pending/rejected individual and batch exports fail server-side | High |

## Confirmed Critical and High findings

No finding met the Critical bar with sufficient runtime evidence.

### BRV-API-002

- Original severity: High
- Verdict: Confirmed
- Final severity: High
- Evidence state: VERIFIED
- Affected subsystems: Auth/API; Tenant/RLS; Private/shared data; RAG/ingestion; Frontend/API contract
- Files/symbols reviewed: `app/api/routes_sources.py:upload_source`; `app/security/auth.py:require_permission`; `app/security/rls.py:Identity.scope_level`; `scripts/seed.py:CONTRIB_PERMS`; `app/ingestion/pipeline.py:ingest_source`; `app/rag/retriever.py:vector_search, lexical_search`; frontend source-upload consumers cited by T8
- Verified failure path: Authenticated `doc:create:own_dept` principal -> multipart `department_ids` or omitted/empty value -> unvalidated `SourceDepartment` rows or global source -> IDs copied to `Chunk.department_ids` -> retrieval treats empty scope as global -> other departments with document-read permission can retrieve the content. The standard frontend omits `department_ids`, so its default path creates global content.
- Compensating controls: Route authentication and scoped permission parsing are present; both retrieval branches apply the stored chunk-scope predicate. These controls trust the write-time metadata and therefore do not prevent a scoped writer from manufacturing an allowed/global retrieval label.
- Reachability: Reachable
- Business/security impact: Cross-department disclosure of uploaded operational content and loss of the private/shared boundary.
- Root cause: Implementation
- Minimal fix: Resolve permissible source departments from the authenticated principal, reject empty/global and foreign scope for `own_dept`, and require an explicit global-publisher permission for shared publication.
- Optional larger improvement: Define one authoritative publication/classification policy reused by UI upload, API, CLI ingestion, and background ingestion.
- Required test: Seed two departments; upload as a `doc:create:own_dept` actor using omitted, own, and foreign scopes; assert only own scope succeeds and retrieval by the other department returns no chunk.
- Blocks pilot: Yes
- Confidence: High
- Remaining evidence needed: No evidence blocks the verdict; a live DB/HTTP reproduction is still required as the fix's regression proof.

### BRV-RAG-001

- Original severity: High (conditional)
- Verdict: Confirmed
- Final severity: High
- Evidence state: VERIFIED
- Affected subsystems: Auth/API; Private/shared data; RAG/ingestion; Egress/secrets; Frontend/API contract
- Files/symbols reviewed: `app/api/routes_sources.py:upload_source`; `app/security/sensitivity.py:ingest_sensitive`; `app/ingestion/pipeline.py:ingest_source`; `app/rag/embedding.py:embed`; `.env:CLOUD_ENABLED, EMBEDDING_PROVIDER, CLOUD_EMBEDDING_*`
- Verified failure path: Authenticated document writer -> omits department scope and supplies a non-sensitive `knowledge_type` -> `ingest_sensitive` returns false -> pipeline calls `embed(..., sensitive=False)` -> current workspace selects `openai_compatible` embedding with a configured endpoint, model, and credential -> raw document blocks are sent to the external embedding provider.
- Compensating controls: Sensitive knowledge types, sensitive-department metadata, and global-plus-unknown classification fail closed; `embed` refuses cloud use when `sensitive=True` and logs a content hash before egress. They are bypassed because both inputs to the classification decision are caller-influenced on this route.
- Reachability: Reachable
- Business/security impact: A private, PII, or financial upload can be mislabeled and leave the controlled environment; the same global label also makes it shared retrieval content.
- Root cause: Mixed
- Minimal fix: Remove caller authority over sensitivity, default new uploads to sensitive, and permit cloud embedding only after a server-authoritative classification with a privileged shared-publication decision.
- Optional larger improvement: Establish a single provenance/classification record that is immutable across source, chunk, index, and egress decisions.
- Required test: Use a fake cloud embedding client and adversarial multipart inputs; assert no provider call for a private fixture regardless of supplied `knowledge_type` or omitted department scope.
- Blocks pilot: Yes
- Confidence: High
- Remaining evidence needed: Provider-side receipt/audit would strengthen runtime proof but does not block the static call-chain and active-configuration verdict.

### BRV-PLAT-001

- Original severity: High (conditional)
- Verdict: Confirmed
- Final severity: High
- Evidence state: VERIFIED
- Affected subsystems: Private/shared data; RAG/ingestion; Egress/secrets
- Files/symbols reviewed: `app/rag/retriever.py:retrieve`; `app/rag/rerank.py:llm_rerank`; `app/llm/router.py:chat, decide`; `.env:CLOUD_ENABLED, RERANK_ENABLED, RERANK_PROVIDER, CLOUD_API_KEY, CLOUD_BASE_URL`
- Verified failure path: Authenticated retrieval -> scoped/private chunks are selected -> current configuration enables provider `llm` reranking -> passage text is placed in the rerank prompt -> `llm.chat` is called with `sensitive=False` and `allow_cloud_task=True` -> router selects the configured cloud client.
- Compensating controls: Retrieval applies department predicates before rerank, and the router normally classifies supplied context/fails closed on unknown sensitivity. `llm_rerank` supplies no context and explicitly marks the prompt non-sensitive, bypassing that compensating classifier.
- Reachability: Reachable
- Business/security impact: Department-scoped/private retrieved text can be disclosed to an external model provider during a normal read request.
- Root cause: Mixed
- Minimal fix: Compute sensitivity from the selected passages and force local reranking whenever any passage is sensitive; never pass a hard-coded false classification.
- Optional larger improvement: Use a typed egress envelope carrying provenance and sensitivity, enforced centrally for every provider call.
- Required test: Configure cloud plus LLM rerank with a fake provider, retrieve a sensitive scoped chunk, and assert the cloud client receives no request while local/no-rerank fallback succeeds.
- Blocks pilot: Yes
- Confidence: High
- Remaining evidence needed: No evidence blocks the verdict; provider/network audit is needed for incident scoping, not for the code decision.

### BRV-BIZ-001

- Original severity: High
- Verdict: Confirmed
- Final severity: High
- Evidence state: VERIFIED
- Affected subsystems: Tenant/RLS; Accounting/financial state; Voucher/approval
- Files/symbols reviewed: `app/api/routes_drafts.py:propose`; `app/accounting/ap_service.py:create_invoice_draft`; `app/erp/draft_queue.py:resolve_draft_department, create_draft, draft_scope_filter`
- Verified failure path: Scoped draft creator -> generic route passes no department, or AP creator has zero/multiple departments -> `create_draft` stores `department_id=NULL` -> `draft_scope_filter` deliberately includes NULL/global rows for own-department approvers -> financial workflow data is visible across departments.
- Compensating controls: Authentication, maker-checker, payload hashing, scoped list predicates, and manual ERP import exist. None assigns or validates the draft department before the global row is committed.
- Reachability: Reachable
- Business/security impact: Cross-department visibility and handling of financial proposals, with ambiguous ownership and approval responsibility.
- Root cause: Implementation
- Minimal fix: Make department resolution mandatory in the shared creation service and reject ambiguous non-admin identities; permit global financial drafts only through an explicit privileged path.
- Optional larger improvement: Use typed accounting commands that always carry an authoritative organizational owner.
- Required test: Exercise generic and AP routes with zero, one, and multiple departments; assert non-admin zero/multiple cases fail and no NULL-scoped draft is persisted.
- Blocks pilot: Yes
- Confidence: High
- Remaining evidence needed: No evidence blocks the verdict; production role assignments only affect the number of reachable actors.

### BRV-BIZ-002

- Original severity: High
- Verdict: Confirmed
- Final severity: High
- Evidence state: VERIFIED
- Affected subsystems: Auth/API; Tenant/RLS; Accounting/financial state; Voucher/approval
- Files/symbols reviewed: `app/api/routes_drafts.py:approve, reject`; `app/security/auth.py:require_permission`; `app/erp/draft_queue.py:approve_draft, reject_draft, draft_scope_filter`
- Verified failure path: Principal with `draft:approve:own_dept` -> submits a foreign draft UUID -> route admits the scoped permission -> service loads the row with `db.get` without scope -> if pending and not self-created, approve changes it to approved; reject similarly changes it to rejected.
- Compensating controls: Advisory locking, pending-state check, maker-checker, payload hash verification, and audit logging are present. They protect concurrency, self-approval, and drift, but do not verify the approver's department authority over the object.
- Reachability: Reachable
- Business/security impact: Unauthorized cross-department approval or rejection of financial workflow state.
- Root cause: Implementation
- Minimal fix: Load the draft with `Draft.id == draft_id` plus `draft_scope_filter(identity)` inside both service methods, before any lock-dependent transition; return a non-enumerating denial.
- Optional larger improvement: Centralize all draft state transitions behind one scoped state-machine repository.
- Required test: Seed departments A/B and an A-only approver; assert list/get/approve/reject for B's draft are all denied and B's status/audit trail are unchanged.
- Blocks pilot: Yes
- Confidence: High
- Remaining evidence needed: No evidence blocks the verdict; UUID acquisition affects exploit convenience, not object-level authorization correctness.

### BRV-BIZ-003

- Original severity: High
- Verdict: Confirmed
- Final severity: High
- Evidence state: VERIFIED
- Affected subsystems: Auth/API; Accounting/financial state; Voucher/approval; Number integrity
- Files/symbols reviewed: `app/api/routes_drafts.py:DraftIn, propose`; `app/erp/draft_queue.py:create_draft, approve_draft`; `app/accounting/journal.py:JournalEntryPayload`; `app/accounting/journal_export.py:journal_to_rows`
- Verified failure path: Scoped draft creator -> posts `kind="journal_entry"` with arbitrary JSON -> generic creation stores it without `JournalEntryPayload` or number-integrity validation -> a second approver verifies only unchanged hash/maker-checker -> export renders the unvalidated payload for ERP import.
- Compensating controls: XML/agent accounting paths use deterministic journal construction, approval requires a different actor by default, payload drift is detected, and final ERP import is manual. The generic route bypasses the deterministic schema/number gate, and approval does not restore it.
- Reachability: Reachable
- Business/security impact: A formally approved/exportable accounting artifact can contain malformed, unbalanced, or unsupported values outside the deterministic accounting evidence chain.
- Root cause: Implementation
- Minimal fix: Allowlist draft kinds and validate/revalidate `journal_entry` with the strict accounting schema and number invariants at create, approve, and export boundaries.
- Optional larger improvement: Replace unrestricted generic financial drafts with typed domain commands while retaining a non-financial generic draft type if needed.
- Required test: Submit malformed, unbalanced, unknown-account, and valid journal payloads through the generic route; invalid cases must never reach approved/exportable state.
- Blocks pilot: Yes
- Confidence: High
- Remaining evidence needed: No evidence blocks the verdict; a production manual-import control can reduce realized loss but cannot validate the application boundary.

### BRV-FE-001

- Original severity: High
- Verdict: Confirmed
- Final severity: High
- Evidence state: VERIFIED
- Affected subsystems: Frontend/API contract; Accounting/financial state; Voucher/approval
- Files/symbols reviewed: `app/api/routes_drafts.py:export_draft, export_batch`; `frontend-react/src/features/chat/DraftCard.tsx`; `frontend-react/src/features/drafts/DraftsQueuePage.tsx`; `frontend-react/src/features/money/MoneyEnginePage.tsx`
- Verified failure path: Approver-visible pending or rejected journal draft -> individual or batch export request -> backend applies object scope/kind only and omits `Draft.status == "approved"` -> CSV/XLSX is returned -> artifact can be used in the documented manual ERP-import step before approval.
- Compensating controls: Export requires `draft:approve`, applies department scope, accepts only `journal_entry`, and ERP import remains a human operation. These controls do not enforce the application's approval state before producing the posting artifact.
- Reachability: Reachable
- Business/security impact: The approval lifecycle can be bypassed at the system's financial-output boundary; rejected proposals remain exportable.
- Root cause: Implementation
- Minimal fix: Require approved status in both backend queries and return a stable conflict/denial for pending or rejected rows; hide/disable the UI actions consistently.
- Optional larger improvement: Emit an immutable approved export record containing draft hash, approver, timestamp, and source lineage.
- Required test: For pending, rejected, and approved drafts, verify individual CSV/XLSX and mixed batch export; only approved items may be returned and no partial unsafe batch is allowed.
- Blocks pilot: Yes
- Confidence: High
- Remaining evidence needed: No evidence blocks the verdict; an ERP-side import policy would be an additional compensating control, not a replacement for this gate.

## Other confirmed candidates

| ID | Final severity | Evidence state | Reachability | Verified failure path / compensating control | Minimal fix and required test |
|---|---|---|---|---|---|
| BRV-API-003 | Medium | VERIFIED | Reachable | Authenticated ask/agent/scan endpoints reach costly services without route limits; authentication and global infrastructure capacity are partial controls. | Add endpoint-class limits; burst-test 429 before downstream invocation. |
| BRV-RAG-003 | Medium | VERIFIED | Reachable on operator reindex | Filename match deletes prior rows before replacement succeeds; explicit operator invocation limits exposure. | Stable identity plus transactional replacement; collision/failure test. |
| BRV-RAG-004 | Medium | VERIFIED | Reachable | Stored heading/version evidence is dropped before SSE/UI; source UUID/page are partial provenance. | Extend citation contract; assert source/location/version end to end. |
| BRV-PLAT-002 | Medium | VERIFIED | Configuration-dependent | Supplied production overlay inherits known DB credentials, but DB is internal-network only. | External secret plus default-rejection preflight. |
| BRV-PLAT-003 | Medium | VERIFIED | Configuration-dependent | Private volume is mounted but backup covers DB/uploads only; DB backup is a partial control. | Include private data and run a full restore drill. |
| BRV-PLAT-006 | Medium | VERIFIED | Configuration-dependent | Process startup can precede DB/migration/vector validation; compose health and CI migration are partial controls. | Deployment preflight and negative startup tests. |
| BRV-PLAT-007 | Medium | VERIFIED | Configuration-dependent | Optional overlay exposes Keycloak `start-dev` with predictable admin bootstrap credentials; it is not part of the base/prod overlay unless explicitly selected. | Production mode/external secret preflight. |
| BRV-AGENT-002 | Medium | VERIFIED | Reachable on audit-store failure | Run/tool audit helpers swallow errors; draft creation retains its own transactional audit and approval gate. | Define fail-closed/degraded behavior and inject audit failures. |
| BRV-BIZ-004 | Medium | VERIFIED | Reachable | Repeated AP XML submissions create independent drafts; pending review, maker-checker, and manual import limit impact. | Canonical invoice idempotency key and repeat-upload test. |
| BRV-EVAL-004 | Medium | VERIFIED | Reachable in the gate | Final-output substring detection does not exercise real retrieval/compaction; production framing is a partial control. | Add real adversarial retrieval/compaction trajectory. |
| BRV-EVAL-005 | Medium | VERIFIED | Reachable in the gate | Any nonempty citation passes and lifecycle checks retrieval metadata only; source UUID/page are partial evidence. | Validate answer-to-source/location/version linkage. |
| BRV-EVAL-006 | Medium | VERIFIED | Reachable in CI | Checked-out readiness/lifecycle commands are not release-gated; unit tests of temporary fixtures are partial controls. | Add static checked-out audit and seeded lifecycle jobs. |

## Split or disputed findings

No candidate required `Split`. The distinct remediation and enforcement layers of `BRV-BIZ-003` (payload integrity) and `BRV-FE-001` (approval-status export gate) are preserved rather than merged.

## Downgraded and rejected findings

| ID | Verdict | Final severity | Reason | Compensating control |
|---|---|---|---|---|
| BRV-DATA-001 | Downgraded | Medium | Absence of native RLS/backstop is verified, but no current application or deployed-role path was shown to read another department's rows. High would depend on an omitted predicate or direct DB privilege not evidenced. | Reviewed retrieval/list paths apply application predicates; production overlay keeps PostgreSQL off the public network. |
| BRV-DATA-003 | Downgraded | Medium | Raw history becomes a system-position summary, but no model/tool action caused by adversarial content was reproduced. | Recent memory and retrieved chunks are framed; router summary defaults to local/fail-closed; tool permissions and financial approval remain separate gates. |
| BRV-RAG-002 | Downgraded | Medium | Global unmanifested ingestion requires an explicit operator-only `--allow-unmanifested` action; it is not the default application path. | Manifest-only is default and the opt-in help text identifies the exceptional path. |
| BRV-BIZ-005 | Downgraded | Low | Mock tax/anomaly outputs are clearly marked `is_demo` and no direct ERP posting/export path for those kinds was verified. | Demo banner/provenance, maker-checker, kind-limited export, and manual ERP import. |
| BRV-EVAL-001 | Downgraded | Medium | The CI gate overstates deployed-agent coverage, but a mock-only gate is an evidence-quality/release assurance gap, not itself a reachable trust-boundary violation. | Deterministic detectors, full pytest job, DB service, and migrations still run in CI. |
| BRV-EVAL-002 | Downgraded | Medium | Final-turn-only scoring can miss an earlier failure, but no production failure is created by the evaluator itself. | Each final turn is still checked for hard fails; product-layer controls remain independent. |
| BRV-EVAL-003 | Downgraded | Medium | The draft probe omits approve/reject, but the exploitable failure is already captured and blocked under `BRV-BIZ-002`. | Scoped list predicate and its probe remain valid for the narrower list boundary. |

No finding was Rejected.

## Need more evidence

| ID | Missing evidence | Exact file/config/runtime evidence | Potential severity | Blocks decision |
|---|---|---|---|---|
| BRV-DATA-002 | Observable cross-user disclosure and actual session-ID acquisition path | Two-user DB fixture; `/api/agent/ask` request using the other user's session UUID; captured model input/output and absence/presence of ownership records | High | Yes; do not retain High without the reproduction |
| BRV-DATA-004 | Applicable retention, legal hold, deletion, and archival ownership requirements | Approved retention/erasure policy; production data categories; archival owner model; backup/restore and deletion semantics | Medium | Yes for lifecycle design, not for the seven confirmed pilot blockers |

## Cross-subsystem root causes

| Root cause | Related IDs | Evidence-backed boundary | Immediate handling |
|---|---|---|---|
| Caller-controlled authority metadata | BRV-API-002, BRV-RAG-001 | Request metadata determines global/department scope and ingest sensitivity, then propagates to retrieval and embedding. | Fail closed at upload; derive scope/classification from principal and trusted policy. |
| Sensitivity state discarded at provider boundary | BRV-PLAT-001 | Scoped passage data is reclassified as explicitly non-sensitive in reranking. | Preserve/derive sensitivity at each egress call; local fallback for sensitive content. |
| Financial invariants enforced on only some entry paths | BRV-BIZ-001, BRV-BIZ-003, BRV-BIZ-004, BRV-FE-001 | Generic creation/export bypasses department, typed journal, idempotency, or status invariants used by safer paths. | Put invariants in shared service/export boundaries, not only specialized creators/UI. |
| Object scope omitted on state transition | BRV-BIZ-002, related BRV-DATA-001 and BRV-EVAL-003 | List/read predicates exist, but approval/rejection loads by ID and the DB has no independent row backstop. | Add service predicate now; decide database isolation model separately. |
| Runtime assurance detached from the real execution path | BRV-EVAL-001–006, BRV-DATA-003 | Mock/final-only checks can be green without exercising real memory, tools, provenance, or every turn. | Retain deterministic tests and add small seeded real-path gates. |
| Deployment safety depends on operator choices | BRV-PLAT-002, BRV-PLAT-003, BRV-PLAT-006, BRV-PLAT-007 | Credentials, restore coverage, migration/vector readiness, and optional IdP mode are not uniformly preflighted. | Add fail-fast deployment checks and restore evidence. |

## Pilot blockers

| ID | Blocking reason | Required remediation | Required test |
|---|---|---|---|
| BRV-API-002 | A scoped writer can publish content globally/into a foreign department. | Server-authoritative write scope and privileged global publication. | Two-department upload plus retrieval isolation test. |
| BRV-RAG-001 | Active cloud embedding can receive privately sourced content after caller-controlled misclassification. | Trusted classification and sensitive-by-default upload. | Fake-provider adversarial upload test proving zero egress. |
| BRV-PLAT-001 | Active LLM rerank sends scoped passages to cloud as non-sensitive. | Sensitivity-aware/local rerank. | Sensitive-chunk rerank test proving zero cloud call. |
| BRV-BIZ-001 | Financial drafts can be committed as globally visible workflow state. | Mandatory, fail-closed organizational owner. | Zero/one/multi-department creation test. |
| BRV-BIZ-002 | Own-department approver can transition a foreign draft by UUID. | Scoped service query for every transition. | Cross-department approve/reject integration test. |
| BRV-BIZ-003 | Generic journal route bypasses deterministic schema and number integrity. | Shared kind/schema/number validation at create/approve/export. | Invalid generic journal lifecycle test. |
| BRV-FE-001 | Pending/rejected journals can be exported for manual ERP import. | Backend approved-status gate on individual and batch export. | Status-matrix export contract test. |

Conditional operational prerequisites before using the affected deployment path: `BRV-PLAT-002` (default DB credential), `BRV-PLAT-003` (private-data recovery), `BRV-PLAT-006` (schema/vector readiness), and `BRV-PLAT-007` (optional Keycloak overlay).

## Direct T12 remediation candidates

| ID | Implementation scope | Files/modules | Required test |
|---|---|---|---|
| BRV-API-002 | Source upload authorization and global-publisher rule | `app/api/routes_sources.py`, auth permission seed/admin vocabulary | Two-department upload/retrieval isolation |
| BRV-RAG-001 | Trusted ingest classification and sensitive default | source route, `app/security/sensitivity.py`, ingestion/embedding boundary | Adversarial metadata with fake cloud embedder |
| BRV-PLAT-001 | Sensitivity-aware rerank | `app/rag/retriever.py`, `app/rag/rerank.py`, router test doubles | Private chunk never calls cloud reranker |
| BRV-DATA-002 | Session ownership guard, independent of final severity | `app/api/routes_agent.py`, conversation/session service | Cross-user session UUID denied before memory read |
| BRV-DATA-003 | Trust framing through compaction | `app/agent/memory.py`, agent summary preparation | Adversarial compaction/next-turn test |
| BRV-BIZ-001 | Mandatory draft department | `app/erp/draft_queue.py`, generic/AP callers | Organizational-scope matrix |
| BRV-BIZ-002 | Scoped approval/rejection | `app/erp/draft_queue.py`, route/service tests | Foreign transition denied |
| BRV-BIZ-003 | Typed journal validation | draft route/queue and accounting schema/export | Invalid payload lifecycle rejected |
| BRV-BIZ-004 | AP idempotency identity | invoice parser/AP service/draft persistence | Repeat/renamed upload deduplicated |
| BRV-FE-001 | Approved-only export | draft export routes and frontend controls | Individual/batch status matrix |
| BRV-API-003 | Endpoint rate limits | ask/agent/scan routes and limiter config | 429 test without downstream call |
| BRV-RAG-002–004 | CLI scope, replacement safety, citation contract | ingestion CLI/pipeline/models/retrieval/SSE | Scope rejection, collision rollback, provenance E2E |
| BRV-PLAT-002–003, BRV-PLAT-006–007 | Deployment preflight and recovery scripts | compose/deploy/config/backup-restore | Negative preflight and restore drill |
| BRV-AGENT-002 | Audit failure policy | agent loop/tool audit helpers | Injected audit persistence failure |
| BRV-EVAL-001–006 | Real-path and whole-trajectory gates | eval harness/probes/CI | Pre-fix regressions fail deterministic/seeded jobs |

## T11 architecture inputs

| Decision topic | Related finding IDs | Options | Constraints | Evidence |
|---|---|---|---|---|
| Independent database isolation model for pooled HTTP, agent, MCP, and worker access | BRV-DATA-001; related BRV-BIZ-002, BRV-DATA-002 | Native PostgreSQL RLS with transaction-local principal context; strictly separated least-privilege service roles plus mandatory repository predicates; hybrid backstop | Async connection pooling must not leak context; background jobs need explicit principals; migrations/admin tasks need controlled bypass; local `draft_scope_filter` fix must not wait for this decision | `alembic/versions/0004_db_roles.py:upgrade` creates unfiltered views/no policies; `app/database/__init__.py` uses one base-table session factory with no role/context switch; reviewed read paths do have application predicates |

No decision about KG, planner/executor/verifier, service splitting, or repository restructuring is introduced by T10.
