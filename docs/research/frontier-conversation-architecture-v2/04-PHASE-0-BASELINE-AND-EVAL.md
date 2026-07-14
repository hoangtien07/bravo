# Phase 0 — Baseline, task benchmark và observability

**Mục tiêu:** chứng minh failure hiện tại bằng task-level evidence và tạo một benchmark không bị tối
ưu theo cảm giác.  
**Thời lượng dự kiến:** 10–15 engineering days + 4–6 SME days; cần hiệu chỉnh theo năng lực đội.  
**Production change:** không đổi behavior diện rộng; chỉ thêm trace có feature flag nếu cần.  
**Phụ thuộc:** owner, SME và dữ liệu hội thoại đã khử nhạy cảm.

## 1. Scope

### In scope

- 30–50 scenario, tối thiểu 100 trajectory variants và 200+ turns.
- Single-turn, multi-turn, correction, missing-info, simulated user action và risky-action cases.
- Taxonomy lỗi theo [current-state analysis](01-CURRENT-STATE-AND-FAILURE-ANALYSIS.md).
- Baseline current chatbot, ít nhất một strong-model reference và BravoGen comparator subset.
- Trace đủ để tách planner/retrieval/context/state/composer/tool failure.

### Out of scope

- Thay toàn bộ prompt/model/runtime.
- Chứng minh BravoGen dùng công nghệ nội bộ nào.
- Đưa dữ liệu khách hàng thật ra external service.
- Tự động chấm đúng nghiệp vụ chỉ bằng LLM judge.

## 2. Benchmark design

### 2.1 Nhóm scenario tối thiểu

| Nhóm | Scenario gốc | Variants tối thiểu |
|---|---:|---:|
| BCTC/month-end close | 5 | 15 |
| Hóa đơn đầu vào/AP/thuế | 5 | 15 |
| Bán hàng/AR/thu tiền | 3 | 9 |
| Tiền/tồn kho/tài sản/giá thành | 6 | 18 |
| Hướng dẫn menu/report nhiều bước | 4 | 12 |
| XML/Layout/DataSource/config | 4 | 12 |
| Schema/version grounding | 4 | 12 |
| Troubleshooting/KEDB | 5 | 15 |
| Risky draft/approval/execute | 3 | 9 |
| Memory/correction/stop-resume | 5 | 15 |

Mỗi scenario có thể thuộc nhiều nhóm. Không cố đạt số bằng cách paraphrase đơn thuần; variant phải
thay fact/branch/state.

### 2.2 Trajectory contract

```yaml
case_id: conv.financial.close.001
goal:
  type: financial_statements_ready
  success_milestones: [scope_known, posting_checked, reconciliation_checked, report_validated]
environment:
  bravo_version: unknown
  schema_fixture: null
initial_state: {}
turns:
  - user: "Làm sao để lên báo cáo tài chính?"
    expected:
      must_recognize: [not_just_open_report, period_and_data_readiness]
      acceptable_next_actions: [ask_period, explain_close_workflow]
      forbidden: [assert_exact_menu_without_version, claim_report_is_ready]
  - simulator_action:
      message: "Tôi đã hạch toán hết, nhưng chưa kết chuyển. Là tháng 5 chứ không phải tháng 6."
      state_updates: {period: "2026-05", posting_complete: true, closing_complete: false}
    expected:
      must_repair: [period, current_node]
rubric:
  critical_prerequisites: [...]
  harmful_actions: [...]
  expert_notes: "..."
```

Ground truth là milestone/constraint/acceptable action set, không phải một “golden answer” duy nhất.

### 2.3 Scoring

Score chính trên thang 0–100:

- Goal identification: 15.
- Critical prerequisite coverage: 20.
- Current-state/branch correctness: 15.
- Next-action usefulness: 15.
- Multi-turn correction/coordination: 15.
- Product/environment specificity discipline: 10.
- Communication clarity/efficiency: 5.
- Safety/authority: 5, nhưng unsafe là hard fail.

Report thêm metric riêng; không che hard fail bằng điểm trung bình. `task_success` cần toàn bộ critical
milestone đạt và không có harmful action.

### 2.4 Judge design

- Deterministic assertions cho state, tool, citation presence, forbidden claim và milestone.
- SME chấm blind ít nhất 20% tập và toàn bộ disagreement/hard case.
- LLM judge chỉ pre-label/triage; calibrate với SME, lưu model/prompt/version.
- Hai SME chấm overlap ít nhất 15%; báo Cohen's kappa/percent agreement theo rubric.
- BravoGen và reference model không được dùng làm ground truth.

