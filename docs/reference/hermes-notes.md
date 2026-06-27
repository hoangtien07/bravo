# hermes-agent (Hermes / NousResearch) — Reference Notes

**Là gì:** Framework **agentic CLI/TUI** mã nguồn mở, nhiều star (NousResearch). Một agent đa nền tảng (CLI, TUI React-Ink, Telegram/Discord/Slack, desktop) với vòng lặp tự cải thiện: tự sinh & nâng cấp *skills*, lưu phiên (SQLite FTS5), **nén ngữ cảnh**, chạy được từ VPS rẻ tới GPU cluster.

**Vai trò với BRAVO:** **kho pattern kỹ thuật agent** ở quy mô lớn, được kiểm chứng bởi cộng đồng. Mượn về: **nén trajectory** (sống còn vì LLM cục bộ context nhỏ), **write-approval staging** (khớp non-invasive), kiến trúc **tool registry/toolset**, **provider abstraction** có nhánh offline, **state/resume**, **cron + script-injection**, và **mô hình tin cậy bảo mật** (sandbox là biên, heuristic không phải biên).

**Stack:** Python · OpenAI-compatible client cho ~30 nhà cung cấp LLM (gồm Ollama/LM Studio/vLLM qua `base_url`) · SQLite (WAL) cho state · plugin/skill dạng thư mục có manifest · Docker/s6-overlay để self-host. File lõi **rất lớn**: `cli.py` (~700KB), `run_agent.py`, `hermes_state.py` (~233KB), `trajectory_compressor.py`.

> ⚠️ Đây là **framework cloud-default, đơn người dùng, không RLS**. Mượn *pattern*, không fork khối; mọi thứ phải gập vào 4 bất biến của BRAVO.

---

## 1. Nén ngữ cảnh — trajectory_compressor.py ⭐⭐ — *điểm vàng cho LLM cục bộ*
- Chiến lược **head/tail bảo vệ, nén giữa**: giữ system + human/tool đầu tiên; giữ `protect_last_n_turns` (mặc định 4) turn cuối; **chỉ nén phần giữa đủ** để lọt `target_max_tokens` (~15K mặc định).
- Vùng nén bị thay bằng **một summary** (`summary_target_tokens` ~750) gắn prefix `"[CONTEXT SUMMARY]:"`; gọi LLM phụ để tóm tắt *hành động tool + kết quả + quyết định + dữ liệu* (không chỉ cấu trúc). Có retry + backoff, fallback nếu thất bại.
- **Boundary snapping** theo cặp `<tool_call>`/`<tool_response>` để không cắt giữa một lần gọi tool. Đếm token bằng tokenizer HF. Có metric đầy đủ (ratio, tokens_saved, turns_removed).

**Lấy cho BRAVO:** Qwen cục bộ context nhỏ ⇒ đây là kỹ thuật trực tiếp dùng được. Với BRAVO: **luôn bảo vệ** system + ngữ cảnh người dùng (đơn vị/kỳ) + **các bản nháp đang chờ duyệt + dòng số có trích dẫn**; chỉ nén phần hội thoại trung gian. Khác Letta (nén dạng memory blocks) — Hermes nén *trajectory message*; hai cách bù nhau, xem [[letta-notes]].

## 2. Write-approval staging ⭐ — *khớp nguyên tắc non-invasive của BRAVO*
- `tools/write_approval.py`: cổng phê duyệt theo subsystem (`memory.write_approval`, `skills.write_approval`). Khi bật → **không commit; stage vào `~/.hermes/pending/{memory,skills}/*.json`** chờ duyệt.
- Phân biệt **foreground** (người dùng có mặt → có thể *inline prompt* duyệt ngay) vs **background/daemon** (luôn stage, vì luồng nền không hỏi được). Trả `approved` / `staged` / `blocked`.
- `acp_adapter/edit_approval.py`: hook qua ContextVar — yêu cầu duyệt **trước khi ghi file** khi tích hợp editor (Zed/VS Code).
- `tools/registry.py`: mỗi tool có `check_fn` (TTL-cache) probe điều kiện (API key/Docker…); tool bị ẩn khỏi schema nếu không thoả.

