"""Audit log immutability with RLS policies (REG-DATA-1)

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-12

"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    op.execute("ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;")

    op.execute("""
        CREATE POLICY audit_log_select ON audit_log
        FOR SELECT
        USING (true);
    """)

    op.execute("""
        CREATE POLICY audit_log_insert ON audit_log
        FOR INSERT
        WITH CHECK (true);
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_roles WHERE rolname = 'med_therm_app'
            ) THEN
                CREATE ROLE med_therm_app;
            END IF;
        END
        $$;
    """)

    op.execute("ALTER TABLE audit_log FORCE ROW LEVEL SECURITY;")

    op.execute("COMMENT ON TABLE audit_log IS 'Immutable audit trail table - REG-DATA-1 compliance: no UPDATE/DELETE allowed';")


def downgrade():
    op.execute("ALTER TABLE audit_log NO FORCE ROW LEVEL SECURITY;")

    op.execute("DROP POLICY IF EXISTS audit_log_insert ON audit_log;")
    op.execute("DROP POLICY IF EXISTS audit_log_select ON audit_log;")

    op.execute("ALTER TABLE audit_log DISABLE ROW LEVEL SECURITY;")
