"""Fail-closed policy for future browser/computer-use adapters.

This layer deliberately does not control a browser.  It is the server-side boundary every future
adapter must pass before creating a proposal.  All potentially state-changing actions remain
HITL-only, so enabling a model flag can never grant unattended ERP access.
"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from app.config import Settings
from app.security.rls import Identity

_READ_ACTIONS = {"navigate", "screenshot"}
_SIDE_EFFECT_ACTIONS = {"click", "type"}
_ALL_ACTIONS = _READ_ACTIONS | _SIDE_EFFECT_ACTIONS


class ComputerUsePolicyError(PermissionError):
    pass


@dataclass(frozen=True)
class ComputerUseProposal:
    action: str
    url: str
    description: str
    step_count: int = 1

    @property
    def requires_approval(self) -> bool:
        # Even a browser click may submit a form or change ERP state; treat it as unsafe.
        return self.action in _SIDE_EFFECT_ACTIONS


def _allowed_hosts(settings: Settings) -> set[str]:
    return {item.strip().lower() for item in settings.computer_use_allowed_domains.split(",") if item.strip()}


def _host_allowed(host: str, allowed: set[str]) -> bool:
    host = host.lower().rstrip(".")
    return any(host == item or host.endswith("." + item) for item in allowed)


def authorize_proposal(proposal: ComputerUseProposal, identity: Identity, settings: Settings) -> None:
    if not settings.computer_use_enabled:
        raise ComputerUsePolicyError("Computer-use chưa được bật ở môi trường này.")
    if not (identity.is_admin or "computer:use" in identity.permissions):
        raise ComputerUsePolicyError("Không có quyền đề xuất computer-use.")
    if proposal.action not in _ALL_ACTIONS:
        raise ComputerUsePolicyError("Hành động computer-use không được hỗ trợ.")
    if not proposal.description.strip():
        raise ComputerUsePolicyError("Phải nêu rõ mục đích của thao tác.")
    if not 1 <= proposal.step_count <= settings.computer_use_max_steps:
        raise ComputerUsePolicyError("Số bước vượt giới hạn an toàn.")
    parsed = urlparse(proposal.url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ComputerUsePolicyError("Chỉ cho phép URL HTTPS có hostname rõ ràng.")
    allowed = _allowed_hosts(settings)
    if not allowed or not _host_allowed(parsed.hostname, allowed):
        raise ComputerUsePolicyError("Tên miền chưa nằm trong allowlist computer-use.")
