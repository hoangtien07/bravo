---
name: agentic-engineering-workflow
description: Turn ambiguous features, complex bugs, audit findings, remediation work, pilot blockers, and architectural changes into an aligned, vertically sliced, test-driven implementation workflow with explicit verification and independent review. Use when Codex must plan or implement substantial multi-file software work, convert a requirement or PRD into executable tasks, or coordinate autonomous coding safely. Do not trigger for simple factual questions or trivial, isolated edits unless the user invokes it explicitly.
---

# Agentic Engineering Workflow

Turn consequential software work into a shared design, small end-to-end slices, verified changes, and an auditable handoff. Preserve workspace rules and evidence boundaries throughout.

## Establish the working baseline

Before planning or editing:

1. Locate the repository root and read every applicable `AGENTS.md` plus any required project-state documents in their prescribed order.
2. Inspect the current branch, commit, worktree, migration head, build/test entry points, and existing design artifacts. Never expose secrets while doing so.
3. Treat code, tests, migrations, and runtime evidence as stronger than historical completion claims.
4. Preserve unrelated user changes. Do not reset, overwrite, commit, push, or edit outside the requested workspace without authority.
5. Inspect the relevant code and documentation before asking questions. Do not ask for facts available locally.
6. Identify mandatory containment, authorization, migration, baseline-freeze, or release gates. Do not begin product implementation while a gate that applies to the requested change remains unmet.

Record facts, user decisions, Codex assumptions, and evidence gaps separately.

## Classify the work

Choose the lightest workflow that safely resolves the request.

### Type A: small and clear

Use for a typo, label change, simple configuration update, or localized bug with a verified cause.

- Confirm scope briefly.
- Skip a PRD and long interview.
- Implement directly, run focused verification, and report evidence.
- Do not widen the change into opportunistic refactoring.

### Type B: moderate with consequential ambiguity

Use when a bounded change has decisions that can alter implementation.

- Inspect the codebase first.
- State current facts and assumptions.
- Ask only high-impact questions, commonly three to ten in total.
- Ask one question at a time when later decisions depend on earlier answers.
- Produce the smallest useful decision brief before implementation when decisions need a durable record.

### Type C: large, architectural, security-sensitive, or complex remediation

Use for large features, cross-cutting changes, migrations, security work, audit remediation, and pilot blockers.

- Complete the alignment workflow.
- Produce a PRD, decision brief, or remediation brief.
- Decompose into vertical slices and map dependencies.
- Define acceptance, verification, rollback, and review before implementation.
- Do not implement while a material business, architecture, security, data, public-API, or operating-cost decision remains unresolved.

Do not use a fixed interview length. Stop when the shared design is safe and implementation-ready.

## Align on a shared design

For Type B and C work:

1. Build an internal decision tree covering outcome, actors, business flow, data, authorization, security, migration and compatibility, failure modes, observability, testing, rollback, and non-goals.
2. Ask only questions whose answers can change the design or safety posture.
3. For each question, explain its impact briefly, recommend an option, and state meaningful trade-offs.
4. Do not decide major architecture, business rules, security posture, destructive migration, public API, or material operating cost on the user's behalf.
5. Record confirmed decisions as they are made and expose unresolved evidence gaps.
6. End with a shared design concept: desired outcome, constraints, chosen decisions, remaining questions, and success evidence. Do not end with only a transcript of questions.

## Choose the destination document

Create no design document for a clear Type A change. Otherwise choose the smallest durable artifact:

- Use a decision brief for a moderate design choice: context, decision, alternatives, consequences, acceptance, and open questions.
- Use a PRD for a large feature. Read [references/prd-template.md](references/prd-template.md) only when creating or reviewing one.
- Use a remediation brief for a confirmed finding or pilot blocker: finding and evidence, affected paths, containment, target state, closure evidence, rollback, owner, and residual risk.

Keep the artifact focused on the agreed destination and constraints, not the conversation history. Cite code, tests, migrations, runtime output, and governing documents precisely.

## Decompose into vertical slices

