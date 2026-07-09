# Findings M — Technical Decision Synthesis sau 2 lượt research

> Ngày tổng hợp: 2026-07-09. Input: Critical Review + Horizon Scan tới 2026-07-09, đối chiếu với repo BRAVO AI Copilot. Mục tiêu: chốt hướng kỹ thuật theo tư duy phản biện, tránh sửa khi chưa có bằng chứng nội bộ, và ghi lại vùng đã nghiên cứu để lần sau không quét lại.

## 1. Verdict: đủ dùng chưa?

**Đủ dùng để dừng broad research và chuyển sang synthesis/experiment backlog.** Hai lượt đã phủ các trục có rủi ro kiến trúc cao: secure/permission-aware RAG, retrieval cho tài liệu tài chính text+table, parser/provenance, citation/claim verification, NL2SQL/semantic layer, spreadsheet/agent reliability, HITL/draft, pass^k/state eval.

**Chưa đủ để chốt tham số hoặc rewrite implementation.** Các paper chủ yếu là benchmark tiếng Anh, filings/enterprise docs, US-GAAP hoặc dataset tổng quát. Với BRAVO/Vietnamese accounting, quyết định đúng là **ADD_EVAL trước khi CHANGE** cho các điểm như RRF weight, rerank depth, ANN filter mode, table routing, semantic IR, citation verifier.

**Không cần tiếp tục research rộng ngay.** Research tiếp chỉ nên là targeted nếu một checkpoint cần quyết định kiến trúc hoặc nếu có thay đổi pháp lý/sản phẩm mới sau 2026-07-09.

## 2. Spot-check nguồn quan trọng

Đã kiểm nhanh một số nguồn then chốt trên arXiv ngày 2026-07-09:

| source | kết quả kiểm | ảnh hưởng |
|---|---|---|
| HONEYBEE, arXiv:2505.01538 | Có thật; SIGMOD 2026; RBAC dynamic partitioning giảm latency so với RLS trong benchmark vector DB | Không thay RLS ngay; thêm trial khi corpus/tenant lớn |
| Participant-Aware Access Control, arXiv:2509.14608 | Có thật; nhấn mạnh deterministic authorization cho mọi participant trong tương tác | Thêm test/policy cho nội dung nhiều bên |
| Securing the Agent, arXiv:2605.05287 | Có thật; enterprise multitenant retrieval/tool use; server-side orchestration | Củng cố RLS trước context + tool gating |
| From BM25 to Corrective RAG, arXiv:2604.01733 | Có thật; financial text+table; BM25 mạnh, hybrid+rerank tốt nhất | ADD_EVAL retrieval ablation; không khóa tham số top-k theo cảm tính |
| RealDocBench, arXiv:2606.07401 | Có thật; field-level QA/layout trên regulated docs | Thêm field/cell-level parser eval |
| SpreadsheetBench 2, arXiv:2606.29955 | Có thật; best model 34.89% task accuracy | Không tự động hóa spreadsheet end-to-end ngoài HITL |
| FinGround, arXiv:2604.23588 | Có thật; atomic financial claim verification | Mở rộng verify-gate sang claim/citation |
| EntSQL, arXiv:2606.03363 | Có thật; best English system 15.9% với enterprise knowledge | Giữ no-free-form-SQL |
| Semantic Layers for Reliable LLM Analytics, arXiv:2604.25149 | Có thật; semantic doc cải thiện accuracy | Thêm semantic layer eval, không mở free SQL |

## 3. Final decision table