**Lấy cho BRAVO:** pattern *stage-rồi-duyệt* + phân biệt nguồn gọi (foreground/background) là chính xác cái BRAVO cần. Khác biệt: Hermes chỉ gate memory/skills; **BRAVO phải gate MỌI tác vụ ghi** (tạo bút toán/hoá đơn nháp) và đẩy pending về **Draft Queue trên ERP** (mượn workflow duyệt của arkon), không phải file `~/.hermes/pending`. Cùng họ với `requires_approval` của Letta — xem [[letta-notes]] và [[arkon-notes]].

## 3. Vòng lặp agent + ngân sách + ngắt sạch
- `agent/conversation_loop.py` → `run_conversation()`: while còn `max_iterations` (mặc định ~90) & `iteration_budget`; gọi `chat.completions.create(tools=…)` → nếu có `tool_calls` thì thực thi (tuần tự/đồng thời) rồi append `role:tool` → lặp; không có tool_calls ⇒ trả lời xong. Có **"grace call"** một lần khi vừa hết budget.
- `agent/error_classifier.py`: phân loại lỗi (rate_limit/token_limit/permission/billing/network) → fallback model + backoff jitter. Kiểm tra **context tối thiểu của Ollama** (≥~64K) và cảnh báo nếu nhỏ.
- Ngắt sạch qua `_interrupt_requested` / SIGINT / `/stop`.

**Lấy cho BRAVO:** loop **đồng bộ + ngân sách iteration rõ ràng** hợp với on-prem (tài nguyên dự đoán được). Mượn: trần lặp + budget + grace-call + ngắt sạch. Đối chiếu với agent loop của BRAVO (ADR-0010) và tool-rules của Letta.

## 4. Tool registry / Toolsets / Skills / Plugins (kiến trúc mở-ở-cạnh)
- **Tool**: `tools/registry.py` auto-discover (quét `tools/*.py` tìm `registry.register(...)`), mỗi tool có `name/toolset/schema/handler/check_fn/requires_env`. `toolsets.py` gom tool thành bộ (web/research/terminal…) bật/tắt **theo nền tảng** qua config.
- **Skill**: thư mục `skills/<category>/<name>/` có `SKILL.md` (frontmatter: name/description/version/platforms/config) + `scripts/` + `references/` + `tests/`; `optional-skills/` là loại nặng không bật mặc định. `agent/curator.py` theo dõi tần suất dùng → **auto-archive skill cũ**, skill *pinned* được miễn.
- **Plugin**: `plugins/<name>/plugin.yaml` (kind: general/memory/model-provider/context-engine/image-gen); `register(ctx)` đăng ký tool/CLI/hook (pre/post tool, pre/post LLM). **Chính sách cứng: plugin KHÔNG sửa file lõi** — cần năng lực mới thì mở rộng *surface* chung.

**Lấy cho BRAVO:** mô hình **lõi hẹp + mở rộng ở cạnh** rất đáng học để giữ lõi gọn (anti-over-engineering). `SKILL.md` frontmatter + `check_fn`/`requires_env` là khuôn tốt cho ERP tools (khai báo điều kiện sẵn sàng, ẩn tool khi thiếu cấu hình). **Lưu ý RLS**: skill/memory của Hermes không có ngữ cảnh tenant → BRAVO phải bơm `user_id`/`department` vào mọi dispatch để skill không rò dữ liệu chéo.

## 5. Provider abstraction + nhánh offline
- `providers/__init__.py` + `plugins/model-providers/*`: `ProviderProfile` (name/api_mode/models/base_url…), **lazy-discover** (chỉ nạp provider khi chọn → khởi động nhẹ). Định tuyến theo tác vụ (embedding/vision/title dùng model khác nhau).
- **Offline**: provider `custom` + `base_url: http://localhost:11434/v1` (Ollama), Ollama-Cloud, LM Studio/vLLM tương tự; có hướng dẫn local-ollama (yêu cầu context ≥65K). Cấu hình `fallback_providers` cho phép **90% local + 10% cloud** khi task khó.

