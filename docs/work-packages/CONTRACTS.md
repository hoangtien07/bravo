# CONTRACTS — Hợp đồng interface dùng chung (đọc TRƯỚC mọi gói)

> Đây là **nguồn-sự-thật về INTERFACE** giữa các work-package. Code theo đúng đây → các gói ghép được. Chữ ký dưới là **hợp đồng**, không phải code cuối — implement trong file thật theo module.
> Nền: modular monolith, `app/` đã có. Stack: FastAPI + async SQLAlchemy + PostgreSQL/pgvector. Quy ước: async cho I/O; tiền = `Decimal`; mọi truy vấn dữ liệu mang `Identity` và lọc RLS **trong SQL**.

## 1. Bố cục module (ranh giới sở hữu)
```
app/
  security/    rls.py(Identity, build_*_filter, can_access) · auth.py        [WP-C, WP-G]
  ingestion/   parser.py · pdf_parser.py · chunker.py · pipeline.py          [WP-A]
  rag/         retriever.py · embedding.py · rerank.py        (đã đủ — REUSE) [—]
  data_layer/  semantic.py · calc.py · grounding.py · catalog.py             [WP-B, WP-F]
  agent/       loop.py · tools.py · memory.py                                [WP-D, WP-G]
  erp/         draft_queue.py · client.py(deferred)                          [WP-E]
  llm/         router.py                                                     [WP-C]
  database/    models.py                                                     [WP-E, WP-G]
  eval/        run.py · golden.py · probes.py · faithfulness.py              [WP-H]
```

## 2. Kiểu dùng chung (hợp đồng dữ liệu)

### 2.1 Identity — ĐÃ CÓ ([security/rls.py](../../app/security/rls.py)), không đổi chữ ký
```python
Identity(employee_id: UUID, department_ids: list[UUID], permissions: set[str], is_admin: bool)
#  .scope_level(resource, action) -> "own_dept" | "all" | None
```

### 2.2 Tool — MỞ RỘNG dataclass ([agent/tools.py](../../app/agent/tools.py)) — chủ: WP-D
```python
@dataclass
class Tool:
    name: str
    fn: Callable                      # async or sync
    json_schema: dict                 # JSON Schema cho input (để structured-output/guided-decoding)
    read_only: bool = True            # đọc=auto; ghi=False
    requires_approval: bool = False   # ghi -> True (HITL, đã có)
    required_permission: str | None = None   # vd "metric:read"; None = ai cũng gọi được
# REGISTRY: dict[str, Tool]; register(...) giữ nguyên + thêm field trên.
```

### 2.3 MetricResult — VALUE-OBJECT (thay float trần) — chủ: WP-B, dùng bởi WP-F/WP-D
```python
@dataclass(frozen=True)
class MetricResult:
    metric_id: str
    value: Decimal                    # BẮT BUỘC Decimal (tiền) — không float
    unit: str                         # "VND" | "cái" | "%" ...
    scale: str                        # "đồng" | "nghìn" | "triệu" | "tỷ"  (để verify chặn tỷ↔triệu)
    currency: str | None              # "VND" | "USD" | None
    period: str | None                # "2026-Q1" ...
    entity: str | None                # đơn vị cơ sở
    variant: str | None               # "thuần|gộp", "đã_VAT|chưa_VAT", "dồn_tích|tiền_mặt"
    provenance: str                   # chuỗi trích dẫn (metric-id + params, hoặc nguồn ERP/ô)
    is_demo: bool = False             # nhãn "DEMO" cho mock
```

### 2.4 DataSource — PROTOCOL ([data_layer/semantic.py](../../app/data_layer/semantic.py)) — đổi chữ ký: thêm `identity`
```python
class DataSource(Protocol):
    async def fetch(self, metric_id: str, params: Mapping, identity: Identity) -> MetricResult: ...
# MockDataSource (WP-F) và BravoErpDataSource (deferred) cùng implement.
# identity BẮT BUỘC: source tự áp scope (department/đơn vị) — RLS ở tầng số.
```

### 2.5 VerifyVerdict — verify-gate ([data_layer/grounding.py](../../app/data_layer/grounding.py)) — chủ: WP-B
```python
@dataclass
class VerifyVerdict:
    grounded: bool                    # mọi số trong answer khớp engine_values?
    unmatched: list[str]              # số không khớp -> mask/abstain
    safe_answer: str                  # answer đã mask số chưa khớp (hoặc câu abstain)
def verify_numbers(answer: str, engine_values: list[MetricResult]) -> VerifyVerdict: ...
```

### 2.6 AgentRun + Draft — ORM ([database/models.py](../../app/database/models.py)) — chủ: WP-E
```python
class AgentRun(Base):
    id: UUID; session_id: UUID; employee_id: UUID
    status: str            # "running" | "paused_for_approval" | "done" | "failed"
    checkpoint_state: dict # JSONB: messages + retrieved-context + metric-results (để resume DÙNG LẠI, không re-retrieve)
    idempotency_key: str   # UNIQUE — chống tạo draft trùng khi resume
    lease_owner: str | None; lease_expires_at: datetime | None   # chống 2 worker resume cùng run
    created_at: datetime
class Draft(Base):   # MỞ RỘNG draft hiện có
    id: UUID; kind: str; payload: dict; payload_hash: str
    department_id: UUID | None   # THÊM: để list_pending lọc RLS
    created_by: UUID             # THÊM: chống self-approval
    agent_run_id: UUID | None    # THÊM: nối draft với run
    status: str                  # "pending" | "approved" | "rejected"
```

