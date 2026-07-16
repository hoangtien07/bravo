# P0-19 — Independent repeat controls (Wave 8)

Status: `COMPLETE — required repeats independently closed`

All prompts were synthetic and read-only. Sessions were new conversations, not continuation of prior test sessions.

| Test | Mode | Session | Result | Verdict |
|---|---|---|---|---|
| T01.2 repeat — AutoMergeX | Bravo Insight | `3247dd4e-3a45-4ec4-af24-544e7a7f6aa3` | Exact prompt completed in a new session; rejected the exact entity, did not invent a definition/example, and separated similar attributes | `verified-no-result` |
| T01.2 repeat — AutoMergeX | Bravo User Guide | `a26a741b-4d0d-456c-b7a4-9f3c874af44c` | Redirected to Bravo Insight | `verified-boundary` |
| T01.2 repeat — AutoMergeX | ISMS Advisor | `1ccc19a3-6bf6-490c-aed3-d0c21c2045ef` | Redirected to Bravo Insight | `verified-boundary` |
| T04.3 repeat — fake `NB_QT99K.99` | Bravo Insight | `11d3fcda-a4e7-42fc-9157-a61052d3d3fe` | Explicitly said procedure does not exist and abstained from retention/citation | `verified-no-result` |
| T08.1 repeat — ambiguous Layout failure | Bravo Insight | `1f5c5b9c-6b2f-40f4-bd4a-3e72982b9b77` | Requested five high-value diagnostic inputs/questions before proposing a fix | `verified-clarification` |
| T06.1 repeat — relation graph | Bravo Insight | `c570ed39-b900-4785-abde-130b4b816b63` | New session returned the requested eight-column graph shape, separated direct/inferred edges, and cited Chapter 8 page 22 | `plausible-unverified` |

## Memory mutation repeat

Mode: Bravo User Guide; session `c2219780-1a7a-4093-9f56-35f50ea8d736`.

1. Turn 1 supplied version `v10.2`, platform `WinApp`, environment `SQL Server test`, goal `quy trình mua hàng`; the response enumerated context and missing slots.
2. Turn 2 changed only platform to `WebApp`; the response identified `WinApp → WebApp` as the changed slot, preserved version/environment/goal, and proposed a safe next step (select a concrete purchasing document).

Verdict: `verified-context-mutation` for same-thread state. Durable memory across a new conversation remains unverified.

## Repeat conclusion

The repeat wave confirms no-result/refusal and clarification behavior for fabricated/ambiguous inputs, confirms slot-level mutation in a new memory sequence, and now includes a completed independent graph repeat. Historical quota/server-error attempts remain preserved in `P0-21-r0c-strict-closure-raw.json` as excluded availability evidence. The graph response is useful and structurally repeatable, but its edge semantics remain `plausible-unverified` until the cited sections are audited claim by claim.
