-- WP-00 non-owner runtime-role provisioning.
--
-- Run this script as the database owner/migrator with psql variables, for example:
--   psql "$MIGRATOR_DATABASE_URL" -v db_name=bravo -f deploy/runtime-roles.sql
--
-- It contains no password and never creates a LOGIN role. Create the login credentials in the
-- approved secret manager, then attach them to the NOLOGIN roles below. Keep the migrator/owner
-- DSN out of API, MCP, worker, and backup processes.

BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bravo_api_runtime') THEN
        CREATE ROLE bravo_api_runtime NOLOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE NOINHERIT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bravo_worker_runtime') THEN
        CREATE ROLE bravo_worker_runtime NOLOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE NOINHERIT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bravo_backup_runtime') THEN
        CREATE ROLE bravo_backup_runtime NOLOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE NOINHERIT;
    END IF;
END
$$;

REVOKE ALL ON DATABASE :"db_name" FROM bravo_api_runtime, bravo_worker_runtime, bravo_backup_runtime;
GRANT CONNECT ON DATABASE :"db_name" TO bravo_api_runtime, bravo_worker_runtime, bravo_backup_runtime;
GRANT USAGE ON SCHEMA public TO bravo_api_runtime, bravo_worker_runtime;
REVOKE CREATE ON SCHEMA public FROM bravo_api_runtime, bravo_worker_runtime;

-- Transitional legacy-shell grant surface. The API still owns drafts, conversations and audit
-- writes; it must be narrowed table-by-table before a production claim. It is nevertheless a
-- non-owner/NOBYPASSRLS role, so FORCE RLS on chunks is effective during this V2 demonstrator.
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public
    TO bravo_api_runtime, bravo_worker_runtime;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public
    TO bravo_api_runtime, bravo_worker_runtime;

ALTER ROLE bravo_api_runtime SET statement_timeout = '5s';
ALTER ROLE bravo_api_runtime SET idle_in_transaction_session_timeout = '10s';
ALTER ROLE bravo_worker_runtime SET statement_timeout = '30s';
ALTER ROLE bravo_worker_runtime SET idle_in_transaction_session_timeout = '30s';

COMMIT;

-- Operator-only follow-up; do not place passwords in this file:
--   CREATE ROLE bravo_api_login LOGIN PASSWORD '<secret-manager value>'
--       NOSUPERUSER NOBYPASSRLS IN ROLE bravo_api_runtime;
--   CREATE ROLE bravo_worker_login LOGIN PASSWORD '<secret-manager value>'
--       NOSUPERUSER NOBYPASSRLS IN ROLE bravo_worker_runtime;
-- Point BRAVO_API_DATABASE_URL and BRAVO_WORKER_DATABASE_URL at those login roles. Run the
-- read-only scripts/verify_native_rls_cutover.py with the API role only after ENABLE/FORCE RLS.
