from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.regulatory.log_parser import parse_raw_logs
from app.regulatory.engine import RegulatoryEngine
from app.models.findings import ComplianceReport
from app.models.logs import LogEntry
from app.database import get_async_db
from app.services.persistence import PersistenceService

router = APIRouter()


class LogEntryInput(BaseModel):
    timestamp: str
    log_type: str
    raw_value: str
    parsed_value: Optional[Any] = None
    sensor_id: Optional[str] = None


class ValidateRequest(BaseModel):
    raw_logs: Optional[List[str]] = None
    entries: Optional[List[LogEntryInput]] = None
    filter_rules: Optional[List[str]] = None
    include_sources: Optional[List[str]] = None
    exclude_sources: Optional[List[str]] = None
    device_id: Optional[str] = None


class ValidateResponse(BaseModel):
    report: dict
    analysis_session_id: Optional[str] = None


class AnalysisSessionListItem(BaseModel):
    id: str
    device_name: Optional[str]
    status: str
    created_at: str
    completed_at: Optional[str]
    result_summary: Optional[str]
    violation_count: int
    latest_analysis_data: Optional[dict[str, Any]] = None
    ai_analysis: Optional[dict[str, Any]] = None


class AnalysisSessionDetail(AnalysisSessionListItem):
    logs: List[dict]
    violations: List[dict]
    config: Optional[dict]


class AnalysisListResponse(BaseModel):
    items: List[AnalysisSessionListItem]
    total: int
    limit: int
    offset: int


class DeleteAnalysisResponse(BaseModel):
    success: bool
    deleted: int
    session_id: Optional[str] = None


def _parse_entries_from_input(input_entries: List[LogEntryInput]) -> List[LogEntry]:
    entries: List[LogEntry] = []

    for entry_input in input_entries:
        try:
            ts = datetime.fromisoformat(entry_input.timestamp.replace('Z', '+00:00'))
        except ValueError:
            try:
                ts = datetime.strptime(entry_input.timestamp, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue

        from app.models.logs import LogType
        try:
            log_type = LogType(entry_input.log_type)
        except ValueError:
            continue

        entry = LogEntry(
            timestamp=ts,
            log_type=log_type,
            raw_value=entry_input.raw_value,
            parsed_value=entry_input.parsed_value,
            sensor_id=entry_input.sensor_id,
            metadata={}
        )
        entries.append(entry)

    return entries


def _orm_session_to_list_item(session) -> dict:
    import logging
    import json
    logger = logging.getLogger(__name__)
    
    from app.models.orm import AnalysisSession
    device_name = session.device.name if session.device else None
    
    config = session.config or {}
    
    logger.info(f"[DEBUG] _orm_session_to_list_item: session.id = {session.id}")
    logger.info(f"[DEBUG] config type = {type(config)}")
    logger.info(f"[DEBUG] config value = {json.dumps(config, default=str, indent=2)[:2000]}")
    logger.info(f"[DEBUG] config keys = {list(config.keys()) if isinstance(config, dict) else 'NOT A DICT'}")
    
    latest_analysis_data = None
    ai_analysis = None
    
    if isinstance(config, dict):
        latest_analysis_data = config.get("_latest_analysis_data")
        ai_analysis = config.get("_ai_analysis")
        logger.info(f"[DEBUG] _ai_analysis from config = {ai_analysis is not None}")
        if ai_analysis:
            logger.info(f"[DEBUG] _ai_analysis type = {type(ai_analysis)}")
            logger.info(f"[DEBUG] _ai_analysis keys = {list(ai_analysis.keys()) if isinstance(ai_analysis, dict) else 'NOT A DICT'}")
    else:
        logger.warning(f"[DEBUG] config is NOT a dict! type={type(config)}, value={config}")
    
    result = {
        "id": str(session.id),
        "device_name": device_name,
        "status": session.status.value if hasattr(session.status, 'value') else str(session.status),
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        "result_summary": session.result_summary,
        "violation_count": len(session.violations) if session.violations else 0,
    }
    
    if latest_analysis_data:
        result["latest_analysis_data"] = latest_analysis_data
        logger.info(f"[DEBUG] Added latest_analysis_data to result")
    
    if ai_analysis:
        result["ai_analysis"] = ai_analysis
        logger.info(f"[DEBUG] Added ai_analysis to result with {len(ai_analysis.get('insights', []))} insights")
    else:
        logger.info(f"[DEBUG] NOT adding ai_analysis to result (ai_analysis={ai_analysis})")
    
    logger.info(f"[DEBUG] Final result keys = {list(result.keys())}")
    
    return result


def _orm_log_to_dict(log_entry) -> dict:
    payload = log_entry.payload or {}
    return {
        "id": str(log_entry.id),
        "timestamp": log_entry.timestamp.isoformat() if log_entry.timestamp else None,
        "log_type": log_entry.log_type,
        "raw_log_type": payload.get("raw_log_type"),
        "source": log_entry.source,
        "raw_value": payload.get("raw_value"),
        "parsed_value": payload.get("parsed_value"),
    }


def _orm_violation_to_dict(violation) -> dict:
    evidence = violation.evidence or {}
    return {
        "id": str(violation.id),
        "reg_code": violation.reg_code,
        "severity": violation.severity,
        "status": violation.status,
        "description": violation.description,
        "rule_description": evidence.get("rule_description"),
        "category": evidence.get("category"),
        "findings_evidence": evidence.get("findings_evidence"),
        "remediation_hint": evidence.get("remediation_hint"),
        "risk_score": violation.risk_score,
        "detected_at": violation.detected_at.isoformat() if violation.detected_at else None,
    }


@router.post("/validate", response_model=ValidateResponse)
async def validate_logs(
    request: ValidateRequest,
    db: AsyncSession = Depends(get_async_db),
):
    entries: List[LogEntry] = []
    device_id = request.device_id or "unknown"

    if request.raw_logs:
        parsed_entries, warnings = parse_raw_logs(request.raw_logs)
        entries.extend(parsed_entries)

    if request.entries:
        parsed_from_input = _parse_entries_from_input(request.entries)
        entries.extend(parsed_from_input)

    if not entries:
        raise HTTPException(
            status_code=400,
            detail="No log entries provided. Include 'raw_logs' or 'entries' in request."
        )

    engine = RegulatoryEngine()
    report = engine.validate(
        logs=entries,
        filter_rules=request.filter_rules,
        device_id=device_id,
        include_sources=request.include_sources,
        exclude_sources=request.exclude_sources
    )

    persistence = PersistenceService(db)
    try:
        session = await persistence.save_analysis_session(
            device_id=device_id,
            logs=entries,
            report=report,
            config={
                "filter_rules": request.filter_rules,
                "include_sources": request.include_sources,
                "exclude_sources": request.exclude_sources,
            },
            raw_logs=request.raw_logs,
        )
        return ValidateResponse(
            report=report.to_dict(),
            analysis_session_id=str(session.id),
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to save analysis session: {e}", exc_info=True)
        return ValidateResponse(
            report=report.to_dict(),
            analysis_session_id=None,
        )


@router.get("/analysis", response_model=AnalysisListResponse)
async def list_analysis_sessions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    device_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_db),
):
    persistence = PersistenceService(db)
    sessions, total = await persistence.get_analysis_sessions(
        limit=limit,
        offset=offset,
        device_id=device_id,
    )
    
    items = [_orm_session_to_list_item(s) for s in sessions]
    
    return AnalysisListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/analysis/{session_id}")
