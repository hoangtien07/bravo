# V2 external-gate execution packet

Status: `READY FOR AUTHORIZED EXECUTION — NO EXTERNAL GATE HAS PASSED`

Date: 2026-08-02

## Purpose and council decision

This packet continues the accepted synthetic three-case plan after the developer delivery. It
turns the remaining external gates into reviewable inputs and evidence outputs; it does not grant
authority to run them, select a model, inspect secrets, or use customer data.

| Option considered | Decision | Reason |
|---|---|---|
| Mark the plan complete from developer tests | Rejected | Structural, synthetic tests do not prove runtime containment, model quality, SME truth, or user-time benefit. |
| Invent a model pin, reviewer truth, or runtime-role result | Rejected | That would simulate authority/evidence and violate the accepted V2 gates. |
| Prepare a bounded execution packet and hold each gate open until its owner supplies evidence | **Selected** | Preserves the developer result while making the next authorized work reproducible and auditable. |

The source baseline for this packet is commit `8b0a7ec86709cab06ce1d4f586bc330cb6a461c1` and
Alembic head `0019_case_v2_defaults`. The inaccessible untracked `.tmp-pytest/` artifact is
outside this baseline and is recorded in `evidence/v2/V2-DEVELOPER-TRACK-STATUS.md`.

## Accurate delivery boundary

| Work package | Current evidence | Not yet satisfied |
|---|---|---|
| WP-02–04 Bank core, deterministic checks and durable API | Implemented and synthetic HTTP/native-RLS tested | Non-owner runtime cutover and quality verdict |
| WP-05 Bank reasoning/evaluation | Deterministic, read-only explanation exists | Owner-pinned model adapter, frozen matched A/B/C/D run, blind quality gate |
| WP-06 Bank UX | Contract-first FigmaMake and `frontend-react` synthetic workflow controls exist | Human usability/accessibility acceptance beyond automated checks |
| WP-07 Voucher Review | Typed deterministic **preview** exists | Approved policy/fixture truth, durable case/review/export lifecycle, held-out evaluation |
| WP-08 Period Close Readiness | Typed deterministic **preview** exists | Approved policy/fixture truth, durable handoff/export lifecycle, held-out evaluation |
| WP-09 configuration | Synthetic manifest and capability backstops exist | Owner-pinned model/egress decision and the non-functional Governance mock acceptance |
| WP-10 integration/release evidence | Focused backend/frontend checks and isolated durable DB proof exist | A/B/C/D, blind SME, manual baseline, full operational proof and release result |

Therefore the developer implementation must be called a **synthetic demonstrator scaffold**, not a
complete V2 quality/release plan. The previews are intentionally not promoted to durable workflows
until their policies and golden truth are approved.

## Gate 1 — operator: non-owner runtime containment

**Authority:** database/runtime/secrets operator in an approved isolated synthetic environment.

**Inputs:** a maintenance window; separate API/MCP, worker, migrator, backup and break-glass roles;
secret-manager injection; no credentials committed or pasted into this repository.

**Procedure:**

1. Provision the NOLOGIN role design in `deploy/runtime-roles.sql`; attach LOGIN credentials only
   through the approved secret manager.
2. Use `deploy/docker-compose.rls-cutover.yml` to run API/MCP as the non-owner role and worker as
   its separately reviewed role. The owner/migrator DSN must not reach these processes.
3. Arm only reviewed RLS surfaces and run the read-only preflight:
   `NATIVE_RLS_ENABLED=true python scripts/verify_native_rls_cutover.py`.
4. Run two-user/two-department negative probes through real HTTP, MCP and worker entry points;
   verify own-department and global access still work, while cross-department access is absent.
5. Run the approved isolated backup/restore and offline/egress drill. Exercise rollback before
   admitting traffic.

