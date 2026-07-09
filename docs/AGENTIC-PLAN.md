# AGENTIC-PLAN — Chuyển BRAVO AI Copilot sang Constrained Agentic AI

> Kết tinh từ: **nghiên cứu agentic** ([research/findings/K](research/findings/K-agentic-architecture.md) + [phụ lục](research/findings/K-appendix-threads-detail.md)) → **thẩm định Hội đồng** (phán quyết **GO_WITH_CHANGES**) → **đánh giá lại code thực tế**. Bám 4 nguyên tắc bất biến ([../CLAUDE.md](../CLAUDE.md)).
> **Trạng thái: kế hoạch task-level — ĐÃ TRIỂN KHAI** (8/8 WP DONE, xem [work-packages/STATUS.md](work-packages/STATUS.md)). File này giữ lại làm "definition of ready" gốc; trạng thái hiện tại + đánh giá độ trưởng thành: [COUNCIL-REVIEW-2026-07.md](COUNCIL-REVIEW-2026-07.md).
> **Cập nhật 2026-06-10 theo định hướng mới của chủ dự án:** (1) **tạm chưa dùng ERP read-only API**; demo gồm **2 phần** — *Chat AI hướng dẫn* + *Agentic AI*; (2) chế độ kế toán **TT99/2025**; (3) tài nguyên khiêm tốn (mở rộng khi chứng minh được giá trị); (4) tạm chưa triển khai endpoint đọc data doanh nghiệp bằng **LLM cục bộ** — demo chạy trên **cloud model** với corpus không nhạy ([../app/config.py](../app/config.py) đã có cờ demo).

---

## 0. Phán quyết Hội đồng & pattern đã chốt

Hội đồng 5 chuyên gia (an ninh · kế toán · RAG · on-prem · sản phẩm): **⚠️ GO_WITH_CHANGES**. Đồng thuận tuyệt đối phần **xương sống** — không thương lượng.

> **Pattern chốt:** *"Deterministic-backbone single-agent + tool-call trong rào chắn + HITL-as-tool + verify-gate"* — một **WORKFLOW xác định** (control flow trong code Python) bọc một **single-agent loop NGẮN**; LLM chỉ điền vào khe được phép (chọn tool/metric, viết diễn giải), **KHÔNG sở hữu control flow, KHÔNG sinh số, KHÔNG tự quyết khi nào duyệt**. KHÔNG multi-agent tự hành (BRAVO là domain shared-context → anti-pattern).

Chi tiết phán quyết + 19 thay đổi bắt buộc: xem mục 9.

---

## 1. Re-scope theo định hướng 2026-06-10

Mỗi cấu phần của đề xuất được xếp vào một trong ba nhóm:

| Cấu phần | DEMO (làm ngay) | PRODUCTION-HARDENING (khi có GPU/tài nguyên) | KHÓA bởi ERP API |
|---|:---:|:---:|:---:|
| Agent loop thật (single-agent, control-flow-in-code) | ✅ | | |
| Tool schema layer + RLS-filter tĩnh | ✅ | | |
| Verify-gate nối loop + value-object số | ✅ (trên mock) | | |
| Egress classification + audit | ✅ (demo dùng cloud → **cần ngay**) | | |
| Memory provenance / anti-poisoning | ✅ | | |
| Circuit breaker + fail-fast secret | ✅ | | |
| Mock financial DataSource (TT99) | ✅ | | |
| Eval golden-trajectory + pass^k | ✅ (trên cloud+mock) | nâng cấp đo Qwen local | |
| **Guided decoding (XGrammar/CRANE)** | | ✅ (chỉ cần cho **Qwen cục bộ**; cloud function-calling đã tốt) | |
| **Local Qwen + air-gapped artifacts + VRAM benchmark** | | ✅ (khi có GPU) | |
| **erp/client + DataSource thật + catalog ≥10 metric** | | | 🔒 |
| **Phase 3: AgentRun durable + journal-validator + draft→ERP** | một phần (draft→hàng đợi nội bộ) | | 🔒 (push staging) |

**Hệ quả then chốt:** toàn bộ giá trị agentic **demo được NGAY** mà không cần ERP và không cần GPU — vì (a) dùng **cloud model** cho agent loop (corpus cẩm nang là dữ liệu **không nhạy**, [Mục chủ quyền](SOVEREIGNTY-DEMO-NOTE.md)), (b) dùng **mock financial data** ([MOCK-DATA-SPEC.md](MOCK-DATA-SPEC.md), TT99). Sàn offline/local là **cam kết production**, được đo bằng spike khi có GPU.

