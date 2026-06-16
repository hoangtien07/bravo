"""W0.1 — boot-guard + nạp catalog runtime.

Hai bất biến vận hành: (1) import data_layer là đủ để REGISTRY có whitelist metric (không
còn abstain 100% vì catalog rỗng); (2) ở production, secret mặc định -> fail-closed boot.
"""
from __future__ import annotations

import pytest

from app.config import Settings


def test_catalog_auto_loaded_on_import():
    # Chỉ cần chạm data_layer là catalog đã register (side-effect ở __init__).
    from app.data_layer.semantic import REGISTRY

    ids = REGISTRY.ids()
    assert len(ids) >= 19, f"catalog rỗng lúc runtime ({len(ids)}) — metric_lookup sẽ abstain 100%"
    assert "doanh_thu_thuan" in ids
    assert "quy_luong_thang" in ids  # metric nhạy HR vẫn trong whitelist


def test_boot_guard_local_is_noop():
    Settings(env="local", jwt_secret="change-me").validate_boot()  # không raise


@pytest.mark.parametrize("env", ["production", "staging", "prod"])
def test_boot_guard_blocks_default_secret_in_prod(env):
    with pytest.raises(RuntimeError, match="boot-guard"):
        Settings(env=env, jwt_secret="change-me",
                 mcp_token_pepper="x" * 32).validate_boot()


def test_boot_guard_blocks_cloud_without_key():
    with pytest.raises(RuntimeError, match="cloud_enabled"):
        Settings(env="production", jwt_secret="a" * 32, mcp_token_pepper="b" * 32,
                 cloud_enabled=True, cloud_api_key="", cloud_base_url="").validate_boot()


def test_boot_guard_passes_with_strong_secrets():
    Settings(env="production", jwt_secret="a" * 40, mcp_token_pepper="b" * 40).validate_boot()
