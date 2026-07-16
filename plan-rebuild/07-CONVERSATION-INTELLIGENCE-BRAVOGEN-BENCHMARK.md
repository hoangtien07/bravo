# Conversation Intelligence Core and BravoGen benchmark

Status: `SEPARATE R1 TRACK — conversational quality only`

## 1. Product problem

The current chatbot often retrieves relevant text and reformulates the request, but does not reliably build the expert's causal/workflow model behind the answer.

Examples:

- “Lên báo cáo tài chính” is treated as a navigation question instead of an outcome that depends on complete postings, reconciliation, allocation/depreciation/exchange-rate processing where applicable, period-end entries, closing, mapping and variance checks.
- The UNC/DocNo request is paraphrased into three implementation bullets, while a useful answer should identify sequence scope, concurrency, insert/update behavior, account changes, cancellation behavior, version/schema uncertainty and an acceptance test matrix.

The goal is therefore not “more citations” or “longer answers”. It is:

> Infer the user's real outcome, connect cross-domain prerequisites and BRAVO operations, expose consequential uncertainty, and synthesize a natural next-action answer.

## 2. Keep this track independent from the Engineering Workbench

This track produces a high-quality consultation response and typed conversation-state update. It may recommend opening a workbench job, but it is not responsible for proving a generated Layout/SQL/config patch.

| Track | Primary output | Truth/quality gate |
|---|---|---|
| Conversation Intelligence | Useful natural answer, clarification and state update | Blind SME task merit and hard-failure rubric |
| Engineering Workbench | Canonical technical case, diff, build/test evidence | Parser/validator/compiler/test/handover gates |

Shared components are limited to identity/environment, TaskBrief, EvidenceBundle, version scope, permissioned tools, traces and artifact references.

## 3. What BravoGen behavior actually demonstrates

Observed useful behavior is an external behavioral reference, not proof of its internal implementation. In the collected cases, BravoGen often:

- restates the intended outcome in operational terms;
- expands a short request into prerequisites and steps;
- connects BRAVO concepts with accounting/ERP or technical reasoning;
- gives examples and edge cases;
- adds a realistic test/acceptance sequence;
- presents a coherent answer rather than exposing internal agent steps.

These behaviors do not prove GraphRAG, ticket self-learning, a workflow engine, a particular model, or autonomous tools. BRAVO should reproduce the observable benefit using architecture that can be tested locally.

## 4. Root-cause hypotheses

R1 must isolate five hypotheses instead of assuming the model or code is solely responsible.

| ID | Hypothesis | Diagnostic comparison |
|---|---|---|
| H1 | Current model ceiling is too low | Same A/B/C pipelines with primary versus stronger frontier model |
| H2 | Retrieval lacks the right business/procedural evidence | Live retrieval versus fixed oracle EvidenceBundle |
| H3 | No explicit outcome/prerequisite representation | System C with versus without prerequisite planner |
| H4 | Synthesis copies context instead of resolving the task | Same evidence/plan through current versus new synthesizer |
| H5 | Missing critic/state causes skipped steps and bad follow-up | C with critic/state versus ablated variants |

The architecture decision must report which hypothesis explains each failure cluster.

## 5. Conversation Core v2

### 5.1 Observed diagnosis of the current code

The current project already contains useful typed `EnvironmentProfile`, `TaskState`, `WorkflowCard` and `ContextManifest` models. The problem is not that it has no structure at all.

The weakness is at the enforcement/synthesis boundary:

- `ConsultantService._prompt` serializes the selected workflow/current milestone into a text instruction for the existing loop;
- the main loop still asks one model decision to choose `tool`, `clarify` or a final free-text `answer`;
- the deterministic critic only adds bounded warning prefixes for a small number of token patterns, such as opening a financial report too early or claiming execution;
- there is no required typed prerequisite plan, claim/evidence map, answer outline and completeness result that the synthesizer must consume before it can answer.

This explains why a workflow card can exist while the final answer still paraphrases the retrieved/request text. It is evidence of a code/representation gap, not proof that the current model is adequate. The matched-model and stronger-model ablations are still required.