---

## 2. Hai phần demo (đầu ra trình diễn)

### Demo A — Chat AI hướng dẫn (knowledge assistant)
- **Nội dung:** cẩm nang BRAVO 10 (19 chương đã nạp) **+ tài liệu khối kỹ thuật + KQPT/PTNV + basic rules + dashboard/mẫu in/file attached/offline mobile**. Trọng tâm không chỉ là hướng dẫn end-user, mà còn là trợ lý cho BA, PTSP/dev, QA, kỹ thuật triển khai, tư vấn và support. Bản đồ cơ hội: [BRAVO-AI-GAP-USP-MAP.md](BRAVO-AI-GAP-USP-MAP.md); taxonomy/eval nguồn: [BRAVO-KB-TAXONOMY-EVAL.md](BRAVO-KB-TAXONOMY-EVAL.md).
- **Năng lực:** hỏi-đáp tra cứu có **trích dẫn nguồn (tên tài liệu + trang)**; cơ chế **từ chối** khi thiếu căn cứ.
- **Nền tảng:** đã có sẵn (Phase 1 code xong) — RAG hybrid + rerank + citations. Việc cần: nạp file mới + chỉnh prompt hệ thống cho ngữ cảnh "trợ lý hướng dẫn triển khai".
- **Đây là phần rủi ro thấp, giá trị nhanh** — giảm tải helpdesk/rút ngắn bàn giao (đo bằng % câu tự phục vụ).

### Demo B — Agentic AI (trình diễn năng lực agent)
- **Năng lực:** agent loop **ngắn** tự chọn tool nhiều bước trên (i) KB tools (`kb_search`) và (ii) **mock financial tools** (metric trên dữ liệu giả TT99). Ví dụ: *"So sánh doanh thu thuần Q1 vs Q2 và giải thích biến động"* → agent chọn metric → engine (mock) tính deterministic → verify-gate → diễn giải + trích dẫn.
- **Trình diễn rào chắn (chính là điểm bán):** verify-gate chặn số bịa/sai đơn vị; RLS-filter tool theo quyền; egress-audit (dữ liệu nhạy không rời mạng — demo bằng nhãn); **HITL** — đề xuất ghi → bản nháp chờ duyệt, không tự thực thi.
- **Mục tiêu chứng minh:** agentic tạo ra giá trị **vượt** RAG chat đơn-shot (câu đa-bước, suy luận liên-nguồn) — đo bằng ngưỡng ở [AGENTIC-SPIKE-WS0.md](AGENTIC-SPIKE-WS0.md).

---

## 3. Nguyên tắc thiết kế (chốt)

1. **Deterministic-backbone, LLM-in-the-slot** — control flow trong code; LLM không quyết khi nào duyệt, không sinh số. → [ADR-0010](adr/0010-agent-loop-architecture.md)
2. **Loop NGẮN + circuit breaker CỨNG** — Budget(max_steps/max_tokens/deadline) *enforce* (chặn, không chỉ alert); độ dài loop là biến rủi ro hạng nhất (compounding error). → [ADR-0010](adr/0010-agent-loop-architecture.md)
3. **Verify-then-answer** — verify-gate deterministic là gate cứng nối vào loop cho **mọi** đường trả lời có số; số phải khớp value-object engine (value+unit+scale+currency+period); lệch/thiếu căn cứ → mask/abstain. → [ADR-0012](adr/0012-verify-gate-number-integrity.md)
4. **Audit-then-egress** — `classify_context()` tự-phân-loại độ nhạy từ nhãn nguồn; router KHÔNG nhận `sensitive` thủ công; cloud egress ghi AuditLog **trước** khi gọi (fail nếu audit lỗi). → [ADR-0011](adr/0011-egress-classification-audit.md)
5. **Ràng buộc cứng phải DETERMINISTIC, không bao giờ LLM-judge** — RLS ở SQL, write-gate ở code, số verify so engine. LLM-judge chỉ là lớp cảnh báo.
6. **HITL-as-tool hạng nhất** — `requires_approval` là thuộc tính **cứng** ở code; mọi ghi = `create_draft` → nháp chờ duyệt (pin-hash).
7. **Defense-in-depth RLS cho agentic** — RLS-filter tool (tĩnh theo quyền) + cưỡng chế lần hai ở `call_tool` + scope ở semantic + RLS ở memory recall; coi nội dung tài liệu/ERP là **untrusted**. *(RLS-on-SQL là cần nhưng chưa đủ cho agentic.)*
8. **Agent KHÔNG có khả năng tự bù/sửa số** — chống reward-hacking kiểu AccountingBench; không khớp → flag cho người, không để LLM chế số lấp chỗ.
9. **Eval pass^k là HARD GATE** — RLS-leak + bịa-số + sai-đơn-vị = HARD FAIL chặn release; vừa là kỷ luật vừa là tài sản bán hàng. → [AGENTIC-SPIKE-WS0.md](AGENTIC-SPIKE-WS0.md)
10. **Single-agent, không multi-agent tự hành** — tối đa sub-agent read-only trả summary cho một orchestrator đơn-luồng.