**Lấy cho BRAVO:** xác nhận hướng đi **Model Router** (ADR-0003/0009): local mặc định + cloud opt-in. Mượn: lazy discovery + per-task model + fallback list. **Đảo ưu tiên**: Hermes cloud-default; BRAVO **local-default, cloud chỉ khi người dùng bật** và đi qua egress-classifier (ADR-0011).

## 6. State / resume + tự động hoá + bảo mật
- **State**: `hermes_state.py` — SQLite WAL, bảng `sessions` (có `parent_session_id`, `end_reason=compression/branched`), `messages` (cờ `compacted`), FTS5 search; `/resume` khôi phục lịch sử; fallback `journal_mode=DELETE` khi WAL lỗi (NFS/SMB).
- **Cron/routines**: `cron/scheduler.py` tick ~60s theo cron expr; **chặn prompt-injection** khi ráp prompt; **disable cứng** các toolset nguy hiểm (`cronjob`/`messaging`/`code_execution`) trong job nền; **script-injection**: chạy script pre-run, stdout làm ngữ cảnh cho agent (vd watcher báo "CHANGE DETECTED"). `batch_runner.py` xử lý song song có checkpoint/resume.
- **Serving**: `mcp_serve.py` phơi ~9 MCP tool (conversations/messages/permissions…) cho Claude Code/Cursor; `gateway/` đa nền tảng + API OpenAI-compatible có khoá; `acp_adapter/` cho editor.
- **Bảo mật** (`SECURITY.md`): **biên tin cậy = cô lập mức OS** (container/VM/sandbox); approval-gate & redaction chỉ chặn "lỗi hợp tác", **không phải biên** chống LLM thù địch. Scrub biến môi trường (strip API key) cho subprocess shell/MCP/cron; nạp skill/plugin = full access ⇒ biên là *operator review trước khi cài*. Mọi surface ra ngoài cần xác thực.

**Lấy cho BRAVO:** (a) state SQLite + parent/branch + FTS5 = mẫu lưu *phiên hội thoại + workflow đang duyệt* (đối chiếu nền tảng chat của BRAVO, ADR-0015); (b) cron + script-injection = cơ chế cho agent chủ động (anomaly/AR-collections agent của BRAVO) — *script làm việc cơ học, agent chỉ reasoning*; (c) **bài học bảo mật cốt lõi**: coi RLS/redaction/approval là tầng *trong tiến trình* và **dựa cô lập OS làm biên thật** — đúng tinh thần chủ quyền dữ liệu của BRAVO.

---
## ✅ Việc cần làm khác đi cho BRAVO
- **Không có RLS/đa-tenant** — phải tự thêm: bơm `user_id`/`department`/`đơn vị` vào tool dispatch, query, memory, skill; lọc ở tầng SQL (arkon), không lọc trong RAM.
- **Cloud-default → đảo thành local-default**: cloud chỉ opt-in qua egress-classifier; dữ liệu kế toán/HR/PII không tự rời mạng.
- **Write-approval phải phủ MỌI tác vụ ghi** (không chỉ memory/skills) và đẩy về Draft Queue ERP, không phải file pending cục bộ.
- **Nén ngữ cảnh phải bảo toàn dòng số có trích dẫn** — không được tóm tắt làm mất nguồn/số trang (vi phạm nguyên tắc 3).
- **Đơn giản hoá**: bỏ ~30 provider, đa nền tảng gateway, user-modeling ngoài — BRAVO chỉ cần 1–2 provider + kênh nội bộ; giữ lõi hẹp.
- **Online compression**: nén của Hermes chạy hậu kỳ theo batch; BRAVO cần nén *trong* agent loop khi áp lực context. Tham chiếu chéo: [[letta-notes]] (memory blocks), [[arkon-notes]] (draft→duyệt), [[agent-ai-notes]] (verify-gate thực chiến).
