# Biên bản Hội đồng — BRAVO đáp ứng bao nhiêu % so với mặt bằng agentic doanh nghiệp 7/2026

- **Ngày:** 2026-07-05
- **Yêu cầu:** Chấm điểm BRAVO AI Copilot so với các hệ AI agentic doanh nghiệp lớn (tính đến 7/2026); lập hội đồng chuyên gia + end-user phản biện khó tính; lên kế hoạch sửa.
- **Phương pháp:** 3 nhóm hội đồng độc lập (benchmark agentic · 4 end-user khó tính · kiến trúc sư/SRE) chấm trên khảo sát code thật (file:line kiểm chứng), nhánh `bravo-v0.1`.
- **Liên quan:** [MATURITY-LADDER.md](MATURITY-LADDER.md) · [ADR-0016](adr/0016-pivot-standalone-ap-vertical.md) (Accepted theo biên bản này) · [VISION.md](VISION.md).

---

## 0. Phán quyết một dòng

> **BRAVO đáp ứng ≈ 30–32% mặt bằng hệ agentic doanh nghiệp lớn tháng 7/2026.**

Đây **không phải** "sản phẩm 32% hoàn thiện đều". Đây là profile **rất lệch**: lõi an toàn–grounding thuộc **top ngành** (có 4 thứ các hãng lớn *chưa* có), nhưng phần "enterprise" trong "enterprise agentic" hiện **gần bằng 0** (vòng giá trị đứt hai đầu, 0 authn/SSO, 0 observability, dữ liệu mock, chưa có user thật — tự nhận L1/4).

**So chuẩn:** Microsoft Copilot Studio / Agent Framework · Salesforce Agentforce · ServiceNow AI Agents · OpenAI AgentKit/Assistants · Google Agentspace/Vertex AI Agent Builder · AWS Bedrock AgentCore · Claude Agent SDK/Enterprise · LangGraph Platform · đối thủ VN **MISA AVA**.

---

## 1. Ma trận năng lực (12 chiều)

| # | Chiều | Chuẩn ngành giữa 2026 | BRAVO | Dẫn chứng |
|---|-------|----------------------|:-----:|-----------|
| 1 | **Orchestration / multi-agent** | Planner + sub-agent + handoff + retry + durable execution là mặc định (LangGraph checkpoint/resume, Bedrock AgentCore Runtime, Agentforce topics→actions, Copilot Studio multi-agent GA). | **15%** | Loop ReAct đơn, control-flow trong Python (ADR-0010); 1 tool đọc dữ liệu thật; không planning/sub-agent/retry. Cộng: budget tracker fail-closed (`loop.py:453`). |
| 2 | **Tool ecosystem & integrations** | Hàng trăm–nghìn connector (Copilot Studio ~1.400, Agentforce+MuleSoft, Agentspace); MCP là lingua franca được mount sẵn. | **5%** | 1 tool thật; ERP client stub 8 dòng (`app/erp/client.py`); MCP server 1 tool **chưa mount** vào runtime. Chiều thấp nhất. |
| 3 | **RAG / grounding** | Hybrid + rerank + citation tới document/page, permission-aware retrieval, connector đa nguồn. | **65%** | Vector+BM25+RRF+ViRanker; **citation tới trang/sheet/ô — sâu hơn chuẩn ngành**; verify-gate số trước khi phát. Trừ: chỉ nguồn upload, chưa connector, chưa test ở scale. |
| 4 | **Memory** | 3 lớp session/user/long-term có scope (AgentCore Memory, Letta-style) — chuẩn mới nổi. | **55%** | Core/recall/archival RLS-scoped ngang chuẩn; chưa chứng minh ở quy mô, chưa có memory UI; eviction còn TODO (`memory.py:5`). |
| 5 | **Guardrails & safety** | Content filter + injection defense chủ yếu **xác suất** (Bedrock Guardrails, Azure content safety), egress qua network policy. | **60%** | Injection framing **tất định fail-closed** + verify-gate số + audit-then-egress + fail-closed-to-local. Cơ chế tất định **ngành lớn chưa có**. Trừ: phủ hẹp (chỉ số tài chính), chưa red-team. |
| 6 | **Evals** | Eval dashboard + LLM-judge + regression suite; hiếm ai gate CI bằng detector tất định. | **50%** | pass^k k=8 + 5 hard-fail detector tất định gate CI — **vượt chuẩn phương pháp luận**; nhưng dataset ~41 trajectory mock + pytest chưa cài được trong .venv ⇒ giá trị bị chặn bởi hạ tầng test. |
| 7 | **Observability** | OTel tracing per-step, token/cost metrics, session replay — yêu cầu mua hàng bắt buộc. | **5%** | 0 OTel/metrics/tracing. Chỉ audit log nghiệp vụ. Với enterprise 2026 là disqualifier. |
| 8 | **Identity / SSO / RBAC** | OIDC/SAML/SCIM/Entra ID mặc định; permission-aware thường là ACL post-filter. | **30%** | **Không authn** (0 SSO/OIDC/AD) — chặn mọi thương vụ. Nhưng **authz tầng dữ liệu vượt chuẩn**: RLS lọc trong SQL phủ mọi đường (`app/security/rls.py`), đa số ngành lớn chỉ post-filter. |
| 9 | **HITL & governance** | Approval workflow, maker-checker, audit trail, admin governance console. | **45%** | Draft approval + maker-checker + pg_advisory_lock chống double-post + Nợ=Có by-construction. Trừ nặng: draft **không đẩy về đâu** (TODO Phase 3); không governance UI. |
| 10 | **Deployment / scale / reliability** | Managed runtime, autoscale, HA, backup/DR, VPC/private endpoint. | **20%** | Docker-compose, không backup/DR, không rate-limit, chưa load-test. Cộng: **air-gap-capable by design**. Trừ: demo chạy cloud gpt-4o-mini ⇒ **tự vi phạm bất biến #4**. |
| 11 | **Cost controls** | Token budget, cost dashboard, routing theo cost. | **20%** | Budget tracker per-session + router, nhưng 0 cost-tracking/dashboard/quota per-user (budget ước `len//4`). |
| 12 | **UX / admin surface / ecosystem** | No-code builder, admin console, analytics, marketplace/template. | **10%** | React SPA chat; streaming **giả** (`loop.py:467` cắt chuỗi 48 ký tự); không admin UI, frontend 0 test, 0 i18n, 0 marketplace. |

