"""Create/update WP-00 non-owner login roles from secret DSNs without printing them."""
from __future__ import annotations

import asyncio
import os
from urllib.parse import unquote, urlsplit

import asyncpg


class ProvisionError(RuntimeError):
    pass


def _dsn(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise ProvisionError(f"{name} is required")
    return value.replace("postgresql+asyncpg://", "postgresql://", 1)


def _login_from_dsn(value: str, expected_name: str) -> tuple[str, str]:
    parsed = urlsplit(value)
    username = unquote(parsed.username or "")
    password = unquote(parsed.password or "")
    if username != expected_name or not password:
        raise ProvisionError(f"{expected_name} DSN must contain that login and a password")
    return username, password


def _literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


async def provision() -> None:
    owner_dsn = _dsn("DATABASE_URL")
    api_login, api_password = _login_from_dsn(_dsn("BRAVO_API_DATABASE_URL"), "bravo_api_login")
    worker_login, worker_password = _login_from_dsn(
        _dsn("BRAVO_WORKER_DATABASE_URL"), "bravo_worker_login")
    connection = await asyncpg.connect(owner_dsn)
    try:
        for role in ("bravo_api_runtime", "bravo_worker_runtime", "bravo_backup_runtime"):
            await connection.execute(
                f"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{role}') "
                f"THEN CREATE ROLE {role} NOLOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE; "
                "END IF; END $$;")
        for login, password, group in ((api_login, api_password, "bravo_api_runtime"),
                                       (worker_login, worker_password, "bravo_worker_runtime")):
            exists = await connection.fetchval("SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = $1)", login)
            if exists:
                await connection.execute(
                    f"ALTER ROLE {login} LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE "
                    f"INHERIT PASSWORD {_literal(password)}")
            else:
                await connection.execute(
                    f"CREATE ROLE {login} LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE "
                    f"INHERIT PASSWORD {_literal(password)}")
            await connection.execute(f"GRANT {group} TO {login}")
        database_name = await connection.fetchval("SELECT current_database()")
        await connection.execute(f"GRANT CONNECT ON DATABASE {database_name} TO bravo_api_runtime, bravo_worker_runtime")
        await connection.execute("GRANT USAGE ON SCHEMA public TO bravo_api_runtime, bravo_worker_runtime")
        await connection.execute("REVOKE CREATE ON SCHEMA public FROM bravo_api_runtime, bravo_worker_runtime")
        await connection.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO bravo_api_runtime, bravo_worker_runtime")
        await connection.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO bravo_api_runtime, bravo_worker_runtime")
        await connection.execute("ALTER ROLE bravo_api_runtime SET statement_timeout = '5s'")
        await connection.execute("ALTER ROLE bravo_api_runtime SET idle_in_transaction_session_timeout = '10s'")
        await connection.execute("ALTER ROLE bravo_worker_runtime SET statement_timeout = '30s'")
        await connection.execute("ALTER ROLE bravo_worker_runtime SET idle_in_transaction_session_timeout = '30s'")
    finally:
        await connection.close()


def main() -> int:
    try:
        asyncio.run(provision())
    except (ProvisionError, asyncpg.PostgresError, OSError) as exc:
        print(f"WP-00 role provisioning failed: {exc}")
        return 2
    print("WP-00 non-owner runtime roles provisioned; no DSN or password was printed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