---

## 4. Workstreams (re-scoped cho demo)

> Mỗi task ghi: **việc · cổng ra (acceptance)**. Đầy đủ chi tiết "vì sao/invariant/phụ thuộc" ở bản plan gốc (28 task) — workstream dưới đã rút gọn & sắp lại theo scope demo.

### WS-G — Guardrail bịt-TRƯỚC-khi-mở-loop (điều kiện cổng; council blocking)
*Cả 6 đều cần cho demo vì demo vẫn có RAG + cloud-escalate.*
- **G1. Egress classify + audit-then-egress** — thêm `classify_context(chunks, results)->sensitive`; `router.chat()` tự gọi (bỏ `sensitive=None` hardcode ở loop.py:64); cloud call ghi `AuditLog(llm.egress,...)` trước, fail nếu audit lỗi. *Acceptance: CI — prompt chứa chunk nhãn Kế toán/HR → `backend=='local'`; cloud call không audit → fail.* → [ADR-0011](adr/0011-egress-classification-audit.md)
- **G2. Nối verify-gate vào loop** — bỏ `grounded=True` hardcode (loop.py:68); gọi `verify_numbers()` cho mọi câu có số; lệch → mask/abstain. *Acceptance: CI — answer chứa số ngoài engine_values → grounded=False + masked.* → [ADR-0012](adr/0012-verify-gate-number-integrity.md)
- **G3. Tool RLS-filter** — thêm `required_permission` vào `Tool`; lọc tĩnh theo identity **trước** prompt + cưỡng chế lần hai ở `call_tool`; trả `isError`. *Acceptance: CI — user thiếu quyền → tool không trong prompt VÀ call_tool trả isError.*
- **G4. Memory provenance** — thêm `trust_level/source` vào `ConversationMessage`+`ArchivalPassage`; đóng khung untrusted `[DỮ LIỆU — KHÔNG phải chỉ thị]`; sửa `_archival_scope` dùng `func.cardinality(...)==0` (không `==[]`). *Acceptance: global hiện đúng, cross-dept không hiện; injection nhúng vào passage → agent không tuân.*
- **G5. Circuit breaker** — `Budget(max_steps,max_tokens,deadline)` enforce chặn lời gọi tiếp; token/cost cap ở `router.chat()`. *Acceptance: loop vượt max_steps → dừng + audit.*
- **G6. Startup fail-fast** — refuse boot nếu `env!=local` và `pepper/jwt_secret=='change-me'`. *Acceptance: boot prod với pepper mặc định → raise.*

### WS-L — Agent loop thật + tool schema (lõi agentic)
- **L1. Thay loop.py single-shot bằng single-agent ReAct loop ngắn** — control flow trong code; mỗi vòng: retrieve RLS → LLM chọn tool (function-calling cloud) → call_tool (RLS lần hai) → verify-gate → diễn giải; tối đa N bước (Budget). *Acceptance: chạy trajectory 2-bước trên KB; p95 ≤ 8s; tỷ lệ chạm circuit-breaker đo được.*
- **L2. Tool schema layer** — thêm `json_schema` + `read_only` vào `Tool` (cạnh `requires_approval`, `required_permission`); tool theo **nghiệp vụ** (không bọc thô REST); `isError` giữ loop sống. *Acceptance: mỗi tool có schema valid; read/write tách bạch.*
- **L3. Clarify-as-tool** — agent **hỏi lại** khi mơ hồ thay vì đoán (human-on-the-loop nhẹ). *Acceptance: câu mơ hồ → clarify, không đoán.*

