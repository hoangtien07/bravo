# T8 — Frontend/API Consumer Consistency

Scope read: T0/T1/T4 artifacts; `frontend-react/src/**`, frontend build config, API client/types/SSE handling, and directly consumed backend routes/schemas. No frontend test was found under `frontend-react`; no build/typecheck was run because the baseline records no usable host Node/package-manager toolchain.

## Frontend → backend contract map

| Consumer | Endpoint / contract | VERIFIED consumer behavior | Boundary note |
|---|---|---|---|
| Chat store | `POST /api/chat/{conversation_id}/messages` accepts `{question}` and streams id/source/step/tool/draft/answer/done/error events. | `api/sse.ts:streamChat` uses authenticated fetch stream; `store/chat.ts` stores citations, tool events, draft event, grounding and routing state. | Client-generated UUID is accepted only after backend `ensure_conversation` owner check. |
| Conversation UI | `/api/conversations/*`, `/api/shared/{token}`, feedback/share/delete contracts. | `ChatView`, `ConversationSidebar`, and `SharedPage` call the matching routes. | Shared page is deliberately unauthenticated by token; T1 owns token/access policy. |
| Knowledge upload | `POST /api/sources` accepts multipart `file`, optional `knowledge_type`, optional comma-separated `department_ids` whose default is global. | `DocumentsPage` sends file and optional free-text knowledge type, but never `department_ids`; chat upload sends file only. | Consumer behavior creates globally scoped sources and exposes caller-controlled classification (continued T3 findings). |
| Invoice/AP UI | `POST /api/invoices/draft` multipart file → `{draft_id, kind, status, needs_review, validation_flags, journal}`. | `MoneyEnginePage` and XML branch in `ChatView` submit file and render `journal` as a draft card. | No client-side department parameter exists; T5 owns service-level scope/approval correctness. |
| Draft approval/export | `/api/drafts`, approve/reject, individual export and batch export. | Queue, money, chat, anomaly, and tax screens invoke matching endpoints with JSON bodies where required. | Consumer exposes export without a state gate; backend also accepts any scoped `journal_entry` status (BRV-FE-001). |
| Tax/anomaly | `/api/agents/tax/reconcile`, `/api/agents/anomaly/scan` and filtered draft list. | Pages display `DemoBanner`, invoke scan/reconcile, then create/approve/reject shared drafts. | T5’s `MockDataSource` workflow remains visible as an approvable shared draft state. |
| Graph/source file | `/api/graph`, `/api/sources/{id}/file`. | `GraphView` uses authenticated fetch and opens a blob for a selected source. | Route RLS is backend-enforced; frontend supplies no tenant/scope fields. |
| Auth/admin | Login, `/api/me`, OIDC config/login, admin user/department/usage routes. | Client bearer wrapper and admin JSON payloads match observed Pydantic schemas. | Direct `fetch` paths bypass the wrapper’s 401 reset behavior (BRV-FE-003). |

## Findings

