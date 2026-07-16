# BRAVO Engineering Workbench Contract v0.1

Status: `DESIGN INPUT FOR R1 — not production approval`

## 1. Purpose

This contract defines the Atlas-like pipeline for technical work that must be checked rather than merely answered: BRAVO Layout/XML, SQL, DataSource, schema/configuration changes, technical implementation packs and reproducible tests.

The first target is not autonomous execution. It is a demonstrably useful, reviewable outcome:

> Input requirement/image/file → canonical technical case → isolated workspace and diff → deterministic validation/build/test → reviewable result.

This is not the BravoGen conversational benchmark and is not the general chatbot reasoning architecture. Conversation quality is handled separately in `07-CONVERSATION-INTELLIGENCE-BRAVOGEN-BENCHMARK.md`.

## 2. Keep product and engineering concepts separate

| Concept | Responsibility | Example |
|---|---|---|
| Profile/mode | User-facing source, prompt, tool and safety policy bundle | Auto, User Guide, Implementation, ISMS |
| Workbench capability | Versioned technical pipeline with input/output/validator contract | Layout Patch, Technical Implementation Pack |
| Job | One isolated run with a workspace and state machine | normalize → plan → patch → build → test → review |
| Tool | One permissioned read or draft-producing operation | schema lookup, KEDB search, create XML draft |

Rules:

- the router may select the Implementation profile and a compatible workbench capability;
- the user may override the profile, but not RLS, permissions, or risk policy;
- a workbench capability is not a conversational mode or a model;
- a mode must not be implemented as a model name alone;
- an action workflow is not a fourth knowledge mode.

The visible product profiles may remain:

1. `Auto` — default routing with the selected profile visible;
2. `BRAVO User Guide` — usage and business workflow guidance;
3. `Implementation & Technical` — schema, configuration, issue, impact and drafts;
4. `ISMS/Policy` — only when governed, versioned policy sources and evaluation exist.

## 3. Ownership boundaries

### BRAVO platform owns

- identity, tenant/customer/environment scope and RLS;
- conversation and task identity;
- persistence, checkpoint and resume semantics;
- tool inventory, permissions, rate limits and idempotency;
- artifact store and content hashes;
- approval, execution and verification states;
- audit/trace retention and release gates.

### Engineering Workbench owns

- technical requirement normalization and environment-gap detection;
- canonical technical case construction;
- workspace/job planning through typed ports;
- generation of bounded patches/proposals;
- orchestration of deterministic validators, builds and tests;
- immutable job events, result manifests and proposed revisions.

### Deterministic engineering adapters own

- parsers, mappings and transformations that can be encoded;
- schema/lint/compiler/business-rule validators;
- build/test commands, normalized comparison and artifact packaging;
- explicit preconditions, postconditions and invariants.

### Model never owns

- permission decisions;
- claims that a schema object exists without a verified snapshot;
- promotion of an issue resolution to verified KEDB;
- approval, execution, or verification status;
- silent override of deterministic results.

## 4. Minimum shared contracts

Names below describe semantic contracts. Reuse current environment, identity, artifact, approval and run semantics through adapters; do not reuse conversational state as the job's source of truth.

### `TaskBrief`

```yaml
contract_version: bravo.task-brief/v1
task_id: uuid
task_epoch: integer
goal_type: string
requested_outcome: string
profile: auto|bravo_user_guide|implementation|isms
risk: U0|U1|U2|U3|U4
environment:
  bravo_version: string|null
  module: string|null
  customer_environment: string|null
  database_schema_ref: string|null
inputs: []              # text/image/file manifests, never implicit local paths
known_facts: []
constraints: []
assumptions: []
open_questions: []
corrections: []
```

### `WorkbenchJob`

```yaml
job_id: uuid
capability_id: bravo.technical-implementation-pack
capability_version: 0.1.0
task_brief_ref: uuid
requested_operation: analyze|draft|validate|build|test|revise
allowed_tools: []
effective_permissions: []
deadline_ms: integer
idempotency_key: string
workspace_ref: string|null
```

The platform resolves `allowed_tools` and the command allowlist from policy. The model cannot add entries or construct an unrestricted shell command.

### `EvidenceBundle`