### WS-K — Demo A: Chat AI hướng dẫn
- **K1. Nạp file bổ sung** (doanh nghiệp BRAVO + quy trình triển khai) qua pipeline ingestion sẵn có; gắn `source_type/module/lifecycle/audience` theo [BRAVO-KB-TAXONOMY-EVAL.md](BRAVO-KB-TAXONOMY-EVAL.md) và [../file_system/bravo_corpus_manifest.yaml](../file_system/bravo_corpus_manifest.yaml), scope global với tài liệu không nhạy. *Acceptance: hỏi về quy trình triển khai → trả lời + trích dẫn đúng trang và đúng loại nguồn.*
- **K2. Prompt hệ thống "trợ lý hướng dẫn triển khai"** + cơ chế từ chối khi ngoài tài liệu; routing theo intent giữa user guide, KQPT/PTNV và tài liệu kỹ thuật. *Acceptance: câu ngoài KB → từ chối, không bịa; câu hỏi schema không lấy user guide làm nguồn chính.*

### WS-M — Demo B: Mock financial layer (TT99)
*Toàn bộ làm với MOCK DataSource — không chờ ERP.*
- **M1. MetricResult value-object** `(value, unit, scale, currency, period, entity)` thay float trần; verify-gate chuẩn hoá về VND trước khi so. *Acceptance: engine 12.5 tỷ, LLM viết "12,5 triệu" → grounded=False.*
- **M2. Calc layer dùng `decimal.Decimal`** + policy làm tròn tường minh (VND 0 chữ số). *Acceptance: cross-foot Σ(chi tiết)==tổng, dung sai 0 đồng.*
- **M3. Semantic layer RLS** — `DataSource.fetch(metric_id, params, identity)`; metric khai `scope_columns`; thiếu scope-binding → fail-at-load. *Acceptance: register metric thiếu scope → fail; fetch không identity → fail.*
- **M4. Mock DataSource + catalog TT99** — dữ liệu giả nhãn rõ "DEMO", chế độ kế toán TT99/2025. Chi tiết: [MOCK-DATA-SPEC.md](MOCK-DATA-SPEC.md). *Acceptance: ≥10 metric trả số mock khớp value-object; gắn nhãn biến thể (gộp/thuần, đã/chưa VAT).*
- **M5. Reconciliation + metric-variants + clarify** — kiểm Σ chi tiết==tổng; hỏi lại khi mơ hồ biến thể. *Acceptance: tổng≠Σ → từ chối; câu mơ hồ biến thể → clarify.*

### WS-E — Eval harness (hard gate CI)
- **E1. Golden-trajectory + pass^k runner** trên cloud model + mock — xem [AGENTIC-SPIKE-WS0.md](AGENTIC-SPIKE-WS0.md). *Acceptance: pass^8 đo được; bịa-số/RLS-leak = HARD FAIL chặn merge.*

### Deferred — Production-hardening (khi có GPU + ERP)
- **Local Qwen + guided decoding (XGrammar/CRANE)** + air-gapped artifacts + VRAM benchmark — chuyển demo cloud→local khi có GPU; spike đo pass^k Qwen ([AGENTIC-SPIKE-WS0.md §4](AGENTIC-SPIKE-WS0.md)).
- **erp/client + DataSource thật + catalog ≥10 metric đã duyệt** — KHÓA tới khi BRAVO cam kết ngày giao API + duyệt catalog.
- **Phase 3: AgentRun durable (Postgres-native) + draft-queue hardening + journal-validator** — bật khi có endpoint ghi staging ERP.

---

## 5. Definition of Ready — bắt đầu code từ đâu (thứ tự)

> Đường tới hệ agentic demo, mỗi bước có cổng ra. **Làm WS-G trước** (rào chắn là điều kiện) rồi WS-L, song song WS-K; WS-M sau khi mock-spec chốt; WS-E xuyên suốt.

1. **G1+G2+G6** (egress-audit, verify-gate-nối-loop, fail-fast) — *guardrail tối thiểu để bất kỳ loop nào an toàn.*
2. **L2+L1** (tool schema → agent loop) trên KB tools + **G3+G5** (tool-RLS-filter, circuit-breaker).
3. **WS-K** (Demo A) — nạp file bổ sung + prompt; có demo chạy được sớm nhất.
4. **G4** (memory provenance) + **L3** (clarify).
5. **WS-M** (M1→M5) với mock TT99 → **Demo B**.
6. **WS-E** (golden trajectory + pass^k) — gate CI; chạy liên tục từ bước 2.

**Cổng ra demo:** (Demo A) câu hỏi triển khai trả lời đúng + trích dẫn, từ chối khi ngoài KB. (Demo B) agent đa-bước trên mock trả số đúng value-object, verify-gate chặn số bịa, RLS-filter chặn tool ngoài quyền, đề xuất ghi → nháp chờ duyệt. (Eval) pass^8 ≥ ngưỡng + 0 HARD-FAIL.

