"""Configure the approved cloud-only WP-00 runtime without printing secret values."""
from __future__ import annotations

import argparse
import os
import re
import secrets
from pathlib import Path


_ASSIGNMENT = re.compile(r"^([A-Z0-9_]+)=.*$")
_REQUIRED_CLOUD = ("CLOUD_BASE_URL", "CLOUD_MODEL", "CLOUD_API_KEY")
_UPDATES = {
    "BRAVO_ENV_FILE": ".env.wp00",
    "EGRESS_POLICY": "cloud_only",
    "CLOUD_ENABLED": "true",
    "DEMO_ALLOW_CLOUD_ANSWERS": "true",
    "LLM_LOCAL_BASE_URL": "",
    "LLM_LOCAL_MODEL": "",
    "LLM_LOCAL_API_KEY": "",
    "EMBEDDING_PROVIDER": "local",
    "EMBEDDING_MODEL": "BAAI/bge-m3",
    "EMBEDDING_DIM": "1024",
    "RERANK_ENABLED": "false",
}

_CLOUD_EMBEDDING_UPDATES = {
    **_UPDATES,
    "EMBEDDING_PROVIDER": "openai_compatible",
    "EMBEDDING_MODEL": "text-embedding-3-small",
    "EMBEDDING_DIM": "1536",
    "CLOUD_EMBEDDING_MODEL": "text-embedding-3-small",
}

_OPENAI_COMPATIBLE_UPDATES = {
    **_CLOUD_EMBEDDING_UPDATES,
    "CLOUD_BASE_URL": "https://api.openai.com/v1",
    "CLOUD_MODEL": "gpt-4o-2024-11-20",
}


def _https_url(value: str) -> str:
    """Normalize a human-entered compatible endpoint without exposing it in logs."""
    value = value.strip()
    if value and not value.startswith(("https://", "http://")):
        return "https://" + value
    return value


def configure(path: Path, *, cloud_embedding: bool = False, openai_compatible: bool = False,
              clear_exposed_credentials: bool = False) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    values: dict[str, str] = {}
    for line in lines:
        match = _ASSIGNMENT.match(line)
        if match:
            values[match.group(1)] = line.split("=", 1)[1]
    missing = [key for key in _REQUIRED_CLOUD if not values.get(key, "").strip()]
    if missing:
        raise ValueError("cloud LLM configuration is incomplete: " + ", ".join(missing))
    normalized_urls = {"CLOUD_BASE_URL": _https_url(values["CLOUD_BASE_URL"])}
    if values.get("CLOUD_EMBEDDING_BASE_URL", "").strip():
        normalized_urls["CLOUD_EMBEDDING_BASE_URL"] = _https_url(values["CLOUD_EMBEDDING_BASE_URL"])

    updates = dict(_OPENAI_COMPATIBLE_UPDATES if openai_compatible else
                   _CLOUD_EMBEDDING_UPDATES if cloud_embedding else _UPDATES)
    if clear_exposed_credentials:
        # An exposed bearer credential must not remain usable.  This deliberately does not accept
        # a replacement key on the command line; inject the new value through the approved secret
        # source after provider-side rotation.
        updates["CLOUD_API_KEY"] = ""
        updates["CLOUD_EMBEDDING_API_KEY"] = ""
    weak = {"", "change-me", "change-me-in-production", "change-me-256-bit-random"}
    for key in ("JWT_SECRET", "MCP_TOKEN_PEPPER"):
        if values.get(key, "").strip() in weak or len(values.get(key, "")) < 16:
            updates[key] = secrets.token_hex(32)

    written: set[str] = set()
    output: list[str] = []
    for line in lines:
        match = _ASSIGNMENT.match(line)
        key = match.group(1) if match else None
        if key in updates:
            if key not in written:
                output.append(f"{key}={updates[key]}")
                written.add(key)
            continue
        if key in normalized_urls:
            output.append(f"{key}={normalized_urls[key]}")
            written.add(key)
            continue
        output.append(line)
    for key, value in updates.items():
        if key not in written:
            output.append(f"{key}={value}")

    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text("\n".join(output) + "\n", encoding="utf-8")
    try:
        temporary.chmod(0o600)
    except OSError:
        pass
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", default=".env.wp00")
    parser.add_argument("--cloud-embedding", action="store_true",
                        help="Use text-embedding-3-small (1536 dimensions) via the approved cloud provider.")
    parser.add_argument("--openai-compatible", action="store_true",
                        help="Set the approved OpenAI-compatible endpoint/model and 1536 embeddings.")
    parser.add_argument("--clear-exposed-credentials", action="store_true",
                        help="Clear cloud credential fields after exposure; replacement is never accepted here.")
    args = parser.parse_args()
    path = Path(args.env_file)
    if not path.is_file():
        raise SystemExit(f"Environment file not found: {path}")
    try:
        configure(path, cloud_embedding=args.cloud_embedding,
                  openai_compatible=args.openai_compatible,
                  clear_exposed_credentials=args.clear_exposed_credentials)
    except ValueError as exc:
        print(f"WP-00 cloud configuration rejected: {exc}")
        return 2
    embedding = "1536-dimension cloud embeddings" if (args.cloud_embedding or args.openai_compatible) else "1024-dimension local embeddings"
    print(f"Configured cloud LLM and {embedding} without printing secrets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
