"""Change FK ondelete from SET NULL to CASCADE for analysis_session

When an AnalysisSession is deleted:
- LogEntry with that session_id should be CASCADE deleted
- DetectedViolation with that session_id should be CASCADE deleted

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-16

"""
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    op.execute("""
        DO $$
        DECLARE
            constraint_name text;
        BEGIN
            SELECT tc.constraint_name INTO constraint_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
              ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = 'log_entries'
              AND kcu.column_name = 'analysis_session_id'
              AND tc.constraint_type = 'FOREIGN KEY';

            IF constraint_name IS NOT NULL THEN
                EXECUTE 'ALTER TABLE log_entries DROP CONSTRAINT ' || quote_ident(constraint_name);
            END IF;
        END $$;
    """)

    op.execute("""
        ALTER TABLE log_entries
        ADD CONSTRAINT fk_log_entries_analysis_session
        FOREIGN KEY (analysis_session_id)
        REFERENCES analysis_sessions(id)
        ON DELETE CASCADE;
    """)

    op.execute("""
        DO $$
        DECLARE
            constraint_name text;
        BEGIN
            SELECT tc.constraint_name INTO constraint_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
              ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = 'detected_violations'
              AND kcu.column_name = 'analysis_session_id'
              AND tc.constraint_type = 'FOREIGN KEY';

            IF constraint_name IS NOT NULL THEN
                EXECUTE 'ALTER TABLE detected_violations DROP CONSTRAINT ' || quote_ident(constraint_name);
            END IF;
        END $$;
    """)

    op.execute("""
        ALTER TABLE detected_violations
        ADD CONSTRAINT fk_detected_violations_analysis_session
        FOREIGN KEY (analysis_session_id)
        REFERENCES analysis_sessions(id)
        ON DELETE CASCADE;
    """)


def downgrade():
    op.execute("""
        ALTER TABLE log_entries
        DROP CONSTRAINT IF EXISTS fk_log_entries_analysis_session;
    """)

    op.execute("""
        ALTER TABLE log_entries
        ADD CONSTRAINT fk_log_entries_analysis_session_setnull
        FOREIGN KEY (analysis_session_id)
        REFERENCES analysis_sessions(id)
        ON DELETE SET NULL;
    """)

    op.execute("""
        ALTER TABLE detected_violations
        DROP CONSTRAINT IF EXISTS fk_detected_violations_analysis_session;
    """)

    op.execute("""
        ALTER TABLE detected_violations
        ADD CONSTRAINT fk_detected_violations_analysis_session_setnull
        FOREIGN KEY (analysis_session_id)
        REFERENCES analysis_sessions(id)
        ON DELETE SET NULL;
    """)
