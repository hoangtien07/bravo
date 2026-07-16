# Council decision: workspace assets, engineering principles, and rebuild boundary

Status: `PROPOSED — use as the architecture guardrail for R1`

## 1. The question being decided

The question is not whether `atlas-builder`, LangGraph, Pydantic AI, or another repository has more features. It is:

> For one developer, what is the smallest architecture that can repeatedly produce BRAVO 10 answers and artifacts that are more useful than BravoGen on a bounded benchmark, while preserving authorization, evidence, approval, and operational safety?

This reframing avoids two common mistakes:

- treating a framework or repository as the product architecture;
- interpreting “create a clean core” as permission to rewrite the whole platform.

The workspace audit is therefore a capability audit. A repository is adopted only when it closes a measured gap with lower lifecycle cost than implementing a narrow adapter locally.

## 2. Corrections to the supplied thesis

The supplied analysis is directionally correct, with four refinements.

1. **Consultation is the universal intake and control surface, not necessarily a packaged skill.** Domain skills use the same typed contracts, but a normal grounded answer does not need to pretend to be an executable skill.
2. **BravoGen modes and BRAVO skills are different abstractions.** A mode is a user-facing policy/retrieval profile. A skill is a versioned domain capability. A workflow is one invocation's state machine. A tool is a permissioned operation.
3. **The Agent Skills specification is a packaging and progressive-disclosure convention, not a runtime.** It does not provide authorization, durable state, validation, approval, or safe execution. BRAVO must own those contracts.
4. **“Better than BravoGen” must be a bounded, testable release claim.** It cannot mean globally smarter. It means winning a frozen, blind benchmark for named BRAVO tasks without increasing hard failures.

## 3. Council composition and common ground

The review uses six viewpoints:

| Viewpoint | Primary concern | Council position |
|---|---|---|
| Product/ERP lead | Real BRAVO outcomes | Optimize for complete business/technical workflow, not fluent prose |
| Domain architect | Stable domain boundaries | Put a canonical domain model between conversation and artifacts/actions |
| Runtime architect | Replaceability and state | Keep the agent framework behind ports; BRAVO owns state and policy |
| Security/SRE | Failure containment | Draft-first, fail-closed, observable transitions, no hidden mutation |
| Evaluation lead | Causal evidence | Same-model/evidence bake-off, golden cases, negative gates, blind SMEs |
| Solo-maintainer | Complexity budget | One vertical slice, one runtime, one state store, no speculative platform |

Consensus: retain the current BRAVO platform boundary and run two independent strangler tracks:

1. **Conversation Intelligence Core** — improve task understanding, business prerequisite reasoning and useful natural answers; compare it with BravoGen.
2. **BRAVO Engineering Workbench** — turn technical requirements into canonical models, diffs, Layout/SQL/config drafts, builds and tests; judge it by deterministic engineering gates.

They may share TaskBrief, environment scope, evidence, permissions, traces and artifact storage. They do not share a quality verdict: a passing build does not prove a good conversation, and a helpful answer does not prove a correct artifact. Full rewrite is not authorized by the available evidence.

## 4. Engineering principles applied to this decision

### 4.1 Information hiding and deep modules

Parnas' decomposition principle and Ousterhout's “deep module” guidance lead to the same rule: modules should hide volatile decisions. The following must be ports, not imports spread throughout the core:

- model/runtime provider;
- retrieval and schema/KEDB access;
- tool execution;
- state persistence;
- artifact storage;
- validation;
- approval and handover.

The public contracts should be smaller than their implementations. A framework-specific message, checkpoint, or tool object must not become a domain model.

### 4.2 Hexagonal architecture

The shared domain core must run in tests without FastAPI, Postgres, a browser, a vector database, or a live LLM. These systems connect through adapters. This makes the same golden fixture usable against the current Consultant path, System C, and future runtime challengers.

### 4.3 Strangler fig

Replace one observable capability at a time behind the existing API and security boundary. Do not port feature parity. Traffic can be routed per frozen benchmark family, with the legacy path remaining available until the new slice passes its gate.

### 4.4 Functional core, imperative shell

