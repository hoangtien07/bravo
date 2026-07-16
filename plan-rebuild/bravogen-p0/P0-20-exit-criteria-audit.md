# P0-20 — R0 exit-criteria audit

Status: `PASS — collection gate`

| Criterion | Evidence | Status |
|---|---|---|
| All three visible modes exercised | P0-02, P0-12…P0-19; User Guide, Insight, ISMS | PASS |
| At least 30 independent tests | 34 prior cases + valid Wave 7/8 controls (invalid concurrent records excluded) | PASS |
| At least 10 cross-mode controls | P0-18 plus P0-21 strict closure: five identical anchors × three modes = 15 additional valid observations | PASS |
| At least 5 fabricated-entity tests | T01.2, T04.1/T04.3/T04.4, T06.4, T08.4 and repeats | PASS |
| At least 5 citation audits | P0-05, P0-17, T05.2/T11.2 audits | PASS |
| At least 3 graph traversal tests | T06.1–T06.4 plus completed independent T06.1 repeat in P0-19/P0-21 | PASS |
| At least 3 multi-turn/context sequences | T13.1–T13.4 plus P0-19 memory mutation | PASS |
| Important tests have independent repetition | T01.2 completed in Insight/User Guide/ISMS repeats; T04.3, T08.1, T06.1 and memory mutation independently repeated | PASS |
| Findings carry evidence labels | OBSERVED / INFERRED / UNVERIFIED / PLAUSIBLE-UNVERIFIED used throughout | PASS |
| No customer data, scripts, mutations or credentials stored | Scope notes in P0-00/P0-11; only synthetic prompts sent | PASS |

## Gate decision

R0 black-box collection is complete. Proceed to the next phase only as a rebuild-design decision based on this evidence. Do not claim that BravoGen uses GraphRAG, ticket self-learning, a workflow engine, or enforceable authorization unless separately demonstrated.

## Availability notes

Earlier quota and server-error attempts are retained as excluded attempts, not converted into model-quality wins or failures. Both required Insight repeats were subsequently completed in new conversations. P0-21 also closes the fifth strict cross-mode anchor at 15/15 observations.