Prefer a small observable behavior that crosses only the required layers over horizontal batches such as “database, then backend, then frontend.”

For each slice:

1. Define a user-visible or system-visible outcome.
2. Bound scope and out-of-scope work.
3. State explicit dependencies and remove implicit ones.
4. Define acceptance criteria, negative cases, and completion evidence.
5. Map tests and verification commands to the acceptance criteria.
6. Identify likely files/modules without treating the list as permission for broad edits.
7. Label status as `ready`, `blocked`, `in progress`, or `completed`.
8. Label execution as `human-in-loop` or `AFK-safe`.

Read [references/issue-template.md](references/issue-template.md) only when writing or reviewing slice issues.

Build a dependency graph after drafting the slices. Identify foundation, blocked, parallel-safe, AFK-safe, and human-decision work. Mark work parallel-safe only when ownership and integration boundaries are genuinely independent. Do not assign multiple agents to a central module without an integration strategy. Do not spawn sub-agents unless the user or applicable workspace instructions permit it.

## Implement one ready slice

For each selected slice:

1. Re-check the current worktree and applicable instructions.
2. Confirm that dependencies and decisions are resolved.
3. Read only the relevant implementation and tests.
4. Prefer test-driven development:
   - Add a test for the desired behavior.
   - Confirm it fails for the expected reason.
   - Add the minimum implementation that makes it pass.
   - Refactor only while the test remains green.
5. Never weaken tests, skip a failing test, or redefine acceptance merely to obtain a pass.
6. Keep interfaces narrow and hide substantial logic behind cohesive modules. Avoid clusters of shallow helpers and out-of-scope architecture cleanup.
7. Preserve existing conventions unless the agreed design requires a change.

For UI work, verify relevant loading, empty, error, and success states; responsive behavior; and component/E2E tests. Inspect the rendered result or request human visual QA. Do not claim visual correctness from a successful build alone.

## Verify with matching evidence

Run the feedback loops proportionate to risk: focused unit tests, integration tests, type checking, lint/format checks, security probes, migration checks, build, and runtime smoke tests.

- Map each acceptance criterion to observed evidence.
- Require matching evidence for exact financial, schema, version, execution, or closure claims.
- Treat `draft`, `validated`, `approved`, `executed`, and `verified` as distinct states.
- Never execute generated SQL, configuration, or mutations automatically; retain required draft/approval gates.
- If a check cannot run, name the check, reason, and residual risk.
- Do not call work complete based only on code changes.

## Review independently

After implementation, use a clean context or independent reviewer when permitted. Give the reviewer only the confirmed requirements, acceptance criteria, diff, test evidence, and relevant code. Review tests before implementation quality.

Read [references/review-checklist.md](references/review-checklist.md) for the ordered review. Classify findings by severity and evidence. If independent review is unavailable, perform a structured self-review and state that limitation.

Do not close an unresolved QA finding. Convert it into a follow-up issue with evidence and ownership.

## Apply project-specific safety

When the workspace is BRAVO or has equivalent governed data flows:

- Distinguish `confirmed finding`, `need more evidence`, `downgraded/rejected finding`, and `pilot blocker`.
- Require closure evidence before marking a blocker closed.
- For tenant isolation, trace HTTP, agent execution, MCP, background worker, and connection-pool/session-reuse entry points.
- Require database-level authorization backstops; model prompts and in-memory filters do not enforce RLS.
- Do not close an isolation blocker after fixing only one path.
- Preserve offline capability and controlled cloud egress.

Apply these rules conditionally from workspace evidence; do not invent BRAVO-specific modules in unrelated repositories.

## Close and hand off

1. Confirm the source of truth and update operational documentation when behavior changed.
2. Mark superseded plans clearly without deleting audit-worthy artifacts.
3. Record final changes, verification evidence, unresolved risks, and the next ready issue.
4. Use [references/handoff-template.md](references/handoff-template.md) when a fresh context must continue the work.
5. Keep the handoff minimal; do not copy the full conversation.

Report the outcome first. Include files changed, verification results, unrun checks, residual risks, and any user action still required.

