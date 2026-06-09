"""Tool registry & approval (findings/J HITL). Phase 2.

Read tools run automatically. WRITE tools set requires_approval -> produce a Draft
(pinned by payload hash) for human approval; the agent never auto-executes a write.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class Tool:
    name: str
    fn: Callable
    requires_approval: bool = False  # write tools -> True (non-invasive, ADR + VISION §2)


REGISTRY: dict[str, Tool] = {}


def register(name: str, *, requires_approval: bool = False):
    def deco(fn: Callable) -> Callable:
        REGISTRY[name] = Tool(name=name, fn=fn, requires_approval=requires_approval)
        return fn
    return deco


def payload_hash(payload: dict) -> str:
    """Pin args by hash (findings/J anti-drift): reject execution if hash changed."""
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
