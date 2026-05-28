from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid
import logging

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, undefer

from app.models.orm import (
    Device,
    AnalysisSession,
    LogEntry as LogEntryORM,
    DetectedViolation,
    ComplianceReport as ComplianceReportORM,
    AuditLog,
)
from app.models.enums import (
    AnalysisSessionStatus,
    AuditAction,
    DeviceStatus,
    ViolationStatus,
    ReportStatus,
    LogType as DbLogType,
)
from app.models.findings import ComplianceReport, Finding
from app.models.logs import LogEntry as LogEntryModel

logger = logging.getLogger(__name__)


def _map_log_type_to_db_enum(raw_log_type: str) -> str:
    raw_upper = raw_log_type.upper()
    
    if "TEMP" in raw_upper:
        return DbLogType.TELEMETRY.value
    if "SENSOR" in raw_upper:
        return DbLogType.TELEMETRY.value
    if "ALARM" in raw_upper:
        return DbLogType.ALERT.value
    if "WARNING" in raw_upper:
        return DbLogType.ALERT.value
    if "DOOR" in raw_upper:
        return DbLogType.EVENT.value
    if "DEVICE" in raw_upper:
        return DbLogType.STATUS.value
    if "FAN" in raw_upper:
        return DbLogType.TELEMETRY.value
    if "BATTERY" in raw_upper:
        return DbLogType.TELEMETRY.value
    if "VOLTAGE" in raw_upper:
        return DbLogType.TELEMETRY.value
    if "HUMIDITY" in raw_upper:
        return DbLogType.TELEMETRY.value
    if "COOLING" in raw_upper:
        return DbLogType.TELEMETRY.value
    if "SYNC" in raw_upper:
        return DbLogType.STATUS.value
    
    return DbLogType.TELEMETRY.value


_TELEMETRY_LOG_TYPES = {
    "TEMP_READING": "temperature",
    "HUMIDITY": "humidity",
    "VOLTAGE": "voltage",
    "FAN_SPEED": "fan_speed",
    "BATTERY_LEVEL": "battery",
}


def _extract_telemetry_series_from_logs(logs: List[LogEntryModel]) -> Dict[str, List[Dict[str, Any]]]:
    series: Dict[str, List[Dict[str, Any]]] = {key: [] for key in _TELEMETRY_LOG_TYPES.values()}

    for log_model in logs:
        metric_key = _TELEMETRY_LOG_TYPES.get(log_model.log_type.value)
        if not metric_key:
            continue

        value = log_model.parsed_value
        if value is None:
            continue

        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            continue

        timestamp = log_model.timestamp
        series[metric_key].append({
            "timestamp": timestamp.isoformat(),
            "time": timestamp.strftime("%H:%M"),
            "value": numeric_value,
            "source": "log_file",
        })

    for key in series:
        series[key] = sorted(series[key], key=lambda point: point["timestamp"])

    return {k: v for k, v in series.items() if v}


class PersistenceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_device(self, device_id: str) -> Device:
        if not device_id or device_id == "unknown":
            device_id = "default-device"

        result = await self.db.execute(
            select(Device).where(Device.name == device_id)
        )
        device = result.scalar_one_or_none()

        if device:
            return device

        device = Device(
            name=device_id,
            serial_number=device_id,
            status=DeviceStatus.REGISTERED,
        )
        self.db.add(device)
        await self.db.commit()
        await self.db.refresh(device)
        return device

    async def save_analysis_session(
        self,
        device_id: str,
        logs: List[LogEntryModel],
        report: ComplianceReport,
        config: Optional[Dict[str, Any]] = None,
        raw_logs: Optional[List[str]] = None,
    ) -> AnalysisSession:
        logger.info(f"Saving analysis session for device: {device_id}")

        device = await self.get_or_create_device(device_id)
        
        full_config: Dict[str, Any] = dict(config or {})
        
        existing_latest: Dict[str, Any] = {}
        if config and "_latest_analysis_data" in config:
            existing_latest = dict(config["_latest_analysis_data"])
        
        full_config["_latest_analysis_data"] = {
            "deviceId": device_id,
            "analyzedAt": report.analyzed_at.isoformat() if report.analyzed_at else datetime.utcnow().isoformat(),
            "rawLogs": raw_logs or [],
            "validationResult": report.to_dict(),
        }
        
        if existing_latest.get("temperatureData"):
            full_config["_latest_analysis_data"]["temperatureData"] = existing_latest["temperatureData"]
        elif logs:
            telemetry = _extract_telemetry_series_from_logs(logs)
            if telemetry.get("temperature"):
                full_config["_latest_analysis_data"]["temperatureData"] = telemetry["temperature"]
            if telemetry:
                full_config["_latest_analysis_data"]["telemetrySeries"] = telemetry
        elif existing_latest.get("telemetrySeries"):
            full_config["_latest_analysis_data"]["telemetrySeries"] = existing_latest["telemetrySeries"]

        session = AnalysisSession(
            device_id=device.id,
            status=AnalysisSessionStatus.PENDING,
            config=full_config,
            started_at=datetime.utcnow(),
        )
        self.db.add(session)
        await self.db.flush()

        log_entries: List[LogEntryORM] = []
        for log_model in logs:
            raw_log_type = log_model.log_type.value
            db_log_type = _map_log_type_to_db_enum(raw_log_type)
            
            log_orm = LogEntryORM(
                device_id=device.id,
                analysis_session_id=session.id,
                timestamp=log_model.timestamp,
                log_type=db_log_type,
                source=log_model.sensor_id or "log_parser",
                payload={
                    "raw_log_type": raw_log_type,
                    "raw_value": log_model.raw_value,
                    "parsed_value": log_model.parsed_value,
                    "metadata": log_model.metadata,
                },
            )
            log_entries.append(log_orm)

        self.db.add_all(log_entries)
        await self.db.flush()

        findings = report.findings or []
        for finding in findings:
            if finding.passed:
                continue

            evidence_list = []
            for ev in finding.evidence:
                evidence_list.append({
                    "entry_index": ev.entry_index,
                    "timestamp": ev.timestamp.isoformat() if ev.timestamp else None,
                    "log_type": ev.log_type,
                    "raw_value": ev.raw_value,
                    "explanation": ev.explanation,
                })

            violation = DetectedViolation(
                device_id=device.id,
                analysis_session_id=session.id,
                reg_code=finding.rule_id,
                severity=finding.severity.value,
                status=ViolationStatus.OPEN,
                description=finding.message,
                evidence={
                    "rule_description": finding.rule_description,
                    "category": finding.category,
                    "findings_evidence": evidence_list,
                    "remediation_hint": finding.remediation_hint,
                },
                risk_score=1.0 if finding.severity.value == "critical" else 0.5,
                detected_at=finding.timestamp,
            )
            self.db.add(violation)

        session.status = AnalysisSessionStatus.COMPLETED
        session.completed_at = datetime.utcnow()
        session.result_summary=f"Total: {report.total_entries} logs, Passed: {report.passed_count}, Failed: {report.failed_count}, Critical: {report.critical_count}"

        session_id_str = str(session.id)
        
        await self.db.commit()

        await self.log_audit(
            action=AuditAction.CREATE,
            actor="system",
            resource_type="analysis_session",
            resource_id=session_id_str,
            description=f"Analysis session created for device {device_id}",
            new_value={
                "device_id": device_id,
                "total_logs": len(logs),
                "passed_count": report.passed_count,
                "failed_count": report.failed_count,
                "critical_count": report.critical_count,
            },
        )

        logger.info(f"Analysis session saved: {session_id_str}")
        return session

    async def update_analysis_with_ai(
        self,
        session_id: uuid.UUID,
        ai_analysis: Any,
    ) -> Optional[AnalysisSession]:
        from app.ai.analyst.models import AIAnalysisResult
        
        logger.info(f"Updating analysis session with AI analysis: {session_id}")
        
        session = await self.get_analysis_session(session_id)
        if not session:
            logger.warning(f"Session not found for AI update: {session_id}")
            return None
        
        ai_analysis_dict: Dict[str, Any] = {}
        if isinstance(ai_analysis, AIAnalysisResult):
            try:
                ai_analysis_dict = ai_analysis.model_dump(mode='json')
            except Exception as e:
                logger.warning(f"model_dump(mode='json') failed: {e}, trying fallback")
                try:
                    import json
                    from pydantic.json import pydantic_encoder
                    ai_analysis_dict = json.loads(json.dumps(ai_analysis.model_dump(), default=pydantic_encoder))
                except Exception as e2:
                    logger.warning(f"Fallback also failed: {e2}, using manual conversion")
                    ai_analysis_dict = {
                        "session_risk_overview": ai_analysis.session_risk_overview.model_dump() if hasattr(ai_analysis.session_risk_overview, 'model_dump') else str(ai_analysis.session_risk_overview),
                        "insights": [
                            {
                                "id": i.id,
                                "priority": i.priority.value if hasattr(i.priority, 'value') else str(i.priority),
                                "category": i.category,
                                "title": i.title,
                                "evidence": i.evidence,
                                "why_matters": i.why_matters,
                                "risk_score_contribution": i.risk_score_contribution,
                            }
                            for i in ai_analysis.insights
                        ],
                        "natural_language_summary": ai_analysis.natural_language_summary,
                        "generated_at": ai_analysis.generated_at.isoformat() if ai_analysis.generated_at else None,
                    }
        elif isinstance(ai_analysis, dict):
            ai_analysis_dict = ai_analysis
        
        if not session.config:
            session.config = {}
        
        session.config["_ai_analysis"] = ai_analysis_dict
        
        logger.info(f"[DEBUG] Before commit: session.config keys = {list(session.config.keys())}")
        logger.info(f"[DEBUG] _ai_analysis has insights = {len(ai_analysis_dict.get('insights', []))}")
        
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(session, "config")
        
        await self.db.commit()
        await self.db.refresh(session)
        
        logger.info(f"[DEBUG] After refresh: session.config keys = {list(session.config.keys()) if session.config else []}")
        if session.config and "_ai_analysis" in session.config:
            logger.info(f"[DEBUG] _ai_analysis in DB has insights = {len(session.config['_ai_analysis'].get('insights', []))}")
        
        await self.log_audit(
            action=AuditAction.UPDATE,
            actor="system",
            resource_type="analysis_session",
            resource_id=str(session_id),
            description="AI analysis added to session",
            new_value={
                "has_ai_analysis": True,
                "insights_count": len(ai_analysis_dict.get("insights", [])),
                "risk_level": ai_analysis_dict.get("session_risk_overview", {}).get("risk_level"),
            },
        )
        
        logger.info(f"AI analysis added to session: {session_id}")
        return session

    async def get_analysis_sessions(
        self,
        limit: int = 20,
        offset: int = 0,
        device_id: Optional[str] = None,
    ) -> tuple[List[AnalysisSession], int]:
        query = select(AnalysisSession).options(
            selectinload(AnalysisSession.device),
            selectinload(AnalysisSession.violations),
            undefer(AnalysisSession.config),
        )

        count_query = select(AnalysisSession)

        if device_id:
            device_result = await self.db.execute(
                select(Device).where(Device.name == device_id)
            )
            device = device_result.scalar_one_or_none()
            if device:
                query = query.where(AnalysisSession.device_id == device.id)
                count_query = count_query.where(AnalysisSession.device_id == device.id)

        query = query.order_by(AnalysisSession.created_at.desc())
        count_result = await self.db.execute(count_query)
        total = len(count_result.scalars().all())

        query = query.offset(offset).limit(limit)
        result = await self.db.execute(query)
        sessions = list(result.scalars().unique().all())

        return sessions, total

    async def get_analysis_session(self, session_id: uuid.UUID) -> Optional[AnalysisSession]:
        query = select(AnalysisSession).options(
            selectinload(AnalysisSession.device),
            selectinload(AnalysisSession.log_entries),
            selectinload(AnalysisSession.violations),
            undefer(AnalysisSession.config),
        ).where(AnalysisSession.id == session_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def delete_analysis_session(self, session_id: uuid.UUID) -> bool:
        session = await self.get_analysis_session(session_id)
        if not session:
            return False

        device_name = session.device.name if session.device else "unknown"
        session_id_str = str(session_id)

        await self.db.delete(session)
        await self.db.commit()

        await self.log_audit(
            action=AuditAction.DELETE,
            actor="system",
            resource_type="analysis_session",
            resource_id=session_id_str,
            description=f"Analysis session deleted for device {device_name}",
            old_value={
                "device_id": device_name,
            },
        )

        logger.info(f"Analysis session deleted: {session_id_str}")
        return True

    async def delete_all_analysis_sessions(self) -> int:
        from sqlalchemy import delete

        result = await self.db.execute(
            select(AnalysisSession.id)
        )
        session_ids = [str(r[0]) for r in result.all()]
        count = len(session_ids)

        if count > 0:
            await self.db.execute(delete(AnalysisSession))
            await self.db.commit()

            for session_id in session_ids:
                await self.log_audit(
                    action=AuditAction.DELETE,
                    actor="system",
                    resource_type="analysis_session",
                    resource_id=session_id,
                    description="Analysis session deleted via bulk delete",
                )

            logger.info(f"Deleted {count} analysis sessions (bulk)")

        return count

    async def save_compliance_report(
        self,
        device_id: str,
        aggregated_report: Any,
    ) -> ComplianceReportORM:
        logger.info(f"Saving compliance report for device: {device_id}")

        device = await self.get_or_create_device(device_id)

        summary_dict = {}
        if hasattr(aggregated_report, 'summary'):
            summary_dict = dict(aggregated_report.summary)

        report = ComplianceReportORM(
            device_id=device.id,
            status=ReportStatus.COMPLETED,
            period_start=aggregated_report.time_range_start or datetime.utcnow(),
            period_end=aggregated_report.time_range_end or datetime.utcnow(),
            compliance_score=self._calculate_compliance_score(aggregated_report),
            summary=summary_dict,
            generated_by="system",
            generated_at=datetime.utcnow(),
        )
        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)

        await self.log_audit(
            action=AuditAction.GENERATE_REPORT,
            actor="system",
            resource_type="compliance_report",
            resource_id=str(report.id),
            description=f"Compliance report generated for device {device_id}",
        )

        return report

    async def get_reports(
        self,
        limit: int = 20,
        offset: int = 0,
        device_id: Optional[str] = None,
    ) -> tuple[List[ComplianceReportORM], int]:
        query = select(ComplianceReportORM).options(
            selectinload(ComplianceReportORM.device),
        )

        count_query = select(ComplianceReportORM)

        if device_id:
            device_result = await self.db.execute(
                select(Device).where(Device.name == device_id)
            )
            device = device_result.scalar_one_or_none()
            if device:
                query = query.where(ComplianceReportORM.device_id == device.id)
                count_query = count_query.where(ComplianceReportORM.device_id == device.id)

        query = query.order_by(ComplianceReportORM.created_at.desc())
        count_result = await self.db.execute(count_query)
        total = len(count_result.scalars().all())

        query = query.offset(offset).limit(limit)
        result = await self.db.execute(query)
        reports = list(result.scalars().unique().all())

        return reports, total

    async def get_logs(
        self,
        device_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[List[LogEntryORM], int]:
        query = select(LogEntryORM).options(
            selectinload(LogEntryORM.device),
        )

        count_query = select(LogEntryORM)

        conditions = []

        if device_id:
            device_result = await self.db.execute(
                select(Device).where(Device.name == device_id)
            )
            device = device_result.scalar_one_or_none()
            if device:
                conditions.append(LogEntryORM.device_id == device.id)

        if start_date:
            conditions.append(LogEntryORM.timestamp >= start_date)
        if end_date:
            conditions.append(LogEntryORM.timestamp <= end_date)

        if conditions:
            combined = and_(*conditions)
            query = query.where(combined)
            count_query = count_query.where(combined)

        query = query.order_by(LogEntryORM.timestamp.desc())
        count_result = await self.db.execute(count_query)
        total = len(count_result.scalars().all())

        query = query.offset(offset).limit(limit)
        result = await self.db.execute(query)
        logs = list(result.scalars().unique().all())

        return logs, total

    async def log_audit(
        self,
        action: AuditAction,
        actor: str = "system",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        description: Optional[str] = None,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        request_context: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        audit_entry = AuditLog(
            action=action.value,
            actor=actor,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            old_value=old_value,
            new_value=new_value,
            request_context=request_context,
        )
        self.db.add(audit_entry)
        await self.db.commit()
        await self.db.refresh(audit_entry)
        return audit_entry

    def _calculate_compliance_score(self, aggregated_report: Any) -> float:
        if not hasattr(aggregated_report, 'summary'):
            return 100.0

        summary = aggregated_report.summary or {}

        critical = summary.get('critical_count', 0) or summary.get('critical', 0) or 0
        high = summary.get('high_count', 0) or summary.get('high', 0) or 0
        medium = summary.get('medium_count', 0) or summary.get('medium', 0) or 0
        low = summary.get('low_count', 0) or summary.get('low', 0) or 0

        if critical > 0:
            return 0.0

        penalty = (critical * 35) + (high * 15) + (medium * 5) + (low * 1)
        score = max(0.0, 100.0 - penalty)
        return score
