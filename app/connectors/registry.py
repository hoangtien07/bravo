"""Configuration-driven connector boundary.

The registry intentionally contains descriptors only.  It stops an LLM/runtime from discovering
an unconfigured integration, and establishes the permission/approval checks that concrete
adapters must call before reading or proposing an external action.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.security.rls import Identity
from app.utils.yaml_compat import safe_load_file

_VALID_KINDS = {"internal", "external"}
_VALID_OPERATIONS = {"search", "read", "propose_write"}


class ConnectorPolicyError(PermissionError):
    """Raised before a connector adapter can read or propose a side effect."""


@dataclass(frozen=True)
class Connector:
    id: str
    title: str
    kind: str
    enabled: bool
    required_permission: str
    operations: tuple[str, ...]
    data_classification: str

    @property
    def requires_approval(self) -> bool:
        return "propose_write" in self.operations


def _default_catalog_path() -> Path:
    return Path(__file__).resolve().parents[2] / "file_system" / "bravo_connectors.yaml"


@lru_cache(maxsize=4)
def load_catalog(path: str = "") -> tuple[Connector, ...]:
    raw = safe_load_file(Path(path) if path else _default_catalog_path()) or {}
    rows = raw.get("connectors") if isinstance(raw, dict) else None
    if not isinstance(rows, list):
        raise ValueError("connector catalog phải có connectors là một danh sách")
    seen: set[str] = set()
    connectors: list[Connector] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("mỗi connector phải là mapping")
        connector = Connector(
            id=str(row.get("id") or "").strip(),
            title=str(row.get("title") or "").strip(),
            kind=str(row.get("kind") or "").strip(),
            enabled=bool(row.get("enabled", False)),
            required_permission=str(row.get("required_permission") or "").strip(),
            operations=tuple(str(x) for x in (row.get("operations") or [])),
            data_classification=str(row.get("data_classification") or "internal").strip(),
        )
        if (not connector.id or not connector.title or connector.id in seen
                or connector.kind not in _VALID_KINDS or not connector.required_permission
                or not connector.operations or any(x not in _VALID_OPERATIONS for x in connector.operations)):
            raise ValueError(f"connector không hợp lệ: {connector.id or '<missing id>'}")
        seen.add(connector.id)
        connectors.append(connector)
    return tuple(connectors)


def _permitted(connector: Connector, identity: Identity) -> bool:
    return identity.is_admin or connector.required_permission in identity.permissions


def available_connectors(identity: Identity, *, path: str = "") -> list[Connector]:
    """Only enabled connectors that the caller is allowed to discover."""
    return [connector for connector in load_catalog(path) if connector.enabled and _permitted(connector, identity)]


def authorize_operation(connector_id: str, operation: str, identity: Identity, *, path: str = "") -> Connector:
    """Mandatory preflight for every concrete connector adapter.

    `propose_write` does not execute anything.  The caller must create an AgentApproval/Draft
    afterwards, preserving BRAVO's no-direct-write invariant.
    """
    connector = next((item for item in load_catalog(path) if item.id == connector_id), None)
    if connector is None or not connector.enabled:
        raise ConnectorPolicyError("Connector chưa được cấu hình hoặc chưa bật.")
    if operation not in connector.operations:
        raise ConnectorPolicyError("Thao tác không nằm trong hợp đồng của connector.")
    if not _permitted(connector, identity):
        raise ConnectorPolicyError("Không có quyền dùng connector này.")
    return connector