| area | verdict | quyết định | repo impact | hành động kế tiếp |
|---|---|---|---|---|
| RLS trước context/retrieval | KEEP + ADD_EVAL | Giữ authorization deterministic trước context; không post-filter bằng LLM | `app/security/rls.py`, `app/rag/retriever.py`, `tests/test_rls.py`, `tests/test_memory_rls.py` | P0 leak/revocation/cache/memory probes |
| pgvector/ANN filtered recall | ADD_EVAL | RLS đúng về bảo mật nhưng có thể starve recall/latency khi filter selectivity thấp | `app/rag/retriever.py`, `app/eval/retrieval_eval.py` | Benchmark exact vs ANN scoped recall |
| RBAC partition/HONEYBEE | WATCH/TRIAL | Hấp dẫn khi corpus lớn; chưa đáng thay infra hiện tại | design spike, không rewrite | Chỉ mở khi p95 latency hoặc recall scoped thất bại |
| Participant-aware ACL | ADD_EVAL | Kiểm quyền theo người hỏi là chưa đủ cho nội dung nhiều participant | security policy/tests | Thêm scenario tài liệu có nhiều phòng ban/bên liên quan |
| Hybrid BM25 + vector + rerank | KEEP + ADD_EVAL | Giữ hướng hybrid, nhưng không canonize RRF/top-k/depth | `app/rag/retriever.py`, `app/rag/rerank.py` | Ablation BM25/vector/RRF/weighted/rerank |
| Rerank depth top-150 -> top-20 | ADD_EVAL | Có evidence rerank tốt, nhưng depth là tham số corpus-specific | `app/rag/rerank.py` | Sweep quality/latency |
| Table/cell provenance | KEEP + ADD_EVAL | Finance cần page/sheet/cell provenance; markdown đủ chỉ cho bảng đơn giản | `app/ingestion/parser.py`, `app/eval` | Table-cell citation eval + routing |
| LLM không tự tính số | KEEP | Invariant vẫn đúng; số phải từ calc/semantic layer deterministic | `app/data_layer/calc.py`, `app/data_layer/grounding.py` | Enforce Decimal + formula/cross-foot eval |
| Verify-gate hiện tại | CHANGE | Numeric gate chưa đủ; cần claim/citation support cho câu high-risk | `app/data_layer/grounding.py`, `app/eval/faithfulness.py` | Atomic claim + citation entailment gate |
| No free-form SQL | KEEP | NL2SQL enterprise vẫn quá yếu/rủi ro; semantic layer là default | `docs/adr/0005-no-free-form-sql.md`, `app/data_layer/catalog.py` | Catalog abstain + scope-binding eval |
| Expert read-only NL2SQL sandbox | DEFER | Có thể hữu ích sau này, nhưng không thuộc default finance path | ADR backlog | Chỉ xét sau injection/read-only/abstain eval |
| Single constrained agent | KEEP | Control-flow-in-code phù hợp finance hơn autonomous/multi-agent | `app/agent/loop.py`, `app/eval/passk.py` | pass^k + perturb/fault eval |
| Multi-agent write | DEFER/REJECT | Chưa có evidence đủ cho BRAVO MVP, tăng audit/security risk | agent backlog | Chỉ cho read-only decomposition nếu pass^k tốt hơn |
| Spreadsheet automation end-to-end | DEFER | Benchmark mới cho thấy độ tin cậy quá thấp | AP/export workflows | Giữ HITL/export-only |
| HITL draft/payload hash | KEEP | Maker-checker, hash pinning, no direct ERP write vẫn là invariant | `app/erp/draft_queue.py` | Tamper/replay/idempotency tests |
| Single LLM judge score | REJECT | LLM judge bias; không dùng làm release gate duy nhất | `app/eval` | Deterministic first, calibrated judge secondary |

## 4. Top 10 changes/evals đáng làm nhất

1. **P0 — RLS leak/revocation/cache/memory eval:** unauthorized chunk count = 0, revoke freshness rõ ràng.
2. **P0 — ANN filtered recall benchmark:** exact vs HNSW/iterative scoped search theo filter selectivity.
3. **P0 — Claim/citation verification gate:** high-risk finance/legal/accounting claims phải được citation support, không chỉ có citation.
4. **P0 — Table-cell provenance eval:** page/sheet/table/row/column/cell citation accuracy cho AP/tax docs.
5. **P0 — Metric catalog abstention:** out-of-catalog question phải từ chối/đề nghị metric thay vì bịa query.
6. **P0 — Prompt injection through retrieved content:** poisoned docs không được escalade tool/write/egress.
7. **P0 — Agent pass^k state eval:** pass^8, final-state correctness, hard-fail taxonomy.
8. **P1 — Hybrid retrieval ablation:** BM25/vector/RRF/weighted fusion/rerank trên query tiếng Việt BRAVO.
9. **P1 — Rerank depth sweep:** quality vs p95 latency; chốt dynamic depth nếu cần.
10. **P1 — Table routing eval:** markdown vs structured store/solver cho simple/cross-row/cross-sheet tasks.