- **Functional/domain core:** typed task state, prerequisites, canonical cases, deterministic transformations, validators, state transition rules.
- **Imperative shell:** LLM calls, retrieval, database reads, file creation, external tools, persistence, approval notifications.

The model may propose; deterministic code validates; policy decides whether the proposal can progress.

### 4.5 Design by contract

Each skill invocation needs explicit preconditions, postconditions, and invariants. Examples:

- precondition: BRAVO version/schema snapshot is known before an exact field claim;
- postcondition: every generated artifact has a manifest, hashes, validation report, and status;
- invariant: `draft != validated != approved != executed != verified`;
- invariant: a model response cannot move state across an approval boundary.

### 4.6 Evolutionary architecture and fitness functions

Architecture claims must have executable fitness functions: dependency direction, contract validation, state-transition tests, negative-case blocking, latency/cost budgets, and framework-isolation tests. An architecture diagram without these tests is documentation, not protection.

### 4.7 Add agent complexity only after measurement

Use prompt chaining, routing, and deterministic gates before graph orchestration or multi-agent collaboration. Add a graph only when the task has independently branching/rejoining state that cannot be represented clearly in the current workflow contract. Add a durable workflow engine only after measured long-running/retry/resume requirements exceed current checkpoints.

## 5. Workspace repository audit

The classifications below mean:

- **Adopt:** use through a narrow adapter in the decision slice;
- **Learn:** copy the architectural pattern, not the codebase;
- **Pilot:** isolated experiment that cannot block R1;
- **Defer:** potentially useful after a measured trigger;
- **Reject for core:** do not make it a core dependency.

| Repository | What it contributes | Decision for R1 | Reason |
|---|---|---|---|
| `bravo` | Auth/RLS, API, retrieval, tool policy, drafts, approval, audit, checkpoints, eval fixtures | **Adopt platform services** | These are costly and safety-sensitive assets already present; the weak point is reasoning/domain synthesis, not the whole platform |
| `atlas-builder` | Canonical domain representation, deterministic transformation, validators, audit, handover, golden bundle pattern | **Learn; optional later adapter** | Strong domain-compiler pattern but prototype-style flat scripts, path/subprocess coupling, missing runtime data/tests, and unsafe manual/overlay edge cases |
| `agents-cli` | Evaluation/build/deploy lifecycle for Google ADK agents | **Learn/Pilot only** | Useful evaluation ergonomics; not the BRAVO request runtime, and cloud/deployment assumptions add scope |
| `arkon` | Map–reduce–plan review–refine–verify–commit knowledge workflow and resumable drafts | **Learn only** | Useful knowledge-production and skill-governance pattern; license and product scope make direct core adoption unattractive |
| `DocsGPT` | RAG/chat ingestion, agent profiles and model capability catalog | **Learn or adapter benchmark** | Can inform ingestion/retrieval UX; replacing BRAVO's platform with it does not solve ERP workflow reasoning |
| `graphiti` | Temporal/bi-temporal facts, provenance and hybrid graph retrieval | **Defer** | Valuable only after version/supersession queries show a measured win; adds graph storage, LLM ingestion cost and operating burden |
| `letta` | Stateful memory and typed tool-transition concepts | **Learn; reject full runtime for R1** | BRAVO already has scoped task state/checkpoints; adopting a second state owner creates semantic conflict |
| `zenml` | Reproducible offline pipelines, artifacts and experiment orchestration | **Defer outer loop** | Useful for later ingestion/eval promotion; too heavy for the online reasoning decision path |
| `zenml/kitaru` | Replay/durable agent execution experiments | **Isolated micro-pilot** | May test deterministic replay, but must not own production state or block the core decision |
| `generative-ai` | Grounding/evaluation samples and provider examples | **Reference only** | Examples are not a maintained domain architecture or production product |

No workspace repository should be imported wholesale as the BRAVO core. Combining them would create several platforms with overlapping state, tool, memory and evaluation ownership.

## 6. Atlas Builder assessment

### 6.1 What is worth carrying forward

Atlas demonstrates a useful product pattern:

```text
unstructured evidence
  -> canonical domain representation
  -> deterministic transformations
  -> typed artifact
  -> validation/audit
  -> human handover gate
```

This pattern is the main reason the output is actionable. It narrows the model's freedom and makes correctness testable. It is directly applicable to BRAVO technical implementation, import preparation, financial close readiness, and support-resolution packs.