### Trọng số & phép tính

Theo tiêu chí mua hàng enterprise 2026 (tích hợp + vận hành nặng hơn thuật toán): tools 13 · orchestration 12 · RAG 12 · identity 10 · guardrails 10 · observability 8 · HITL 8 · deployment 8 · evals 6 · memory 5 · cost 3 · UX 5 = 100.

`(12×15 + 13×5 + 12×65 + 5×55 + 10×60 + 6×50 + 8×5 + 10×30 + 8×45 + 8×20 + 3×20 + 5×10) / 100 =` **≈ 31,7%**.

Lý do trọng số: doanh nghiệp 2026 mua agent vì nó **nối được vào hệ thống hiện có và vận hành được** (tools+identity+observability+deploy = 39%), không vì kiến trúc đẹp.

### 4 điểm BRAVO có mà nhiều hãng lớn CHƯA có (không phóng đại)

1. **RLS lọc trong SQL** phủ toàn bộ đường RAG + memory (đa số chỉ ACL post-filter).
2. **pass^k hard-fail detector tất định** gate CI (RLS-leak/số-bịa/sai-đơn-vị/egress/injection).
3. **Citation tới ô/sheet/số trang** (Copilot/Agentspace dừng ở doc/page).
4. **Air-gap-capable + audit-then-egress** (Bedrock/Azure có private endpoint nhưng không air-gap thuần; MISA AVA cloud-only).

So riêng với **MISA AVA**: BRAVO thua về "đã ship trên dữ liệu thật", thắng về độ sâu kiểm soát an toàn.

---

## 2. Top 10 khoảng cách chí tử (tác động × chi phí sửa)