## 5. Top 10 thứ không nên làm để tránh over-engineering

1. Không mở free-form SQL trên ERP default path.
2. Không build full multi-agent write workflow cho MVP.
3. Không tự động hóa spreadsheet end-to-end ngoài HITL.
4. Không rewrite RLS sang RBAC partition/HONEYBEE trước khi có bottleneck thật.
5. Không thêm Temporal/durable orchestration nặng trước khi có failure/retry data.
6. Không build FT-RAG/table graph infra lớn khi table-cell eval chưa chứng minh markdown/structured routing thiếu.
7. Không dùng một LLM-judge score làm release gate.
8. Không khóa vĩnh viễn RRF/top-k/rerank depth bằng benchmark ngoài domain.
9. Không nghiên cứu lại local model/GPU/Qwen trong vòng này; chủ đề này đã tách khỏi quyết định hiện tại.
10. Không dựa vào vendor claim về semantic layer/RAG security nếu không có benchmark hoặc internal eval.

## 6. ADR/docs có thể cần cập nhật

| file | mức độ | nội dung |
|---|---|---|
| `docs/adr/0012-verify-gate-number-integrity.md` | CHANGE/extend | Tạo ADR mới hoặc amendment: verify-gate high-risk = number integrity + claim/citation support |
| `docs/adr/0005-no-free-form-sql.md` | KEEP/clarify | Bổ sung semantic-layer scope-binding, catalog abstention, expert sandbox = deferred |
| `docs/adr/0010-agent-loop-architecture.md` | KEEP/clarify | Thêm pass^k/state/fault eval là điều kiện nới agent autonomy |
| `docs/SECURITY-RLS.md` | UPDATE | Participant-aware ACL, revocation/tombstone, cache/memory leak, ANN filtered recall |
| `docs/BRAVO-KB-TAXONOMY-EVAL.md` | UPDATE | Thêm claim-force/citation entailment, field/cell-level provenance |
| `docs/work-packages/STATUS.md` | UPDATE | Thêm các eval P0/P1 vào backlog thực thi |
| `docs/ROADMAP.md` | UPDATE | Chuyển broad research sang experiment gates |

## 7. Final experiment backlog

| priority | experiment | hypothesis | minimal dataset | metric/pass gate | repo area |
|---|---|---|---|---|---|
| P0 | RLS leak + revocation freshness | No unauthorized context after permission changes | 3 departments, 20 docs, revoke/update events | 0 leaks; revoke semantics documented | security/rag/memory |
| P0 | ANN filtered recall | Scoped ANN does not silently starve | 1k-10k chunks with skewed ACL filters | recall@10 >= 0.95 exact or fallback | rag/eval |
| P0 | Prompt injection via retrieved content | Untrusted docs cannot steer tools | 30 poisoned docs | unsafe tool/write/egress = 0 | agent/security |
| P0 | Table-cell citation | Finance answers cite exact cell/source | 30 AP/tax tables, 100 questions | cell citation >= 0.98 for high-risk | ingestion/eval |
| P0 | Claim/citation entailment | Citation warrants claim force | 100 claim-source triples | 0 unsupported P0 claims | grounding/eval |
| P0 | Metric catalog abstention | Out-of-catalog asks are refused/routed | 50 in, 50 out | out recall >= 0.95; false abstain <= 0.10 | data_layer/catalog |
| P0 | Agent pass^k state eval | Workflow reliable across repeated runs | 40 trajectories, k=8 | pass^8 >= 0.95; 0 hard fails | agent/eval |
| P0 | Draft tamper/replay | Hash/lock prevents drift/double approve | 10 draft scenarios | tamper/replay success = 0 | erp/draft_queue |
| P1 | Retrieval ablation | Chosen hybrid config is Pareto-best | 100 Vietnamese BRAVO queries | nDCG/recall + p95 target | rag/eval |
| P1 | Rerank depth sweep | Depth has measurable quality gain | same as retrieval ablation | >3% quality gain within latency budget | rag/rerank |
| P1 | Table routing | Markdown only for simple tables | 60 table tasks | route solver when markdown < 0.95 | ingestion/data_layer |
| P2 | RBAC partition trial | Partitioning helps only at scale | large synthetic ACL corpus | latency/recall/storage trade-off | design spike |

