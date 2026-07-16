# P0-23 — R0 post-processing and decision analysis

Status: `COMPLETE — collection processed; architecture decision remains open`

## 1. Data used

- 34+ prior synthetic black-box cases from P0-02 through P0-20.
- Strict closure set in `P0-21-r0c-strict-closure-raw.json`:
  - five identical anchors across all three modes: 15 observations;
  - two independent Insight repeats;
  - 17 unique valid records and no missing record.
- Manual quality layer in `P0-22-r0-quality-scoring.json`.
- Current-system evidence from `docs/CONSULTANT-INTELLIGENCE-IMPLEMENTATION.md`, the 30-case structural fixture and the production release-gate artifact.

The P0-21 collection gate is valid, but it is not itself a quality pass. Fourteen records retain a full accessibility-tree capture; the three closure records are normalized excerpts and are explicitly marked as such. The final profile override was authorized by the user and is now represented truthfully in metadata.

## 2. Quality-scoring summary

Scale: 0–4. Scores measure the captured behavior, not a hidden implementation.

| Dimension | Mean | N | Interpretation |
|---|---:|---:|---|
| Mode fit | 3.82 | 17 | Strong visible scope/routing behavior |
| Task usefulness | 2.76 | 17 | Useful overall, but redirects depress end-user progress |
| Domain reasoning | 2.12 | 17 | Uneven; strong in native answers, minimal in redirects |
| Uncertainty control | 3.24 | 17 | Usually abstains/routes well, with one critical exception |
| Evidence quality | 1.62 | 8 | Weakest area for direct factual answers |
| Safety | 3.76 | 17 | Strong behavioral refusal/routing in the tested sample |

Expected redirects form 8/17 records. They score 4.0 for mode fit and uncertainty control but only 2.0 for usefulness. The nine direct/clarifying answers average 3.44 for usefulness and 3.11 for domain reasoning, but only 1.62 for evidence quality.

Verdict distribution:

- 8 `verified-boundary`;
- 1 `verified-clarification`;
- 1 `verified-no-result`;
- 6 `plausible-unverified`;
- 1 `unsupported`.

## 3. What makes BravoGen feel more useful

### 3.1 It models a task, not only a document lookup

The strongest example is the reporting question. The useful response connects opening balances, accounting postings and period-end closing before report access. The weaker response merely explains how to open and run the report. This exactly matches the user's diagnosis of the current BRAVO chatbot.

The reusable capability is therefore a workflow/prerequisite model:

```text
user goal
  -> current business state
  -> required prerequisites
  -> missing or contradictory facts
  -> safe next step
  -> detailed procedure
```

This should not be implemented as a larger system prompt. It needs typed workflow state, task-specific retrieval and a completeness critic.

### 3.2 It has visible domain contracts

The three modes consistently change scope, response shape and redirects. This is useful product behavior, but mode labels alone are not the advantage. The underlying reusable contract is:

- source and metadata scope;
- required context slots;
- output contract;
- allowed tools/actions;
- abstention and escalation rules;
- domain-specific evaluation.

For BRAVO, manual mode selection should be an override. Automatic routing should normally prevent the user from receiving a redirect and having to repeat the same question.

### 3.3 It asks high-value diagnostic questions

The Layout XML answer requests the XML fragment, parent container, screen type, platform, visibility/evaluator logic, DataSource and logs before proposing a fix. This is more useful than generic refusal and safer than an immediate patch.

The reusable capability is a diagnostic question policy keyed by task state, not generic “please provide more detail” wording.

### 3.4 It can express relationship knowledge

The purchase-flow answers distinguish direct and inferred relationships and make prerequisites visible. That output shape is valuable. The evidence does not prove a graph database or GraphRAG. A small curated relationship/workflow card can reproduce the product value before any graph infrastructure is justified.

### 3.5 It exposes support intelligence as a product surface