| # | Khoảng cách | Đề xuất sửa |
|---|-------------|-------------|
| 1 | Vòng giá trị đứt hai đầu (ERP stub, draft không đẩy đi đâu) | **Accept ADR-0016**: ship "Copilot AP độc lập" → xuất Excel/CSV nhập tay, bỏ phụ thuộc ERP API. |
| 2 | Demo chạy cloud gpt-4o-mini, vi phạm bất biến #4 | Dựng đường Qwen-2.5 (vLLM/Ollama) chạy 1 kịch bản AP end-to-end, biến "offline" thành demo quay video được. |
| 3 | 0 SSO/OIDC | Keycloak self-host (air-gap) + Authlib OIDC middleware, map claim phòng ban → RLS context. |
| 4 | 0 observability | OTel SDK + span per step/tool/LLM, export otel-lgtm self-host; tận dụng audit log sẵn có. |
| 5 | pytest không cài được ⇒ 160 test + eval gate "trên giấy" | Sửa .venv (uv sync dev), bật CI chạy full test + pass^k thật, badge xanh trước khi nói L2. |
| 6 | Streaming giả (`loop.py:467`) | Router streaming API, stream token thật qua SSE; giữ verify-gate (stream sau verify / verify-per-sentence). |
| 7 | Structured output regex | Guided decoding (vLLM `guided_json`/outlines) hoặc native function-calling + Pydantic fail-closed. |
| 8 | MCP chưa mount + chỉ 1 tool | Mount FastMCP vào runtime, thêm 3–4 tool đọc (tra bút toán/công nợ/tài liệu/trạng thái draft). |
| 9 | Eval dataset 41 trajectory mock | Thu 200+ trajectory từ hoá đơn XML thật (ẩn danh) + câu hỏi helpdesk thật. |
| 10 | Không rate-limit/backup/DR | slowapi per-user + pg_dump định kỳ + runbook restore 1 trang. |

**Khó tính nhất:** khoảng cách lớn nhất không nằm trong 12 chiều — là **chưa có user thật nào** (L1/4). Mọi hệ so sánh đều đã có production traffic. 32% là chấm *năng lực hệ thống*; *bằng chứng thị trường* hiện = 0. Ưu tiên #1 (ADR-0016) là con đường ngắn nhất sửa cả hai.

---

## 3. Hội đồng End-User khó tính

Bốn vai phản biện gay gắt trên sản phẩm **hôm nay**.

### 3.1 Chị Hằng — Kế toán trưởng (8 năm BRAVO ERP)
**Phản biện:** (1) Duyệt bút toán trên chat xong **không đẩy về ERP** → vẫn nhập tay hai lần, và nhập tay chính là chỗ sinh sai số. (2) Anomaly/Tax chạy **số mock** → nhìn 5 giây là mất niềm tin cả con số đúng. (3) Duyệt nháp **rải rác trong chat**, không có màn hàng đợi lọc/duyệt-lô (dù API `GET /drafts?status=pending` đã có). (4) Thiếu **nhật ký ai-tạo-ai-duyệt** in được cho kiểm toán. (5) Hoá đơn thật 70% là **PDF scan**, không phải XML sạch.
**Điều kiện dùng thử:** trang hàng đợi duyệt + duyệt lô; nút xuất Excel đúng format nhập BRAVO có cột tham chiếu hoá đơn gốc; nhật ký in được; **không thấy bất kỳ số mock nào** (thà để trống).
**Thừa nhận tốt:** gate Nợ=Có bắt buộc + AI **từ chối khi không có nguồn** — hơn khối phần mềm từng dùng.

### 3.2 Anh Tú — Helpdesk BRAVO (40 ticket/ngày)
**Phản biện:** (1) Cẩm nang 19 chương chỉ phủ một phần ticket; **không upload tài liệu qua UI** → phải nhờ chạy script. (2) **Streaming giả** = chờ full câu rồi mới thấy chữ chạy; chậm thì Ctrl+F PDF còn nhanh hơn. (3) Cần **nút copy trả lời + trích dẫn** một chạm để dán Zendesk. (4) 20 anh em helpdesk mà tạo tài khoản/reset mật khẩu bằng script Python là bất khả thi.
**Điều kiện:** trả lời đúng nguồn <10s; nút copy kèm nguồn; có người trực nạp tài liệu tuần đầu; tài khoản tạo sẵn cho cả team.
**Thừa nhận tốt:** trích dẫn số trang bấm nhảy thẳng vào PDF — đúng cái cần nhất.

