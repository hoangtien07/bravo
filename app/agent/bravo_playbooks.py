"""Lifecycle playbooks for BRAVO copilot modes.

The YAML file is data owned by the BRAVO domain team. This module only validates and
renders a short hint for the agent prompt.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.rag.bravo_intent import infer_query_intent
from app.utils.yaml_compat import safe_load_file

DEFAULT_PLAYBOOK_PATH = Path("file_system/bravo_lifecycle_playbooks.yaml")


@dataclass(frozen=True)
class BravoPlaybook:
    mode: str
    usp: str
    lifecycle_stage: str
    users: tuple[str, ...] = ()
    preferred_source_types: tuple[str, ...] = ()
    triggers: tuple[str, ...] = ()
    required_outputs: tuple[str, ...] = ()
    guardrails: tuple[str, ...] = ()
    value_metrics: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, raw: dict) -> "BravoPlaybook":
        required = ("mode", "usp", "lifecycle_stage")
        missing = [k for k in required if not raw.get(k)]
        if missing:
            raise ValueError(f"playbook missing required fields: {missing}")
        return cls(
            mode=str(raw["mode"]),
            usp=str(raw["usp"]),
            lifecycle_stage=str(raw["lifecycle_stage"]),
            users=tuple(raw.get("users") or ()),
            preferred_source_types=tuple(raw.get("preferred_source_types") or ()),
            triggers=tuple(raw.get("triggers") or ()),
            required_outputs=tuple(raw.get("required_outputs") or ()),
            guardrails=tuple(raw.get("guardrails") or ()),
            value_metrics=tuple(raw.get("value_metrics") or ()),
        )


def _load_yaml(path: Path) -> dict:
    return safe_load_file(path) or {}


@lru_cache(maxsize=4)
def load_playbooks(path: str = str(DEFAULT_PLAYBOOK_PATH)) -> tuple[BravoPlaybook, ...]:
    p = Path(path)
    raw = _load_yaml(p)
    items = raw.get("playbooks") or []
    if not isinstance(items, list):
        raise ValueError("playbooks must be a YAML list")
    playbooks = tuple(BravoPlaybook.from_dict(item) for item in items)
    modes = [p.mode for p in playbooks]
    dupes = sorted({m for m in modes if modes.count(m) > 1})
    if dupes:
        raise ValueError(f"duplicate playbook modes: {dupes}")
    return playbooks


def select_playbooks(query: str, *, path: str = str(DEFAULT_PLAYBOOK_PATH)) -> tuple[BravoPlaybook, ...]:
    intent = infer_query_intent(query)
    playbooks = load_playbooks(path)
    q = query.lower()

    scored: list[tuple[float, BravoPlaybook]] = []
    for pb in playbooks:
        score = 0.0
        if intent.lifecycle_stage and pb.lifecycle_stage == intent.lifecycle_stage:
            score += 3.0
        score += len(set(intent.source_types) & set(pb.preferred_source_types)) * 1.0
        score += sum(0.5 for trig in pb.triggers if trig.lower() in q)
        if pb.mode == "voucher_assistant" and "purchase" in intent.modules:
            score += 0.5
        if score > 0:
            scored.append((score, pb))

    scored.sort(key=lambda item: item[0], reverse=True)
    return tuple(pb for _score, pb in scored[:2])


def render_playbook_hint(query: str, *, path: str = str(DEFAULT_PLAYBOOK_PATH)) -> str:
    try:
        selected = select_playbooks(query, path=path)
    except Exception:
        # Playbooks are helpful product data, not a hard runtime dependency for chat.
        # Readiness audit catches invalid files before demo/release.
        return ""
    if not selected:
        return ""

    lines = ["BRAVO lifecycle playbook hint:"]
    for pb in selected:
        lines.append(f"- mode={pb.mode}; usp={pb.usp}; lifecycle={pb.lifecycle_stage}")
        if pb.preferred_source_types:
            lines.append("  preferred_sources=" + ", ".join(pb.preferred_source_types))
        if pb.required_outputs:
            lines.append("  required_outputs=" + "; ".join(pb.required_outputs[:5]))
        if pb.guardrails:
            lines.append("  guardrails=" + "; ".join(pb.guardrails[:4]))
    return "\n".join(lines)
