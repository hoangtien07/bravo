# Phase R1 — Decision benchmark and root-cause isolation

Status: `PREPARATION — documentation baseline verified; execute after operational containment proof, baseline freeze, and fixture/SME gate`

The earlier `READY TO EXECUTE` marker is superseded. As of 2026-07-24, the intended containment
increment is committed on a clean baseline, but its runtime/production proofs and the immutable
A/B answer capture remain open. The benchmark is separate from the Engineering Workbench gate;
capture an immutable A/B baseline before implementing Conversation Core v2.

## 1. Objective

Determine, with blind task-quality evidence, whether BRAVO should:

1. repair the current Consultant/legacy path;
2. replace only the reasoning core using a strangler architecture; or
3. create a fully separate clean project.

R1 must also answer the immediate root-cause question: is conversational quality limited mainly by the model, retrieval/context, workflow representation, critic/answer synthesis, or coupling in the current core?

## 2. Freeze during R1

Until the decision report is signed:

- no new autonomous jobs;
- no live BravoGen fallback/token rotation;
- no GraphRAG/graph-database commitment;
- no mass porting of legacy features;
- no additional workflow scaffolds unless required by the frozen benchmark;
- only bug fixes needed to run the benchmark reproducibly.

## 3. Decision set

Create 24 trajectories, four per family:

| Family | Required coverage |
|---|---|
| Accounting/report readiness | financial statements, trial balance, closing prerequisites, discrepancy |
| Image + implementation analysis | the DocNo/UNC screenshot case, Layout/DataSource change, concurrency, test plan |
| Troubleshooting | ambiguous UI, database/log error, integration failure, ranked diagnostics |
| Schema/version grounding | table/field existence, relationship, unknown version, conflicting snapshots |
| Support intelligence | similar symptom/different cause, verified resolution, supersession, empty KEDB |
| Multi-turn/risk | corrections, changed platform/version, stop/resume, draft → approval boundary |

Every trajectory must include:

- `case_id`, family and risk class;
- prompt and supplied attachment/context;
- version/module/environment facts;
- expected outcome, not expected prose;
- must-include reasoning/prerequisites;
- acceptable alternatives;
- must-not-claim and hard-fail conditions;
- clarification trigger and minimum required facts;
- approved source/evidence bundle or explicit `evidence_missing` fixture;
- expected workflow-state mutations for later turns.

At least eight cases must come from redacted real work patterns. If real cases are not yet approved, R1 may start with synthetic fixtures but cannot issue the final architecture decision.

## 4. Systems under test

| ID | System | Purpose |
|---|---|---|
| A | Legacy chat path | Current production-style baseline |
| B | Current Consultant path | Measures value of the recently added typed workflow/critic layer |
| C | Clean strangler reasoning slice | Tests a fresh core without rewriting trusted platform services |
| D | BravoGen native mode | External behavioral reference, never the gold answer |

System C reuses A/B auth, RLS, retrieval services, read tools and approval boundaries through adapters. It owns only:

```text
TaskBrief
  -> workflow/prerequisite planner
  -> retrieval/tool request plan
  -> evidence-aware synthesis
  -> completeness/assumption critic
  -> natural answer
  -> typed multi-turn state update
```

The orchestration framework must remain behind an interface. One framework implementation is enough for R1; framework comparison is out of scope.

### System C implementation profile

System C will use Pydantic AI as the first real reasoning runtime, while retaining the current BRAVO Postgres state/checkpoint, RLS, retrieval, tool, draft, approval and audit services through adapters. Pydantic Graph, Temporal, Kitaru, ZenML and a second observability platform are excluded from the primary R1 request path unless a measured failure requires them. LangGraph remains a conditional challenger, not a parallel build. The rationale and adoption gates are recorded in `03-OSS-CORE-DECISION-PYDANTIC-LANGGRAPH-ZENML-KITARU.md`.

## 5. Model-versus-code isolation matrix

### Primary comparison

Run A, B and C with:

- the same cloud model/version;
- the same temperature and token budget;
- the same approved evidence bundle;
- identical prompt/attachment inputs;
- no hidden external fallback.

This comparison answers whether the pipeline/core improves quality independent of model choice.

### Controlled ablations

Run the following on the eight highest-value cases:

1. C without workflow/prerequisite cards;
2. C without completeness critic;
3. C with oracle evidence bundle versus live retrieval;
4. B and C with one stronger frontier model;
5. C with task state reset versus preserved multi-turn state.

Interpretation:

| Result | Likely cause |
|---|---|
| Stronger model lifts all systems similarly | model ceiling dominates |
| C beats B with the same model/evidence | core representation/synthesis problem |
| Oracle evidence lifts B/C strongly | ingestion/retrieval/metadata problem |
| Removing workflow cards loses prerequisites | workflow representation is causal |
| Removing critic reintroduces skipped steps/unsafe certainty | critic is causal |
| All variants fail the same cases | benchmark knowledge/evidence gap or model limitation |

## 6. Evaluation rubric

Score each answer from 1–5; calculate a weighted Task Merit Score (TMS):

| Dimension | Weight |
|---|---:|
| Business/technical workflow completeness | 30% |
| Factual and evidence-grounded correctness | 20% |
| Practical task usefulness | 15% |
| Clarification and assumption control | 15% |
| Natural conversational quality | 10% |
| Safety and approval discipline | 10% |

Hard failures override the weighted score:

- claims an exact table/field/version fact without a matching snapshot;
- claims a resolution is verified without a governed KEDB/issue record;
- skips a mandatory accounting prerequisite and instructs the user to trust the report;
- invents a BRAVO menu/control/procedure as fact;
- claims a script/config/database change was executed when it was not;
- produces or executes a risky mutation outside draft/approval policy;
- ignores an explicit correction, pause or scope change.

Record both absolute TMS and blind pairwise preference. Reviewers must not see system/model identifiers.

## 7. SME protocol

1. Appoint two reviewers covering accounting/ERP and technical implementation/support. A third adjudicator handles disagreements on hard failures.
2. Calibrate on six anchor cases.
3. Require weighted kappa ≥ 0.60 before scoring the full set.
4. Randomize answer order and strip model/system metadata.
5. Reviewers score must-include/must-not items before subjective naturalness.
6. Store scores, rationale and evidence pointers; do not promote external answers into knowledge.

## 8. Trace contract

For A/B/C, retain a privacy-minimized trace per run:

- normalized input/attachment manifest;
- selected task/workflow and confidence;
- known facts, unknowns and corrections;
- retrieval queries, metadata filters and evidence IDs;
- plan/prerequisite nodes;
- critic findings and changes made;
- final answer hash, latency, token use and cost;
- tool/approval events;
- failure stage: perception, routing, retrieval, planning, synthesis, critic or state.

This is required to decide architecture. A score without a causal trace cannot distinguish a model win from a pipeline win.

## 9. Execution phases

### R1.0 — Data contract repair (1–2 working days)

Deliverables:

- `app/eval/decision_benchmark.yaml` with 24 trajectories;
- immutable attachment/source fixtures;
- schema validation for must-include/must-not/hard-fail fields;
- explicit capture fidelity and run manifest.

Exit gate: 24 cases validate; no customer data is present; at least eight real-pattern cases are owner-approved or marked as blocking the final decision.

### R1.1 — Baseline capture (2 working days)

Run A and B with the locked primary model. Capture answers and traces without changing prompts after seeing output.

Exit gate: ≥95% runnable cases; every failure has a stage label; current Consultant gets a real TMS baseline instead of a structural pass.

### R1.2 — Clean strangler slice (3–5 working days)

Implement only three deep workflow packs:

1. financial close/report readiness;
2. screenshot-to-technical implementation plan (DocNo/UNC case);
3. troubleshooting/schema/KEDB clarification and fail-closed grounding.

These are benchmark packs selected to isolate reasoning failures. They do not define the commercial
product or select Financial Close as the objective of `Công việc AI`. The first Accounting Work
capability is Reconciliation & Exception Investigator under ADR-0032; add matched anchors for one
bounded reconciliation subtype without deleting the existing close coverage. Paid-pilot and
production decisions remain governed by ADR-0033 and
`10-FRONTIER-BRAVO-ACCOUNTING-AGENT-PLAN.md`. Voucher Evidence Review and Period Close Readiness
receive bounded functional anchors only after the Bank deterministic gate passes.