```text
user text / image / file / prior task state
  -> perception and normalization
  -> TaskBrief + real outcome
  -> profile + capability routing
  -> context sufficiency / highest-information question
  -> business prerequisite plan
  -> evidence plan
  -> EvidenceBroker (guide + business + schema + KEDB as needed)
  -> typed reasoning proposal
  -> completeness / assumption / contradiction critic
  -> natural answer synthesis
  -> typed scoped state delta
  -> trace and evaluation event
```

The model runtime sits behind a `ReasoningPort`. Pydantic AI is the first adapter because the current decision favors typed input/output and a small request loop. The domain contracts and evaluation do not import it. LangGraph is introduced only if real branching/interrupt/resume behavior beats the simpler adapter on at least two workflows.

## 6. The missing intelligence layer

Retrieval answers “what passages look similar”. Expert consultation also needs “what must be true before this outcome is valid”. Core v2 needs four governed knowledge forms:

1. **Outcome/prerequisite models** — business milestones, ordering, conditions, exceptions and completion signals.
2. **BRAVO operation maps** — which screens/functions/reports/configurations support each milestone, with version/environment scope.
3. **Schema and technical facts** — exact objects/relationships only when grounded in an approved snapshot.
4. **Support/KEDB cases** — symptoms, differentiating conditions, root causes, verified resolutions and supersession.

These are not all prose chunks. Workflow prerequisites and decision tables should be typed/versioned; documents remain evidence attached to their nodes.

### Example: financial-report readiness

```text
Goal: reliable financial statements
  -> period and reporting scope known
  -> source documents complete and posted
  -> subledgers reconciled with general ledger
  -> period processes applicable to the customer completed
  -> closing/period-end entries completed
  -> report mappings and opening balances checked
  -> reports generated
  -> variances and control totals reviewed
```

The answer selects and explains applicable nodes. It must not blindly repeat every possible accounting process, and it must not jump straight to the report menu.

## 7. Helpful under uncertainty, strict on exact facts

The chatbot must not fall back to “không tìm thấy tài liệu” whenever evidence is incomplete.

Advisory policy:

- state the likely workflow and why it matters;
- distinguish supplied fact, domain inference and environment-specific uncertainty;
- give conditional branches;
- ask one high-information clarification when it materially changes the path;
- offer the next diagnostic or verification step.

Hard boundaries:

- do not invent an exact BRAVO menu, field, table, procedure, issue resolution or version behavior;
- do not say a technical change was validated/executed without Workbench evidence;
- do not promote BravoGen text or a plausible answer to knowledge truth;
- do not allow a profile override to widen RLS or tools.

Provenance remains in the trace for exact claims and debugging. UI citations are selective: exact/versioned claims, conflicts, user request, or audit-sensitive answers. Citation volume is not a primary conversational score.

## 8. Profiles/modes

Use one core with policy bundles, not three model-specific codepaths.

| Profile | Reasoning emphasis | Evidence/tool scope | Answer contract |
|---|---|---|---|
| User Guide / Business | Outcome, accounting/ERP prerequisites, multi-step BRAVO use | user guides + reviewed business workflow | goal → prerequisites → BRAVO steps → checks → targeted question |
| Insight / Technical | requirement analysis, schema/configuration, troubleshooting, support | technical docs + schema/KEDB + read tools; optional Workbench handoff | interpretation → hypotheses/impact → plan → tests → uncertainty/handoff |
| ISMS / Policy | effective policy/control and approval workflow | governed policy corpus only | applicable control → obligations → evidence/approval → exception |

`Auto` is the default router and displays the selected profile. ISMS stays hidden until corpus ownership, effective dates and an eval suite exist. The user can correct routing but cannot change the underlying authorization policy.

## 9. Benchmark design

### 9.1 Dataset levels

- **6 development anchors:** fast smoke/regression loop.
- **24 frozen trajectories covering the existing 66 turns:** architecture and BravoGen comparison set.
- **Future held-out set:** required before a production-wide claim to prevent overfitting to the known benchmark.

The 24 trajectories retain the existing families: accounting/report readiness, image/technical analysis, troubleshooting, schema/version grounding, support intelligence, and multi-turn/risk.

The Engineering Workbench may be invoked in a technical trajectory, but its build/test score is reported separately. The conversation answer is still judged as a conversation answer.

### 9.2 Systems