Specific case IDs and resolutions make the answer feel operationally useful. However, the captured issue response did not expose auditable issue status, affected version, verification owner or supersession. Those answers must not be automatically ingested into BRAVO knowledge.

The BRAVO equivalent needs a governed KEDB record:

```text
symptom + product version + environment + cause
  + diagnostic discriminator
  + verified resolution
  + verifier/date
  + supersedes/deprecates
  + evidence link
```

## 4. Important negative findings

### 4.1 Schema grounding failed the strongest test

When version and schema snapshot were deliberately absent, Insight asserted that `B30BizDoc` and related tables definitely existed. This is `unsupported`, not a useful best effort. Any future BRAVO runtime must fail closed for exact schema/table/field claims unless a matching snapshot or approved schema registry is present.

### 4.2 Citation shape is not claim support

The average evidence-quality score is the lowest dimension. Broad user-guide pages and policy links often do not prove every generated role, rule, edge or technical detail. Citation should remain lightweight in the UI but strict inside evaluation and debugging.

### 4.3 Good routing can still create a bad conversation

Eight responses are correct redirects. If BRAVO exposes the same behavior literally, users must switch profiles and repeat prompts. The runtime should route internally and display the selected profile as an explanation/override, not make routing work the user's responsibility.

### 4.4 Structured output can be synthesized without a graph

The stable relationship table supports the need for relationship-aware reasoning. It does not justify a graph database. Building GraphRAG now would risk recreating infrastructure without proving incremental task quality.

### 4.5 BravoGen is not a safe live fallback or learning oracle

Do not add production token rotation or a hidden live fallback from unanswered BRAVO questions to BravoGen. Reasons:

- availability and quota are outside BRAVO control;
- source/version/permission boundaries cannot be enforced end to end;
- a plausible but unsupported answer could be shown as BRAVO truth;
- automatic ingestion creates feedback poisoning and provenance debt;
- the black-box evidence does not establish provider authorization, stable API contract or data-processing terms.

BravoGen can remain an offline benchmark/advisory source. Any candidate knowledge derived from it must be `review_required` and activated only after BRAVO evidence-owner verification.

## 5. Assessment of the current project

### What is already valuable

The current codebase already contains many correct primitives:

- typed goal/task state and workflow cards;
- accounting prerequisite critic;
- conversation correction/pause/resume handling;
- schema/KEDB evidence types with fail-closed empty results;
- RLS, read tools, draft/approval and durable checkpoints;
- structural benchmark, SME review contract and production release gates;
- feature flags and rollout controls.

These components are candidates for reuse after behavioral testing. Rewriting them immediately would create work without evidence of a quality gain.

### What remains unproven

- The current 30-case benchmark is structural: 30/30 proves contract conformance, not answer quality.
- Seven of ten workflow cards are scaffolds awaiting SME content.
- There is no verified support-ticket/KEDB corpus and no production schema snapshot coverage.
- There is no blind SME calibration or Task Merit Score baseline.
- All five required production gates are still pending.
- The local replay proves HTTP/state behavior and latency, not that the answer is less “vô hồn”.

### Architecture implication

The evidence does not support either extreme:

- **Do not continue feature-by-feature patching** inside the legacy loop without a quality gate.
- **Do not start a full greenfield rewrite** before isolating whether the main failure is model capability, retrieved context, workflow representation or answer synthesis.

The best current option is a **strangler vertical slice**:

- new, isolated reasoning core behind an adapter;
- reuse current auth, RLS, knowledge stores, read tools, approval and audit;
- compare against both the legacy path and current Consultant path;
- promote only if it wins a blind benchmark with the same model and evidence bundle.

## 6. Current decision

`R0 COMPLETE; R1 REQUIRED; FEATURE EXPANSION FROZEN`

Working recommendation: test a clean reasoning core as a strangler slice, not a full new product repository yet. The architecture decision must be made after R1 distinguishes model effects from code/pipeline effects.

