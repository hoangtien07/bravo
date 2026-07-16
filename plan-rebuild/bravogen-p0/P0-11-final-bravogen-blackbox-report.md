# P0-11 — Final BravoGen black-box report

Status: `R0 COMPLETE — strict cross-mode and repeat closure verified`

## A. Executive summary

Six waves of permitted, synthetic, read-only conversations were completed across the three visible modes: Bravo Insight, Bravo User Guide and ISMS Advisor. The sample contains 34 independent case executions, four graph-oriented probes, multiple fabricated-entity probes, four same-thread memory/context probes and live inspection of three emitted source URLs.

The strongest observed differentiator is not a proven model or framework. It is a behavior bundle: mode-scoped answer contracts, domain-aware prerequisite linking, clarification before risky troubleshooting, explicit no-result abstention, workflow-safe refusal, and context-slot tracking. BravoGen sometimes gives a useful answer even when the citation is broad or unavailable; conversely, a citation-shaped answer is not automatically claim-level proof.

## B. Behavioral architecture hypotheses

Observed behavior is consistent with some combination of mode/profile routing, document and/or graph-like retrieval, response templates for procedure/troubleshooting/policy/self-audit, a context-slot representation, and safety policy gates. These are behavioral hypotheses only. The runs do **not** prove GraphRAG, a graph database, self-learning from tickets, tool calling, multi-agent orchestration, a workflow engine or any specific foundation model.

## C. Mode-by-mode assessment

| Mode | Observed strengths | Observed limits |
|---|---|---|
| Bravo User Guide | Best procedural/domain linkage: procurement sequence, prerequisites, read-only next steps, context-slot questions | Source labels can be broad (`Knowledge Graph - Bravo 10`, `knowledge_graph`); exact schema and claim-level provenance often absent |
| Bravo Insight | Technical clarification, ranked hypotheses and accounting prerequisite reasoning; rejects fabricated XML/schema entities | Some “tra cứu/knowledge graph” claims have no exposed trace; page-level citations may not support every generated detail |
| ISMS Advisor | Strong refusal/approval routing, policy self-audit and correction of malformed/misapplied citations | Must not be treated as proof of policy truth until the cited document section is opened and matched |

## D. Retrieval and reasoning assessment

- T01.6 connected financial statements to posting, COGS, depreciation/allocation, AR/AP reconciliation, FX revaluation, closing and trial-balance checks.
- T06.1–T06.3 produced graph-like relationship output; T06.4 produced a clean `no-result` for a fabricated graph query.
- T08.3 asks diagnostic questions; T08.4 ranks hypotheses and limits itself to read-only checks.
- A useful answer can still be `plausible-unverified` when the source is broad or the citation is not claim-level. Use usefulness and verification as separate scores.

## E. Citation assessment

Live audit in `P0-17-live-citation-audit.md` found:

- `NB_QT27K.09`, page 3: `VALID_FULL` for the quoted monthly-backup retention sentence.
- `NB_QT.01`, page 3: `VALID_PARTIAL` for document-control scope; the cited role sequence requires additional pages.
- `Chapter17_Accounting`, page 84: `VALID_PARTIAL`; the page and section exist, but visible text did not prove the entire generated accounting sequence.

T05.2 detected that a previous `NB_QT27K.15` citation was misapplied and that non-HTTP citation anchors were malformed. This demonstrates self-audit behavior, not automatic correctness of replacement links.

## F. Knowledge Graph assessment

Graph-like observations include forward traversal (PO → NM → payment), reverse traversal from invoice/NM, direct vs inferred labels with confidence values, and a no-result branch. The correct P0 conclusion is “graph-backed behavior is plausible and useful to reproduce,” not “BravoGen uses GraphRAG.” Provenance, node/edge stability and query semantics remain open.

## G. Hallucination and abstention

- Fabricated XML attributes, fake procedure codes and fake graph entities were rejected or returned no-result in the tested prompts.
- Strong abstentions named missing data and a safe next step; T04.3 replaced a fake policy code with a current procedure and an auditable URL.
- Unsupported inference remains possible; most domain expansions therefore remain `plausible-unverified`.

## H. Security and permission behavior

For synthetic payroll/database requests, BravoGen refused direct SQL or production change, described integrity/confidentiality/audit risks, and routed to draft → review → approval → DBA execution with staging/synthetic data. These are observed safety behaviors, not evidence of a real authorization engine.

## I. Consistency and memory

- Same-thread context retained version, platform, environment and goal, then requested missing workflow/type/approval/inventory slots.
- A WinApp → WebApp mutation preserved unchanged slots and adapted UI guidance.
- T05.2 referenced and audited the immediately prior answer.
- Durable memory across a new conversation, persistence policy and server-side storage are unverified.

## J. Evidence table

| Finding ID | Finding | Type | Supporting tests | Confidence |
|---|---|---|---|---|
| F-001 | Mode-scoped behavior is visible | OBSERVED | T01.2, T04.1, T11.1, T13.1 | High |
| F-002 | Domain prerequisite linking improves usefulness | OBSERVED | T01.5, T01.6, T03.3, T06.1–T06.3, T13.3 | Medium-high |
| F-003 | Fabricated entities can be rejected/no-result | OBSERVED | T01.2, T04.1, T04.4, T06.4, T08.4 | Medium-high |
| F-004 | Citation quality is mixed, including valid partial/full cases | OBSERVED | T04.3, T05.2, T01.6, T11.2; P0-17 | High |
| F-005 | Sensitive action requests route to approval-safe alternatives | OBSERVED | T11.1, T11.2, T12.1 | High |
| F-006 | Context slots can be retained and selectively mutated | OBSERVED | T13.1–T13.4, T05.2 | Medium |
| F-007 | Graph-backed implementation is not proven | INFERRED/UNVERIFIED | T06.1–T06.4, T13.3 | High that implementation is unknown |

## K. R0 collection gate

`P0-20-exit-criteria-audit.md` records a PASS for the black-box collection gate. P0-21 adds a strict closure set of five identical anchors across all three modes (15/15 valid observations) and closes the two required Insight repeats in independent conversations. Together with the 34+ prior cases, fabricated-entity/no-result tests, citation audits, graph traversals and multi-turn sequences, R0 now has no outstanding collection gap. This is a collection pass, not proof of BravoGen internal implementation.

## L. Open questions

See `P0-10-open-questions.md`. The most important unresolved items are whether modes select different corpora/tools or primarily policies/templates; whether graph provenance is stable and document-backed; whether retrieval/tool traces are observable; how version conflicts are handled; whether memory persists across conversations; and whether safety gates correspond to enforceable permissions.

## Scope boundary

This report records evidence for the rebuild decision and does not propose an internal BravoGen architecture. It does not store tokens, cookies or customer data, and no scripts or customer databases were executed or modified.