### 3.3 Anh Long — IT Manager/CIO (quản trị AD domain)
**Phản biện:** (1) **LLM đi cloud OpenAI** = loại từ vòng hồ sơ; tài liệu hứa on-prem nhưng bản chạy gọi cloud = nói một đằng làm một nẻo, sẽ tự bật Wireshark kiểm egress. (2) **Không SSO/AD** + **không cả đổi mật khẩu** (`routes_auth.py` chỉ có login + /me) → 300 user chung văn hoá `demo123`. (3) Thêm user bằng **script Python** = chưa nghĩ đến người vận hành. (4) **Không backup/SLA** → hỏng thì dữ liệu duyệt 6 tháng đi đâu, ai restore, bao lâu? (5) **Mật khẩu điền sẵn** trên form login = tư duy demo, chưa từng xây để vận hành.
**Điều kiện (pilot mạng cô lập):** LLM local hoàn toàn, cho chặn outbound để chứng minh; đổi/reset mật khẩu + tắt demo123; tài liệu backup/restore dù chỉ `pg_dump`; danh sách mọi endpoint egress bằng văn bản. SSO cho nợ đến bản mua nhưng phải trong hợp đồng.
**Thừa nhận tốt:** kiến trúc "AI không tự tính số, không free-form SQL, con người là cổng ghi cuối" (ADR-0004/0005 + maker-checker) — tư duy an toàn đúng đắn hiếm thấy.

### 3.4 Chị Mai — CFO (người quyết chi tiền)
**Phản biện:** (1) AI định khoản sai, kế toán duyệt nhầm — **ai chịu trách nhiệm?** Không SLA/điều khoản = mặc định tôi chịu → trả tiền để mua thêm rủi ro. (2) **ROI ở đâu** khi vòng chưa khép: AI làm phần rẻ nhất (định khoản), phần đắt nhất (nhập tay ERP) còn nguyên. (3) Money Engine thật đứng cạnh Anomaly/Tax **mock không dán nhãn** — phát hiện hàng mẫu trộn hàng thật thì nghi ngờ luôn phần thật. (4) TCO ẩn: mỗi việc quản trị cần một kỹ sư biết Python, báo giá không ghi.
**Điều kiện:** pilot khoanh đúng luồng AP có **thước đo trước/sau bằng số** (phút/hoá đơn, % nháp bị sửa); văn bản 1 trang về trách nhiệm & phạm vi; pilot miễn phí; mọi màn mock **gỡ hoặc dán nhãn DEMO to**.
**Thừa nhận tốt:** maker-checker là **đúng ngôn ngữ kiểm soát nội bộ** — giải trình được với HĐQT/kiểm toán.

### 3.5 Top 12 việc chặn người dùng

| # | Việc | Mức | Ai đòi |
|---|------|-----|--------|
| 1 | Khép vòng duyệt → xuất Excel/CSV ngay trong luồng duyệt | **BLOCKER** | Hằng, Mai |
| 2 | Trang hàng đợi duyệt nháp tập trung (lọc, duyệt lô, tổng Nợ/Có) | **BLOCKER** | Hằng |
| 3 | LLM chạy local thật trên pilot, chứng minh zero-egress | **BLOCKER** | Long |
| 4 | Gỡ / dán nhãn DEMO mọi màn mock; không trộn mock với số thật | **BLOCKER** | Hằng, Mai |
| 5 | Quản trị user tối thiểu qua UI + bỏ điền sẵn demo123 | **BLOCKER** | Long, Tú |
| 6 | Audit trail duyệt bút toán xem/in được | MAJOR | Hằng, Mai, Long |
| 7 | Nạp tài liệu nhanh trong pilot (UI upload sau) | MAJOR | Tú |
| 8 | Độ trễ <10s + streaming thật | MAJOR | Tú |
| 9 | Backup/restore có tài liệu, có lịch | MAJOR | Long |
| 10 | Văn bản trách nhiệm + phạm vi cam kết | MAJOR | Mai |
| 11 | Nút copy trả lời + trích dẫn một chạm | MINOR | Tú |
| 12 | Hỗ trợ hoá đơn PDF/scan ngoài XML sạch | MINOR (pilot) / MAJOR (bán) | Hằng |

### 3.6 Phán quyết end-user về ADR-0016 — ỦNG HỘ 4/4