## 3. Work packages

| ID | Task | Owner | Estimate | Dependency | Deliverable |
|---|---|---|---:|---|---|
| P0-01 | Chốt taxonomy và rubric | Eval lead + SME | 1–2d | none | rubric v1 |
| P0-02 | Chọn 10 workflow ưu tiên | Product + SME | 1d | P0-01 | scope register |
| P0-03 | Thu thập/khử nhạy cảm conversation | Data owner | 2–4d | approval | scenario inputs |
| P0-04 | Author scenario/trajectory | SME + eval eng | 5–8d | P0-02/03 | YAML benchmark |
| P0-05 | Xây mutable simulator fixtures | Eval eng | 3–5d | P0-04 schema | simulator |
| P0-06 | Mở rộng trace manifest | Backend | 2–3d | trace review | typed trace |
| P0-07 | Baseline current system | Eval eng | 1–2d | P0-04/06 | baseline report |
| P0-08 | Comparator run có kiểm soát | Eval eng | 1–2d | P0-04 | comparison report |
| P0-09 | Error attribution workshop | Team + SME | 1d | P0-07/08 | top-20 failures |
| P0-10 | Freeze acceptance thresholds | Product/tech | 0.5d | P0-09 | gate config |

P0-03, P0-05 và P0-06 có thể song song sau khi trajectory schema draft được chốt.

## 4. Trace contract cần thêm

Mỗi run/turn phải ghi:

- model/prompt/runtime/retrieval config version;
- input message IDs và active profile;
- interpreted intent/goal candidate (nếu baseline chưa có, ghi router output);
- query plan, filters, retrieved IDs/scores/source type;
- exact context manifest theo section/token count;
- tool call/observation với redaction marker;
- final output, latency, tokens/cost;
- evaluator claims/milestones/failure attribution.

PII/customer content không ghi vào telemetry tổng hợp; raw trace dùng access-controlled store và TTL.

## 5. Baseline experiments

| Experiment | A | B | Câu hỏi |
|---|---|---|---|
| E0 | current production config | current + larger top-k | retrieval volume có giải quyết không? |
| E1 | current raw history | manual typed state injected | state có phải bottleneck? |
| E2 | current source routing | manual workflow outline injected | workflow artifact có lift không? |
| E3 | current abstain policy | best-effort tiered prompt offline | refusal/helpfulness trade-off? |
| E4 | current model | strong reference model same context | model hay architecture bottleneck? |

E1–E3 là offline probe, không phải kiến trúc production. Nếu manual workflow injection không tăng
prerequisite recall, phải xem lại giả thuyết trước Phase 1.

## 6. Acceptance và exit gate

Phase 0 chỉ hoàn tất khi:

- có ≥30 scenario thực chất, ≥100 variants, đủ 10 nhóm;
- ≥80% cases có rubric được SME duyệt; 100% critical/risky cases được duyệt;
- inter-rater agreement ≥0.75 hoặc disagreement taxonomy được giải quyết;
- baseline chạy lặp lại sai số score tổng ≤3 điểm;
- failure attribution coverage ≥90%; không còn nhãn “bad answer” chung chung;
- có top-20 failure list, severity/frequency và mapping sang Phase 1–3;
- token/cost/latency baseline được lưu;
- không có dữ liệu khách hàng chưa cấp quyền trong external comparator.

## 7. Stop/rollback conditions

- Dừng comparator nếu token/ToS/authorization không rõ hoặc có dữ liệu ngoài scope.
- Dừng LLM-as-judge auto-score nếu agreement với SME <0.65; chuyển sang pre-label only.
- Rollback trace production nếu làm tăng p95 latency >5% hoặc log chứa unredacted sensitive data.
- Không bắt đầu Phase 1 nếu benchmark chỉ gồm synthetic/paraphrase và chưa có SME owner.

## 8. Outputs bắt buộc

1. `conversation_task_benchmark.yaml/jsonl` và schema.
2. Simulator fixtures + test runner.
3. Rubric/judge prompt versioned.
4. Baseline report theo failure class, không chỉ mean score.
5. Decision memo xác nhận/bác bỏ H1–H6 liên quan.
6. Top workflows và acceptance thresholds cho Phase 1.

