from __future__ import annotations

import json
from pathlib import Path

from scripts.v2_runtime_evidence import (
    build_manifest,
    production_network_failures,
    static_compose_projection,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_static_compose_projection_keeps_topology_but_never_environment_values(tmp_path):
    _write(tmp_path / "compose.yml", """
services:
  api:
    image: bravo:latest
    ports: ["80:8000"]
    environment:
      DATABASE_URL: postgresql://user:very-secret@db/bravo
      REDIS_URL: redis://:another-secret@redis/0
""")
    projection = static_compose_projection(tmp_path, ["compose.yml"])
    encoded = json.dumps(projection)
    assert projection["services"]["api"]["ports"] == ["80:8000"]
    assert projection["services"]["api"]["environment_keys"] == ["DATABASE_URL", "REDIS_URL"]
    assert "very-secret" not in encoded
    assert "another-secret" not in encoded


def test_manifest_declares_static_not_runtime_proof(tmp_path, monkeypatch):
    _write(tmp_path / "pyproject.toml", "[project]\nname = 'example'\n")
    _write(tmp_path / "FigmaMake_UI" / "pnpm-lock.yaml", "lockfileVersion: '9.0'\n")
    _write(tmp_path / "file_system" / "bravo_corpus_manifest.yaml", "version: 1\nsystem_version: B10R1\n")
    _write(tmp_path / "docker-compose.yml", "services: {}\n")
    _write(tmp_path / "docker-compose.prod.yml", "services: {}\n")
    _write(tmp_path / "alembic" / "versions" / "0012.py", "revision = '0012'\ndown_revision = '0011'\n")
    _write(tmp_path / "alembic" / "versions" / "0013.py", "revision = '0013'\ndown_revision = '0012'\n")
    monkeypatch.setattr("scripts.v2_runtime_evidence._git_value", lambda *_: "git-value")
    monkeypatch.setattr("scripts.v2_runtime_evidence._python_snapshot_hash", lambda: "packages-hash")
    manifest = build_manifest(tmp_path, code_baseline="code-baseline")
    assert manifest["alembic_heads"] == ["0013"]
    assert manifest["git"]["conversation_code_baseline"] == "code-baseline"
    assert manifest["runtime_proof"]["status"] == "not_collected"
    assert manifest["secret_handling"]["reads_env_files"] is False


def test_network_preflight_rejects_keycloak_dev_overlay():
    projection = {
        "services": {
            "caddy": {"ports": ["80:80", "443:443"]},
            "keycloak": {"ports": ["8080:8080"]},
        }
    }

    failures = production_network_failures(projection)

    assert failures == ["keycloak publishes unapproved host port(s): ['8080:8080']"]
