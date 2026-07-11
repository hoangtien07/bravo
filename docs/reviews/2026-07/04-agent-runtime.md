# T4 — Agent Runtime, Tool Authority & MCP Boundary

Scope read: T0/T1/T2/T3/T6 artifacts; `app/agent/**`, `app/llm/router.py`, `app/mcp/server.py`, agent/conversation/draft routes, direct draft dependency, and agent/MCP tests. No test was run: the baseline records no usable host Python/pytest toolchain.

## Responsibility loop and request paths

| Flow | VERIFIED implementation trace | Authority / output boundary |
|---|---|---|
| HTTP agent turn | `app/api/routes_agent.py:agent_ask` requires `doc:read`, accepts `AgentAskRequest.session_id`, then constructs `AgentSession` and calls `step`. | Per-tool permission is not implied by the route permission; it is evaluated in the registry. Session ownership is not checked on this path (BRV-DATA-002). |
| Conversation SSE turn | `app/api/routes_conversations.py:chat_stream` first calls `conv_svc.ensure_conversation(..., identity.employee_id)`, then uses the conversation UUID as `AgentSession.session_id` and calls `step_stream`. | This path has a conversation-owner gate before agent memory is loaded. |
| Agent turn | `app/agent/loop.py:AgentSession._prepare_turn` loads history, adds the caller turn, rewrites the retrieval query, retrieves with `identity`, frames each retrieved chunk, filters tools, and adds optional playbook text to messages. `step` / `step_stream` then repeat decision → `call_tool` → observation until answer/clarify/budget stop. | Retrieval gets the caller `Identity`; only tools surviving the registry filter are exposed to the model. Playbook selection supplies a prompt hint, not a code-enforced source/tool allowlist. |
| Financial answer | `loop._metric_lookup` delegates to deterministic `data_layer.semantic.execute`; `loop._finish_answer` / `_stream_answer` invoke `verify_numbers` only when an engine value was obtained. | Metric number claims are checked against engine values; KB-only answers are marked grounded when citations exist, without the number gate. |
| Draft lifecycle | `tools.call_tool` routes every `read_only=False` tool to `draft_queue.create_draft`; `draft_queue.approve_draft` completes the linked run through `runs.complete_on_approval`. `routes_drafts:approve` requires `draft:approve`. | Built-in `create_journal_entry` validates a journal payload before draft creation; the built-in write function is not executed. Scope resolution rejects a non-admin identity with no single resolvable department. T5 should verify accounting/approval semantics. |
| MCP KB search | `mcp.server:search_kb` extracts Bearer token, calls `kb_search`; `kb_search` resolves an `Identity` then calls `retriever.retrieve(db, identity, ...)`. | Missing/invalid token returns an error response; current server exposes only `search_kb`. Retrieval/RLS behavior is handed to T2/T3. |

## Tool and context controls observed

| Control | VERIFIED evidence | Boundary note |
|---|---|---|
| Tool authority | `app/agent/tools.py:filter_tools_by_permission` omits tools without `required_permission`; `call_tool` repeats the check before execution. `metric_lookup` requires `metric:read`; `create_journal_entry` requires `draft:create`. | A forged model tool name is rechecked. Existing permission vocabulary inconsistency remains cross-referenced as BRV-API-001. |
| Write authority | `Tool.__post_init__` forces approval for `read_only=False`; `call_tool` creates a draft and does not call the write function. | Direct draft creation has an explicit department resolution gate for non-admin identities. |
| Prompt-data boundary | `loop._prepare_turn` wraps retrieved `Chunk.content` with `frame_untrusted`; `MemoryStore.recall_recent_for_prompt` frames rows whose stored `trust_level` is not `trusted`. | Long-history summary is inserted as a `system` message without the same frame (BRV-DATA-003). |
| Egress routing | Decision calls supply `context=chunks + engine_values` to `llm.chat`; `router._classify` derives sensitivity from supplied context. The optional compose stream supplies an empty `engine_values` list only on the non-metric branch; `classify_context([])` is fail-closed local. | T6's `BRV-PLAT-001` remains limited to LLM rerank; no additional cloud-egress path was verified in this T4 scope. |
| Budget/abstention | `Budget` limits steps, token count, and deadline; `step` returns a safe stop message on `BudgetExceeded`; malformed or missing decisions lead to clarify/answer fallback. | The structured-output retry makes an additional LLM call before a second budget check (BRV-AGENT-001). |

## Findings

