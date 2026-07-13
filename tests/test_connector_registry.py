from pathlib import Path

import pytest

from app.connectors.registry import ConnectorPolicyError, authorize_operation, load_catalog
from app.security.rls import Identity


def _identity(*permissions: str) -> Identity:
    return Identity(employee_id="00000000-0000-0000-0000-000000000001", department_ids=[],
                    permissions=set(permissions), is_admin=False)


def test_disabled_connector_is_not_discoverable_or_callable():
    path = Path("file_system/bravo_connectors.yaml")
    assert "sharepoint_knowledge" not in {item.id for item in load_catalog(str(path)) if item.enabled}
    with pytest.raises(ConnectorPolicyError):
        authorize_operation("sharepoint_knowledge", "read", _identity("connector:sharepoint:read"),
                            path=str(path))


def test_enabled_connector_requires_declared_permission():
    path = "file_system/bravo_connectors.yaml"
    with pytest.raises(ConnectorPolicyError):
        authorize_operation("workspace_documents", "read", _identity(), path=path)
    assert authorize_operation("workspace_documents", "read", _identity("doc:read"), path=path).id == "workspace_documents"
