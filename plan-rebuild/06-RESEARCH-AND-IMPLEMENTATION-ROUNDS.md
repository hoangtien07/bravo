# Research and implementation rounds

Status: `PROPOSED EXECUTION SEQUENCE`

## 1. Why the work is split

Repository selection, engineering artifact correctness, chatbot quality, knowledge ingestion, and production execution are different decisions. Combining them into one “agent platform” phase would make root-cause attribution impossible and encourage overengineering.

After the shared foundation is mapped, work splits into two parallel tracks:

- **Track C — Conversation Intelligence:** judged against current chat and BravoGen on conversational task merit.
- **Track E — Engineering Workbench:** judged by canonical, static, build, test and handover evidence.

The tracks share platform adapters but have independent success/failure decisions.

The work is split into research/decision rounds with explicit exit gates. A later round is not authorized merely because an earlier document mentions it.

## 2. Round R-A — Ecosystem and architecture boundary

Purpose: decide what to reuse, learn, defer, and reject before adding code.

Deliverables:

- workspace repository capability matrix;
- council decision and dissent;
- platform/domain/runtime ownership map;
- overengineering budget;
- initial Conversation Core and Engineering Workbench contracts.

Exit gate:

- the strangler boundary is accepted;
- no duplicate auth/state/approval system is planned;
- the first conversation anchors and engineering fixture are named;
- every proposed new framework has a measured trigger.

Result: documented in `04-WORKSPACE-REPO-COUNCIL-DECISION.md`, `05-BRAVO-ENGINEERING-WORKBENCH-CONTRACT.md` and `07-CONVERSATION-INTELLIGENCE-BRAVOGEN-BENCHMARK.md`.

## 3. Round R-B — Contract-to-code feasibility spike

Purpose: prove that both track contracts can reuse the current platform without inheriting the legacy loop or sharing a false quality verdict.

Timebox: 2–3 working days.

Work:

1. map current `EnvironmentProfile`, `TaskState`, retrieval needs, artifacts, drafts, approvals and agent runs to Contract v0.1;
2. identify schema changes versus adapter-only mappings;
3. create pure-Python shared contracts plus separate fake Conversation and Workbench ports;
4. encode the state-transition table and invariant tests;
5. model the conversation anchors separately from the UNC engineering golden/negative cases;
6. prove no import from FastAPI, SQLAlchemy, Pydantic AI or LangGraph is required by the domain package.

Exit gate:

- conversation and engineering fixtures validate independently;
- state transitions fail closed;
- the current platform can be adapted without a second source of truth;
- no production mutation is possible.

Stop/rework if this requires duplicating tenant state, artifact ownership or approval semantics.

## 4. Round R-C — Immutable baseline and evidence oracle

Purpose: isolate whether current failure comes from model, retrieval, workflow representation, or synthesis.

Timebox: 2–3 working days plus fixture preparation.

Work:

- freeze 6 anchor trajectories as a fast development suite;
- retain the full 24-trajectory/66-turn set for the decision run;
- capture Legacy A, Consultant B and BravoGen D outputs unchanged;
- create a fixed evidence bundle for each anchor;
- score current outputs with the existing TMS rubric;
- label failure stage and hard failures;
- lock model/version/temperature/token budget for A/B/C.

Recommended six development anchors:

1. financial-report readiness and accounting prerequisites;
2. UNC/DocNo screenshot → implementation analysis;
3. Layout XML draft with an unverified attribute trap;
4. schema/version unknown → conditional guidance and clarification;
5. same symptom, different version/root cause in support/KEDB;
6. multi-turn correction, pause and resume.

Exit gate:

- every anchor has expected outcomes, must-include/must-not and evidence bundle;
- output order is blindable;
- baseline traces show enough stage information for causal analysis;
- the six anchors are explicitly labelled smoke/development, not superiority evidence.

## 5. Track C / Round C1 — Conversation Core v2

Purpose: build the smallest clean conversational reasoning slice behind existing platform adapters.

Timebox: 3–5 working days.

Allowed implementation:

- Pydantic AI adapter as the first runtime;
- typed TaskBrief/EvidenceBundle/prerequisite plan/conversation result;
- prerequisite planner and assumption/completeness critic;
- current BRAVO retrieval/read-tool/task-state adapters;
- trace extensions needed by the frozen evaluator.

Not allowed:

- feature parity with the legacy loop;
- Temporal, graph database, multi-agent, external expert fallback;
- a second UI or identity store;
- online self-learning;
- write execution.

Exit gate:

- System C runs all six anchors through the existing API boundary;
- the same evidence oracle can feed B and C;
- framework objects do not leak into domain state;
- stage-level traces are complete.

## 6. Track E / Round E1 — Engineering Workbench

Purpose: prove that technical requirements can produce checked engineering outcomes rather than an unverified AI answer.

Timebox: 3–5 working days.

Build the `bravo.technical-implementation-pack` workbench capability for two initial cases:

- UNC/DocNo positive golden case;
- missing version/schema negative case.

Outputs:

- typed requirement/domain case;
- assumptions and unresolved facts;
- implementation plan;
- SQL/Layout/config drafts only where supported;
- test matrix including concurrency and edge cases;
- validation report and artifact manifest;
- review/handover status.

Optional IDE/web scope is adapter-only:

- headless disposable workspace and allowlisted commands first;
- VS Code extension later for diff, Tasks and Test Explorer presentation;
- Playwright only for a stable web target and stored test/trace artifacts;
- no IDE, browser session or AI coding extension owns job state or validation truth.

Exit gate:

- negative case cannot become ready/approved;
- all artifacts are owner-scoped and hash-pinned;
- validator results cannot be overwritten by the model;
- repeated deterministic stages normalize identically;
- user correction invalidates only affected outputs.

