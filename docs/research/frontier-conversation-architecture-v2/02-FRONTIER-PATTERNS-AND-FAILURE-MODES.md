# Frontier patterns và failure modes liên quan

## 1. Cách dùng nghiên cứu

Đây không phải bảng xếp hạng framework. Các nguồn được dùng để rút ra pattern và anti-pattern có
thể kiểm chứng. Tài liệu sản phẩm chứng minh capability/contract; paper benchmark cung cấp bằng
chứng về failure; claim marketing không được xem là bằng chứng chất lượng cho BRAVO.

## 2. Pattern có thể áp dụng

### 2.1 Chọn workflow xác định trước khi chọn agent mở

Anthropic khuyến nghị bắt đầu từ pattern đơn giản có thể ghép, dùng workflow cho task có đường đi
dự đoán được và agent cho task mở; mỗi tầng agentic tăng latency/cost và làm debug khó hơn
([Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)).

Áp dụng: accounting close, invoice processing, diagnostic ladder và approval là workflow card có
branch rõ. Model có quyền lập kế hoạch trong giới hạn, không được tự phát minh policy hay state machine.

### 2.2 Context là tài nguyên hữu hạn

“Context rot”, compaction, structured note-taking và just-in-time context đều chỉ ra long context
không đồng nghĩa sử dụng tốt
([Anthropic context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)).
Nghiên cứu Lost in the Middle cho thấy vị trí thông tin ảnh hưởng đáng kể đến khả năng dùng thông tin
([paper](https://arxiv.org/abs/2307.03172)).

Áp dụng: tạo `ContextCompiler`; pin goal/current node/constraints, lấy artifact theo nhu cầu, tóm tắt
tool output và giữ link đến raw trace. Summary không được làm mất correction hoặc contradiction.

### 2.3 Tách session, state và memory

Google ADK phân biệt Session/Event, State, Memory và InvocationContext
([sessions](https://google.github.io/adk-docs/sessions/),
[context](https://google.github.io/adk-docs/context/)). OpenAI Agents SDK Sessions hỗ trợ history,
limiting và compaction, đồng thời cảnh báo không trộn các continuation mechanism không tương thích
([sessions](https://openai.github.io/openai-agents-python/sessions/)).

Áp dụng: transcript, task state, user preference, environment fact và organization knowledge có
scope/lifecycle khác nhau. Không có một bảng `memory` chung cho tất cả.

### 2.4 Manager giữ ownership; specialist là tool

OpenAI phân biệt manager/agents-as-tools và handoff. Manager phù hợp khi một agent phải giữ final
answer và guardrail chung
([orchestration](https://openai.github.io/openai-agents-python/multi_agent/)). Anthropic ghi nhận
multi-agent phù hợp breadth-first, task độc lập; kém phù hợp khi các bước phụ thuộc chung một context,
đồng thời tiêu tốn nhiều token hơn
([multi-agent research](https://www.anthropic.com/engineering/built-multi-agent-research-system)).

Áp dụng: conversation owner gọi schema analyst, KEDB search, finance planner dưới dạng capability.
Chỉ offline research jobs độc lập mới cân nhắc worker song song.

### 2.5 Query decomposition và activity trace

Azure AI Search agentic retrieval tách query phức tạp thành subquery song song, semantic rerank và
trả activity log; đổi lại có thêm latency và một số tính năng preview
([overview](https://learn.microsoft.com/en-us/azure/search/agentic-retrieval-overview)). Contextual
Retrieval cho thấy chunk cần được làm giàu bằng ngữ cảnh tài liệu trước embedding/BM25
([Anthropic](https://www.anthropic.com/engineering/contextual-retrieval)).

Áp dụng: decomposition phải bắt nguồn từ plan node, không chỉ từ paraphrase. Trace phải chỉ ra
query nào phục vụ prerequisite nào.

### 2.6 Memory cần benchmark riêng

LongMemEval tách extraction, multi-session reasoning, temporal reasoning, updates và abstention;
các hệ thống giảm đáng kể chất lượng khi hội thoại kéo dài
([paper](https://arxiv.org/abs/2410.10813)). StateFuse, một kết quả mới 2026, nhấn mạnh giữ xung đột
thay vì ép thành một fact duy nhất, nhưng chưa đủ để coi là giải pháp phổ quát
([paper](https://arxiv.org/abs/2607.05844)).

Áp dụng: benchmark memory riêng cho correction, supersede, temporal scope và conflict; không chỉ
kiểm tra “model nhớ tên”.

### 2.7 Eval phải mô phỏng người dùng và trạng thái

τ-bench đo agent xử lý policy, tool và user trong task thực tế; τ²-bench mở rộng sang dual-control,
nơi user và agent cùng thay đổi environment
([τ-bench](https://arxiv.org/abs/2406.12045),
[τ²-bench](https://arxiv.org/abs/2506.07982)). ToolSandbox cho thấy state dependency và thiếu thông
tin là failure class khó
([paper](https://arxiv.org/abs/2408.04682)). CRMArena-Pro báo cáo multi-turn business task thấp hơn
single-turn đáng kể
([paper](https://arxiv.org/abs/2505.18878)).

Áp dụng: BRAVO eval phải có simulated user, mutable ledger và milestone. Một response đẹp không đồng
nghĩa task hoàn thành.

### 2.8 Chẩn đoán retrieval và generation riêng

RAGChecker đánh giá retrieval và generation theo claim thay vì gộp thành một score
([paper](https://arxiv.org/abs/2408.08067)).

Áp dụng: khi thiếu “kết chuyển”, phải biết planner không tạo node, retriever không lấy artifact hay
composer bỏ qua context. Nếu không, đội sẽ tối ưu sai subsystem.

### 2.9 Knowledge improvement phải có Solve Loop/Evolve Loop

KCS yêu cầu capture, structure, reuse, improve trong Solve Loop và quản lý content health ở Evolve
Loop
([KCS Practices Guide](https://library.serviceinnovation.org/KCS_Practices_Guide_v6)). Intercom cũng
phân biệt source native/synced và nhấn mạnh content phải được quản lý chủ động
([Knowledge sources](https://www.intercom.com/help/en/articles/9440354-knowledge-sources-to-power-ai-agents-and-self-serve-support)).

Áp dụng: failed conversation sinh gap/candidate artifact; không tự ingest nguyên văn câu trả lời.
Risk class quyết định review/promotion.

### 2.10 External grounding là tool call có provenance

Google Search grounding trả search calls, results và inline grounding metadata
([Gemini API](https://ai.google.dev/gemini-api/docs/google-search)). Đây là pattern tốt cho BravoGen:
external expert là tool có request/response/provenance/timeout, không phải hidden fallback.

## 3. Failure modes của frontier systems cần tránh

| Failure | Bằng chứng/pattern | BRAVO guardrail |
|---|---|---|
| Agent loop quá mức | framework abstraction che prompt/tool và làm tăng complexity | workflow card trước; max steps/budget |
| Context stuffing | long context bỏ sót thông tin giữa | context compiler + position-aware tests |
| Over-compaction | summary mất nuance/correction | typed ledger + raw event pointer |
| Multi-agent coordination tax | duplicate search, token/cost, shared context yếu | single owner; multi-agent gate |
| Sequential planning bị multi-agent làm tệ | architecture-task mismatch | không fan-out workflow kế toán phụ thuộc state |
| Retrieval score che planner failure | aggregate RAG metric | component attribution |
| Hallucinated tool/schema state | stateful tool benchmarks vẫn khó | read tool + precondition + no-guess contract |
| User-agent coordination failure | user thay đổi state giữa turn | observe/reconcile/replan loop |
| Memory stale/conflicting | update và temporal reasoning yếu | supersedes/conflict/effective-time fields |
| Prompt injection qua external data | RAG không loại bỏ injection | treat content as data, tool allowlist, output isolation |
| External answer becomes truth | source confidence bị lẫn | candidate-only ingestion + review/eval |
| Optimize citation over task | proxy metric | TMS north star; citation risk-tiered |
| Fine-tune context collapse | playbook bị rút gọn/mất edge cases | explicit artifact curation trước training |

Về security, OWASP xác định indirect prompt injection có thể đến từ document/tool output và RAG
không tự loại bỏ rủi ro
([Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)). AgentDojo cũng cho thấy
task utility và resistance to injection phải được đo cùng nhau
([paper](https://arxiv.org/abs/2406.13352)).

## 4. Emerging research — dùng như giả thuyết, không như quyết định

- Agentic Context Engineering đề xuất generation/reflection/curation để phát triển playbook và cảnh
  báo “brevity bias/context collapse” ([ACE](https://arxiv.org/abs/2510.04618)). Áp dụng thử cho
  offline candidate jobs; không cho tự cập nhật production prompt.
- Science of Scaling Agent Systems cho thấy topology phải khớp loại task; hệ đa-agent có thể tăng
  decomposable reasoning nhưng làm giảm sequential planning
  ([paper](https://arxiv.org/abs/2512.08296)). Dùng làm test gate, không làm lý do xây swarm.
- Managed memory của Vertex/AWS có lifecycle/IAM và short/long-term separation
  ([Vertex Memory Bank](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/memory-bank/overview),
  [AWS AgentCore Memory](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory.html)).
  Có thể mua storage/extraction, nhưng BRAVO vẫn phải sở hữu meaning, conflict policy và eval.

## 5. Kết luận build/buy/adopt

| Capability | Quyết định |
|---|---|
| Goal/task/domain schemas | Build, BRAVO sở hữu |
| Workflow authoring/review | Build thin authoring + Git/JSONB trước |
| Embedding/vector/BM25/rerank | Adopt commodity components |
| Session storage/compaction primitives | Adopt qua runtime nếu đạt contract |
| Domain memory policy | Build |
| Durable execution | Theo decision pack cũ; spike DBOS/candidates |
| External expert integration | Build gateway mỏng; không scrape credential lifecycle |
| Evaluation harness | Extend current BRAVO eval; dùng patterns τ/RAGChecker |
| Graph DB/GraphRAG | Defer, benchmark-gated |
| Fine-tuning | Defer đến sau Phase 3 |

## 6. Những claim không được đưa ra

- Không suy luận BravoGen dùng GraphRAG, tự học ticket hay có workflow engine từ output/UI.
- Không suy luận sản phẩm frontier “giải xong memory” chỉ vì có Memory API.
- Không dùng benchmark tổng quát để hứa hẹn accuracy BRAVO.
- Không coi một paper mới hoặc vendor demo là production proof.
- Không coi output giống chuyên gia là verified knowledge nếu thiếu environment/version/evidence.

