"""Create a redaction-safe V2 containment baseline manifest.

The manifest intentionally records only hashes and non-secret topology facts.  It never reads
``.env`` files, renders Compose with interpolation, or writes environment values to disk.
It is therefore suitable as the first, static part of the runtime evidence ledger.  A later
operator-run proof may attach a separately redacted effective-Compose projection and runtime
probe results.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml


DEFAULT_COMPOSE_FILES = ("docker-compose.yml", "docker-compose.prod.yml")
DEFAULT_CORPUS_MANIFEST = "file_system/bravo_corpus_manifest.yaml"
PYTHON_LOCK_CANDIDATES = ("uv.lock", "poetry.lock", "Pipfile.lock", "requirements.lock")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _git_value(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def _alembic_heads(root: Path) -> list[str]:
    """Derive migration heads without opening a database or configuration file."""
    revisions: set[str] = set()
    children: set[str] = set()
    for path in sorted((root / "alembic" / "versions").glob("*.py")):
        source = path.read_text(encoding="utf-8")
        revision = re.search(r"^revision\s*=\s*[\"']([^\"']+)[\"']", source, re.MULTILINE)
        down = re.search(r"^down_revision\s*=\s*(.+)$", source, re.MULTILINE)
        if not revision or not down:
            continue
        revisions.add(revision.group(1))
        children.update(re.findall(r"[\"']([^\"']+)[\"']", down.group(1)))
    return sorted(revisions - children)


def _environment_keys(value: Any) -> list[str]:
    if isinstance(value, dict):
        return sorted(str(key) for key in value)
    if isinstance(value, list):
        return sorted(str(item).split("=", 1)[0] for item in value)
    return []


def _port_projection(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict):
            published = item.get("published")
            target = item.get("target")
            protocol = item.get("protocol", "tcp")
            if published is not None and target is not None:
                result.append(f"{published}:{target}/{protocol}")
    return sorted(result)


def static_compose_projection(root: Path, compose_files: list[str]) -> dict[str, Any]:
    """Return topology facts while deliberately excluding every configuration value."""
    files: list[dict[str, str]] = []
    services: dict[str, dict[str, Any]] = {}
    for relative in compose_files:
        path = root / relative
        if not path.is_file():
            raise FileNotFoundError(f"Compose file not found: {relative}")
        raw = path.read_bytes()
        files.append({"path": relative, "sha256": _sha256_bytes(raw)})
        document = yaml.safe_load(raw) or {}
        for name, spec in (document.get("services") or {}).items():
            if not isinstance(spec, dict):
                continue
            current = services.setdefault(str(name), {
                "image": None,
                "ports": [],
                "environment_keys": [],
                "uses_env_file": False,
                "has_build": False,
            })
            if spec.get("image"):
                current["image"] = str(spec["image"])
            current["ports"] = sorted(set(current["ports"]) | set(_port_projection(spec.get("ports"))))
            current["environment_keys"] = sorted(
                set(current["environment_keys"]) | set(_environment_keys(spec.get("environment"))))
            # The reference is useful for a later operator audit, but a secret-file path is not.
            current["uses_env_file"] = bool(current["uses_env_file"] or spec.get("env_file"))
            current["has_build"] = bool(current["has_build"] or "build" in spec)
    return {"compose_files": files, "services": dict(sorted(services.items()))}


def production_network_failures(projection: dict[str, Any]) -> list[str]:
    """Check the declared production topology without rendering any secret interpolation."""
    failures: list[str] = []
    services = projection["services"]
    expected_caddy_ports = {"80:80", "443:443"}
    if "caddy" not in services:
        failures.append("production topology has no caddy ingress service")
    for name, service in services.items():
        ports = set(service["ports"])
        if name == "caddy":
            missing = expected_caddy_ports - ports
            extra = ports - expected_caddy_ports
            if missing:
                failures.append(f"caddy is missing approved ingress port(s): {sorted(missing)}")
            if extra:
                failures.append(f"caddy has unapproved published port(s): {sorted(extra)}")
        elif ports:
            failures.append(f"{name} publishes unapproved host port(s): {sorted(ports)}")
    return failures


def _python_snapshot_hash() -> str:
    output = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True)
    return _sha256_bytes(output.encode("utf-8"))


def _lockfile_projection(root: Path) -> dict[str, str | None]:
    output: dict[str, str | None] = {
        "pyproject.toml": sha256_file(root / "pyproject.toml"),
        "FigmaMake_UI/pnpm-lock.yaml": sha256_file(root / "FigmaMake_UI" / "pnpm-lock.yaml"),
        "python_lockfile": None,
    }
    for candidate in PYTHON_LOCK_CANDIDATES:
        path = root / candidate
        if path.is_file():
            output["python_lockfile"] = f"{candidate}:{sha256_file(path)}"
            break
    return output


def build_manifest(
    root: Path,
    *,
    code_baseline: str,
    compose_files: list[str] | None = None,
    corpus_manifest: str = DEFAULT_CORPUS_MANIFEST,
) -> dict[str, Any]:
    """Build an artifact without reading secret stores or talking to runtime services."""
    root = root.resolve()
    compose_files = compose_files or list(DEFAULT_COMPOSE_FILES)
    corpus_path = root / corpus_manifest
    corpus = yaml.safe_load(corpus_path.read_text(encoding="utf-8")) or {}
    projection = static_compose_projection(root, compose_files)
    static_failures = production_network_failures(projection)
    return {
        "schema_version": "bravo-v2-runtime-baseline/v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "secret_handling": {
            "reads_env_files": False,
            "renders_interpolated_compose": False,
            "records_environment_values": False,
            "records_credentials": False,
        },
        "git": {
            "head": _git_value(root, "rev-parse", "HEAD"),
            "branch": _git_value(root, "branch", "--show-current"),
            "conversation_code_baseline": code_baseline,
        },
        "alembic_heads": _alembic_heads(root),
        "dependency_inputs": {
            **_lockfile_projection(root),
            "python_executable": sys.version.split()[0],
            "python_package_snapshot_sha256": _python_snapshot_hash(),
        },
        "corpus_manifest": {
            "path": corpus_manifest,
            "sha256": sha256_file(corpus_path),
            "version": corpus.get("version"),
            "system_version": corpus.get("system_version"),
        },
        "static_compose_projection": projection,
        "static_network_preflight": {
            "status": "passed" if not static_failures else "failed",
            "failures": static_failures,
        },
        "runtime_proof": {
            "status": "not_collected",
            "reason": "Requires an operator-run, redacted effective-Compose projection and live probes.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root (default: current directory)")
    parser.add_argument("--code-baseline", required=True,
                        help="Named source baseline; no secret or environment data is accepted.")
    parser.add_argument("--compose-file", action="append", dest="compose_files",
                        help="Static Compose input; repeat to include an explicit topology overlay.")
    parser.add_argument("--require-production-network", action="store_true",
                        help="Exit non-zero unless the static topology exposes only Caddy 80/443.")
    parser.add_argument("--out", required=True, help="Output JSON path")
    args = parser.parse_args()

    manifest = build_manifest(
        Path(args.root), code_baseline=args.code_baseline, compose_files=args.compose_files)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if not args.require_production_network or manifest["static_network_preflight"]["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