| ID | Severity tạm thời | Evidence state | File:symbol | Evidence ngắn | Consumer/impact | Next action | Needs Sol review |
|---|---|---|---|---|---|---|---|
| BRV-DATA-002 | High | INFERRED | `app/api/routes_agent.py:agent_ask`; `app/agent/loop.py:AgentSession._prepare_turn`; `app/agent/memory.py:recall_recent` | `/agent/ask` accepts caller-supplied `session_id` and constructs `AgentSession` directly. `_prepare_turn` loads messages by that session UUID; unlike `/chat/{conversation_id}/messages`, this route does not call `ensure_conversation` or another ownership check. | A caller knowing another session UUID can place that session’s prior turns in the agent prompt. The actual disclosure in model output is not demonstrated here, so that last step remains inferred. | Retain T2 ID; require server-side session ownership/creation before memory access and add an `/agent/ask` cross-user session test. | Yes |
| BRV-DATA-003 | High | VERIFIED | `app/agent/memory.py:history_for_prompt`; `app/agent/loop.py:_summarize`, `_prepare_turn` | Old raw message content is concatenated into the summarizer input; resulting text is persisted as `MemoryBlock("summary")` and later inserted as a `system` message, while only recent rows receive `frame_by_trust`. | Persisted/LLM-produced summary crosses from untrusted history into high-priority prompt context on later turns. | Retain T2 ID; define a trusted-summary contract and test adversarial historical content through compaction and the next turn. | Yes |
| BRV-AGENT-001 | Medium | VERIFIED | `app/agent/loop.py:AgentSession._llm_decide`, `step`, `step_stream` | The loop calls `tracker.check()` before `_llm_decide`, but `_llm_decide` may issue one retry `llm.chat(...)` after malformed output without another tracker check; both calls are counted only after `_llm_decide` returns. | A malformed response can make one additional LLM call after an applicable token/deadline threshold and does not consume a distinct step before retry. | Charge/check the retry before dispatch; add max-token, deadline, and retry-count tests. | No |
| BRV-AGENT-002 | Medium | VERIFIED | `app/agent/loop.py:_open_run`, `_close_run`, `_audit`; `app/agent/tools.py:_audit_attempt` | Agent-run and generic tool/budget audit helpers catch all exceptions and continue. A turn can therefore create/use a draft path even when its AgentRun or tool-attempt audit record was not persisted; draft creation has its own audit in `draft_queue.create_draft`. | Run-level lifecycle and attempted-tool observability can be absent or incomplete, weakening reconciliation of a user turn to a draft without bypassing the draft’s own approval gate. | Decide which audit/run writes must be transactional for operational reconciliation; add a DB-failure behavior test. | No |

## Test evidence and runtime gaps

| Evidence | State | Notes |
|---|---|---|
| `tests/test_agent_loop.py` covers tool filtering/recheck, write-to-draft rather than direct execution, budget tracker, bounded trajectory, and metric verification. | Read only; not executed | No test exercises malformed-decision retry against a spent budget, long-history summary trust transition, or `/agent/ask` session ownership. |
| `tests/test_chat.py` checks the `/chat/{id}/messages` owner path and multi-turn prompts when Postgres is reachable. | Read only; not executed | This does not cover the separate `/agent/ask` route. |
| `tests/test_agent_runs.py` covers run pause then completion on approval when Postgres is reachable. | Read only; not executed | It does not simulate failure of run/audit persistence during a live agent turn. |
| `tests/test_mcp_server.py` checks invalid token rejection and MCP mount; its token-extraction test reconstructs header behavior rather than invoking the closure through a full MCP request. | Read only; not executed | A valid-token, scoped retrieval, and deployed FastMCP context handshake remain `NEED FILE/CONTEXT`. |

## Handoff

| Task | Recommended input | Important references | Missing context |
|---|---|---|---|
| T5 — Accounting/ERP | `app/agent/tools.py`, `app/agent/loop.py`, `app/erp/draft_queue.py`, `app/api/routes_drafts.py`, accounting tests | `create_journal_entry`, `_build_journal_payload`, `approve_draft`, BRV-AGENT-002 | ERP export/import execution and production approval roles are `NEED FILE/CONTEXT`. |
| T2 — Data/memory follow-up | `app/api/routes_agent.py`, `app/agent/memory.py`, conversation service/tests | BRV-DATA-002, BRV-DATA-003 | A reproducible cross-user request and database role behavior are `NEED FILE/CONTEXT`. |
| T3 — RAG follow-up | `app/agent/loop.py:_prepare_turn`, `app/mcp/server.py:kb_search` | identity passed to `retriever.retrieve`, `frame_untrusted` | Valid MCP token and scoped retrieval integration result are `NEED FILE/CONTEXT`. |
| T6 — Platform/egress follow-up | `app/agent/loop.py:_llm_decide`, `_stream_answer`, `app/llm/router.py` | sensitivity context handoff; T6 `BRV-PLAT-001` | Runtime cloud flags and provider behavior are `NEED FILE/CONTEXT`. |

## T4 exit check

- HTTP, conversation SSE, agent loop, tool, draft/run, and MCP request paths are mapped from code.
- Tool filtering/recheck, draft-only write path, number verification, retrieved-text framing, and fail-closed empty compose context are recorded as implementation evidence.
- Four evidence-backed findings are listed; no target architecture, production change, or test execution is included.
