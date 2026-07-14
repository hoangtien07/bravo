# Phase 3 — Plan-aware retrieval, read tools và response critic

**Mục tiêu:** lấy đúng tri thức/evidence cho từng node nghiệp vụ, dùng fact môi trường khi cần và phát
hiện câu trả lời nhảy bước hoặc khẳng định quá mức.  
**Thời lượng dự kiến:** 18–28 engineering days + 5–8 SME days.  
**Phụ thuộc:** Phase 1 plan contract, Phase 2 ContextManifest; có thể spike index song song.

## 1. Retrieval architecture

### Pass A — Resolve domain plan

Input intent/state → GoalCard/WorkflowCard candidates. Dùng exact taxonomy + lexical/vector hybrid.
Planner chọn theo applicability và environment, không theo similarity score đơn thuần.

### Pass B — Fulfil node needs

Planner phát `RetrievalNeed`:

```yaml
need_id: uuid
plan_node_id: reconcile_subledgers
artifact_types: [business_rule, guide, action_map]
query: "đối chiếu công nợ phải trả với sổ cái trước khóa kỳ"
filters:
  module: [AP, GL]
  bravo_version: "10.x"
evidence_level: U1
required: true
```

Retriever có thể decompose thành subquery, chạy hybrid search, rerank rồi merge/dedupe. Mỗi hit giữ
`need_id`, version, source authority và content hash.

### Read tools

Khi `evidence_level` U3:

- schema snapshot lookup;
- table/field/relation existence;
- configuration/layout metadata read;
- log/search bounded by permission;
- KEDB/issue exact lookup;
- report/form catalog lookup.

Tool phải read-only ở phase này, có timeout/budget/RLS/audit và trả typed observation. “Không thấy”
không đồng nghĩa “không tồn tại” nếu snapshot incomplete; observation phải mang coverage/freshness.

## 2. Artifact ingestion/indexing

- Giữ raw source + normalized chunk + contextual header + metadata.
- Tách artifact type: guide, business rule, GoalCard, WorkflowCard, ActionMap, schema, issue/KEDB,
  policy, template/config.
- Metadata tối thiểu: owner, version/build/environment scope, module, effective time, authority,
  review status, supersedes/deprecated, sensitivity.
- Native typed card không bị chunk như PDF; index field-aware và load canonical object sau retrieval.
- Issue resolution chỉ `verified` khi có owner/evidence/version/condition; transcript similarity là
  candidate, không resolution.

## 3. Query strategy

1. Dùng exact ID/metadata trước semantic khi có version/table/report code.
2. Hybrid lexical/vector cho ngôn ngữ nghiệp vụ/tên viết tắt.
3. Query expansion dùng glossary BRAVO, không tự phát minh synonyms schema.
4. Decompose theo plan dependency; parallel chỉ khi needs độc lập.
5. Rerank theo query + node objective + environment, không theo user text duy nhất.
6. Stop khi required needs đủ; không search loop chỉ vì còn budget.
7. Nếu thiếu, emit typed gap với attempted sources/filters.

## 4. Response critic

Critic nhận GoalFrame, TaskState, plan, ContextManifest, answer draft và tool trace. Rule-first:

- forbidden-before violation;
- missing critical node mention khi answer đề xuất downstream action;
- claim schema/version/issue ID không evidence;
- contradiction active fact;
- unsafe tool/action language;
- no actionable next step;
- clarification không map discriminator.

Model critic chỉ dùng cho semantic coverage/clarity sau deterministic rules. Tối đa một rewrite; nếu
vẫn fail risk gate thì clarify/escalate, không loop.

## 5. GraphRAG decision gate

Không triển khai graph DB ở baseline. Đầu tiên biểu diễn relation trong card/JSONB và materialized
edges nếu cần. Chỉ mở spike khi:

- ≥15% benchmark failures đã được attribution là multi-hop relation retrieval;
- relation không giải được bằng workflow/card query hoặc relational join với SLA chấp nhận được;
- có ontology owner và update strategy;
- tạo được ≥100 relation-heavy queries với ground truth.

Graph spike phải thắng typed/relational baseline ≥10% task success hoặc ≥20% latency/cost ở cùng
quality, và không làm provenance/versioning tệ hơn. Nếu không đạt, đóng spike.

## 6. Work packages

| ID | Task | Owner | Estimate | Dependency | Deliverable |
|---|---|---|---:|---|---|
| P3-01 | RetrievalNeed/Observation schemas | AI/backend | 2–3d | P1/P2 | contracts |
| P3-02 | Artifact metadata migration | Data/backend | 4–7d | source audit | metadata v2 |
| P3-03 | Two-pass retriever | AI/search | 5–8d | P3-01/02 | retrieval pipeline |
| P3-04 | Contextual chunk + reindex experiment | Search | 3–5d | P3-02 | ablation |
| P3-05 | Schema/catalog read tools | Backend/DBA | 5–8d | policy/RLS | tools |
| P3-06 | KEDB retrieval + verification state | Support/backend | 4–7d | schema/card | KEDB search |
| P3-07 | Plan-node reranker | AI/search | 3–5d | P3-03 | rerank model/prompt |
| P3-08 | Rule/model critic | AI/backend | 4–6d | P1/P2 | critic |
| P3-09 | Component eval diagnostics | Eval | 4–6d | P3-03/08 | dashboard/report |
| P3-10 | Shadow/canary | Platform | 3–5d | gates | rollout |

P3-02/04, P3-05/06 và P3-08 có thể song song sau contract review.

## 7. Evaluation matrix

| Layer | Metric |
|---|---|
| Planner | need coverage, correct artifact type, unnecessary need rate |
| Retrieval | context recall/precision per need, version filter correctness |
| Tool | observation accuracy, coverage/freshness, authority violations |
| Composer | claim support, prerequisite use, next action |
| Critic | true/false positive, harmful answer prevented, rewrite success |
| End-to-end | TMS, latency, cost, tool count, external/human escalation |

Ablations bắt buộc: one-pass vs two-pass; raw chunk vs contextual chunk; no-rerank vs rerank; no-critic
vs critic; cards-only vs cards+docs; model-only schema claim vs read tool.

## 8. Acceptance/exit gate

- Required-need context recall ≥90%, precision ≥70% trên verified subset.
- Version/environment filter violation = 0 ở schema/KEDB critical set.
- U3 unsupported specificity giảm ≥80% và absolute ≤1%.
- End-to-end TMS +15% relative so với Phase 2 trên retrieval-dependent set.
- Critic bắt ≥90% harmful-premature seeded cases, false-positive ≤10%.
- p95 latency trong product budget; default tool calls ≤3/turn trừ diagnostic workflow.
- Retrieval loop có hard budget/no-progress stop và typed gap.
- Read tools qua RLS/audit/control plane; không có write path ẩn.

## 9. Stop/rollback conditions

- Disable tool nếu coverage/freshness không được hiển thị hoặc có cross-tenant result.
- Rollback reranker nếu task recall giảm >3 điểm dù MRR tăng.
- Tắt model critic nếu rewrite làm specificity/hallucination tăng hoặc p95 vượt budget mà không có lift.
- Không ship GraphRAG từ demo qualitative.
- Không biến “similar issue” thành verified resolution khi thiếu validation state.
- Feature flags độc lập cho two-pass, tools, reranker và critic để rollback theo component.

## 10. Definition of done

Ngoài code/test, phải có index data sheet, owner/freshness policy, retrieval ablation report, threat
test cho tool output injection, dashboard theo need/node và runbook khi schema/KEDB source stale.

