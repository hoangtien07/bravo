"""Fail-closed config-as-code for the synthetic V2 demonstrator."""
from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core_v2.contracts import CaseType


class DemoConfigError(ValueError):
    pass


class SyntheticDemoConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = Field(pattern=r"^bravo-core-v2-synthetic-demo/v1$")
    demo_id: str = Field(min_length=1)
    synthetic_only: bool
    enabled_case_types: tuple[CaseType, ...]
    capability_flags: dict[str, bool]
    model_egress_policy: str = Field(pattern=r"^deny_until_owner_pins_model$")
    audit_export: str = Field(pattern=r"^privacy_minimized_json$")

    @model_validator(mode="after")
    def fail_closed(self) -> "SyntheticDemoConfig":
        if not self.synthetic_only:
            raise ValueError("the developer demonstrator must be synthetic-only")
        if set(self.enabled_case_types) != set(CaseType):
            raise ValueError("all and only approved V2 case types must be declared")
        if not all(isinstance(value, bool) for value in self.capability_flags.values()):
            raise ValueError("capability flags must be booleans")
        return self


def load_synthetic_demo_config(path: str | Path) -> SyntheticDemoConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    try:
        return SyntheticDemoConfig.model_validate(raw)
    except Exception as exc:
        raise DemoConfigError("invalid Core V2 synthetic demo config") from exc