```yaml
bundle_id: uuid
query_plan: []
items:
  - evidence_id: string
    source_type: user_guide|business_rule|schema|kedb|ticket|policy|user_input
    authority: verified|reviewed|unverified
    bravo_version: string|null
    environment_scope: string|null
    effective_from: string|null
    effective_to: string|null
    content_hash: string
missing_required: []
conflicts: []
```

Citations are not a legalistic product requirement; provenance is a debugging and grounding mechanism. Natural responses may cite lightly, but exact schema, version, policy, or verified-resolution claims must retain evidence pointers in the trace.

### `DomainCase`

Each capability defines a canonical model between input and output. For the first capability:

```yaml
case_type: numbering_requirement
business_goal: string
affected_documents: [UNC, CTNB]
number_format:
  components: []
  reset_scope: null
  sequence_width: 3
triggers: []
concurrency_requirement: null
version_assumptions: []
technical_candidates: []
unresolved: []
```

The case is a proposal until deterministic/evidence checks confirm its fields.

### `ArtifactManifest`

```yaml
artifact_id: uuid
kind: implementation_pack|sql_draft|layout_patch|test_matrix|import_draft
status: draft|validated|blocked|approved|executed|verified|rejected
capability_id: string
capability_version: string
input_hashes: []
evidence_ids: []
files:
  - logical_name: string
    media_type: string
    content_hash: string
generator:
  model: string|null
  tool_versions: {}
validation_report_ref: uuid|null
supersedes: uuid|null
```

### `ValidationFinding` and `ValidationReport`

```yaml
finding_id: string
validator_id: string
severity: info|warning|error|critical
disposition: pass|fail|manual|not_applicable
message: string
location: string|null
evidence_ids: []
remediation: string|null
blocks_transition: boolean
```

The transition policy, not the model, maps findings to allowed next states. `critical + manual` must block handover unless a named approval policy explicitly resolves it.

### `WorkbenchResult`

```yaml
job_id: uuid
outcome: analyzed|drafted|built|tested|blocked|failed|cancelled
summary: string|null
domain_case_ref: uuid|null
artifact_refs: []
validation_report_ref: uuid|null
open_questions: []
assumptions: []
job_events: []
trace_ref: uuid
```

## 5. State machine and invariants

```text
received
  -> understood
  -> evidence_ready | clarification_required | blocked
  -> planned
  -> drafted
  -> validated | blocked
  -> awaiting_approval
  -> approved | rejected
  -> executed
  -> verified | failed
```

Only the transitions supported by a capability are used. R1 ends at `validated`, `tested` or `awaiting_approval`; it does not execute a customer/production mutation.

Mandatory invariants:

1. `drafted` cannot be rendered as “completed”.
2. `validated` does not imply business approval.
3. `approved` does not imply execution.
4. `executed` does not imply outcome verification.
5. Missing required environment/schema facts block exact claims and ready artifacts, but may still produce a conditional analysis and an explicit data request.
6. User correction increments a revision and invalidates only dependent case fields/artifacts.
7. Cancellation prevents new tools and artifacts for that invocation.
8. Every state transition records actor, previous/new state, policy reason and hashes.

This implements two distinct behaviors:

- **advisory fail-soft:** give useful conditional analysis and ask the highest-information question;
- **action/handover fail-closed:** block readiness or execution when required evidence, validation, permission or approval is missing.

## 6. Workbench capability package layout

Agent Skills conventions may be used for discoverable instructions, but the authoritative package is a BRAVO workbench contract:

```text
workbenches/bravo-technical-implementation-pack/
  SKILL.md                       # human/model instructions and discovery metadata
  bravo.workbench.yaml           # authoritative job/build/test manifest
  schemas/
    input.schema.json
    domain-case.schema.json
    result.schema.json
    artifact-manifest.schema.json
  prompts/
    analyze.md
    critic.md
  tools/
    ports.py                     # protocols only
  validators/
    requirement.py
    artifact.py
    state_transition.py
  references/
    workflow-prerequisites.md
  tests/
    golden/
    negative/
    correction/
```

`SKILL.md` is not the authority for permissions or execution. `bravo.workbench.yaml` must include:

- stable ID, semantic version and owner;
- compatible profiles, BRAVO versions/modules and workbench-contract versions;
- input/domain/output schema refs;
- required evidence classes and context;
- requested tool and command capabilities;
- risk classification and approval policy;
- validator IDs and transition policy;
- token/time/cost budgets;
- workspace template, build/test adapters and golden-suite version;
- review, supersede and deprecation status.

Compatibility is explicit:

```text
capability version
× workbench contract
× BRAVO version
× schema snapshot
× mode policy
```

## 7. Standard engineering pipeline

### Step 1 — Define a real outcome

Choose a narrow technical job with an observable artifact, canonical state, deterministic checks, and a negative case. Do not start from “let the agent code freely”.

### Step 2 — Capture expert workflow

Write prerequisites, decision points, failure modes, required environment/version facts, and what a senior BRAVO expert checks before answering. Store verified business/schema facts separately from prompt prose.

### Step 3 — Define the canonical domain case

Create the smallest typed model that expresses the task without UI/model/framework objects. Mark fields as supplied, inferred, verified, conflicting, or missing.

### Step 4 — Partition responsibility

For every step decide:

- deterministic transform;
- retrieval/grounding;
- model reasoning;
- optional human clarification;
- mandatory approval;
- hard fail.

### Step 5 — Implement ports and validators first

Create fakes for retrieval, schema, KEDB, artifacts and approval. The golden case must run without production services. Add state-transition and validator tests before optimizing prompts.

### Step 6 — Add bounded model insertion points

The model receives typed inputs and returns a typed proposal or patch plan. Parse/validation failures are explicit outcomes. The model cannot mark its own output validated and cannot run arbitrary commands.

### Step 7 — Materialize a diff in an isolated workspace

The job may produce:

- a technical summary for the developer;
- assumptions and requested clarifications;
- implementation draft(s);
- test matrix;
- validation findings and handover status.

The source tree is copied or checked out into a disposable workspace. Proposed changes are a diff; the original/customer workspace is never mutated by the draft stage.

### Step 8 — Run golden, negative and correction suites

Minimum per capability before registration:

- one happy-path golden case;
- one missing-evidence block case;
- one contradictory-evidence case;
- one user-correction case;
- one unsafe tool/policy case;
- deterministic normalized rerun test for non-model stages.

### Step 9 — Developer/SME review and versioned registration

An owner signs the capability version and golden suite. Runs pin the version. Parser, validator or build-environment changes create a new version or governed revision.

### Step 10 — Canary and promotion

Start draft-only/read-only, measure hard failures, latency, cost, clarification rate, and SME preference. Action execution is a separate release gate.

Lifecycle:

```text
draft
  -> schema/security validation
  -> offline benchmark
  -> SME review
  -> shadow/canary
  -> promote
  -> regression evaluation
  -> supersede/deprecate/rollback
```

## 8. First vertical workbench capability

### `bravo.technical-implementation-pack` v0.1

Scope:

```text
requirement text/image/XML fragment
  -> TaskBrief
  -> technical DomainCase
  -> version/environment gaps
  -> business + implementation analysis
  -> SQL/Layout/config draft when justified
  -> test matrix
  -> lint/structural/business findings
  -> reviewable package
```

R1 constraints:

- draft-only; no database/config mutation;
- schema claims require a provided snapshot/evidence fixture;
- generated SQL/XML is labelled proposal until validated;
- output may be useful and conditional even when exact environment evidence is missing;
- the UNC/DocNo image case is the primary golden anchor;
- a missing version/schema/master-data fixture is the mandatory fail-closed anchor.

This capability tests whether BRAVO can turn a requirement into a reproducible technical result. It does not test whether the general chatbot converses better than BravoGen.

## 9. IDE and web-test integration decision

### 9.1 Do not make an IDE the execution core

An IDE is valuable as the developer's review surface, but it should not own workbench state, command policy or truth. The core runner must be headless and reproducible so the same job can run from API, CI, a local CLI or an IDE adapter.

Recommended order:

1. isolated workspace/worktree or copied fixture;
2. typed patch/diff;
3. language/parser diagnostics;
4. allowlisted formatter/linter/compiler/build commands;
5. unit/integration tests;
6. optional browser/UI test;
7. result manifest, trace and developer review;
8. optional IDE extension that displays the same job and results.

