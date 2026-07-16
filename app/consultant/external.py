"""External expert boundary. Live calls are disabled until Phase-4 approval gates pass."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExternalRequest:
    purpose: str
    safe_question: str
    profile: str = "auto"


class ExternalGatewayDisabled(RuntimeError):
    pass


class ExternalExpertGateway:
    """No implicit BravoGen fallback, credential rotation, or candidate auto-publish."""
    async def ask(self, request: ExternalRequest) -> str:
        raise ExternalGatewayDisabled(
            "External expert is shadow-only until provider authorization, DLP, quota, and evaluation gates are approved."
        )
