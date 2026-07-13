from __future__ import annotations

import pytest

from app.agent_runtime.openai_agents import OpenAIAgentsRuntime, RuntimeUnavailable
from app.config import Settings


def test_openai_agents_runtime_fails_closed_without_cloud_configuration():
    runtime = OpenAIAgentsRuntime(Settings(cloud_enabled=False))

    with pytest.raises(RuntimeUnavailable, match="CLOUD_ENABLED"):
        runtime._ensure_configured()


def test_openai_agents_runtime_uses_explicit_models():
    settings = Settings(
        cloud_enabled=True,
        cloud_api_key="test-key",
        cloud_base_url="https://api.openai.com/v1",
        openai_agents_fast_model="fast-model",
        openai_agents_reasoning_model="deep-model",
    )
    runtime = OpenAIAgentsRuntime(settings)

    assert runtime.settings.openai_agents_fast_model == "fast-model"
    assert runtime.settings.openai_agents_reasoning_model == "deep-model"
