# Quyết định OSS cho reasoning core: Pydantic AI, LangGraph, ZenML và Kitaru

**Ngày đánh giá:** 2026-07-16  
**Trạng thái:** `DECISION FOR R1 PROTOTYPE` — chưa phải phê duyệt production  
**Đầu vào:** Deep Research report, code BRAVO hiện tại, repo ZenML local, tài liệu chính thức của Pydantic AI, LangGraph, ZenML và Kitaru.

## 1. Quyết định ngắn gọn

BRAVO nên tiếp tục theo **strangler reasoning core**, không vá tiếp loop hiện tại và cũng chưa tách thành một clean platform hoàn toàn.

Ứng viên mặc định cho System C trong R1 là:

```text
Pydantic AI làm consultation/reasoning core
  + contract nghiệp vụ BRAVO hiện có
  + retrieval/schema/KEDB qua adapter
  + Postgres task state/checkpoint hiện có
  + RLS/tool/draft/approval/audit hiện có
  + OpenTelemetry trace hiện có
```

Không đưa `Pydantic Graph`, `Temporal`, `Kitaru`, `ZenML` hay một observability server mới vào đường chạy chính của R1 nếu benchmark chưa chứng minh cần thiết.

- **LangGraph**: challenger có điều kiện, không phải implementation song song mặc định.
- **Kitaru**: runtime thử nghiệm cho replay/fork/diff và wait/resume sau khi core Pydantic AI đã chạy; không dùng đồng thời với Temporal trong R1.
- **ZenML**: chỉ cân nhắc cho outer loop offline như ingestion, batch evaluation, curation và experiment lineage; không dùng làm conversational core.
- **Temporal**: hoãn tới khi có workflow kéo dài qua nhiều giờ/ngày, nhiều side effect và yêu cầu recovery/idempotency mà Postgres/ARQ hiện tại không đáp ứng.

## 2. Điều chỉnh báo cáo Deep Research

### 2.1 Phần đúng và nên giữ

Báo cáo đã xác định đúng các điểm quan trọng:

1. Không thể chữa thiếu hiểu biết nghiệp vụ chỉ bằng prompt dài hoặc thêm RAG.
2. Không nên full rewrite platform khi auth, RLS, retrieval, approval, audit và dữ liệu hiện có vẫn tái sử dụng được.
3. Cần matched-model/matched-evidence benchmark để phân biệt lỗi model, retrieval và architecture.
4. Runtime phải nằm sau adapter; domain contract của BRAVO mới là tài sản bền.
5. Không nên bắt đầu bằng GraphRAG hoặc multi-agent phức tạp.

### 2.2 Phần cần sửa

Khuyến nghị `Pydantic AI + Pydantic Graph + Temporal + Langfuse` là một **target landscape hợp lý**, nhưng là một **R1 stack không tối ưu** cho solo developer và codebase hiện tại.

Nó tạo ít nhất bốn nguồn trạng thái/trace có thể chồng lấn:

1. `TaskState`, `MemoryBlock`, `AgentRun.checkpoint_state` trong Postgres hiện tại;
2. state machine của Pydantic Graph;
3. workflow history của Temporal;
4. trace/dataset của Langfuse.

Điều này làm tăng migration, vận hành và root-cause surface trước khi chứng minh rằng durable execution là nguyên nhân làm câu trả lời hiện tại kém hữu ích. Vấn đề quan sát được hiện nay nằm chủ yếu ở **task representation, business prerequisite planning, evidence composition và answer synthesis**, không phải ở việc workflow không sống sót qua crash.

Tài liệu Pydantic Graph cũng tự khuyến cáo graph không phù hợp cho mọi bài toán và cần nhiều setup. Vì vậy không dùng graph chỉ để biểu diễn pipeline tuyến tính `brief → plan → evidence → answer → critic`.

## 3. Chẩn đoán code BRAVO hiện tại

BRAVO đã cài `pydantic-ai-slim`, nhưng chưa dùng Pydantic AI làm reasoning runtime. Trong `app/agent/loop.py`, Pydantic AI chỉ xác thực JSON quyết định được tạo bởi `router.chat`; control flow, prompt assembly và answer composition vẫn thuộc loop tự viết.