### 6.2 What is not a reusable runtime foundation

Observed limitations in the local snapshot include:

- 88 Python modules in a flat `scripts/` architecture with direct imports and subprocess/path coupling;
- domain/workspace assumptions embedded in `.cursor`, `context`, filenames and local folders;
- no `test_*.py` suite and absent runtime dictionaries, representative samples and a closed test envelope;
- a pipeline that can report `OK` before audit and intentionally does not always block on audit failure;
- a handover gate that blocks `Critical + fail` but exposes a dangerous `Critical + manual` boundary;
- agent overlay behavior that can cross deterministic ownership;
- inconsistent skill pipelines and nondeterministic system-date inputs;
- path confinement and artifact-slug hardening gaps.

Therefore the correct reuse unit is the **pipeline and contract pattern**, not a code copy. If Atlas modules are later used, they should sit behind a typed executor adapter in a container or isolated process, return structured results, and never own BRAVO authorization, state, evidence truth, or approval.

## 7. Architecture decision

### 7.1 Chosen boundary

Build a **bounded Conversation Core v2** and a separate **Engineering Workbench pipeline** inside the current monorepo, while retaining platform services.

```text
Channels / API / UI
        |
BRAVO platform shell
auth | RLS | tenant scope | persistence | audit | approval
        |
Typed ports
        |
Shared foundation
TaskBrief | environment | evidence ledger | permissions | trace
        |                                  |
Conversation Core v2                 Engineering Workbench
business prerequisite reasoning      canonical technical case
        |                             workspace/diff/build/test
answer synthesis + critic             deterministic validators
        |                                  |
Natural answer                        reviewable engineering result
```

Pydantic AI remains the first System C candidate for the **conversation track**. It does not own domain state, authorization, or persistence. LangGraph remains a challenger only when a measured branching-state problem justifies it. The Engineering Workbench is primarily a deterministic build/test pipeline with bounded model insertion points; it does not need to use the same orchestration framework.

Do not split Agent Core v2 into a service yet. Split deployment only for measured independent scaling, security boundary, release ownership, dependency conflict, or background workload isolation.

### 7.2 Explicit non-decisions

R1 does not approve:

- a separate greenfield product with duplicate auth/API/state;
- Temporal, ZenML, Graphiti, or a graph database in the online request path;
- multi-agent production orchestration;
- live BravoGen fallback or automatic learning from external answers;
- automatic SQL/XML/database execution;
- a generic skill DSL or marketplace;
- copying Atlas scripts into the BRAVO core.

## 8. Compatibility rules

Components are compatible only when they comply with contracts, not because they use the same framework.

1. Domain packages depend only on contract types and port protocols.
2. Runtime/framework adapters depend inward; domain models never import a runtime SDK.
3. Persist only BRAVO-owned canonical state, not opaque framework checkpoints as the source of truth.
4. Every tool has schema, read/write classification, required permission, timeout/idempotency policy, and structured error.
5. Every mutation is a draft until explicit approval; approval does not imply execution or verification.
6. Evidence IDs and environment/version scope travel with claims and artifacts.
7. Skill versions are immutable for completed runs; migrations are explicit.
8. A skill cannot widen RLS, tool allowlists, or mode policy.
9. Framework adapters emit a normalized event contract and pass the same conformance suite.
10. Skill composition is declared; the model cannot invent an arbitrary delegation graph.

## 9. Complexity budget for a solo developer

During R1, the allowed new architecture is limited to:

- one reasoning runtime adapter;
- one shared contract package;
- one skill registry;
- one conversation reasoning slice;
- one narrow engineering pipeline for the UNC/Layout benchmark;
- existing Postgres/checkpoint/artifact/approval services;
- existing trace/eval path, extended only for the new contracts.

A new service or framework requires a short ADR containing: measured problem, alternatives, exit/rollback plan, operating cost, and a fitness test that fails without it. “Industry standard”, “future scale”, or repository popularity are not sufficient reasons.

Apply KISS/YAGNI to the runtime and strictness to contracts, validators, action boundaries and evaluation. Do not abstract similar domain rules until at least the third occurrence makes the stable commonality visible.