## 8. Decision checkpoints cần reasoning xtra-high

1. **Exact/RLS SQL vs ANN scoped vector vs RBAC partition:** chỉ quyết sau khi có scoped recall/latency benchmark.
2. **Verify-gate architecture:** deterministic rules, NLI/LLM judge, hoặc hybrid; cần human-labeled claim-source set.
3. **Semantic layer/IR design:** catalog-only, SMQ-like IR, Cube/dbt MetricFlow; cần metric coverage và abstain eval.
4. **Table routing:** markdown/simple vs structured solver/DuckDB/SQL Server view; cần complexity taxonomy.
5. **Agent autonomy boundary:** single agent vs read-only subagents; quyết bằng pass^k/state/fault data.
6. **Durable execution:** Postgres-native minimal vs Temporal; chỉ quyết khi có long-running retry/failure evidence.

## 9. Research ledger: đã tra, không cần quét lại trong vòng tới

| topic | status | lý do không quét lại ngay | trigger mở lại |
|---|---|---|---|
| Generic secure/permission-aware RAG | CLOSED for now | Đã có đủ nguồn 2025-2026 + repo stance rõ | Có incident/leak class mới hoặc đổi vector store |
| RLS before context vs post-filter | CLOSED | Evidence mạnh, quyết định KEEP | Chỉ mở nếu có formal post-filter completeness proof trong stack cụ thể |
| Generic hybrid retrieval/rerank | CLOSED as research, OPEN as eval | Research đủ; còn thiếu số BRAVO | Sau retrieval ablation nội bộ |
| Financial/table QA benchmarks | CLOSED as research, OPEN as eval | TAT-QA/FinQA/DocFinQA/T2/2026 đủ làm template | Khi cần dataset tiếng Việt/VAS mới |
| Citation/faithfulness general literature | CLOSED as research, OPEN as implementation | Đủ để quyết CHANGE verify-gate | Khi chọn cụ thể verifier/NLI/judge |
| Enterprise NL2SQL risk | CLOSED | Evidence mạnh để KEEP no-free-SQL | Chỉ mở cho expert sandbox riêng |
| Spreadsheet agents | CLOSED | SpreadsheetBench 2 đủ để DEFER automation | Khi benchmark đạt mức production-grade hoặc có internal constrained workflow |
| Multi-agent hype | CLOSED | Chưa có evidence cho write workflow finance | Khi read-only subagent pass^k vượt single-agent |
| Local model/GPU/Qwen | OUT OF SCOPE | Không thuộc hai lượt này và đã có ADR riêng | Khi chuẩn bị pilot local thật |
| Vendor semantic layer claims | DO NOT USE as primary | Chỉ dùng nếu có benchmark độc lập/internal eval | Khi vendor cung cấp reproducible evidence |
| Legal/market VN | SEPARATE TRACK | Không quyết định technical architecture ở findings này | Khi cập nhật pháp lý/sales positioning |

## 10. Search log cho lần sau

Đã dùng hoặc nhận từ hai lượt các nhóm query:

- `permission-aware RAG access control vector database ACL`
- `secure multi-tenant RAG changing permissions tombstone`
- `filtered ANN selectivity vector database RLS`
- `financial document QA text table RAG 2026`
- `citation verification RAG claim support benchmark`
- `evidence-force calibration cited RAG`
- `RAG evaluation faithfulness LLM judge reliability`
- `enterprise text-to-SQL semantic layer metrics layer 2026`
- `spreadsheet agent business workflow benchmark 2026`
- `state-based agent eval pass^k fault injection auditability`

Không cần quét lại các query này trước khi có kết quả eval nội bộ hoặc nguồn mới sau 2026-07-09.