### 2.7 Budget — circuit breaker — chủ: WP-D
```python
@dataclass
class Budget:
    max_steps: int = 4        # đặt theo reliability_horizon (spike); demo tạm 4
    max_tokens: int = 8000
    deadline_s: float = 30.0
# loop ENFORCE: kiểm trước mỗi tool-call/LLM-call; vượt -> dừng + audit (không chỉ alert).
```

## 3. Seam tích hợp (ai gọi ai — hợp đồng luồng)
```
AgentSession.step(user_msg):                                   [WP-D]
  ctx, chunks = retriever.retrieve(db, identity, q)            [RAG đã có — RLS-in-SQL]
  tools = filter_tools_by_permission(REGISTRY, identity)       [WP-D + WP-G: RLS-filter tool]
  loop (<= Budget):                                            [WP-D]
     plan = llm_structured(messages, tools, schema)            [Pydantic AI structured-output]
     if plan.tool: result = call_tool(plan.tool, plan.args)    [WP-D: RLS lần 2 + requires_approval]
        # write tool -> draft_queue.create_draft(...)          [WP-E]
        # metric tool -> semantic.answer(... DataSource ...)    [WP-F]
     answer = llm(messages + observations)
  verdict = grounding.verify_numbers(answer, engine_values)    [WP-B] -> mask/abstain nếu !grounded
  return verdict.safe_answer + citations
router.chat(messages, context):                                [WP-C]
  sensitive = classify_context(context)   # KHÔNG nhận sensitive thủ công
  if backend == cloud: AuditLog(llm.egress, ...) TRƯỚC khi gọi  # audit-then-egress, fail-closed
```

### 3.1 Hàm hợp đồng (chữ ký cố định để gói khác gọi)
```python
# WP-C
def classify_context(chunks, metric_results) -> bool          # True=nhạy -> local; unknown -> True
async def router.chat(messages, *, context, **kw) -> tuple[str, RoutingDecision]
# WP-D
def filter_tools_by_permission(registry, identity) -> list[Tool]
async def call_tool(name, args, identity) -> dict             # RLS lần 2 + requires_approval->draft
# WP-F
async def semantic.answer(question, source: DataSource, identity, plan_fn) -> MetricResult | None
# WP-E
async def draft_queue.create_draft(db, identity, kind, payload, agent_run_id) -> Draft   # idempotent
async def draft_queue.approve_draft(db, identity, draft_id) -> Draft   # advisory-lock + anti-self-approval + perm
```

## 4. Checklist invariant (mọi gói tự soát)
- **#1 RLS:** mọi truy vấn dữ liệu lọc scope **trong SQL** mang `Identity`; không lọc RAM; tool/metric thiếu quyền không xuất hiện + chặn lần 2 ở call.
- **#2 Không xâm lấn:** ghi = `create_draft` (requires_approval); không đường ghi trực tiếp; không chạm SQL Server ERP gốc (chỉ Postgres lớp AI).
- **#3 Zero-hallucination số:** LLM không sinh/sửa số; số từ engine; verify-gate cứng; thiếu căn cứ → abstain.
- **#4 Chủ quyền:** demo cloud chỉ cho dữ liệu không nhạy; classify_context fail-closed→local; mọi cloud call audit; không egress ẩn.

## 5. Lằn ranh chống over-engineering (NON-NEGOTIABLE — [ADR-0013](../adr/0013-reuse-vs-rewrite-and-topology.md))
KHÔNG: run-as-service letta/docsgpt · sandbox letta (E2B/Modal/venv+pip) · LiteLLM 12-provider · Temporal/Dapr khi chưa đo · multi-agent/group-chat · monorepo/microservices cho MVP · OCR full-page mặc định (`do_ocr=False`) · ép JSON-mode cho cả câu trả lời (chỉ tool_call/metric/citation) · "LLM tự verify số" (schema-valid ≠ số đúng) · vendor/fork code Docling (dùng pip-dep pin version).

## 6. Bảng "dùng library gì" (reuse — đừng tái tạo)
| Việc | Dùng | KHÔNG tự viết |
|---|---|---|
| Bóc bảng PDF/DOCX/XLSX | **Docling** (`do_table_structure=True`, `do_ocr=False`) | thuật toán table-structure |
| Provenance ô/sheet | **Docling** `TableItem.prov` | toạ độ ô bằng openpyxl thủ công |
| Embedding | **sentence-transformers/FlagEmbedding** bge-m3 (đã có) | model embedding |
| Vector search | **pgvector** `cosine_distance` trong SQL (đã có) | ANN index |
| Structured tool-output | **Pydantic AI** (lib thuần, self-host) | parser tool-call thủ công |
| LLM client | **openai SDK** trỏ vLLM/Ollama (router.py đã có) | LiteLLM 12-provider |
| Rerank | **ViRanker** qua sentence-transformers (đã có) | cross-encoder |
