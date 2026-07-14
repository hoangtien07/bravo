# Phase 2 — Context compiler, conversation state và memory governance

**Mục tiêu:** agent duy trì đúng mục tiêu/constraint/correction qua nhiều lượt mà không nhồi toàn bộ
transcript hoặc học nhầm thành tri thức tổ chức.  
**Thời lượng dự kiến:** 15–22 engineering days.  
**Phụ thuộc:** GoalFrame/TaskState schema v1; có thể phát triển storage/compiler song song cuối Phase 1.

## 1. Memory model

### 1.1 Không dùng một “memory store” chung

| Store | Canonical data | Retention | Retrieval | Authority |
|---|---|---|---|---|
| Event log | raw turn/tool/state events | policy-defined | by task/run | immutable audit |
| Task ledger | active GoalFrame/TaskState | task + archive | direct key | reconciler |
| Episodic summary | progress/decisions | task/session | direct + semantic | checkpoint job |
| User preference | explicit stable preference | user-controlled | direct | user/confirmed inference |
| Environment profile | version/module/schema refs | expiry/versioned | tenant/env | owner/tool |
| Org knowledge | approved cards/KEDB | governed | hybrid/index | knowledge owners |

Transcript fact không tự động lên user memory; user memory không tự động lên environment fact; external
output không tự động lên organization knowledge.

### 1.2 Fact contract

```yaml
fact_id: uuid
key: accounting_period
value: "2026-05"
scope: task
source_type: user_assertion
source_ref: message:123
valid_time: {from: null, to: null}
observed_at: "..."
confidence: 1.0
status: active
supersedes: fact:old
conflicts_with: []
expiry: null
sensitivity: internal
```

Không merge silent hai fact xung đột. Planner có thể hỏi hoặc chọn theo source authority/recency rule,
nhưng conflict vẫn hiện trong trace.

## 2. Context compiler contract

Input: `InvocationContext`, active state, plan needs, token/model budget.  
Output: ordered `ContextBundle` + `ContextManifest`.

```yaml
manifest_id: uuid
sections:
  - name: active_task
    source_refs: [task:...]
    tokens: 410
    pinned: true
  - name: relevant_artifacts
    source_refs: [workflow:wf.financial-close.v1]
    tokens: 1200
  - name: evidence
    source_refs: [chunk:..., tool_observation:...]
    tokens: 1800
omitted:
  - source_ref: message:old
    reason: superseded
budget: {max: 8000, used: 5120}
```

### Selection priority

1. system/security/authority;
2. active goal/current node/critical constraints;
3. corrections/conflicts/open discriminator;
4. current plan artifacts;
5. evidence for claims/actions;
6. recent interaction style/raw text;
7. optional related history.

Compiler phải dedupe, mark source boundary, isolate untrusted content và không để tool/external text
đóng vai instruction.

## 3. Compaction strategy

- Compaction theo task milestone/checkpoint, không chỉ theo token threshold.
- Summary schema: goal, decisions, facts, correction, completed/pending nodes, evidence refs, unresolved
  conflicts, promised follow-up.
- Raw event vẫn tồn tại trong TTL/audit scope; summary có source range/hash.
- Sau compaction chạy invariant checks: active goal/period/risk/approval/pending question không mất.
- Khi summary conflict với typed ledger, ledger thắng và warning được trace.
- Tool output lớn chuyển thành observation summary + artifact pointer; raw content không pin.

## 4. Conversation behaviors bắt buộc

- Pronoun/reference resolution dựa active entities/task.
- “Không, ý tôi là…” supersede fact/goal đúng chỗ.
- “Dừng lại” chuyển task sang paused/cancel request theo runtime boundary; không tự chạy tiếp.
- “Tiếp tục” resume từ current node và kiểm tra environment facts còn hiệu lực.
- Goal switch tạo subtask/new task hoặc pause cũ; không trộn state.
- User báo đã thực hiện action phải được ghi `user_assertion`, không giả thành tool-observed fact.
- Agent phải nhắc lại ambiguity chỉ khi ảnh hưởng nhánh/action đáng kể.

## 5. Work packages

| ID | Task | Owner | Estimate | Dependency | Deliverable |
|---|---|---|---:|---|---|
| P2-01 | Chốt memory/fact scope policy | Architect + security + product | 2–3d | P1 schemas | policy |
| P2-02 | Event/task ledger persistence | Backend | 4–6d | P2-01 | repository + migrations |
| P2-03 | Fact reconcile/conflict engine | Backend | 3–5d | P2-02 | deterministic reducer |
| P2-04 | ContextBundle/Manifest schema | AI/backend | 2–3d | P2-01 | contracts |
| P2-05 | Context compiler v1 | AI/backend | 5–7d | P2-03/04 | compiler |
| P2-06 | Structured compaction/checkpoint | AI/backend | 4–6d | P2-02/04 | compactor |
| P2-07 | Resume/goal-switch semantics | Backend | 3–5d | runtime interface | transitions |
| P2-08 | Long conversation eval set | Eval + SME | 3–5d | P0 | memory benchmark |
| P2-09 | Privacy/retention/user controls | Security/backend | 3–5d | P2-01/02 | TTL/delete/export |
| P2-10 | Shadow/canary dashboard | Platform | 2–3d | P2-05/08 | context metrics |

P2-02/03, P2-04/05 và P2-08 có thể song song sau P2-01.

## 6. Evaluation

### Scenario families

- correction: kỳ, phân hệ, loại chứng từ, khách hàng/environment;
- delayed reference: “cái báo cáo lúc nãy” sau 10–20 turns;
- temporal: version cũ vs mới, fact hết hạn;
- conflict: user assertion khác tool observation;
- goal switch/resume;
- compaction boundary;
- adversarial old context: instruction đã supersede;
- permission change giữa turns.

### Metrics

- active constraint recall ≥95% ở 20 turns, ≥90% ở 50 turns;
- correction adoption ≥98% next turn;
- stale fact use ≤1%; U3/U4 stale fact use = 0;
- plan resume accuracy ≥95%;
- summary invariant preservation = 100% critical fields;
- context useful-token ratio và duplicated-token rate;
- task score vs raw full-history baseline;
- p50/p95 token, cost, latency.

## 7. Acceptance/exit gate

- Multi-turn task success +20% relative trên Phase 0 memory subset.
- Không còn test chỉ assert raw text present; tests assert state transition/plan behavior.
- Context bundle nhỏ hơn raw-history median ≥30% mà TMS không giảm.
- Correction/contradiction/goal switch đều có typed event và reproducible reducer.
- User/environment/org memory separation được security/data owner duyệt.
- Delete/TTL không làm hỏng audit requirement; sensitive traces không vào semantic memory.
- Resume sau compaction và service restart qua interface runtime thành công.

## 8. Stop/rollback conditions

- Nếu compaction làm critical invariant loss >0.5%, tắt compaction cho task class đó.
- Nếu semantic memory trả dữ liệu cross-user/tenant, stop rollout ngay và incident review.
- Nếu context compiler giảm token nhưng task score giảm >3 điểm, rollback selector/version.
- Không bật long-term inferred preferences nếu chưa có confirm/delete UX.
- Không dùng model summary làm source of truth cho approval/tool completion.

## 9. Operational ownership

Backend owner chịu reducer/storage; AI owner chịu compiler/compaction; security/data owner chịu scope,
retention và access; product owner chịu UX correction/delete. Mỗi context/memory version phải xuất hiện
trong eval trace để rollback độc lập model version.