| ID | System | Purpose |
|---|---|---|
| A | Legacy chat | Production-style baseline |
| B | Current Consultant | Measures the current typed workflow/critic additions |
| C | Conversation Core v2 | Clean strangler reasoning/synthesis slice |
| D | BravoGen in correct native profile | External behavioral comparator |

### 9.3 Matched controls

For A/B/C use the same:

- cloud model/version, temperature and token budget;
- prompt input and attachment;
- frozen EvidenceBundle;
- environment/version facts;
- absence of external fallback.

Then run targeted ablations for model strength, oracle/live retrieval, prerequisite planner, critic and multi-turn state. This separates “better model” from “better architecture”.

## 10. Conversational evaluation rubric

| Dimension | Weight |
|---|---:|
| Understands the real user outcome | 15% |
| Business/technical prerequisite completeness | 20% |
| Correct connection to BRAVO operations | 20% |
| Practical next-action usefulness | 15% |
| Assumption control and information-gain clarification | 10% |
| Edge cases, diagnostics and verification | 10% |
| Natural coherent conversation | 10% |

Hard failures override the score:

- skips a mandatory accounting prerequisite and presents the report/result as reliable;
- fabricates an exact screen/schema/version/issue fact;
- confuses a proposed technical approach with a validated implementation;
- ignores a user correction, cancellation or changed environment;
- gives a risky execution instruction without the draft/approval boundary;
- produces a polished paraphrase without materially answering the requested outcome.

Also record:

- blind pairwise preference and reason;
- refusal/abstention usefulness;
- prerequisite recall;
- unsupported exact-claim rate;
- clarification information gain;
- correction fidelity;
- latency, tokens, cost and availability.

## 11. “Better than BravoGen” gate

Do not make a global intelligence claim. The bounded claim is:

> On the frozen BRAVO target set and supplied context, Core v2 is preferred and more complete/useful without more hard failures.

Minimum gate:

- at least two calibrated SMEs and blind randomized outputs;
- at least 60% wins among non-tied C-versus-D comparisons;
- lower confidence bound of the win rate above 50% before using the word “better” externally;
- prerequisite recall at least 90% on critical workflow nodes;
- multi-turn correction fidelity at least 95%;
- zero unsafe execution claims;
- no major regression in any profile/family;
- real-pattern cases represented and the full 66-turn manifest complete.

If C only wins with a stronger model, the decision is a model upgrade. If oracle evidence creates the gain, fix ingestion/retrieval. If planner/critic ablation destroys the gain, the reasoning architecture is causal. If none moves quality, revisit task models and benchmark truth before adding frameworks.

## 12. Implementation sequence

1. Freeze A/B outputs for the six anchors and full manifest before prompt changes.
2. Formalize expected outcome, prerequisite nodes, allowed alternatives and must-not claims.
3. Build a fake/oracle EvidenceBroker and `ReasoningPort` contract.
4. Implement Core v2 only for three deep packs: financial close, technical requirement analysis, and troubleshooting/schema/KEDB.
5. Run matched A/B/C smoke tests and ablations.
6. Correct domain models/evidence gaps; do not tune against BravoGen wording.
7. Run the full 24-trajectory/66-turn blind C-versus-D evaluation.
8. Issue the architecture ADR: retain B, adopt C strangler, upgrade model/retrieval, or—only with demonstrated platform blockers—approve a larger split.

## 13. Definition of done for the conversation track

- The current and new cores consume the same frozen evidence fixture.
- TaskBrief, prerequisite plan, evidence plan, critic findings and state delta appear in a privacy-minimized trace.
- The final answer is natural and does not expose mechanical agent steps unless useful.
- Missing exact evidence produces conditional help, not a dead-end refusal.
- Exact claims remain traceable and unsupported claims are detectable by the evaluator.
- The full blind score and failure clusters, not anecdotal examples, drive the core decision.

## 14. Local code evidence

- Current typed consultant contracts: [contracts.py](D:/VsCode/Workspace/bravo/app/consultant/contracts.py:14).
- Workflow is converted into prompt guidance: [service.py](D:/VsCode/Workspace/bravo/app/consultant/service.py:248).
- Current deterministic critic is a bounded post-answer guard: [critic.py](D:/VsCode/Workspace/bravo/app/consultant/critic.py:15).
- The main decision contract directly permits a free-text final answer: [loop.py](D:/VsCode/Workspace/bravo/app/agent/loop.py:212).
