"""Tool registry, RLS-filtering & approval (findings/J HITL; CONTRACTS §2.2). Phase 2 / WP-D.

Read tools run automatically. WRITE tools (`read_only=False`) NEVER execute — they produce a
Draft (pinned by payload hash) for human approval (invariant #2, non-invasive).

RLS is enforced TWICE (defense-in-depth, invariant #1):
  1. `filter_tools_by_permission` — a tool the identity lacks `required_permission` for is
     never even put in the prompt the LLM sees (it cannot pick what it cannot see).
  2. `call_tool` — re-checks the permission at execution time, so a forged/replayed tool name
     is still blocked. Errors are returned as `{"isError": True, ...}` (never raised) so the
     agent loop stays alive and can clarify/abstain instead of crashing.
"""
from __future__ import annotations

import hashlib
import inspect
import json
from collections.abc import Callable
from dataclasses import dataclass, field

from app.security.rls import Identity


@dataclass
class Tool:
    name: str
    fn: Callable                       # async or sync
    json_schema: dict = field(default_factory=dict)  # JSON Schema cho input (structured-output)
    read_only: bool = True             # đọc = auto-run; ghi = False -> draft
    requires_approval: bool = False    # ghi -> True (HITL, ADR + VISION §2)
    required_permission: str | None = None  # vd "metric:read"; None = ai cũng gọi được

    def __post_init__(self) -> None:
        # Write tools must go through approval — keep the two flags consistent so a
        # mis-registered write tool can never silently auto-execute (invariant #2).
        if not self.read_only:
            self.requires_approval = True


REGISTRY: dict[str, Tool] = {}


def register(name: str, *, json_schema: dict | None = None, read_only: bool = True,
             requires_approval: bool = False, required_permission: str | None = None):
    def deco(fn: Callable) -> Callable:
        REGISTRY[name] = Tool(
            name=name, fn=fn, json_schema=json_schema or {},
            read_only=read_only, requires_approval=requires_approval,
            required_permission=required_permission,
        )
        return fn
    return deco


def _has_permission(identity: Identity, perm: str | None) -> bool:
    """A tool with no `required_permission` is open to anyone. Admin bypasses everything."""
    if perm is None:
        return True
    if identity.is_admin:
        return True
    return perm in identity.permissions


def filter_tools_by_permission(registry: dict[str, Tool], identity: Identity) -> list[Tool]:
    """RLS layer #1: tools the identity may NOT use are removed before the prompt is built.

    The LLM never sees a tool it lacks permission for, so it cannot select it (CONTRACTS §3,
    invariant #1). `call_tool` re-checks (layer #2) for defense-in-depth.
    """
    return [t for t in registry.values() if _has_permission(identity, t.required_permission)]


async def _audit_attempt(db, agent_run_id, identity: Identity, name: str, args: dict,
                         status: str, summary: str | None = None) -> None:
    """Ghi 1 dòng tool_call_attempts (best-effort — db None/giả ở unit-test -> bỏ qua)."""
    if db is None:
        return
    try:
        from app.database.models import ToolCallAttempt
        db.add(ToolCallAttempt(
            agent_run_id=agent_run_id,
            actor_id=getattr(identity, "employee_id", None),
            tool=name, args_hash=payload_hash(args or {}),
            status=status, summary=(summary or "")[:500]))
        await db.commit()
    except Exception:
        pass


async def call_tool(name: str, args: dict, identity: Identity, *, db=None,
                    agent_run_id=None) -> dict:
    """Execute a tool with RLS re-check (layer #2) + HITL.

    Contract (CONTRACTS §3.1): returns a dict; NEVER raises (returns `{"isError": True,...}`
    so the loop survives). Write tools (`read_only=False`) create a Draft and DO NOT execute
    (invariant #2 — zero direct writes). Mọi lần gọi được ghi tool_call_attempts (Tầng 3b).
    """
    tool = REGISTRY.get(name)
    if tool is None:
        return {"isError": True, "error": f"Tool không tồn tại: {name}"}

    # RLS layer #2 — re-check even though filter_tools_by_permission already ran.
    if not _has_permission(identity, tool.required_permission):
        await _audit_attempt(db, agent_run_id, identity, name, args, "failed", "no permission")
        return {"isError": True, "error": f"Không đủ quyền dùng tool: {name}",
                "required_permission": tool.required_permission}

    # Write path: never execute — produce a draft for human approval (invariant #2).
    if not tool.read_only:
        if db is None:
            return {"isError": True, "error": "Tool ghi cần db để tạo draft (không tự thực thi)."}
        from app.erp import draft_queue
        try:
            draft = await draft_queue.create_draft(
                db, identity, kind=name, payload=args, agent_run_id=agent_run_id)
        except TypeError:
            # Stub/real create_draft signature drift (WP-E): fall back without agent_run_id.
            draft = await draft_queue.create_draft(db, identity, kind=name, payload=args)
        await _audit_attempt(db, agent_run_id, identity, name, args, "drafted", f"draft {draft.id}")
        return {"status": "pending_approval", "draft_id": str(draft.id), "is_write": True,
                "message": "Đã tạo bản nháp chờ người duyệt (KHÔNG tự thực thi)."}

    # Read path: execute deterministically. Inject identity/db for tools that need them
    # (e.g. metric_lookup -> semantic.execute applies RLS at the data tier). We only pass
    # what the fn declares, so plain tools keep `fn(**args)`. LLM args can't override these
    # (the tool json_schema never exposes identity/db).
    try:
        params = inspect.signature(tool.fn).parameters
        kw = dict(args)
        if "identity" in params:
            kw["identity"] = identity
        if "db" in params:
            kw["db"] = db
        result = tool.fn(**kw)
        if inspect.isawaitable(result):
            result = await result
        await _audit_attempt(db, agent_run_id, identity, name, args, "executed")
        return {"status": "ok", "result": result}
    except Exception as e:  # keep the loop alive — surface as isError, don't crash the turn
        await _audit_attempt(db, agent_run_id, identity, name, args, "failed", str(e))
        return {"isError": True, "error": f"Tool '{name}' lỗi: {e}"}


def payload_hash(payload: dict) -> str:
    """Pin args by hash (findings/J anti-drift): reject execution if hash changed."""
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