## 7. Round R-F — Independent evaluations and decisions

Purpose: make two decisions with evidence, not one blended score.

Timebox: 3–5 working days plus SME availability.

Conversation decision:

- A vs B vs C with the same model and evidence;
- C with and without workflow prerequisites/critic;
- live retrieval versus oracle evidence;
- C versus BravoGen on the same permitted 24 trajectories/66 turns;
- a stronger-model ablation on the highest-value subset to separate model ceiling from code effects.

Engineering decision:

- canonical extraction against SME-labelled fixtures;
- static/build/test results against known expected outcomes;
- positive, missing-evidence, contradiction, unsafe-command and correction cases;
- headless reproducibility, manifest completeness and false-ready rate;
- IDE/browser adapter value measured separately from core correctness.

Decision:

- adopt Conversation Core v2 when its independent benchmark gates pass;
- adopt the Engineering Workbench capability when its deterministic engineering gates pass;
- retain B when C is within noise and does not reduce complexity;
- approve a full clean product only if platform coupling causes at least three independent, demonstrated failure clusters;
- rework retrieval/knowledge when oracle evidence, rather than core changes, causes the gain.

One track may pass while the other fails. No architecture is selected on answer style alone, and no engineering pipeline is promoted because its chat summary sounds convincing.

## 8. Round R-G — Expand knowledge and skills

Only after R-F.

Conversation knowledge/capabilities and engineering pipelines are expanded separately, one at a time:

1. financial close/report readiness assistant;
2. troubleshooting and verified support-resolution pack;
3. Layout XML/configuration patch pack;
4. import preparation and validation pack;
5. user-guide multi-step procedure assistant;
6. ISMS policy assistant after corpus governance exists.

For conversational capability, extend prerequisite/evidence models and rerun the chat benchmark. For engineering capability, repeat: technical outcome → canonical model → responsibility partition → isolated workspace → validators/build/tests → golden/negative/correction suite → developer review.

Do not introduce a generic marketplace or cross-capability planning layer until independently built capabilities prove the shared abstractions. Do not abstract domain logic merely because two cases look similar; wait for a stable third occurrence.

## 9. Round R-H — Optional infrastructure triggers

These are trigger-based, not scheduled commitments.

| Component | Introduce only when |
|---|---|
| LangGraph | independent branching/rejoin, interrupts, or framework-native replay measurably simplify at least two skills and beat the Pydantic AI adapter |
| Temporal or comparable workflow engine | jobs wait hours/days, must survive deployments, retry external integrations, or coordinate several approvals beyond current checkpoint reliability |
| ZenML | offline ingestion/eval/promotion pipelines need reproducible multi-stage artifact lineage across environments |
| Kitaru | isolated replay experiment proves a concrete debugging/recovery gain without becoming a second state authority |
| Graphiti/graph database | temporal/version/supersession queries beat metadata + relational KEDB on a frozen benchmark enough to justify operations |
| Multi-agent | independently testable specialist roles beat a single agent with tools and deterministic gates on quality/cost/latency |

The only sensible Graphiti pilot, after System C works, is the pair: same symptom with different BRAVO version/root cause; and resolution superseded/deprecated by version or environment. Failure to beat the relational KEDB closes the pilot.

## 10. Candidate sequence after the first decisions

Conversation track:

1. **Reconciliation & Exception Investigator** is the owner-selected deep V2 demonstrator under
   ADR-0032. It validates one bounded reconciliation subtype with an identified user outcome,
   source/scope contract, deterministic engine, liability model and success metric. ADR-0033
   selects the target user/buyer hypothesis and on-prem pilot architecture; WTP and readiness
   remain evidence gates rather than open design choices.
2. **Voucher Evidence & Accounting Review** and **Period Close Readiness** are accepted by
   ADR-0033 as functional/bounded cases implemented sequentially after Bank Reconciliation. They
   reuse the same core and do not authorize BRAVO voucher/close engine duplication.
3. **Financial Close/report readiness** remains benchmark coverage and the Period Close case
   template; it is not evidence that Close is the product objective or most important business
   gap.
4. **Schema/KEDB Troubleshooting** validates version-aware support reasoning and resolution
   governance for Knowledge Chat.

Engineering track:

1. **Technical Implementation Pack** validates the canonical artifact/build/test pipeline.
2. **Layout/XML Patch Workbench** deepens deterministic technical validation.

The two lists deliberately remain separate even when a technical conversation hands off to a workbench job.

## 11. Immediate executable backlog

1. Accept or amend the two-track ownership boundary and both contracts.
2. Select two SME reviewers and freeze the six development anchors plus the full 66-turn manifest.
3. Perform the current-model/contract mapping for Round R-B.
4. Keep conversational assertions and engineering assertions in separate evaluator schemas.
5. Capture A/B baselines before changing prompts or routing.
6. Implement System C only after baseline freeze.
7. In parallel after the shared spike, implement the two-case Technical Implementation Workbench.
8. Run separate conversational and engineering evaluations and issue two linked ADR decisions.

The next coding action should be Round R-B, not another feature patch, not a repository migration and not an IDE extension.

## 12. Open decisions that need an owner, not more framework research

- Whether the visible third profile stays ISMS or is replaced by a higher-frequency BRAVO support profile.
- Named SME/owner and source of truth for each first skill.
- Permitted cloud-model data classes and retention.
- Product budgets for latency, cost and model calls per turn.
- Exact tenant/user/conversation/task memory scopes.
- Whether R1 remains strictly draft-only; the recommendation is yes.
- The timestamp and immutable snapshot rules for the BravoGen comparator.