OpenAI Agents SDK canary hiện cũng chưa phải core thay thế thực sự: adapter mới chạy text-only, chưa sở hữu tools, typed task state, multimodal evidence hay durable approval.

Các nguyên nhân architecture có khả năng làm câu trả lời “vô hồn”:

1. **Một prompt phải làm quá nhiều việc.** System prompt vừa buộc JSON protocol, citation, abstain, tools, safety và style. Các system block tiếp theo lại thêm memory, identity, turn contract, consultant contract và playbook.
2. **Không có artifact lập luận trung gian đủ mạnh.** Workflow hint được chèn vào context, nhưng core không bắt buộc tạo `TaskBrief`, prerequisite plan, evidence claims và answer outline trước khi tổng hợp.
3. **Routing còn heuristic.** `match_workflow()` đếm substring trigger; nó không tạo typed confidence/evidence cho route và dễ bỏ lỡ cách diễn đạt mới.
4. **Critic quá hẹp.** Critic hiện chỉ vá hai nhóm lỗi: nhảy thẳng đến báo cáo tài chính và tuyên bố đã thực thi tác vụ rủi ro. Nó chưa kiểm tra completeness, assumptions, conflicting evidence, version scope hay usefulness.
5. **Hai lần sinh có thể làm loãng kết quả.** Với streaming knowledge turn, loop có thể tạo JSON answer rồi lại gọi model compose; lần compose nhận nhiều prompt block nhưng không có một typed plan/claim set làm xương sống.
6. **Domain coverage chưa đủ sâu.** Chỉ ba workflow có nội dung chi tiết; bảy workflow còn là scaffold. Framework mới không tự sinh ra tri thức BRAVO còn thiếu.

Vì vậy, đây không đơn thuần là vấn đề “model yếu”. Model mạnh hơn có thể làm văn phong tốt hơn, nhưng architecture hiện tại không bảo đảm model phải nối nghiệp vụ kế toán, điều kiện trước–sau, thao tác BRAVO, rủi ro và kiểm thử thành một lời tư vấn hoàn chỉnh.

## 4. Vai trò đúng của từng dự án

| Thành phần | Lớp đúng | Giá trị cho BRAVO | Quyết định hiện tại |
|---|---|---|---|
| Pydantic AI | Agent harness / reasoning core | Typed dependencies, outputs, tools, model abstraction, testing/evals, deferred approval | **Chọn cho System C** |
| LangGraph | Stateful orchestration runtime | Graph/checkpoint, interrupt, replay/time travel, durable state | Challenger khi branching/resume thực sự phức tạp |
| Kitaru | Framework-agnostic durable runtime | Record/checkpoint, faithful replay, fork/diff, wait/resume, versioned deployment | Pilot sau core; không production mặc định |
| ZenML | MLOps/AI pipeline outer loop | Batch ingestion/eval, artifacts, lineage, infrastructure abstraction, scheduled pipelines | Hoãn; tùy chọn cho R2/R3 offline |
| Temporal | General durable workflow engine | Long-running business transaction, signals, retry/recovery, idempotent activities | Hoãn tới action workflow phức tạp |
| BRAVO platform | Product/policy/domain layer | Auth, RLS, corpus, schema/KEDB, state, tools, drafts, approval, audit, UI | **Giữ và bọc bằng adapter** |

Kitaru không phải đối thủ của Pydantic AI hay LangGraph. Chính Kitaru phân lớp stack thành model, harness, runtime và platform; Kitaru nằm ở runtime bên dưới harness. ZenML cũng tuyên bố nó orchestrate pipeline/tool hiện có chứ không thay thế agent framework.

## 5. Vì sao chọn Pydantic AI trước LangGraph

### 5.1 Fit với dự án hiện tại

- Backend BRAVO là Python/Pydantic/FastAPI; các domain contract đã là Pydantic model.
- Dependency Pydantic AI đã có, nên prototype không cần kéo cả ecosystem mới.
- Mục tiêu R1 chỉ có ba vertical slice sâu, chưa phải mạng graph lớn.
- BRAVO cần typed domain artifacts hơn là dynamic graph topology.
- Pydantic AI có model/tool/dependency/output contract và deferred tool approval, nhưng BRAVO vẫn giữ authorization thật trong tool gateway.

