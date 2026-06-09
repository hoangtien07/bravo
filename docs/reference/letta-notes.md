# Letta (MemGPT) — Reference Notes

**Là gì:** Framework agent LLM *có trạng thái* với bộ nhớ dài hạn. **Vai trò với BRAVO:** bộ não agent — bộ nhớ hội thoại + tool-calling gọi REST ERP + cơ chế duyệt.

**Stack:** FastAPI · async SQLAlchemy 2.0 · PostgreSQL + pgvector (cũng hỗ trợ Pinecone/Turbopuffer/sqlite-vec) · Redis · Python 3.11–3.13. Hỗ trợ vLLM/Ollama/llama.cpp/LM Studio cục bộ.

---

## 1. Kiến trúc bộ nhớ ba tầng ⭐⭐ — *điểm vàng*
- **Core memory (trong context):** `letta/schemas/memory.py` — list `Block` (label, value, limit, description), biên dịch vào system prompt; agent tự sửa qua `core_memory_append/replace`; có block read-only. Render nhiều kiểu (XML, line-numbered cho Anthropic, git-backed).
- **Archival memory (lâu dài, vector):** `Passage` có embedding; `archival_memory_insert(content, tags)` / `archival_memory_search(query, top_k, tags)`; lưu `services/passage_manager.py`, `orm/passage.py`. Lọc theo tag.
- **Recall memory (lịch sử hội thoại):** `conversation_search()` lọc theo role/ngày/semantic.

**Context window management:** `services/context_window_calculator/` — đếm token (tiktoken/LLM-specific), đóng gói system + core + tool schema + recall theo budget; khi áp lực context → tóm tắt.

**Lấy cho BRAVO:** core = ngữ cảnh người dùng/phiên (đơn vị, kỳ đang xét); archival = tóm tắt tri thức/bản ghi ERP hay dùng; recall = hội thoại. **Context management cực quan trọng vì LLM cục bộ có context nhỏ.**

## 2. Tool / function-calling ⭐
- `letta/schemas/tool.py` — `Tool`(source_code, json_schema, tool_type, **`return_char_limit`**, **`default_requires_approval`**, `enable_parallel_execution`, `pip_requirements`).
- ToolType: `LETTA_CORE` (memory), `CUSTOM` (Python sandbox), `EXTERNAL_MCP`, `EXTERNAL_COMPOSIO`.
- Thực thi: `letta/services/tool_executor/` — custom tool chạy **sandbox**, agent_state truyền dạng **deep copy** (chặn mutate trái phép); kết quả truncate theo `return_char_limit`.
- Sinh schema từ source: `letta/functions/schema_generator.py`.

**Lấy cho BRAVO:** **ERP read tools** xây theo pattern CUSTOM tool (REST client, type hints + docstring → json_schema). `return_char_limit` chặn response ERP lớn làm tràn context.

## 3. `requires_approval` — *khớp nguyên tắc non-invasive của BRAVO* ⭐
- Tool có cờ `default_requires_approval`; agent_state có khái niệm `pending_approval`. Tool ghi → trả về yêu cầu chờ duyệt thay vì thực thi.

**Lấy cho BRAVO:** đây chính là cơ chế "bản ghi nháp chờ duyệt" ở tầng agent — kết nối với Draft Queue + workflow duyệt (kiểu arkon).

## 4. Vòng lặp agent
- `letta/agent.py` — `step()`: nạp message in-context → biên dịch system prompt (memory + metadata + tool schema) → gọi LLM → parse tool_calls → `execute_tool_and_persist_state()` (route theo tool_type) → persist thay đổi memory → kiểm tra áp lực context (tóm tắt) / heartbeat (chaining).
- **Tool rules:** ràng buộc control-flow (terminal tools, init tools, dependency) — kiểm soát agent chỉ được làm gì.

**Lấy cho BRAVO:** tool rules hữu ích để **cưỡng chế** agent: vd chỉ được gọi ERP read tools đã duyệt; tool ghi luôn `requires_approval`.

## 5. Multi-agent & LLM abstraction
- Multi-agent: `Group` ORM, `delegate_to_agent()`, chia sẻ archival qua `ArchivesAgents`. (Chưa cần cho MVP; hữu ích cho phân tích chủ động nhiều phòng ban về sau.)
- LLM: `letta/llm_api/llm_client.py` factory cho 15+ provider; `letta/local_llm/` cho vLLM/Ollama/llama.cpp/koboldcpp. `docker-compose-vllm.yaml` là tham chiếu deploy LLM cục bộ.

## 6. Cấu trúc
`letta/agent.py` (+ `agents/`) · `schemas/` (memory, tool, message, passage, block) · `orm/` · `services/` (agent/block/message/passage/tool manager, `tool_executor/`, `context_window_calculator/`) · `functions/function_sets/` (base/builtin/multi_agent/files) · `llm_api/` · `local_llm/` · `prompts/` · `server/`.

---
## ✅ Việc cần làm khác đi cho BRAVO
- **Không dùng full framework** — mượn *pattern* memory + tool + approval. Letta nặng; BRAVO cần lõi gọn, kiểm soát chặt hơn.
- Mọi tool **đi qua RLS** (letta không có phân quyền phòng ban — ghép từ arkon).
- ERP tools **read-only**; tool ghi *bắt buộc* `requires_approval` qua tool rules — không để ngỏ.
- Cân nhắc context nhỏ của Qwen cục bộ → tối ưu nén bộ nhớ.
