"""Plan 20: Docker dependency fetches accept an injected CA without weakening TLS."""
from __future__ import annotations

from pathlib import Path


def test_dockerfile_uses_an_ephemeral_corporate_ca_secret_and_keeps_tls_verification_enabled():
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")

    assert dockerfile.count("--mount=type=secret,id=corporate_ca") == 2
    assert "NODE_EXTRA_CA_CERTS=/run/secrets/corporate-ca" in dockerfile
    assert "update-ca-certificates" in dockerfile
    assert "NODE_TLS_REJECT_UNAUTHORIZED=0" not in dockerfile
    assert "--trusted-host" not in dockerfile


def test_corporate_ca_compose_override_is_opt_in_and_requires_an_external_file():
    override = Path("deploy/docker-compose.corporate-ca.yml").read_text(encoding="utf-8")

    assert "source: corporate_ca" in override
    assert "BRAVO_CORPORATE_CA_FILE:?" in override