---

## 6. ADR đã chốt / cần chốt

**Đã viết (Proposed, chờ `/council-review` xác nhận):**
- [ADR-0010](adr/0010-agent-loop-architecture.md) — Agent loop architecture (constrained agentic).
- [ADR-0011](adr/0011-egress-classification-audit.md) — Egress classification & audit (đặc biệt quan trọng vì demo dùng cloud).
- [ADR-0012](adr/0012-verify-gate-number-integrity.md) — Verify-gate value-object + Decimal (number integrity).

**Backlog ADR (chốt khi tới phần tương ứng):** guided decoding cho Qwen cục bộ · AgentRun durable (Postgres-native) · journal-entry validator · chuẩn mực TT99 áp dụng · semantic-layer RLS scope-binding (bổ sung ADR-0005) · eval pass^k governance · revision ADR-0009 (VRAM theo tải agentic).

---

## 7. Câu hỏi: đã chốt & còn mở

**Đã chốt (2026-06-10):** ❶ chưa dùng ERP API → demo trên mock; ❷ chưa dùng LLM cục bộ đọc data → demo trên cloud (corpus không nhạy); ❸ chế độ kế toán **TT99/2025**; ❹ tài nguyên mở rộng sau khi chứng minh giá trị.

**Còn mở (cần chủ dự án/BRAVO):**
- File bổ sung *doanh nghiệp + quy trình triển khai* — định dạng nào (PDF/DOCX), bao nhiêu, scope?
- Mock data: mức "giống thật" mong muốn? (xem [MOCK-DATA-SPEC.md §quyết-định](MOCK-DATA-SPEC.md))
- Ngưỡng giá trị agentic-vs-RAG (xem [AGENTIC-SPIKE-WS0.md](AGENTIC-SPIKE-WS0.md)) — đề xuất mặc định để chốt sau.
- Khi nào có GPU + ERP API → mở Deferred workstreams.

---

## 8. Tham chiếu
- Nghiên cứu: [research/findings/K-agentic-architecture.md](research/findings/K-agentic-architecture.md) (synthesis) · [phụ lục chi tiết](research/findings/K-appendix-threads-detail.md).
- Chủ quyền dữ liệu & vì sao demo dùng cloud: [SOVEREIGNTY-DEMO-NOTE.md](SOVEREIGNTY-DEMO-NOTE.md).
- Mock data: [MOCK-DATA-SPEC.md](MOCK-DATA-SPEC.md) · Spike/eval: [AGENTIC-SPIKE-WS0.md](AGENTIC-SPIKE-WS0.md).
- Nền tảng: [VISION.md](VISION.md) · [ARCHITECTURE.md](ARCHITECTURE.md) · [PLAN.md](PLAN.md) · [adr/](adr/).

---

## 9. Phụ lục — Phán quyết Hội đồng & thay đổi bắt buộc (tóm tắt)

| Thành viên | Phán quyết | Điểm chốt |
|---|---|---|
| security-rls-auditor | ⚠️ GO_WITH_CHANGES | 6 lỗ hổng code bịt trước: egress chưa audit, draft thiếu lock/anti-self-approval/RLS, semantic chưa RLS, recall chưa provenance |
| erp-accounting-expert | ⚠️ GO_WITH_CHANGES | verify-gate cho **sai 1.000 lần (tỷ↔triệu)** lọt, calc float → tổng≠chi tiết, draft chưa cân Nợ=Có, neo TT200 (đã chuyển **TT99**) |
| rag-architect | ⚠️ GO_WITH_CHANGES | verify-gate **chưa nối loop** (`grounded=True` hardcode), thiếu Table-RAG cho số trong tài liệu |
| onprem-deployment-engineer | ⚠️ GO_WITH_CHANGES | VRAM ADR-0009 sai cho tải agentic, guided decoding chưa chứng minh offline *(đều thuộc Deferred — không chặn demo cloud)* |
| product-strategist | ⚠️ GO_WITH_CHANGES | financial KHÓA bởi ERP API; phải spike đo trước; phân nhóm, không big-bang |

**19 thay đổi bắt buộc** đã được hấp thụ vào các workstream trên (WS-G/L/M/E) + Deferred. Những thay đổi áp dụng cho **demo**: 6 guardrail (WS-G), value-object+Decimal+semantic-RLS (WS-M), eval pass^k (WS-E). Những thay đổi chỉ áp dụng **production/Phase 3**: journal-validator, draft-lock, AgentRun durable, guided decoding, air-gapped, VRAM benchmark.
