from pathlib import Path

import pytest

from app.core_v2.demo_config import DemoConfigError, load_synthetic_demo_config


_CONFIG = Path("file_system/core_v2_synthetic_demo.yaml")


def test_synthetic_demo_config_is_complete_and_denies_model_egress_until_pinned():
    config = load_synthetic_demo_config(_CONFIG)
    assert config.synthetic_only is True
    assert config.model_egress_policy == "deny_until_owner_pins_model"
    assert config.capability_flags["accounting_case_v2"] is True


def test_demo_config_rejects_non_synthetic_mode(tmp_path):
    bad = tmp_path / "demo.yaml"
    bad.write_text(_CONFIG.read_text(encoding="utf-8").replace("synthetic_only: true", "synthetic_only: false"), encoding="utf-8")
    with pytest.raises(DemoConfigError):
        load_synthetic_demo_config(bad)