Use language servers or compiler/parser APIs for diagnostics when available. The Language Server Protocol exists precisely to decouple language intelligence from a particular editor. Do not scrape an IDE screen to infer compiler correctness.

### 9.2 Useful IDE integration after the headless runner works

A thin VS Code extension may later provide:

- submit the selected requirement/file to the workbench;
- preview/apply a proposed diff;
- show canonical case, assumptions and evidence;
- expose allowlisted build/test jobs as VS Code Tasks;
- publish results to Test Explorer;
- navigate from a finding to the affected file/location;
- require Workspace Trust before any code execution.

VS Code's official APIs support task providers, test result publication and Workspace Trust. This makes an extension a suitable adapter, not a reason to put VS Code or a specific AI coding extension into the product core.

### 9.3 Web testing

Use Playwright through a `BrowserTestRunner` port when the target really has a stable web surface. Store the test code, screenshots and traces as job artifacts. Prefer role/test-id based locators, web-first assertions and trace capture. Do not let the model click freely in a customer/production session and call that a test.

For BRAVO desktop-only screens, Playwright is not applicable; use the relevant UI automation/test harness only after a dedicated feasibility and safety review. Layout/XML structural validation remains useful even without end-to-end UI automation.

### 9.4 Isolation

Because the machine now has Docker/WSL, use a pinned container/dev-container image for toolchains that can run on Linux. Set CPU/memory/time/network limits and mount only the disposable workspace. A Windows-only BRAVO compiler/runtime needs a separate Windows runner adapter; do not assume a Linux container can validate it.

R1 should not auto-install dependencies, contact customer systems, access production databases or apply generated changes. Dependency resolution must use approved lockfiles/registries and be recorded in the manifest.

## 10. Engineering accuracy ladder and gates

“Correct” has levels; UI syntax success alone is insufficient.

| Level | Evidence | R1 status |
|---|---|---|
| E0 — Parsed | Input and canonical case validate | Required |
| E1 — Static | XML/SQL/config syntax, schema and lint pass | Required where applicable |
| E2 — Build | Project/compiler/build command succeeds in pinned workspace | Required when a runnable fixture exists |
| E3 — Integration | Test database/service fixture passes postconditions | Optional until safe fixture exists |
| E4 — UI | Browser/desktop test proves the intended behavior | Optional, capability-specific |
| E5 — Environment | BRAVO-version/customer-specific acceptance by developer/SME | Human gate; never inferred from E0–E4 |

Metrics:

- canonical extraction accuracy and required-field recall;
- patch applies cleanly to the pinned input revision;
- static/build/test pass and correct failure classification;
- negative-case block rate;
- unsupported assumption rate;
- normalized deterministic-stage rerun;
- manifest/provenance completeness;
- correction-to-diff fidelity;
- false-ready rate, which must be zero on the golden negative set.

## 11. Definition of done for Contract v0.1

The contract is ready to implement when:

1. existing identity/environment, artifact, draft, approval and run models are mapped to the contracts without two competing sources of truth;
2. JSON schemas validate the UNC golden and negative fixtures;
3. state-transition tests prove the mandatory invariants;
4. a fake proposal generator and a model adapter can both sit behind the same proposal port;
5. the canonical/validation package has no direct database, FastAPI, IDE or agent-framework dependency;
6. the current platform can persist/retrieve artifacts and checkpoints through adapters;
7. the engineering evaluator scores the canonical case, diff, build/test results and manifest independently from chatbot TMS;
8. side effects can only pass through the current permissioned action/draft gateway.

## 12. Primary implementation references

- Microsoft, [Language Server Protocol](https://microsoft.github.io/language-server-protocol/).
- Visual Studio Code, [Workspace Trust Extension Guide](https://code.visualstudio.com/api/extension-guides/workspace-trust).
- Visual Studio Code, [Task Provider API](https://code.visualstudio.com/api/extension-guides/task-provider).
- Visual Studio Code, [Testing API](https://code.visualstudio.com/api/extension-guides/testing).
- Playwright, [Best Practices](https://playwright.dev/docs/best-practices).
- Development Containers, [Specification](https://containers.dev/).
- Docker, [Resource constraints](https://docs.docker.com/engine/containers/resource_constraints/).
