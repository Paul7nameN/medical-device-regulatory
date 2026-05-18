"""Initial database schema

Revision ID: 0001
Revises: 
Create Date: 2026-05-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    sa.Enum(
        "ONLINE", "OFFLINE", "MAINTENANCE", "REGISTERED",
        name="device_status_enum"
    ).create(op.get_bind(), checkfirst=True)

    sa.Enum(
        "PENDING", "COMPLETED", "FAILED",
        name="analysis_session_status_enum"
    ).create(op.get_bind(), checkfirst=True)

    sa.Enum(
        "TELEMETRY", "EVENT", "ALERT", "STATUS",
        name="log_type_enum"
    ).create(op.get_bind(), checkfirst=True)

    sa.Enum(
        "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO",
        name="severity_enum"
    ).create(op.get_bind(), checkfirst=True)

    sa.Enum(
        "OPEN", "ACKNOWLEDGED", "RESOLVED",
        name="violation_status_enum"
    ).create(op.get_bind(), checkfirst=True)

    sa.Enum(
        "GENERATING", "COMPLETED", "FAILED",
        name="report_status_enum"
    ).create(op.get_bind(), checkfirst=True)

    sa.Enum(
        "CREATE", "READ", "UPDATE", "DELETE", "LOGIN", "EXPORT", "GENERATE_REPORT",
        name="audit_action_enum"
    ).create(op.get_bind(), checkfirst=True)

    op.create_table(
        "devices",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("model", sa.Text(), nullable=True),
        sa.Column("serial_number", sa.Text(), nullable=True),
        sa.Column("status", postgresql.ENUM(
            "ONLINE", "OFFLINE", "MAINTENANCE", "REGISTERED",
            name="device_status_enum", create_type=False
        ), server_default="REGISTERED", nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("TIMEZONE('utc', NOW())"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("TIMEZONE('utc', NOW())"), nullable=False),
        sa.PrimaryKeyConstraint("id")
    )

    op.create_index(
        "idx_devices_serial_number", "devices", ["serial_number"], unique=True
    )

    op.create_table(
        "analysis_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", postgresql.ENUM(
            "PENDING", "COMPLETED", "FAILED",
            name="analysis_session_status_enum", create_type=False
        ), server_default="PENDING", nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.Column("result_path", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), server_default=sa.text("TIMEZONE('utc', NOW())"), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("TIMEZONE('utc', NOW())"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("TIMEZONE('utc', NOW())"), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id")
    )

    op.create_index(
        "idx_analysis_sessions_device_id", "analysis_sessions", ["device_id"]
    )
    op.create_index(
        "idx_analysis_sessions_device_id_started_at", "analysis_sessions", ["device_id", "started_at"]
    )
    op.create_index(
        "idx_analysis_sessions_status", "analysis_sessions", ["status"]
    )

    op.create_table(
        "log_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("analysis_session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("log_type", postgresql.ENUM(
            "TELEMETRY", "EVENT", "ALERT", "STATUS",
            name="log_type_enum", create_type=False
        ), nullable=False),
        sa.Column("source", sa.Text(), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("TIMEZONE('utc', NOW())"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("TIMEZONE('utc', NOW())"), nullable=False),
        sa.ForeignKeyConstraint(["analysis_session_id"], ["analysis_sessions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    op.create_index("idx_log_entries_timestamp", "log_entries", ["timestamp"])
    op.create_index("idx_log_entries_device_id", "log_entries", ["device_id"])
    op.create_index("idx_log_entries_analysis_session_id", "log_entries", ["analysis_session_id"])
    op.create_index("idx_log_entries_log_type", "log_entries", ["log_type"])
    op.create_index("idx_log_entries_device_timestamp", "log_entries", ["device_id", "timestamp"])

    op.create_table(
        "compliance_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", postgresql.ENUM(
            "GENERATING", "COMPLETED", "FAILED",
            name="report_status_enum", create_type=False
        ), server_default="GENERATING", nullable=False),
        sa.Column("period_start", sa.DateTime(), nullable=False),
        sa.Column("period_end", sa.DateTime(), nullable=False),
        sa.Column("compliance_score", sa.Float(), nullable=True),
        sa.Column("summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("report_path", sa.Text(), nullable=True),
        sa.Column("generated_by", sa.Text(), nullable=True),
        sa.Column("generated_at", sa.DateTime(), server_default=sa.text("TIMEZONE('utc', NOW())"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("TIMEZONE('utc', NOW())"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("TIMEZONE('utc', NOW())"), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id")
    )

    op.create_index("idx_reports_device_id", "compliance_reports", ["device_id"])
    op.create_index("idx_reports_status", "compliance_reports", ["status"])
    op.create_index("idx_reports_generated_at", "compliance_reports", ["generated_at"])
    op.create_index("idx_reports_device_id_period_start", "compliance_reports", ["device_id", "period_start"])

    op.create_table(
        "detected_violations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("analysis_session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("log_entry_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reg_code", sa.Text(), nullable=False),
        sa.Column("severity", postgresql.ENUM(
            "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO",
            name="severity_enum", create_type=False
        ), nullable=False),
        sa.Column("status", postgresql.ENUM(
            "OPEN", "ACKNOWLEDGED", "RESOLVED",
            name="violation_status_enum", create_type=False
        ), server_default="OPEN", nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("risk_score", sa.Float(), nullable=True),
        sa.Column("detected_at", sa.DateTime(), server_default=sa.text("TIMEZONE('utc', NOW())"), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("TIMEZONE('utc', NOW())"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("TIMEZONE('utc', NOW())"), nullable=False),
        sa.ForeignKeyConstraint(["analysis_session_id"], ["analysis_sessions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["log_entry_id"], ["log_entries.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id")
    )

    op.create_index("idx_violations_device_id", "detected_violations", ["device_id"])
    op.create_index("idx_violations_analysis_session_id", "detected_violations", ["analysis_session_id"])
    op.create_index("idx_violations_log_entry_id", "detected_violations", ["log_entry_id"])
    op.create_index("idx_violations_reg_code", "detected_violations", ["reg_code"])
    op.create_index("idx_violations_severity", "detected_violations", ["severity"])
    op.create_index("idx_violations_status", "detected_violations", ["status"])
    op.create_index("idx_violations_device_id_detected_at", "detected_violations", ["device_id", "detected_at"])

    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("TIMEZONE('utc', NOW())"), nullable=False),
        sa.Column("action", postgresql.ENUM(
            "CREATE", "READ", "UPDATE", "DELETE", "LOGIN", "EXPORT", "GENERATE_REPORT",
            name="audit_action_enum", create_type=False
        ), nullable=False),
        sa.Column("actor", sa.Text(), nullable=True),
        sa.Column("resource_type", sa.Text(), nullable=True),
        sa.Column("resource_id", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("old_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("new_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("request_context", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id")
    )

    op.create_index("idx_audit_log_created_at", "audit_log", ["created_at"])
    op.create_index("idx_audit_log_action", "audit_log", ["action"])
    op.create_index("idx_audit_log_resource_type", "audit_log", ["resource_type"])
    op.create_index("idx_audit_log_resource_type_resource_id", "audit_log", ["resource_type", "resource_id"])


def downgrade():
    op.drop_index("idx_audit_log_resource_type_resource_id", table_name="audit_log")
    op.drop_index("idx_audit_log_resource_type", table_name="audit_log")
    op.drop_index("idx_audit_log_action", table_name="audit_log")
    op.drop_index("idx_audit_log_created_at", table_name="audit_log")
    op.drop_table("audit_log")

    op.drop_index("idx_violations_device_id_detected_at", table_name="detected_violations")
    op.drop_index("idx_violations_status", table_name="detected_violations")
    op.drop_index("idx_violations_severity", table_name="detected_violations")
    op.drop_index("idx_violations_reg_code", table_name="detected_violations")
    op.drop_index("idx_violations_log_entry_id", table_name="detected_violations")
    op.drop_index("idx_violations_analysis_session_id", table_name="detected_violations")
    op.drop_index("idx_violations_device_id", table_name="detected_violations")
    op.drop_table("detected_violations")

    op.drop_index("idx_reports_device_id_period_start", table_name="compliance_reports")
    op.drop_index("idx_reports_generated_at", table_name="compliance_reports")
    op.drop_index("idx_reports_status", table_name="compliance_reports")
    op.drop_index("idx_reports_device_id", table_name="compliance_reports")
    op.drop_table("compliance_reports")

    op.drop_index("idx_log_entries_device_timestamp", table_name="log_entries")
    op.drop_index("idx_log_entries_log_type", table_name="log_entries")
    op.drop_index("idx_log_entries_analysis_session_id", table_name="log_entries")
    op.drop_index("idx_log_entries_device_id", table_name="log_entries")
    op.drop_index("idx_log_entries_timestamp", table_name="log_entries")
    op.drop_table("log_entries")

    op.drop_index("idx_analysis_sessions_status", table_name="analysis_sessions")
    op.drop_index("idx_analysis_sessions_device_id_started_at", table_name="analysis_sessions")
    op.drop_index("idx_analysis_sessions_device_id", table_name="analysis_sessions")
    op.drop_table("analysis_sessions")

    op.drop_index("idx_devices_serial_number", table_name="devices")
    op.drop_table("devices")

    sa.Enum(name="audit_action_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="report_status_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="violation_status_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="severity_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="log_type_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="analysis_session_status_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="device_status_enum").drop(op.get_bind(), checkfirst=True)