- **Hằng (mạnh nhất):** "Tôi tin file Excel cầm được, soát từng dòng — **an toàn hơn** đẩy thẳng ERP vì tôi là chốt chặn cuối. Điều kiện: đúng format nhập BRAVO, có cột tham chiếu hoá đơn gốc, và đừng gọi nó là 'tạm thời rồi bỏ' — nó là **tính năng kiểm soát**."
- **Long:** "Không ghi ERP = không xin quyền ghi, không thêm bề mặt tấn công vào hệ lõi. Duyệt pilot dễ hơn mười lần."
- **Mai:** "Lần đầu có thứ **đo được** trên quy trình hẹp, chi phí thấp, không chờ đội .NET. Nhưng xuất Excel chỉ mua vé pilot — muốn ký dài hạn thì lộ trình nối ERP phải có ngày tháng."
- **Tú:** "Ủng hộ với điều kiện pivot **đừng bỏ đói RAG trích dẫn trang** — thứ duy nhất hôm nay dùng được thật."

**Cảnh báo:** ADR-0016 chỉ xứng "Accepted" nếu kèm tối thiểu việc #1, #2, #4 — vì "Copilot AP độc lập" mà thiếu trang hàng đợi duyệt + nút xuất file thì chính là vòng đứt hiện tại khoác tên mới. Hạ tầng backend đã sẵn hơn ADR mô tả (export CSV/XLSX + batch đã nằm trong `routes_drafts.py` và `journal_export.py`); việc còn thiếu chủ yếu là **UI khép vòng** — nằm trong tầm vài tuần.

---

## 4. Kế hoạch sửa theo đợt (roadmap)

Ký hiệu: S ≤ 0.5 ngày · M ≤ 2 ngày · L ≤ 5 ngày.

### WAVE 0 — "Vệ sinh & trung thực" (≤ 1 tuần) — ĐANG THỰC THI

Mục tiêu: mọi tuyên bố (CI xanh, DONE, test, on-prem) thành SỰ THẬT kiểm chứng được; không mất code; chốt hướng.

| # | Việc | File | Nghiệm thu |
|---|------|------|-----------|
| W0.1 | Push branch | git | `origin/bravo-v0.1` tồn tại |
| W0.2 | .venv cài được dev deps | `pyproject.toml`, `README-DEV.md` | `.venv/bin/pytest -q` xanh local |
| W0.3 | CI có Postgres thật | `.github/workflows/ci.yml` | Test RLS/draft/migration chạy trong CI, không skip |
| W0.4 | Ruff blocking | `ci.yml`, `app/` | `ruff check app` = 0 lỗi; CI fail nếu ruff fail |
| W0.5 | Đồng bộ docs mâu thuẫn | `docs/adr/README.md`, `docs/work-packages/README.md` | Không còn claim sai (0012 "CHƯA implement", WP "CHƯA CODE") |
| W0.6 | Chốt ADR-0016 | `docs/adr/0016-*.md` | Status ≠ Proposed; danh sách đóng băng nằm trong ADR |
| W0.7 | Dọn frontend legacy | `frontend/`, `app/main.py` | Chỉ còn `frontend-react/`; app vẫn serve SPA |
| W0.8 | Bỏ hardcode demo123 | `LoginPage.tsx:8` | Bundle production không chứa `demo123` |
| W0.9 | CORS cho dev | `app/main.py`, config | Vite dev gọi được API; prod không đổi |
| W0.10 | Xoá TODO sai hướng | `app/erp/draft_queue.py`, `app/erp/client.py` | Không còn TODO hứa push ERP |
| W0.11 | Dán nhãn DEMO màn mock | `frontend-react/src/features/{anomaly,tax,graph}` | Mọi màn mock có nhãn "DEMO — dữ liệu mock" |

**DoD Wave 0:** CI xanh với Postgres thật + ruff chặn; code đã push; docs không tự mâu thuẫn; ADR-0016 đã chốt; không còn secret/legacy/nhãn-mock-thiếu. **Không viết feature mới.**

### WAVE 1 — "Hết giả" ✅ ĐÃ LÀM (2026-07-05)
Track A (LLM plumbing): ✅ router.chat_stream token thật + usage; ✅ structured output json_object/guided_json + retry 1 lần có ngân sách; ✅ streaming E2E tôn trọng verify-gate (bỏ `_chunk_text`, compose token thật opt-in); ✅ mount MCP `/mcp` + token extraction + test.
Track B (product surface): ✅ trang Drafts queue `/drafts` + xuất CSV/XLSX từng cái + lô; ✅ upload tài liệu `/documents`; ✅ admin tối thiểu `/admin` (CRUD user/phòng ban/đổi+reset mật khẩu); ✅ `create_journal_entry` payload thật qua Number-Integrity Gate.
**Cắt (giữ nguyên):** memory eviction Letta-style — chưa làm, chờ log user thật.

