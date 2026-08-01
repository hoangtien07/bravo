# V2 contract-first design/dev handoff

Status: `READ BEFORE EDITING ACCOUNTING WORK SCREENS`

The current prototype is not the source of business behavior. The canonical handoff is
`../plan-rebuild/14-CONTRACT-FIRST-FIGMAMAKE-HANDOFF.md` from the repository root.

## What design may do now

- Design the Accounting Work shell, inbox, case dossier and responsive states.
- Use the Bank read-only conversation, evidence and finding payloads described in the canonical
  handoff.
- Prepare rendering for synthetic, missing, stale, superseded, abstained, denied and conflict
  states.

## What design must not invent

- Voucher posting, bank connectivity, BRAVO execution, close calculation/report/lock, or an
  approval bypass.
- API fields, state transitions or role permissions that are absent from the backend handoff.
- Claims that a fixture is verified, production data or a completed user/SME evaluation.

## Integration rule

`frontend-react` consumes the real API. This Figma Make project provides visual/interaction
direction only until the case contract is frozen and an example payload plus contract test exists.
For Voucher and Period Close, keep screens in policy/fixture preparation state until their shared
case/API contracts are supplied.
