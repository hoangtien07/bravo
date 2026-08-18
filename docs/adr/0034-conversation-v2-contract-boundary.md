# 0034. Knowledge Chat Conversation Core V2 contract boundary

- **Status:** Accepted — design-only; implementation remains subject to the WP19 fixture and A/B
  baseline gates.
- **Date:** 2026-08-18
- **Scope:** Knowledge Chat and shared Conversation Core V2 contracts only.
- **Depends on:** Plan 19, ADR-0032 and ADR-0033.
- **Supersedes:** none.

## Context

Plan 19 confirms that the legacy Knowledge Chat path can lose task coverage, incorrectly classify
ordinary Vietnamese `bằng` as a technical database request, hard-exclude required guide sources,
and release free-form answers without typed work-product or claim contracts. The completed
`app/core_v2` accounting-case package does not itself replace normal chat.

The remediation must retain the trusted platform shell — authorization/RLS, retrieval, audit,
draft/approval and durable state — while preventing framework/runtime objects from becoming
Conversation Core domain truth. It must not reopen the separately governed Accounting Operations
Hub scope, enable a new model path, or broaden the legacy loop.

## Decision

After the WP19 fixture review, add `app/conversation_v2/` as a framework-independent package with
domain contracts and ports only. The package must not import FastAPI, SSE types, SQLAlchemy models,
database clients, LLM SDKs or provider response objects.

The initial contracts are:

- `TurnEnvelope`: immutable raw input, attachment references, authorization/scope references,
  locale and conversation revision.
- `TaskUnit`: stable id, ordinal, original span, task type, entities, amounts, assumptions,
  requested output and coverage status. Every explicit top-level task has one result state.
- `EvidencePlan` and `EvidenceRef`: source queries/classes, authority/version/scope constraints,
  fallback policy, locator and supported claim types.
- `AccountingWorkProduct`: read-only postings, VAT/settlement calculations, assumptions and
  deterministic rule/calculation lineage. It is not an ERP command.
- `Claim`, `AnswerPlan` and `VerificationResult`: exact value/text, claim type, evidence or
  calculation references, unsupported reason, task coverage, authority and must-not-claim result.
- `ExecutionTrace`: privacy-minimized stage hashes/references, alternatives, timings, model/runtime
  identity, usage, tool outcomes and verifier decisions. It must not persist raw sensitive prompts
  solely for traceability.

Inbound ports provide evidence retrieval, deterministic read-only calculation, canonical state,
authorization and audit. Outbound adapters own API/SSE rendering, persistence, provider calls and
retrieval implementation. The shared verifier is mandatory before any final sync, SSE, offline or
frontier answer segment is released; progress events remain permissible before verification.

## Consequences

- The initial code change is limited to the boundary-safe legacy router containment and its test;
  no prompt/model migration, deterministic engine, endpoint cutover or frontend rewrite follows
  from this ADR.
- The Plan 19 ten-transaction fixture remains review-gated. Its hashes and status are evidence,
  not an SME-quality pass or authorization to post accounting entries.
- Existing `app/core_v2` is reusable only through explicit contracts where semantics match. This
  ADR does not merge Knowledge Chat with an `AccountingCase` lifecycle.
- A later implementation ADR or accepted amendment must define the API adapter, persistence schema,
  full verification behavior and rollout criteria after the frozen fixture and A/B baseline gates
  have been reviewed.
