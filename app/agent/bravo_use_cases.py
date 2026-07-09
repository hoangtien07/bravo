"""BRAVO AI use-case matrix helpers.

Use cases are product/implementation data, not hard-coded behavior. This module validates
the YAML enough for CI and can render summaries for roadmap/review tooling.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.agent.bravo_playbooks import load_playbooks
from app.utils.yaml_compat import safe_load_file

DEFAULT_USE_CASE_PATH = Path("file_system/bravo_ai_use_cases.yaml")


@dataclass(frozen=True)
class BravoUseCase:
    id: str
    name: str
    mode: str
    usp: str
    priority: str
    stage: str
    lifecycle_stage: str
    personas: tuple[str, ...]
    problem: str
    input_sources: tuple[str, ...]
    output_artifacts: tuple[str, ...]
    guardrails: tuple[str, ...]
    success_metrics: tuple[str, ...]
    erp_dependency: str
    readiness: str

    @classmethod
    def from_dict(cls, raw: dict) -> "BravoUseCase":
        required = (
            "id", "name", "mode", "usp", "priority", "stage", "lifecycle_stage",
            "personas", "problem", "input_sources", "output_artifacts", "guardrails",
            "success_metrics", "erp_dependency", "readiness",
        )
        missing = [k for k in required if not raw.get(k)]
        if missing:
            raise ValueError(f"use case missing required fields: {missing}")
        return cls(
            id=str(raw["id"]),
            name=str(raw["name"]),
            mode=str(raw["mode"]),
            usp=str(raw["usp"]),
            priority=str(raw["priority"]),
            stage=str(raw["stage"]),
            lifecycle_stage=str(raw["lifecycle_stage"]),
            personas=tuple(raw["personas"]),
            problem=str(raw["problem"]),
            input_sources=tuple(raw["input_sources"]),
            output_artifacts=tuple(raw["output_artifacts"]),
            guardrails=tuple(raw["guardrails"]),
            success_metrics=tuple(raw["success_metrics"]),
            erp_dependency=str(raw["erp_dependency"]),
            readiness=str(raw["readiness"]),
        )


def _load_yaml(path: Path) -> dict:
    return safe_load_file(path) or {}


@lru_cache(maxsize=4)
def load_use_cases(path: str = str(DEFAULT_USE_CASE_PATH)) -> tuple[BravoUseCase, ...]:
    raw = _load_yaml(Path(path))
    items = raw.get("use_cases") or []
    if not isinstance(items, list):
        raise ValueError("use_cases must be a YAML list")
    use_cases = tuple(BravoUseCase.from_dict(item) for item in items)

    ids = [u.id for u in use_cases]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise ValueError(f"duplicate use case ids: {dupes}")
    return use_cases


def validate_use_cases(
    *,
    use_case_path: str = str(DEFAULT_USE_CASE_PATH),
    playbook_path: str = "file_system/bravo_lifecycle_playbooks.yaml",
) -> list[str]:
    """Return validation issues. Empty list means the matrix is internally consistent."""
    issues: list[str] = []
    use_cases = load_use_cases(use_case_path)
    playbooks = load_playbooks(playbook_path)
    modes = {p.mode: p for p in playbooks}

    for uc in use_cases:
        pb = modes.get(uc.mode)
        if pb is None:
            issues.append(f"{uc.id}: unknown playbook mode {uc.mode}")
            continue
        if uc.usp != pb.usp:
            issues.append(f"{uc.id}: usp {uc.usp} does not match playbook {pb.usp}")
        if uc.lifecycle_stage != pb.lifecycle_stage:
            issues.append(
                f"{uc.id}: lifecycle {uc.lifecycle_stage} does not match playbook "
                f"{pb.lifecycle_stage}"
            )
        if not set(uc.input_sources) & set(pb.preferred_source_types):
            issues.append(f"{uc.id}: input_sources do not overlap preferred_source_types")
        if len(uc.output_artifacts) < 3:
            issues.append(f"{uc.id}: too few output artifacts")
        if len(uc.guardrails) < 2:
            issues.append(f"{uc.id}: too few guardrails")
        if len(uc.success_metrics) < 2:
            issues.append(f"{uc.id}: too few success metrics")

    return issues


def summarize_use_cases(use_cases: tuple[BravoUseCase, ...] | None = None) -> dict[str, dict]:
    use_cases = use_cases or load_use_cases()
    return {
        "by_priority": dict(Counter(u.priority for u in use_cases)),
        "by_stage": dict(Counter(u.stage for u in use_cases)),
        "by_readiness": dict(Counter(u.readiness for u in use_cases)),
        "by_erp_dependency": dict(Counter(u.erp_dependency for u in use_cases)),
    }
