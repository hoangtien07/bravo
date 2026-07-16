from __future__ import annotations

import pytest

from app.config import Settings


def test_retention_requires_a_positive_duration_when_enabled():
    settings = Settings(consultant_state_retention_enabled=True, consultant_state_retention_days=0)

    with pytest.raises(RuntimeError, match="consultant_state_retention_days"):
        settings.validate_boot()


def test_retention_can_remain_disabled_without_a_duration():
    Settings(consultant_state_retention_enabled=False, consultant_state_retention_days=0).validate_boot()
