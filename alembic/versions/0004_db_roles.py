"""W2.4: DB-role least-privilege (lưới an toàn #2 độc lập với predicate Python).

SECURITY-AGENT-DB-ROLE.md §3: RLS predicate trong app là lớp #1; lớp #2 ĐỘC LẬP là DB-role:
  - `bravo_agent` NOLOGIN: chỉ SELECT trên schema `app_safe` (view), read-only,
    statement_timeout chặn DoS. Quên .where() ở một query mới -> vẫn không vượt được view.
  - `bravo_writer` NOLOGIN: chỉ INSERT `drafts`/`audit_log` (ghi = nháp, invariant #2).

MVP: migration ĐỊNH NGHĨA role + view. App vẫn dùng connection DBA (chưa tách pool) -> đây
là production-gate: ở production đổi DATABASE_URL read-path sang bravo_agent. Idempotent.

Revision ID: 0004_db_roles
Revises: 0003_agentrun_draft
"""
from __future__ import annotations

from alembic import op

revision = "0004_db_roles"
down_revision = "0003_agentrun_draft"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'bravo_agent') THEN
            CREATE ROLE bravo_agent NOLOGIN;
        END IF;
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'bravo_writer') THEN
            CREATE ROLE bravo_writer NOLOGIN;
        END IF;
    END $$;
    """)
    op.execute("CREATE SCHEMA IF NOT EXISTS app_safe;")
    # View 'an toàn' — bề mặt đọc duy nhất cho agent role (RLS predicate vẫn áp trong query).
    op.execute("CREATE OR REPLACE VIEW app_safe.v_chunks_scoped AS SELECT * FROM chunks;")
    op.execute("CREATE OR REPLACE VIEW app_safe.v_archival_scoped AS SELECT * FROM archival_passages;")

    # bravo_agent: chỉ đọc, read-only, timeout — KHÔNG chạm bảng gốc (payroll/HR nhạy).
    op.execute("GRANT USAGE ON SCHEMA app_safe TO bravo_agent;")
    op.execute("GRANT SELECT ON app_safe.v_chunks_scoped, app_safe.v_archival_scoped TO bravo_agent;")
    op.execute("ALTER ROLE bravo_agent SET statement_timeout = '5s';")
    op.execute("ALTER ROLE bravo_agent SET default_transaction_read_only = on;")

    # bravo_writer: chỉ INSERT nháp + audit (không UPDATE/DELETE nghiệp vụ).
    op.execute("GRANT INSERT ON drafts, audit_log TO bravo_writer;")


def downgrade() -> None:
    op.execute("REVOKE INSERT ON drafts, audit_log FROM bravo_writer;")
    op.execute("DROP VIEW IF EXISTS app_safe.v_chunks_scoped;")
    op.execute("DROP VIEW IF EXISTS app_safe.v_archival_scoped;")
    op.execute("DROP SCHEMA IF EXISTS app_safe;")
    op.execute("ALTER ROLE bravo_agent RESET statement_timeout;")
    op.execute("ALTER ROLE bravo_agent RESET default_transaction_read_only;")
    op.execute("DROP ROLE IF EXISTS bravo_agent;")
    op.execute("DROP ROLE IF EXISTS bravo_writer;")
