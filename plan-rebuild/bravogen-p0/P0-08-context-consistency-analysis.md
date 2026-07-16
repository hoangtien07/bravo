# P0-08 — Context and consistency analysis

Status: `COMPLETE FOR SAME-THREAD SAMPLE — durable memory unverified`

Theo dõi coreference, topic shift, correction, branch, stop/continue, answer/citation/entity/relation/refusal stability.

| Finding ID | Finding | Type | Supporting tests | Counter-evidence | Confidence |
|---|---|---|---|---|---|
## Wave 4–5 memory sequence

Sequence M-001 (T13.1→T13.2, User Guide): turn 1 established purchasing-analysis intent with missing version/environment; turn 2 added v10.2, WinApp and SQL Server test environment. BravoGen retained all supplied context, separated known vs missing workflow/type/approval/inventory slots and suggested read-only next steps. This is observed conversational behavior; durable server-side memory remains unverified.

Sequence M-002 (T13.3, User Guide): a single-turn synthetic/no-change context was retained while the assistant expanded the purchasing graph sequence. No cross-conversation persistence was tested.

Sequence M-003 (T13.4, User Guide): the platform slot changed from WinApp to WebApp while v10.2, SQL Server test and purchasing-analysis goal remained stable. BravoGen explicitly identified the changed slot and adapted UI guidance. This is observed conversational behavior; it does not prove a durable memory store.

Sequence M-004 (T05.2, ISMS Advisor): the assistant referenced and audited its immediately previous payroll-SQL answer, including correcting a misapplied policy and malformed links. This demonstrates same-thread self-reference, not long-term memory.