async def get_analysis_session_detail(
    session_id: str,
    db: AsyncSession = Depends(get_async_db),
):
    persistence = PersistenceService(db)
    
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    
    session = await persistence.get_analysis_session(session_uuid)
    
    if not session:
        raise HTTPException(status_code=404, detail="Analysis session not found")
    
    base_dict = _orm_session_to_list_item(session)
    
    logs = [_orm_log_to_dict(log) for log in session.log_entries] if session.log_entries else []
    violations = [_orm_violation_to_dict(v) for v in session.violations] if session.violations else []
    
    return {
        **base_dict,
        "logs": logs,
        "violations": violations,
        "config": session.config,
    }


@router.delete("/analysis/all", response_model=DeleteAnalysisResponse)
async def delete_all_analysis_sessions(
    db: AsyncSession = Depends(get_async_db),
):
    import logging
    logger = logging.getLogger(__name__)

    persistence = PersistenceService(db)

    try:
        deleted_count = await persistence.delete_all_analysis_sessions()

        return DeleteAnalysisResponse(
            success=True,
            deleted=deleted_count,
            session_id=None,
        )
    except Exception as e:
        logger.error(f"Failed to delete all analysis sessions: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete all analysis sessions: {str(e)}"
        )


@router.delete("/analysis/{session_id}", response_model=DeleteAnalysisResponse)
async def delete_analysis_session(
    session_id: str,
    db: AsyncSession = Depends(get_async_db),
):
    import logging
    logger = logging.getLogger(__name__)

    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    persistence = PersistenceService(db)

    try:
        deleted = await persistence.delete_analysis_session(session_uuid)
        if not deleted:
            raise HTTPException(status_code=404, detail="Analysis session not found")

        return DeleteAnalysisResponse(
            success=True,
            deleted=1,
            session_id=session_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete analysis session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete analysis session: {str(e)}"
        )


@router.get("/validate/quick-test")
async def quick_test():
    test_logs = [
        "2026-05-14 14:00:10 TEMP_READING 4.3C",
        "2026-05-14 14:00:40 TEMP_READING 9.1C",
        "2026-05-14 14:01:10 TEMP_READING 4.7C",
        "2026-05-14 14:02:30 SENSOR_TIMEOUT SECONDARY_SENSOR",
        "2026-05-14 14:06:30 DOOR_OPEN",
    ]

    entries, _ = parse_raw_logs(test_logs)
    engine = RegulatoryEngine()
    report = engine.validate(entries, device_id="test-device-001")

    return ValidateResponse(
        report=report.to_dict()
    )
