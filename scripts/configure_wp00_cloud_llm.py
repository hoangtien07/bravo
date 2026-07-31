"""Configure cloud LLM plus local bge-m3 embeddings without printing secret values."""
from __future__ import annotations

import argparse
import os
import re
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


def configure(path: Path, *, cloud_embedding: bool = False) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    values: dict[str, str] = {}
    for line in lines:
        match = _ASSIGNMENT.match(line)
        if match:
            values[match.group(1)] = line.split("=", 1)[1]
    missing = [key for key in _REQUIRED_CLOUD if not values.get(key, "").strip()]
    if missing:
        raise ValueError("cloud LLM configuration is incomplete: " + ", ".join(missing))

    written: set[str] = set()
    output: list[str] = []
    for line in lines:
        match = _ASSIGNMENT.match(line)
        key = match.group(1) if match else None
        updates = _CLOUD_EMBEDDING_UPDATES if cloud_embedding else _UPDATES
        if key in updates:
            if key not in written:
                output.append(f"{key}={updates[key]}")
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
    args = parser.parse_args()
    path = Path(args.env_file)
    if not path.is_file():
        raise SystemExit(f"Environment file not found: {path}")
    try:
        configure(path, cloud_embedding=args.cloud_embedding)
    except ValueError as exc:
        print(f"WP-00 cloud configuration rejected: {exc}")
        return 2
    embedding = "1536-dimension cloud embeddings" if args.cloud_embedding else "1024-dimension local embeddings"
    print(f"Configured cloud LLM and {embedding} without printing secrets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
