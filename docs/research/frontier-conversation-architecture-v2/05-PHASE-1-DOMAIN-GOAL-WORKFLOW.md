# Phase 1 — Domain goals, workflow cards và plan repair

**Mục tiêu:** agent nhận ra outcome và prerequisite nghiệp vụ trước khi trả thao tác bề mặt.  
**Thời lượng dự kiến:** 15–25 engineering days + 10–15 SME days.  
**Phụ thuộc:** Phase 0 benchmark/gates; không phụ thuộc lựa chọn durable engine.  
**Rollout:** offline → shadow; chưa production-wide.

## 1. Scope

- Contract `GoalFrame`, `TaskState`, `GoalCard`, `WorkflowCard`, `ActionMap`.
- 10 workflow ưu tiên có SME ownership/versioning.
- Turn interpreter, domain planner và plan repair.
- Tiered response policy thay cho global no-context refusal trong canary path.
- Artifact authoring/validation tối thiểu qua YAML + CI.

Không xây graph database, autonomous authoring, write tools hay full UI authoring trong phase này.

## 2. Workflow priority đề xuất

| Priority | Goal/Workflow | Lý do |
|---:|---|---|
| 1 | Financial statements/month-end close | case điển hình cross-module/prerequisite |
| 2 | Purchase invoice → AP/Tax/GL | volume cao, nhiều branch |
| 3 | Sales invoice → AR/Revenue/Tax | đối xứng nhưng khác nghiệp vụ |
| 4 | Cash/bank receipt-payment reconciliation | evidence/action rõ |
| 5 | Inventory close/valuation | dependency và version/config |
| 6 | Fixed asset/depreciation | periodic workflow |
| 7 | Costing and allocation | branch theo mô hình doanh nghiệp |
| 8 | Report discrepancy drill-down | diagnostic + workflow |
| 9 | Layout XML/DataSource change draft | technical + risk boundary |
| 10 | Database/config troubleshooting | KEDB evidence ladder |

Product owner có thể đổi thứ tự, nhưng phải giữ ít nhất 3 cross-module và 2 diagnostic workflows.

## 3. Artifact quality rules

### GoalCard bắt buộc có

- stable `goal_type`, synonyms, user-visible outcome;
- success signals và anti-goal;
- applicable modules/roles;
- candidate workflows;
- ambiguity/discriminator list;
- examples/non-examples;
- owner, status, semantic version, review date.

### WorkflowCard bắt buộc có

- applicability/version/policy scope;
- nodes với objective, precondition, completion/evidence;
- branch conditions và unknown handling;
- required/forbidden-before relations;
- safe advisory vs inspect/draft/execute capability;
- ActionMap references;
- escalation/exception nodes;
- test case IDs và owner.

### Authoring principle

SME không viết prompt. SME mô tả outcome, dependency, discriminator, evidence và exception; engineer
biên dịch thành schema. Text hướng dẫn chi tiết vẫn ở corpus và được link, không copy toàn bộ vào card.

## 4. Contract/version strategy

- JSON Schema/Pydantic là canonical machine contract.
- YAML review-friendly là authoring source trong Git ở phase đầu.
- `id` ổn định; semantic version cho behavior; content hash cho trace.
- Breaking change tạo version mới; active conversation pin workflow version đến khi replan rõ ràng.
- `effective_from/to`, `bravo_version_range`, `supersedes`, `status` bắt buộc khi applicable.
- CI reject cycle, missing node, unreachable node, forbidden/required conflict và unknown reference.

## 5. Planner policy

Planner pipeline:

1. extract `TurnUpdate` có structured output;
2. reconcile fact/correction với state;
3. score goal candidates;
4. bind workflow khi confidence/gate đủ;
5. xác định current nodes từ evidence;
6. hỏi discriminator nếu các nhánh dẫn đến action khác đáng kể;
7. sinh `PlanDecision` và response needs;
8. persist revision/diff.

Planner phải hỗ trợ:

- `provisional_goal` khi chưa đủ;
- `provisional_plan` khi thiếu WorkflowCard;
- `replan_reason`: correction, new evidence, tool observation, exception, user override;
- maximum plan depth và no-progress detector;
- deterministic validation trước khi composer dùng plan.

## 6. Work packages

| ID | Task | Owner | Estimate | Dependency | Deliverable |
|---|---|---|---:|---|---|
| P1-01 | Chốt domain schemas + examples | Architect + SME | 3–4d | P0 | schemas v1 |
| P1-02 | Schema validators/CI | Backend | 2–3d | P1-01 | validation package |
| P1-03 | Author 10 GoalCards | SME + knowledge eng | 3–5d | P1-01 | goal catalog |
| P1-04 | Author workflow 1–3 | SME + knowledge eng | 5–8d | P1-01 | core cards |
| P1-05 | Author workflow 4–10 | SME + knowledge eng | 8–12d | P1-04 pattern | full v1 set |
| P1-06 | Build Turn Interpreter | AI/backend | 3–5d | schema | structured updater |
| P1-07 | Build State Reconciler | Backend | 3–4d | schema | deterministic state transitions |
| P1-08 | Build Domain Planner | AI/backend | 5–8d | P1-03/04/06/07 | plan decision |
| P1-09 | Tiered answer policy | AI/backend | 2–4d | P1-08 | policy/composer adapter |
| P1-10 | Phase 0 integration/eval | Eval | 3–5d | P1-08/09 | ablation report |
| P1-11 | Shadow telemetry/dashboard | Platform | 2–3d | P1-10 | goal/plan traces |

P1-03/04 và P1-06/07 có thể chạy song song sau P1-01. Workflow 4–10 không chặn canary ba workflow.

## 7. Tests

### Contract/unit

- invalid workflow cycles/unreachable nodes bị reject;
- correction tạo `supersedes`, không duplicate active fact;
- unknown discriminator không tự chọn branch;
- completed node không quay lại trừ khi evidence invalidated;
- workflow version được pin và migration explicit.

### Domain

- BCTC: không generate trước required close/reconcile nodes trong fixture.
- AP invoice: phân biệt nhập, duyệt, ghi sổ, mapping, filter/report state.
- Troubleshooting: không đề xuất resolution trước minimum evidence.
- XML/config: advisory tách khỏi draft/execute.

### Robustness

- synonym, typo, short prompt;
- user đổi kỳ/module/mục tiêu;
- contradictory evidence;
- goal switch và resume previous goal;
- no matching WorkflowCard.

## 8. Acceptance/exit gate

So với Phase 0 baseline trên matched set:

- goal identification +15 điểm phần trăm hoặc đạt ≥85%;
- critical prerequisite recall +20% relative, và ≥90% ở 3 workflow core;
- harmful/premature action rate ≤2% core set, 0 unsafe action;
- next-action usefulness +15% relative theo SME;
- clarification count không tăng >20%, information-gain score tăng;
- unsupported exact BRAVO/schema claim không tăng;
- p95 latency tăng ≤25% hoặc có documented value/cost approval;
- ≥80% plan failures có typed reason, không chỉ free text;
- SME sign-off cho 10 cards và owner/review date.

## 9. Stop/rollback conditions

- Nếu manual workflow injection E2 không có lift, dừng planner build và sửa benchmark/hypothesis.
- Nếu planner chọn sai branch >10% dù discriminator có trong context, chưa rollout; xem model/contract.
- Nếu cards biến thành copy tài liệu dài hoặc menu hard-code không version, reject review.
- Canary dùng feature flag; rollback về existing route/composer mà không migration transcript.
- Không xóa global safety gate cho schema/production; chỉ thay refusal behavior theo uncertainty tier.

## 10. Definition of done

Code, schemas, catalog, tests, migration/feature flag, trace, eval report, authoring guide và on-call
owner đều hoàn tất. “Có prompt planner mới” không đủ để đóng phase.