### 5.2 Không kỳ vọng sai vào framework

Pydantic AI không tự hiểu BRAVO. System C chỉ có cơ hội tốt hơn nếu ép mỗi lượt tạo và tiêu thụ các artifact sau:

```text
TaskBrief
  - mục tiêu thực của người dùng
  - version/module/environment đã biết
  - facts / assumptions / unknowns
  - risk và desired outcome

ConsultationPlan
  - business prerequisites
  - BRAVO operation steps cần evidence
  - schema/issue/tool evidence requests
  - clarification có information gain cao

EvidenceBundle
  - business guidance
  - BRAVO action evidence
  - schema facts
  - KEDB/resolution facts
  - conflicts/gaps/version scope

AnswerDraft
  - analysis
  - ordered implementation/operation steps
  - validation and edge cases
  - assumptions/unknowns
  - action draft or approval request if needed

CriticReport
  - missing prerequisites
  - unsupported exact facts
  - unsafe action claims
  - contradictions
  - practical usefulness gaps
```

### 5.3 Khi nào chuyển sang LangGraph

Chỉ nâng LangGraph thành ứng viên chính nếu prototype Pydantic AI/plain Python gặp ít nhất hai trong các nhu cầu có bằng chứng sau:

- nhiều branch/loop/subgraph khó quan sát bằng code tuyến tính;
- cần interrupt/resume ở nhiều node trong cùng một consultation run;
- cần time-travel/fork state trong online runtime;
- cần concurrency/fan-out có join/reducer;
- logic recovery ở node boundary đang bị tự viết lại đáng kể.

Nếu cần, ưu tiên thử LangGraph Functional API trước explicit graph để giảm rewrite.

## 6. Đánh giá ZenML và Kitaru

### 6.1 ZenML giúp gì

ZenML có giá trị khi BRAVO bước vào outer loop có lịch chạy và nhiều artifact:

- ingestion/re-index corpus theo version;
- build schema snapshot và KEDB candidate batch;
- chạy benchmark A/B/C trên nhiều model/config;
- lưu lineage của dataset, prompt/config, output và metric;
- scheduled regression hoặc deployment pipeline trên hạ tầng khác nhau.

Repo local có các example `agent_comparison`, `agent_outer_loop`, `agentic_hitl_pipeline` và `sandbox_pydantic_ai`. Chúng là pattern tham khảo tốt cho evaluation pipeline và HITL batch pipeline. Tuy nhiên chính example outer-loop ghi rõ là toy example, không phải production template.

Không dùng ZenML trong request path hiện nay vì:

- nó thêm client/server/dashboard/artifact store và khái niệm stack;
- BRAVO đã có FastAPI, Postgres, ARQ/Redis, Docker và eval scripts;
- nó không sửa task understanding hay answer synthesis;
- lợi ích vận hành chưa bù được chi phí cho một solo developer ở R1.

**Gate để thử ZenML:** benchmark/ingestion phải có ít nhất ba pipeline định kỳ, cần lineage/artifact promotion xuyên môi trường, và chi phí tự duy trì bằng ARQ/scripts đã trở thành bottleneck được đo.

### 6.2 Kitaru giúp gì

Kitaru giải đúng một vấn đề rất đáng quan tâm: record mỗi model/tool/decision thành checkpoint, sau đó reproduce baseline rồi fork một biến như model, prompt hoặc tool output để so sánh. Đây có thể là công cụ mạnh cho thí nghiệm “model hay code” của BRAVO.

Kitaru cũng có `wait()` cho human input, resume sau crash, versioned deployments và adapter Pydantic AI. Nhưng cần lưu ý:

- Kitaru là repo riêng, không nằm trong source của clone ZenML;
- phiên bản hiện tại còn `0.x`, cộng đồng nhỏ hơn đáng kể so với ZenML/LangGraph;
- checkpoint chứa prompt/tool/result có rủi ro dữ liệu và cần retention, access control, redaction;
- replay side effect đòi hỏi operation ID/idempotency/deduplication;
- Kitaru không thay auth, authorization, RLS, policy, sandbox hay audit của BRAVO.