| ID | Severity tạm thời | Evidence state | File:symbol | Evidence ngắn | Consumer/impact | Next action | Needs Sol review |
|---|---|---|---|---|---|---|---|
| BRV-API-002 | High | VERIFIED | `frontend-react/src/features/documents/DocumentsPage.tsx:upload`; `features/chat/ChatView.tsx:onUpload`; `app/api/routes_sources.py:upload_source` | Both frontend source-upload paths omit `department_ids`; route default is `""`, parsed as no source departments/global scope. | UI uploads become shared/global by default, feeding T3’s source→chunk retrieval scope failure path. | Retain T2/T3 ID; make scope explicit and server-authoritative, then add frontend/API upload contract coverage. | Yes |
| BRV-RAG-001 | High (conditional) | VERIFIED | `frontend-react/src/features/documents/DocumentsPage.tsx:ktype`, `upload`; `app/api/routes_sources.py:upload_source` | UI offers an arbitrary `knowledge_type` text field and passes it unchanged; T3 verifies this field participates in sensitivity classification before embedding. | A user-facing classification control can influence whether uploaded content is treated as non-sensitive for cloud embedding. | Retain T3 ID; remove untrusted classification authority from the UI path and test adversarial multipart input. | Yes |
| BRV-FE-001 | High | VERIFIED | `frontend-react/src/features/chat/DraftCard.tsx`; `features/drafts/DraftsQueuePage.tsx`; `features/money/MoneyEnginePage.tsx`; `app/api/routes_drafts.py:export_draft`, `export_batch` | Chat draft card exposes CSV while pending; queue exposes individual CSV/XLSX for every listed status and batch export for selected journal drafts. Backend export queries scope/kind only, without `Draft.status == "approved"`. | Pending or rejected journal payloads can be downloaded for manual ERP import, bypassing the UI’s apparent approval lifecycle. | Gate export in backend by approved state and align UI controls; add pending/rejected export contract tests. | Yes |
| BRV-FE-002 | Medium | VERIFIED | `frontend-react/src/api/sse.ts:streamChat`; `frontend-react/src/store/chat.ts:send`, `stop`; `app/api/routes_conversations.py:chat_stream` | Stream parser returns quietly when the reader ends and does not synthesize a terminal event. Abort/network rejection escapes `await streamChat`; `stop` clears sending but does not clear the assistant message’s `streaming` state. | Cancelled/disconnected requests can leave an indeterminate assistant message and skip completion refresh/navigation behavior. | Normalize abort/EOF/error into an explicit terminal state and add stream cancel/EOF tests. | No |
| BRV-API-006 | Medium | VERIFIED | `app/api/routes_conversations.py:gen`; `frontend-react/src/api/sse.ts:streamChat`; `store/chat.ts:send`; `features/chat/ChatView.tsx:onUpload` | Backend serializes `str(exc)` in SSE error events; frontend appends that message into the visible chat. Manual upload code also renders backend `detail` directly. | T1’s raw-error disclosure reaches the end user through the primary UI, including stream failures. | Retain T1 ID; replace client-visible internals with stable error codes/messages and test stream/upload failures. | No |
| BRV-RAG-004 | Medium | VERIFIED | `frontend-react/src/api/types.ts:SseEvent`; `features/chat/ChatView.tsx:cites`; `features/chat/MessageBubble.tsx:focusSource` | SSE retains only `string[]` citation labels; panel supports index/scroll only. It has no source ID, page/cell/heading, content version/hash, or authenticated file link. | T3’s missing citation provenance cannot be repaired by the frontend; users cannot verify a cited source beyond its display string. | Retain T3 ID; extend retrieval/SSE citation contract before adding deep-link UI. | No |
| BRV-FE-003 | Medium | VERIFIED | `frontend-react/src/api/client.ts:api`; `api/sse.ts:streamChat`; `features/chat/ChatView.tsx:onUpload`; `features/drafts/DraftsQueuePage.tsx:exportBatch` | Only `api()` clears the stored token and invokes the unauthorized handler on 401. SSE, uploads, exports, source-file opening, and downloads use direct `fetch`/`downloadFile` without that path. | An expired session on these flows surfaces a local error while leaving stale client authentication state and inconsistent recovery. | Centralize authenticated fetch/error handling or make every direct consumer handle 401 consistently; add frontend contract tests. | No |

## SSE, error, and citation behavior

| Behavior | Evidence | State |
|---|---|---|
| Authenticated POST streaming | Fetch stream includes bearer header and abort signal; backend returns `text/event-stream`. | VERIFIED |
| Success terminal data | `done` maps to grounded/routed-cloud/clarify state in the store. | VERIFIED |
| Backend stream exception | Backend emits a single `error` SSE data record; frontend displays its message. | VERIFIED; continued BRV-API-006 |
| Client abort / EOF terminal state | No local `done`/`error` event is emitted on a normal EOF; abort rejection is not caught in store `send`. | VERIFIED; BRV-FE-002 |
| Citation presentation | Numeric markers open a local side panel indexed by SSE citation order. | VERIFIED; provenance depth limited by BRV-RAG-004 |

## Test/build evidence

| Evidence | State | Notes |
|---|---|---|
| Frontend test files | VERIFIED absent from `frontend-react` file inventory. | No component, SSE, API-contract, or e2e frontend test was found. |
| Build/typecheck commands | `npm run build`; `npm run typecheck` from `frontend-react/package.json`. | Not run: Node/package manager unavailable in baseline. |
| Backend chat tests | `tests/test_chat.py` covers SSE sequence and conversation owner behavior with DB availability. | Read only; it does not exercise the browser parser, abort/EOF handling, frontend upload defaults, or exported draft UI states. |
| Static deployment path | Vite build uses `/static/`; dev proxy routes `/api` and `/shared` to port 8000; FastAPI mounts frontend static files. | VERIFIED relative API design; no frontend environment endpoint variable is used. |

## T8 exit check

- Frontend call sites are mapped to their backend route/schema consumers; no general UI/UX assessment is included.
- Request scope, streaming termination, error rendering, draft lifecycle, and citation-consumer mismatches have file/symbol evidence.
- Seven findings are within the cap; repeated T2/T3/T1 paths retain their existing IDs.
- No production code, configuration, migration, or test was changed.
