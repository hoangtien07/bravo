"""Minimal OpenAI Agents SDK adapter used by the frontier runtime migration.

This module owns provider construction and normalized stream events only.  BRAVO continues to
own identity, RLS, retrieval, audit, draft approval and durable state; those controls must never
be delegated to a model SDK.
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from app.config import Settings


class RuntimeUnavailable(RuntimeError):
    """Raised when the feature flag selects the SDK without a usable cloud configuration."""


@dataclass(frozen=True)
class RuntimeEvent:
    """Provider-neutral event shape consumed by the BRAVO SSE adapter."""

    type: str
    data: dict[str, Any]


class OpenAIAgentsRuntime:
    """OpenAI Responses/Agents SDK boundary with tracing disabled by default.

    The adapter is intentionally small in the first migration slice. It proves the SDK/provider
    path and streaming contract while the legacy AgentSession remains the default production
    runtime. Specialist agents, tools and durable approvals are added on this same boundary.
    """

    def __init__(self, settings: Settings):
        self.settings = settings

    def _ensure_configured(self) -> None:
        if not self.settings.cloud_enabled:
            raise RuntimeUnavailable("OpenAI Agents runtime requires CLOUD_ENABLED=true.")
        if not self.settings.cloud_api_key or not self.settings.cloud_base_url:
            raise RuntimeUnavailable("OpenAI Agents runtime requires cloud API key and base URL.")

    def _provider(self):
        self._ensure_configured()
        try:
            from agents import OpenAIProvider
        except ImportError as exc:  # Useful for local checkout before Docker rebuild installs pin.
            raise RuntimeUnavailable("openai-agents is not installed; rebuild the application image.") from exc
        return OpenAIProvider(
            api_key=self.settings.cloud_api_key,
            base_url=self.settings.cloud_base_url,
            use_responses=True,
            strict_feature_validation=True,
        )

    async def stream_text(self, *, instructions: str, user_input: str,
                          deep_research: bool = False) -> AsyncIterator[RuntimeEvent]:
        """Run one SDK-backed text turn and emit normalized progress/token events.

        No conversation state is sent to OpenAI server storage in this migration slice. BRAVO
        will provide a Postgres-backed SDK session before this becomes the default chat runtime.
        """
        try:
            from agents import Agent, ModelSettings, RunConfig, Runner
        except ImportError as exc:
            raise RuntimeUnavailable("openai-agents is not installed; rebuild the application image.") from exc

        model = (self.settings.openai_agents_reasoning_model if deep_research
                 else self.settings.openai_agents_fast_model)
        agent = Agent(name="BRAVO Coordinator", instructions=instructions, model=model)
        run_config = RunConfig(
            model=model,
            model_provider=self._provider(),
            model_settings=ModelSettings(store=False),
            tracing_disabled=not self.settings.openai_agents_trace_sensitive_data,
            trace_include_sensitive_data=self.settings.openai_agents_trace_sensitive_data,
        )
        result = Runner.run_streamed(
            agent,
            user_input,
            max_turns=self.settings.openai_agents_max_turns,
            run_config=run_config,
        )
        emitted_text = False
        async for event in result.stream_events():
            name = getattr(event, "name", "")
            if name in {"tool_called", "tool_output", "handoff_requested", "handoff_occured"}:
                yield RuntimeEvent("runtime.progress", {"name": name})
                continue
            data = getattr(event, "data", None)
            delta = getattr(data, "delta", None)
            if isinstance(delta, str) and delta:
                emitted_text = True
                yield RuntimeEvent("content.delta", {"delta": delta})
        if not emitted_text and result.final_output:
            yield RuntimeEvent("content.delta", {"delta": str(result.final_output)})
        yield RuntimeEvent("runtime.completed", {"model": model})
