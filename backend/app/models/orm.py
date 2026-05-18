import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Index, ForeignKey, Enum as SQLEnum, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database import Base, UUIDMixin, TimestampMixin
from app.models.enums import (
    LogType,
    AnalysisSessionStatus,
    ViolationStatus,
    ReportStatus,
    AuditAction,
    DeviceStatus,
)
from app.models.findings import Severity


class Device(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "devices"

    name: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[Optional[str]] = mapped_column(Text)
    serial_number: Mapped[Optional[str]] = mapped_column(Text, unique=True)
    status: Mapped[DeviceStatus] = mapped_column(
        SQLEnum(DeviceStatus, name="device_status_enum"),
        default=DeviceStatus.REGISTERED,
        server_default="registered",
    )
    last_seen_at: Mapped[Optional[datetime]] = mapped_column()

    analysis_sessions: Mapped[List["AnalysisSession"]] = relationship(
        "AnalysisSession", back_populates="device", cascade="all, delete-orphan"
    )
    log_entries: Mapped[List["LogEntry"]] = relationship(
        "LogEntry", back_populates="device", cascade="all, delete-orphan"
    )
    violations: Mapped[List["DetectedViolation"]] = relationship(
        "DetectedViolation", back_populates="device", cascade="all, delete-orphan"
    )
    reports: Mapped[List["ComplianceReport"]] = relationship(
        "ComplianceReport", back_populates="device", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_devices_serial_number", "serial_number", unique=True),
    )


class AnalysisSession(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "analysis_sessions"

    device_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("devices.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[AnalysisSessionStatus] = mapped_column(
        SQLEnum(AnalysisSessionStatus, name="analysis_session_status_enum"),
        default=AnalysisSessionStatus.PENDING,
        server_default="pending",
    )
    config: Mapped[Optional[dict]] = mapped_column(JSONB)
    result_summary: Mapped[Optional[str]] = mapped_column(Text)
    result_path: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, server_default=text("TIMEZONE('utc', NOW())")
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column()

    device: Mapped[Optional["Device"]] = relationship("Device", back_populates="analysis_sessions")
    log_entries: Mapped[List["LogEntry"]] = relationship("LogEntry", back_populates="analysis_session")
    violations: Mapped[List["DetectedViolation"]] = relationship(
        "DetectedViolation", back_populates="analysis_session"
    )

    __table_args__ = (
        Index("idx_analysis_sessions_device_id", "device_id"),
        Index("idx_analysis_sessions_device_id_started_at", "device_id", "started_at"),
        Index("idx_analysis_sessions_status", "status"),
    )


class LogEntry(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "log_entries"

    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
    )
    analysis_session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analysis_sessions.id", ondelete="CASCADE"), nullable=True
    )
    timestamp: Mapped[datetime] = mapped_column(nullable=False)
    log_type: Mapped[LogType] = mapped_column(
        SQLEnum(LogType, name="log_type_enum"), nullable=False
    )
    source: Mapped[Optional[str]] = mapped_column(Text)
    payload: Mapped[Optional[dict]] = mapped_column(JSONB)

    device: Mapped["Device"] = relationship("Device", back_populates="log_entries")
    analysis_session: Mapped[Optional["AnalysisSession"]] = relationship(
        "AnalysisSession", back_populates="log_entries"
    )
    violations: Mapped[List["DetectedViolation"]] = relationship(
        "DetectedViolation", back_populates="log_entry"
    )

    __table_args__ = (
        Index("idx_log_entries_timestamp", "timestamp"),
        Index("idx_log_entries_device_id", "device_id"),
        Index("idx_log_entries_analysis_session_id", "analysis_session_id"),
        Index("idx_log_entries_log_type", "log_type"),
        Index("idx_log_entries_device_timestamp", "device_id", "timestamp"),
    )


class DetectedViolation(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "detected_violations"

    device_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("devices.id", ondelete="SET NULL"), nullable=True
    )
    analysis_session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analysis_sessions.id", ondelete="CASCADE"), nullable=True
    )
    log_entry_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("log_entries.id", ondelete="SET NULL"), nullable=True
    )
    reg_code: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[Severity] = mapped_column(
        SQLEnum(Severity, name="severity_enum"), nullable=False
    )
    status: Mapped[ViolationStatus] = mapped_column(
        SQLEnum(ViolationStatus, name="violation_status_enum"),
        default=ViolationStatus.OPEN,
        server_default="open",
    )
    description: Mapped[Optional[str]] = mapped_column(Text)
    evidence: Mapped[Optional[dict]] = mapped_column(JSONB)
    risk_score: Mapped[Optional[float]] = mapped_column()
    detected_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, server_default=text("TIMEZONE('utc', NOW())")
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column()

    device: Mapped[Optional["Device"]] = relationship("Device", back_populates="violations")
    analysis_session: Mapped[Optional["AnalysisSession"]] = relationship(
        "AnalysisSession", back_populates="violations"
    )
    log_entry: Mapped[Optional["LogEntry"]] = relationship("LogEntry", back_populates="violations")

    __table_args__ = (
        Index("idx_violations_device_id", "device_id"),
        Index("idx_violations_analysis_session_id", "analysis_session_id"),
        Index("idx_violations_log_entry_id", "log_entry_id"),
        Index("idx_violations_reg_code", "reg_code"),
        Index("idx_violations_severity", "severity"),
        Index("idx_violations_status", "status"),
        Index("idx_violations_device_id_detected_at", "device_id", "detected_at"),
    )


class ComplianceReport(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "compliance_reports"

    device_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("devices.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[ReportStatus] = mapped_column(
        SQLEnum(ReportStatus, name="report_status_enum"),
        default=ReportStatus.GENERATING,
        server_default="generating",
    )
    period_start: Mapped[datetime] = mapped_column()
    period_end: Mapped[datetime] = mapped_column()
    compliance_score: Mapped[Optional[float]] = mapped_column()
    summary: Mapped[Optional[dict]] = mapped_column(JSONB)
    report_path: Mapped[Optional[str]] = mapped_column(Text)
    generated_by: Mapped[Optional[str]] = mapped_column(Text)
    generated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, server_default=text("TIMEZONE('utc', NOW())")
    )

    device: Mapped[Optional["Device"]] = relationship("Device", back_populates="reports")

    __table_args__ = (
        Index("idx_reports_device_id", "device_id"),
        Index("idx_reports_status", "status"),
        Index("idx_reports_generated_at", "generated_at"),
        Index("idx_reports_device_id_period_start", "device_id", "period_start"),
    )


class AuditLogOnlyCreatedMixin:
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        server_default=text("TIMEZONE('utc', NOW())"),
    )


class AuditLog(UUIDMixin, AuditLogOnlyCreatedMixin, Base):
    __tablename__ = "audit_log"

    action: Mapped[AuditAction] = mapped_column(
        SQLEnum(AuditAction, name="audit_action_enum"), nullable=False
    )
    actor: Mapped[Optional[str]] = mapped_column(Text)
    resource_type: Mapped[Optional[str]] = mapped_column(Text)
    resource_id: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    old_value: Mapped[Optional[dict]] = mapped_column(JSONB)
    new_value: Mapped[Optional[dict]] = mapped_column(JSONB)
    request_context: Mapped[Optional[dict]] = mapped_column(JSONB)

    __table_args__ = (
        Index("idx_audit_log_created_at", "created_at"),
        Index("idx_audit_log_action", "action"),
        Index("idx_audit_log_resource_type", "resource_type"),
        Index("idx_audit_log_resource_type_resource_id", "resource_type", "resource_id"),
    )