All other cases may route through a generic evidence-aware fallback. Do not port unrelated legacy UI or action workflows.

Exit gate: C runs through the existing API adapter, uses existing RLS/read boundaries and exposes stage-level traces.

### R1.3 — Bake-off and ablations (2–3 working days)

- Run frozen A/B/C outputs under matched conditions.
- Capture D/BravoGen only for the same permitted synthetic cases and correct native mode.
- Run eight-case ablation matrix.
- Produce blind review packets.

Exit gate: no missing output is silently replaced; quota/error is availability evidence; all answer variants are anonymized.

### R1.4 — SME review and root-cause report (2–3 working days plus reviewer availability)

Deliverables:

- per-case scores and pairwise preferences;
- inter-reviewer agreement;
- hard-failure list;
- stage-level failure clusters;
- model-versus-code attribution;
- cost/latency comparison.

### R1.5 — Architecture decision (1 working day)

Produce `03-ARCHITECTURE-DECISION.md` with one of the following outcomes.

## 10. Decision gates

### Continue current Consultant core

Choose this when:

- B is within 5% of C on mean TMS and pairwise preference;
- B has no additional hard-failure cluster;
- fixes are localized to evidence/workflow cards or answer synthesis;
- C does not materially reduce trace complexity or change lead time.

### Adopt strangler reasoning core

Choose this when:

- C improves TMS by at least 10% over B with the same model/evidence;
- C wins at least 60% of non-tied blind comparisons;
- C has zero unsafe hard failures and fewer unsupported schema/KEDB claims;
- improvement persists on accounting and image-to-implementation cases;
- the core can remain isolated behind adapters without porting most legacy code.

### Approve full clean project

Choose this only when all strangler conditions pass and evidence shows existing platform coupling blocks the new core in at least three independent failure clusters (for example state ownership, tool policy and persistence). Framework preference or code cleanliness alone is not sufficient.

### Stop/rework

Do not proceed to R2/R3 when:

- reviewer agreement is below 0.60;
- gains come only from a stronger model;
- oracle evidence helps but live retrieval remains poor;
- prototype improves style but not workflow completeness/correctness;
- any system has unresolved unsafe hard failures;
- the real-pattern data gate is not met.

## 11. Production gate remains separate

Even if C wins R1, production-default rollout still requires the five existing release gates:

- SME quality calibration;
- workflow ownership and version mapping;
- verified schema and KEDB coverage;
- memory retention/data boundary;
- canary SLO and on-call ownership.

R1 selects a core. It does not authorize production, external expert fallback or autonomous knowledge promotion.

## 12. Recommended immediate sequence

1. Freeze new Consultant features.
2. Promote the DocNo screenshot case, financial-report prerequisite case and schema-unknown case as the first three R1 anchors.
3. Recruit/assign the two SME reviewers and six calibration anchors.
4. Author the remaining 21 case contracts.
5. Capture A/B baselines before modifying the reasoning core.
6. Build C only after the baseline is immutable.

## 13. Workspace-council amendment

The repository/council round clarifies that the R1 benchmark is the **Conversation Intelligence** decision. It must not be blended with the separate Engineering Workbench quality gate:

- the six named anchors are a fast development suite only;
- the 24 trajectories must preserve and cover all 66 existing benchmark turns for the final comparison;
- System C owns conversational task understanding, prerequisite reasoning, evidence planning, synthesis, critic and scoped state update;
- the UNC/DocNo conversation remains a benchmark anchor, but a passing generated patch/build is not required to score its conversational answer;
- conversational scoring and “better than BravoGen” gates are defined in `07-CONVERSATION-INTELLIGENCE-BRAVOGEN-BENCHMARK.md`;
- the separate `bravo.technical-implementation-pack` workbench uses canonical extraction, validator/build/test, negative blocking and false-ready metrics from `05-BRAVO-ENGINEERING-WORKBENCH-CONTRACT.md`;
- results from the two tracks are reported side by side and never collapsed into one quality score.

Implementation must follow the ownership and complexity boundaries in `04-WORKSPACE-REPO-COUNCIL-DECISION.md`. The staged/two-track sequence is in `06-RESEARCH-AND-IMPLEMENTATION-ROUNDS.md`.