## 10. Council dissent and resolution

### Dissent A: build a completely clean project to escape legacy coupling

Valid concern: current orchestration is coupled and has accumulated heuristics. Resolution: build the new core in a clean package and communicate only through ports, but keep the trusted platform shell. Approve a full split only if R1 identifies at least three independent platform-coupling failure clusters.

### Dissent B: adopt Atlas as the artifact runtime immediately

Valid concern: its deterministic pipeline can accelerate artifact work. Resolution: first reproduce its architectural benefits with one BRAVO-native golden skill. Integrate Atlas later only through a typed, isolated adapter after its P0 handover/overlay/runtime-data gaps are closed.

### Dissent C: design the generic multi-skill platform first

Valid concern: BRAVO will eventually need many modules and modes. Resolution: define the minimum stable contracts now, but generalize only after the second independently authored skill exposes repeated structure.

### Dissent D: use the engineering artifact pipeline to prove the chatbot is better

Resolution: these are different hypotheses. The workbench is evaluated by canonical extraction, static checks, build/test evidence and safe handover. The chatbot is evaluated by business/technical understanding and conversational usefulness. The full chatbot decision set remains 24 trajectories covering the existing 66 turns; six anchors are only its development smoke suite.

## 11. Final council recommendation

Proceed with two coordinated but independently gated strangler tracks. Do not start a full rewrite and do not continue feature-by-feature patching inside the legacy loop. The technical workbench contract is in `05-BRAVO-ENGINEERING-WORKBENCH-CONTRACT.md`; the chatbot-quality track and sequencing are separated in `06-RESEARCH-AND-IMPLEMENTATION-ROUNDS.md` and `07-CONVERSATION-INTELLIGENCE-BRAVOGEN-BENCHMARK.md`.

## 12. Local evidence pointers

- Atlas self-assessment: [COUNCIL_DEMO_ASSESSMENT.md](D:/VsCode/Workspace/atlas-builder/docs/COUNCIL_DEMO_ASSESSMENT.md:56).
- Atlas architecture: [ARCHITECTURE.md](D:/VsCode/Workspace/atlas-builder/docs/ARCHITECTURE.md:5).
- Atlas pipeline can report before audit completes: [lo_pipeline.py](D:/VsCode/Workspace/atlas-builder/scripts/lo_pipeline.py:1308).
- Atlas handover only blocks critical failures: [handover_check.py](D:/VsCode/Workspace/atlas-builder/scripts/handover_check.py:177).
- `agents-cli` evaluation lifecycle: [README.md](D:/VsCode/Workspace/agents-cli/README.md:60), [evaluation.md](D:/VsCode/Workspace/agents-cli/docs/src/guide/evaluation.md:41).
- Arkon MRP/versioned skills: [README.md](D:/VsCode/Workspace/arkon/README.md:27), [SKILLS.md](D:/VsCode/Workspace/arkon/docs/SKILLS.md:90).
- DocsGPT profiles and research flow: [basics.mdx](D:/VsCode/Workspace/DocsGPT/docs/content/Agents/basics.mdx:49).
- Graphiti temporal facts/provenance: [README.md](D:/VsCode/Workspace/graphiti/README.md:42).
- Letta stateful memory/tool model: [README.md](D:/VsCode/Workspace/letta/README.md:19).

## 13. Primary references

- David Parnas, [On the Criteria To Be Used in Decomposing Systems into Modules](https://doi.org/10.1145/361598.361623).
- Alistair Cockburn, [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture).
- Martin Fowler, [Strangler Fig Application](https://martinfowler.com/bliki/StranglerFigApplication.html).
- Neal Ford et al., [Building Evolutionary Architectures](https://evolutionaryarchitecture.com/).
- John Ousterhout, [A Philosophy of Software Design](https://web.stanford.edu/~ouster/cgi-bin/aposd.php).
- Bertrand Meyer, [Applying Design by Contract](https://se.inf.ethz.ch/~meyer/publications/old/dbc_chapter.pdf).
- Anthropic, [Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents).
- Agent Skills, [Specification](https://agentskills.io/specification).
- Model Context Protocol, [Server concepts](https://modelcontextprotocol.io/specification/2025-06-18/server/index).