**Evidence to retain (redacted):** effective Compose digest; role/catalog query result proving
`NOSUPERUSER` and `NOBYPASSRLS`; policy/force state; command/version/time; probe IDs and expected
versus actual status; restore RTO; rollback result; operator identity/approval reference. Do not
retain DSNs, passwords, bearer tokens, raw customer data or raw MCP transcripts.

**Pass criterion:** all three runtime paths reject the cross-scope probe and retain the authorized
own/global path, with a non-owner role and armed policies. A direct SQL test or local owner-role
database is not a substitute.

## Gate 2 — owner: model/version and synthetic evaluation run

**Authority:** named product/model owner, with security/egress approval when any remote provider is
involved.

**Decision record (metadata only):** provider; model family and immutable version/revision;
deployment class (offline or approved synthetic-only egress); region/retention class; prompt,
routing and retrieval configuration hashes; fixture and evidence-snapshot hashes; token/cost/latency
budget; approval reference and expiry. No endpoint credential belongs in the record.

**Required sequence:**

1. Keep `model_egress_policy: deny_until_owner_pins_model` until the decision record is approved.
2. Bind the approved metadata to a versioned synthetic manifest and a narrow `ReasoningPort`
   adapter. It may explain, ask one high-information question, offer a reviewer-selectable mapping
   candidate, narrate or abstain; it cannot change checks, amounts, state, review or export.
3. Freeze matching A/B/C/D anchors and run configuration using the existing baseline tooling. Do
   not overwrite `evidence/v2/ab/wp00-20260731/`.
4. Record hashes and run IDs, then hand blinded outputs to SME reviewers. A changed model/version,
   prompt, retrieval setting, fixture or evidence snapshot starts a new run.

**Pass criterion:** a reproducible synthetic-only run has an owner-approved immutable model/config
record and no unapproved egress. This enables evaluation; it is not a quality pass by itself.

## Gate 3 — SMEs and user-time baseline

**Authority:** two independent, qualified reviewers for Bank reconciliation; owner-approved SMEs
for Voucher and Period policies; representative synthetic-task participants for the manual baseline.

**Inputs:** the sealed held-out answer key remains outside the implementation worktree; blinded
outputs; the rubric/aggregation contract in `app/eval/consultant_sme_review.py`; the WP-01
attestation template; a predefined manual timing/edit protocol.

**Procedure:**

1. Calibrate both Bank reviewers on the agreed anchors and record only reviewer IDs/roles,
   calibration outcome and fixture/policy/held-out hashes.
2. Score randomized, blinded A/B/C/D outputs. Run the aggregator without supplying answer text to
   the repository.
3. Measure manual reviewer time and material edits on the same synthetic cases. Report the Bank
   OD-09 metrics separately from secondary-case observations.
4. Before promoting Voucher/Period previews, approve each policy, golden set and sealed held-out
   manifest; then implement and assess its full bounded lifecycle.

**Pass criterion:** independent evidence satisfies the frozen rubric, hard-failure rules and
OD-09 thresholds. A developer or model self-score is invalid.

## Admission and stop rules

- No real BRAVO database, posting, payment, period lock, automatic approval or customer data is
  authorized by this packet.
- Missing authority, evidence or a failed preflight records the affected gate as `BLOCKED` or
  `FAILED`; it never becomes an inferred pass.
- A model/config/fixture change after freeze invalidates only its dependent evaluation run, not the
  immutable historical baseline.
- A cross-scope, egress, fabricated-execution or critical-truth failure stops promotion and
  triggers rollback/narrowing before further UI or capability expansion.

## Completion evidence index

Only after Gate 1, Gate 2 and Gate 3 have evidence may the owner decide whether to execute the
remaining WP-05, WP-07, WP-08 and WP-10 exits. The final evidence index must name the exact
baseline commit, model/config hashes, fixture hashes, runtime probe reports, blind-review report,
manual-baseline metrics, failure clusters and rollback decision. It must still state that the
result is a synthetic demonstrator, not a pilot or production authorization.
