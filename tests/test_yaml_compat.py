from __future__ import annotations

from app.utils.yaml_compat import _MiniYaml, safe_load_text


def test_yaml_compat_parses_nested_artifact_subset():
    raw = safe_load_text(
        """
version: 1
playbooks:
  - mode: ba_support
    preferred_source_types: [kqpt_ptnv, user_guide]
    triggers:
      - kqpt
      - ptnv
    enabled: true
  - mode: technical_impact
    preferred_source_types: [technical_manual]
"""
    )

    assert raw["version"] == 1
    assert raw["playbooks"][0]["mode"] == "ba_support"
    assert raw["playbooks"][0]["preferred_source_types"] == ["kqpt_ptnv", "user_guide"]
    assert raw["playbooks"][0]["triggers"] == ["kqpt", "ptnv"]
    assert raw["playbooks"][0]["enabled"] is True


def test_yaml_compat_fallback_keeps_none_as_business_value():
    raw = _MiniYaml("erp_dependency: none\nreviewed_by: null\n").parse()

    assert raw["erp_dependency"] == "none"
    assert raw["reviewed_by"] is None
