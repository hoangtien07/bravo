#!/usr/bin/env python3
"""Create and restore a WP-00 backup without exposing database credentials.

This runner deliberately uses ``pg_dump`` and ``pg_restore`` inside the Postgres service.  It
therefore works on operator hosts that do not install Postgres client binaries.  A restore always
targets a distinct Compose project and refuses an existing target project.  It leaves that target
running for inspection; teardown is an explicit operator action outside this command.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tarfile
import time
from datetime import UTC, datetime
from pathlib import Path


class BackupError(RuntimeError):
    pass


def _run(command: list[str], *, input_bytes: bytes | None = None, capture: bool = False) -> str:
    result = subprocess.run(command, input=input_bytes, stdout=subprocess.PIPE if capture else None,
                            stderr=subprocess.PIPE, check=False)
    if result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise BackupError(f"command failed ({command[0]} {command[1]}): {detail[:400]}")
    return result.stdout.decode("utf-8", errors="replace") if capture else ""


def _compose(project: str, env_file: str | None, *args: str) -> list[str]:
    command = ["docker", "compose", "--project-name", project]
    if env_file:
        command.extend(["--env-file", env_file])
    command.extend(["-f", "docker-compose.yml", "-f", "docker-compose.prod.yml"])
    command.extend(args)
    return command


def _service_container(project: str, env_file: str | None, service: str) -> str:
    value = _run(_compose(project, env_file, "ps", "-q", service), capture=True).strip()
    if not value:
        raise BackupError(f"service {service!r} is not running in project {project!r}")
    return value.splitlines()[0]


def _wait_for_postgres(container: str, timeout_seconds: int = 45) -> None:
    """Wait for the target database instead of racing Compose's asynchronous startup."""
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        result = subprocess.run(["docker", "exec", container, "sh", "-ceu",
                                 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"'],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        if result.returncode == 0:
            return
        time.sleep(1)
    raise BackupError("restore target Postgres did not become ready before timeout")


def _volume(project: str, name: str) -> str:
    return f"{project}_{name}"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d_%H%M%S")


def _tar_volume(volume: str, destination: Path, filename: str) -> None:
    _run(["docker", "run", "--rm", "-v", f"{volume}:/source:ro", "-v",
          f"{destination.resolve()}:/out", "busybox", "tar", "czf", f"/out/{filename}",
          "-C", "/source", "."])


def _extract_volume(volume: str, archive: Path) -> None:
    _run(["docker", "run", "--rm", "-v", f"{volume}:/target", "-v",
          f"{archive.parent.resolve()}:/in:ro", "busybox", "tar", "xzf",
          f"/in/{archive.name}", "-C", "/target"])


def _ensure_restore_roles(postgres: str) -> None:
    """Create only NOLOGIN principals referenced by the dump's ACLs before restore."""
    sql = b"""
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bravo_agent') THEN
    CREATE ROLE bravo_agent NOLOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bravo_writer') THEN
    CREATE ROLE bravo_writer NOLOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bravo_api_runtime') THEN
    CREATE ROLE bravo_api_runtime NOLOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bravo_worker_runtime') THEN
    CREATE ROLE bravo_worker_runtime NOLOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bravo_backup_runtime') THEN
    CREATE ROLE bravo_backup_runtime NOLOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
  END IF;
END $$;
"""
    _run(["docker", "exec", "-i", postgres, "sh", "-ceu",
          'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'], input_bytes=sql)


def _metadata(output: Path, timestamp: str, project: str) -> dict[str, object]:
    files = {kind: output / f"{kind}_{timestamp}.{suffix}" for kind, suffix in {
        "db": "dump", "uploads": "tgz", "private": "tgz"}.items()}
    if any(not path.is_file() for path in files.values()):
        raise BackupError("backup artifact set is incomplete")
    return {
        "schema_version": "bravo-wp00-backup/v1",
        "created_at": datetime.now(UTC).isoformat(),
        "source_project": project,
        "synthetic_drill": True,
        "files": {kind: {"name": path.name, "sha256": _sha256(path), "bytes": path.stat().st_size}
                  for kind, path in files.items()},
    }


def backup(project: str, output: Path, env_file: str | None, timestamp: str) -> Path:
    output.mkdir(parents=True, exist_ok=True)
    postgres = _service_container(project, env_file, "postgres")
    remote = f"/tmp/wp00_{timestamp}.dump"
    try:
        _run(["docker", "exec", postgres, "sh", "-ceu",
              f'pg_dump -Fc -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f {remote}'])
        _run(["docker", "cp", f"{postgres}:{remote}", str(output / f"db_{timestamp}.dump")])
    finally:
        _run(["docker", "exec", postgres, "sh", "-ceu", f"rm -f {remote}"])
    _tar_volume(_volume(project, "uploads"), output, f"uploads_{timestamp}.tgz")
    _tar_volume(_volume(project, "private_data"), output, f"private_{timestamp}.tgz")
    manifest = _metadata(output, timestamp, project)
    manifest_path = output / f"manifest_{timestamp}.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"WP-00 backup created; timestamp={timestamp}; artifact_manifest={manifest_path.name}")
    return manifest_path


def verify(output: Path, timestamp: str, project: str, env_file: str | None) -> None:
    manifest = _metadata(output, timestamp, project)
    postgres = _service_container(project, env_file, "postgres")
    remote = f"/tmp/wp00_verify_{timestamp}.dump"
    try:
        _run(["docker", "cp", str(output / f"db_{timestamp}.dump"), f"{postgres}:{remote}"])
        _run(["docker", "exec", postgres, "pg_restore", "--list", remote], capture=True)
    finally:
        _run(["docker", "exec", postgres, "sh", "-ceu", f"rm -f {remote}"])
    for kind in ("uploads", "private"):
        with tarfile.open(output / f"{kind}_{timestamp}.tgz", "r:gz") as archive:
            archive.getmembers()
    print(f"WP-00 backup integrity passed; artifact_hashes={len(manifest['files'])}")


def restore(output: Path, timestamp: str, source_project: str, target_project: str,
            env_file: str | None) -> dict[str, object]:
    if source_project == target_project:
        raise BackupError("restore target project must differ from source project")
    existing = _run(_compose(target_project, env_file, "ps", "-q"), capture=True).strip()
    if existing:
        raise BackupError(f"restore target project {target_project!r} already exists")
    started = time.monotonic()
    _run(_compose(target_project, env_file, "up", "-d", "postgres", "redis"))
    postgres = _service_container(target_project, env_file, "postgres")
    _wait_for_postgres(postgres)
    _ensure_restore_roles(postgres)
    dump = output / f"db_{timestamp}.dump"
    remote = f"/tmp/wp00_restore_{timestamp}.dump"
    try:
        _run(["docker", "cp", str(dump), f"{postgres}:{remote}"])
        _run(["docker", "exec", postgres, "sh", "-ceu",
              f'pg_restore --clean --if-exists --no-owner -U "$POSTGRES_USER" -d "$POSTGRES_DB" {remote}'])
        # Recreate the declarative NOLOGIN runtime grant surface; credentials remain outside the dump.
        sql = Path("deploy/runtime-roles.sql").read_bytes()
        _run(["docker", "exec", "-i", postgres, "sh", "-ceu",
              'psql -v db_name="$POSTGRES_DB" -U "$POSTGRES_USER" -d "$POSTGRES_DB"'], input_bytes=sql)
        _run(["docker", "volume", "create", _volume(target_project, "uploads")])
        _run(["docker", "volume", "create", _volume(target_project, "private_data")])
        _extract_volume(_volume(target_project, "uploads"), output / f"uploads_{timestamp}.tgz")
        _extract_volume(_volume(target_project, "private_data"), output / f"private_{timestamp}.tgz")
        check_sql = (
            "SELECT version_num FROM alembic_version; "
            "SELECT extname FROM pg_extension WHERE extname = 'vector'; "
            "SELECT relrowsecurity, relforcerowsecurity FROM pg_class WHERE oid = 'public.chunks'::regclass; "
            "SELECT count(*) FROM pg_policies WHERE schemaname = 'public' AND tablename = 'chunks' "
            "AND policyname = 'chunks_rls_backstop'; "
            "SELECT has_table_privilege('bravo_api_runtime', 'public.chunks', 'SELECT');"
        )
        check = _run(["docker", "exec", postgres, "sh", "-ceu",
                      f'psql -At -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "{check_sql}"'], capture=True)
        expected = {"vector", "t|t", "1", "t"}
        observed = {line.strip() for line in check.splitlines() if line.strip()}
        if not expected.issubset(observed) or not any(item.startswith("0017") for item in observed):
            raise BackupError("restore catalog validation did not preserve migration/RLS controls")
        # Recovery readiness must not require an online model or a cloud credential.  Run the API
        # once with the egress path disabled, validate /readyz, then terminate it.  The restored
        # database and normal production configuration remain untouched.
        ready_command = (
            "uvicorn app.main:app --host 127.0.0.1 --port 8000 >/tmp/wp00-readyz.log 2>&1 & "
            "pid=$!; ready=0; "
            "for i in $(seq 1 30); do "
            "python -c \"import urllib.request; r=urllib.request.urlopen('http://127.0.0.1:8000/readyz', timeout=2); "
            "assert r.status == 200 and b'\\\"ready\\\":true' in r.read().replace(b' ', b'')\" "
            "&& ready=1 && break || sleep 1; done; "
            "kill $pid; wait $pid || true; test $ready -eq 1"
        )
        _run(_compose(target_project, env_file, "run", "--rm", "--no-deps", "-e",
                      "CLOUD_ENABLED=false", "-e", "EGRESS_POLICY=offline_only", "-e",
                      "LLM_LOCAL_BASE_URL=http://127.0.0.1:9", "-e", "LLM_LOCAL_MODEL=offline-probe", "-e",
                      "LLM_LOCAL_API_KEY=offline-probe", "api", "sh", "-ceu", ready_command), capture=True)
    finally:
        _run(["docker", "exec", postgres, "sh", "-ceu", f"rm -f {remote}"])
    return {
        "schema_version": "bravo-wp00-restore-drill/v1",
        "captured_at": datetime.now(UTC).isoformat(),
        "source_project": source_project,
        "target_project": target_project,
        "synthetic_drill": True,
        "rto_seconds": round(time.monotonic() - started, 2),
        "checks": {"migration_0017": True, "vector_extension": True, "rls_forced": True,
                   "rls_policy": True, "runtime_grants": True, "readyz": True},
        "passed": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("backup", "verify", "restore"))
    parser.add_argument("--project", default="bravo-wp00")
    parser.add_argument("--target-project", default="bravo-wp00-restore")
    parser.add_argument("--output", default=".wp00-backups")
    parser.add_argument("--timestamp")
    parser.add_argument("--env-file", help="Passed to Docker Compose; never read by this script.")
    parser.add_argument("--evidence-out", help="Redaction-safe restore report path.")
    args = parser.parse_args()
    output = Path(args.output).resolve()
    timestamp = args.timestamp or _timestamp()
    try:
        if args.command == "backup":
            backup(args.project, output, args.env_file, timestamp)
        elif args.command == "verify":
            verify(output, timestamp, args.project, args.env_file)
        else:
            report = restore(output, timestamp, args.project, args.target_project, args.env_file)
            if args.evidence_out:
                path = Path(args.evidence_out)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"WP-00 isolated restore passed; target_project={args.target_project}")
    except (BackupError, OSError, tarfile.TarError) as exc:
        print(f"WP-00 backup/restore failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