**Quyết định:** pilot Kitaru ở chế độ local/offline trên 2–3 benchmark anchors sau khi Pydantic AI System C tồn tại. Không đưa Kitaru vào production request path, không triển khai đồng thời Kitaru và Temporal, và không để replay gọi write tool thật.

## 7. Kiến trúc R1 đề xuất

```text
FastAPI / SSE / current UI
        |
        v
ConsultationRuntime interface
        |
        +-- LegacyRuntimeAdapter       (System A)
        +-- ConsultantRuntimeAdapter   (System B)
        +-- PydanticConsultationCore   (System C)
                   |
                   +-- TaskUnderstanding
                   +-- WorkflowPrerequisitePlanner
                   +-- EvidencePlanner
                   +-- AnswerSynthesizer
                   +-- CompletenessCritic
                   |
                   +-- EvidenceBroker adapter
                   |     +-- current hybrid retrieval
                   |     +-- schema snapshot lookup
                   |     +-- KEDB lookup
                   |
                   +-- ActionGateway adapter
                   |     +-- current RLS/tool registry
                   |     +-- draft/approval boundary
                   |
                   +-- TaskStateRepository adapter
                         +-- current Postgres state/checkpoints
```

Nguyên tắc ownership:

- framework sở hữu model loop và typed artifact generation;
- BRAVO sở hữu identity, permissions, source scope, domain truth, approval và audit;
- model không được tự quyết định authorization;
- framework state không trở thành source of truth nghiệp vụ;
- mọi implementation phải xuất cùng trace contract để benchmark được.

## 8. R1 implementation plan đã thu gọn

### R1-A — Đóng băng baseline

1. Khóa model, temperature, token budget và evidence pack.
2. Chạy System A/B trên 6 anchors trước khi sửa prompt/core.
3. Lưu output, stage trace, latency, token/cost và hard-failure flags.
4. Không dùng BravoGen làm gold answer; chỉ dùng làm behavioral reference.

### R1-B — Xây System C tối thiểu

1. Tạo `ConsultationRuntime` interface và normalized events.
2. Tạo typed contracts: `TaskBrief`, `ConsultationPlan`, `EvidenceRequest`, `EvidenceBundle`, `AnswerDraft`, `CriticReport`, `TaskStateDelta`.
3. Dùng Pydantic AI làm model/tool runtime thật, không chỉ làm JSON parser.
4. Bọc retrieval hiện tại thành `EvidenceBroker`; không rewrite retriever.
5. Bọc tools/drafts thành `ActionGateway`; giữ RLS và approval hiện tại.
6. Chỉ triển khai ba workflow sâu:
   - báo cáo tài chính/khóa sổ;
   - ảnh DocNo/UNC → phương án kỹ thuật + test;
   - troubleshooting/schema/KEDB fail-closed.
7. Synthesis phải dựa trên plan + evidence claims, không nhận raw prompt soup.
8. Critic trả typed findings và chỉ cho phép một bounded revision.

### R1-C — Decision benchmark

1. Chạy A/B/C với cùng model/evidence.
2. Ablation System C:
   - bỏ workflow plan;
   - bỏ critic;
   - oracle evidence so với live retrieval;
   - reset state so với preserve state;
   - model hiện tại so với model mạnh hơn.
3. Blind SME pairwise review và TMS theo `02-R1-DECISION-BENCHMARK-PLAN.md`.
4. Chỉ chọn core dựa trên quality gain và failure trace, không dựa vào độ đẹp của code.

### R1-D — Kitaru micro-pilot, không chặn quyết định core

1. Wrap đúng một System C flow read-only.
2. Checkpoint: task brief, evidence bundle, answer draft, critic report.
3. Chạy observed → reproduced → forked với một biến duy nhất.
4. Cấm external write tools; redact prompt/evidence trước artifact persistence.
5. Đo thời gian tích hợp, fidelity của replay, storage overhead và debugging value.
6. Chỉ giữ Kitaru nếu replay giảm rõ thời gian root-cause/ablation so với eval harness hiện tại.

### R2/R3 — ZenML optional outer loop

Chỉ bắt đầu spike ZenML sau R1 nếu gate ở mục 6.1 đạt. Candidate đầu tiên là một pipeline offline:

```text
load frozen benchmark
  -> run selected cores/configs
  -> deterministic checks
  -> prepare blind SME packet
  -> aggregate quality/cost/latency
  -> publish immutable experiment artifact
```

Không deploy chatbot như ZenML pipeline ở giai đoạn này.

## 9. Acceptance gates

### Chọn Pydantic AI core

- System C tăng mean TMS ít nhất 10% so với B với cùng model/evidence;
- thắng ít nhất 60% blind non-tied comparisons;
- không tăng unsafe hard failures;
- cải thiện phải xuất hiện ở cả accounting và ảnh → technical plan;
- code mới không bypass RLS, approval hoặc audit.

### Chọn LangGraph thay Pydantic AI

- Pydantic implementation bị ít nhất hai failure cluster do orchestration/state, không phải do domain data;
- LangGraph prototype giải được chúng với cùng model/evidence;
- tổng state/trace ownership đơn giản hơn hoặc ít nhất không phức tạp hơn;
- gain chất lượng/khả năng resume bù chi phí dependency và migration.

### Giữ Kitaru

- reproduce control đủ ổn định trên benchmark anchors;
- fork/diff giúp phân lập thay đổi tốt hơn harness hiện tại;
- không lưu dữ liệu vượt policy;
- side-effect boundary chứng minh idempotent/fail-closed;
- chi phí vận hành phù hợp solo dev.

### Dùng ZenML

- outer-loop pipeline định kỳ và artifact lineage đã trở thành nhu cầu thật;
- thay scripts/ARQ đem lại giảm maintenance đo được;
- không kéo ZenML vào online latency path;
- có owner cho server, artifact store, retention và upgrade.

## 10. Việc không làm

- Không rewrite auth/RLS/retrieval/data model/UI chỉ để đổi framework.
- Không port toàn bộ `app/agent/loop.py` sang Pydantic AI ngay một lần.
- Không cài Pydantic Graph nếu plain typed pipeline đủ dùng.
- Không chạy Temporal và Kitaru cùng lúc trong R1.
- Không dùng ZenML để che thiếu benchmark/domain contracts.
- Không thêm multi-agent specialist trước khi single consultation core vượt benchmark.
- Không tự động học/promote câu trả lời BravoGen thành BRAVO truth.
- Không để approval primitive của framework thay thế server-side authorization.

## 11. Nguồn chính

- Deep Research report: `C:\Users\tienph\Downloads\deep-research-report (2).md`
- ZenML local clone: `D:\VsCode\Workspace\zenml`
- ZenML: <https://github.com/zenml-io/zenml>
- Kitaru: <https://github.com/zenml-io/kitaru>
- Pydantic AI durable execution: <https://pydantic.dev/docs/ai/integrations/durable_execution/overview/>
- Pydantic Graph: <https://pydantic.dev/docs/ai/graph/graph/>
- Pydantic AI deferred tools/approval: <https://pydantic.dev/docs/ai/tools-toolsets/deferred-tools/>
- Pydantic Evals: <https://pydantic.dev/docs/ai/evals/evals/>
- LangGraph overview: <https://docs.langchain.com/oss/python/langgraph/overview>
- LangGraph persistence: <https://docs.langchain.com/oss/python/langgraph/persistence>
- LangGraph Functional API: <https://docs.langchain.com/oss/python/langgraph/functional-api>

## 12. Kết luận

Phương án tốt nhất không phải “Pydantic AI hay LangGraph” theo nghĩa chọn một logo, và ZenML/Kitaru không thay đổi câu hỏi đó.

Phương án tốt nhất cho BRAVO hiện nay là **một reasoning core mới, nhỏ, Pydantic-first, nằm sau adapter và dùng lại platform hiện có**. Nó trực tiếp nhắm vào nguyên nhân làm câu trả lời thiếu chiều sâu: không có task brief, prerequisite plan, evidence claim model và completeness critic đủ mạnh. LangGraph chỉ được đưa lên khi topology/durability thật sự là bottleneck. Kitaru có tiềm năng lớn cho replay-based improvement nhưng cần pilot vì độ non trẻ và rủi ro dữ liệu/replay. ZenML là công cụ outer-loop về sau, không phải thuốc chữa chất lượng hội thoại.