### WAVE 2 — "Enterprise floor" ✅ ĐÃ LÀM (2026-07-05)
✅ OIDC (Authlib) gate theo settings + Keycloak compose (`deploy/docker-compose.keycloak.yml`, `docs/SSO-OIDC.md`); ✅ observability (`/metrics` prometheus-fastapi-instrumentator + OTel OTLP → otel-lgtm compose); ✅ rate-limit slowapi/người + GPU concurrency semaphore; ✅ cost/token tracking từ usage thật (`/api/admin/usage` + bảng Admin); ✅ backup `scripts/backup.sh` + `docs/RUNBOOK-DR.md`; ✅ boot-guard mở rộng.
> **Còn cần hạ tầng ngoài để chốt:** chạy Keycloak thật (OIDC end-to-end), GPU thật (đo pass^k local + sizing), và **chạy drill restore thật** để điền RTO vào RUNBOOK. Code + compose + gate đã sẵn.

### WAVE 3 — "Giá trị thật theo ADR-0016" (song song từ khi W1.6–W1.9 xong; cổng L2→L3)
AP E2E trên ≥50 hoá đơn thật; export chuẩn nhập BRAVO (golden-file test); corpus thật + đo recall@k/MRR; Qwen local trên GPU thật + pass^k + GPU sizing note; offline bundle air-gap.
**DoD:** ≥1 kế toán dùng luồng AP hàng tuần trên hoá đơn thật + số willingness-to-pay (≥3 phỏng vấn).

### Sơ đồ phụ thuộc
```
W0.* ──► mọi thứ sau
W1.1 ─► W1.2 ─► W2.4      W1.3 ─► W1.4      W1.3 ─► W3.4
W1.5, W1.6, W1.7, W1.8, W1.9: song song
W1.6+W1.7 ─► W3.1 ─► W3.2      W3.3 ∥ W3.1      W3.3+W1.3 ─► W3.4 ─► W3.5
W2.1, W2.2: khởi động song song từ giữa Wave 1      W2.5, W2.6: song song
W0.6 (ADR-0016 Accepted) ─► toàn bộ Wave 3
```

---

## 5. Danh sách CẮT (không làm — chống "bẫy L1")

1. **Anomaly / Tax / Knowledge Graph** — đóng băng nguyên trạng (không gỡ, không mở rộng, không sửa ngoài crash) tới L3 + ≥1 khách thật.
2. **AR-collections, IFRS, money-engine ngoài AP** — chỉ giữ docs, không code.
3. **Push draft → ERP staging (Phase 3)** — xoá khỏi roadmap; export file là đầu ra chính thức (ADR-0016).
4. **Memory eviction + summarize kiểu Letta** — thay bằng hard-cap; làm thật chỉ khi log user thật cho thấy cần.
5. **Langfuse self-host** — hoãn tới L3 (stack v3 quá nặng cho air-gap L2); otel-lgtm đủ.
6. **Helm/K8s installer** — L4 theo ladder; compose đủ tới khi có khách ký.
7. **Fine-tune, multi-tenant SaaS, thêm tool/engine mới cho loop** — cấm tới khi qua cổng L3.
8. **Deploy GCP public demo như cổng L2** — hạ ưu tiên; cổng thật là kế toán thật dùng luồng AP (có thể chạy LAN nội bộ).

## 6. Ba rủi ro cần theo dõi
1. **Verify-gate vs streaming** (W1.4) — điểm duy nhất có thể phá invariant nếu làm ẩu; giữ nguyên tắc "số tài chính không phát trước khi qua gate".
2. **Export chuẩn BRAVO phụ thuộc con người** — xin template import + chứng từ thật từ kế toán NGAY từ Wave 0 (critical path phi-kỹ-thuật).
3. **`_token_from_context` MCP** phiên bản-nhạy — pin version `mcp` + integration test HTTP thật.
