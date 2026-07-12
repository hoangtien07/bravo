"""Tool inventory & least-privilege audit gate (OWASP LLM06 Excessive Agency, Findings O #8).

Excessive agency comes from too much *functionality*, too many *permissions*, or too much
*autonomy*. bravo already enforces the mechanics in `call_tool` (RLS re-check, write->draft,
on-behalf-of identity injection). This module makes the CONTRACT explicit and *auditable*:

  - describe_registry() -> a flat inventory (for docs / monitoring / review).
  - audit_registry()    -> least-privilege violations; empty list = clean.
  - main()              -> prints inventory + audit, exits non-zero on violation (CI gate,
                           same spirit as agent-ai handover_check exit-code).

The audit is intentionally a *static* check over the tool registry — it never executes a
tool. Wire it into CI so a newly-registered tool that grants itself excessive agency
(anonymous write, unvalidated write payload) fails the build instead of shipping.
"""
from __future__ import annotations

import inspect
from dataclasses import dataclass, field

from app.agent.tools import Tool


@dataclass
class InventoryRow:
    name: str
    mode: str                    # "read" | "write->draft"
    required_permission: str | None
    validated: bool              # write tools: has a payload_builder gate
    requires_approval: bool
    on_behalf_of: bool           # runs under the CALLER identity (never a tool-owned one)


@dataclass
class AuditReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return not self.errors


def describe_registry(registry: dict[str, Tool]) -> list[InventoryRow]:
    """Flat, sorted inventory of every registered tool (for docs/monitoring/review)."""
    rows = [
        InventoryRow(
            name=t.name,
            mode="read" if t.read_only else "write->draft",
            required_permission=t.required_permission,
            validated=t.payload_builder is not None,
            requires_approval=t.requires_approval,
            # bravo tools never carry their own identity: call_tool injects the caller's
            # identity, and the json_schema never exposes identity/db, so the LLM cannot
            # escalate. Every tool therefore acts strictly on-behalf-of the caller.
            on_behalf_of=True,
        )
        for t in registry.values()
    ]
    return sorted(rows, key=lambda r: r.name)


def audit_registry(registry: dict[str, Tool]) -> AuditReport:
    """Least-privilege audit. Errors block (CI gate); warnings are advisory."""
    report = AuditReport()
    for t in registry.values():
        # 1. No anonymous writes: a write tool MUST gate on an explicit permission.
        if not t.read_only and not t.required_permission:
            report.errors.append(
                f"{t.name}: write tool without required_permission (anonymous write)")
        # 2. Writes must be approval-gated (invariant #2). __post_init__ enforces this;
        #    audit catches any object built bypassing the constructor.
        if not t.read_only and not t.requires_approval:
            report.errors.append(
                f"{t.name}: write tool not marked requires_approval (would auto-execute)")
        # 3. Writes must VALIDATE their payload before drafting (number-integrity/statutory
        #    gate). An unvalidated write draft can carry hallucinated numbers (invariant #3).
        if not t.read_only and t.payload_builder is None:
            report.errors.append(
                f"{t.name}: write tool without payload_builder (unvalidated draft payload)")
        # 4. Permission strings must be `resource:action[:scope]` so Identity.scope_level can
        #    parse them; a malformed permission silently denies/opens.
        perm = t.required_permission
        if perm is not None and ":" not in perm:
            report.warnings.append(
                f"{t.name}: required_permission '{perm}' is not 'resource:action' shaped")
        # 5. T3-lite: a read tool OPEN to everyone (no required_permission) MUST consume the caller
        #    `identity` so it can RLS-filter in-query; a read tool that ignores identity can leak
        #    across tenants silently (call_tool only INJECTS identity to fns that declare it).
        if t.read_only and t.required_permission is None:
            try:
                params = inspect.signature(t.fn).parameters
            except (TypeError, ValueError):
                params = {}
            if "identity" not in params:
                report.errors.append(
                    f"{t.name}: open read tool without an `identity` param (may bypass RLS)")
    return report


def main() -> int:
    from app.agent.loop import _register_builtin_tools
    from app.agent.tools import REGISTRY

    _register_builtin_tools()
    rows = describe_registry(REGISTRY)
    print("BRAVO tool inventory:")
    for r in rows:
        val = "validated" if r.validated else ("-" if r.mode == "read" else "UNVALIDATED")
        print(f"  {r.name:22} {r.mode:13} perm={str(r.required_permission):16} {val}")
    report = audit_registry(REGISTRY)
    for w in report.warnings:
        print("WARN:", w)
    for e in report.errors:
        print("ERROR:", e)
    print("least-privilege audit:", "PASS" if report.clean else "FAIL")
    return 0 if report.clean else 1


if __name__ == "__main__":
    raise SystemExit(main())
