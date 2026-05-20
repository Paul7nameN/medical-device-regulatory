from fastapi import APIRouter, HTTPException, Query, Body, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.logs import LogEntry
from app.models.findings import ComplianceReport
from app.regulatory.engine import RegulatoryEngine
from app.regulatory.log_parser import parse_raw_logs
from app.reports.aggregator import ComplianceReportAggregator
from app.reports.models import AggregatedComplianceReport
from app.database import get_async_db
from app.services.persistence import PersistenceService
from app.ai.analyst.engine import AIAnalystEngine

try:
    from app.models.dynamic_rules import ExtractedRule
    DYNAMIC_RULES_AVAILABLE = True
except ImportError:
    DYNAMIC_RULES_AVAILABLE = False

router = APIRouter()
logger = logging.getLogger(__name__)


class RulesetMetaInput(BaseModel):
    source: str = "extracted"
    filename: Optional[str] = None
    extracted_at: Optional[str] = None
    model_used: Optional[str] = None
    rule_count: int = 0
    average_confidence: Optional[float] = None
    ruleset_name: Optional[str] = None


class GenerateReportRequest(BaseModel):
    raw_logs: Optional[List[str]] = None
    entries: Optional[List[Dict[str, Any]]] = None
    device_id: str = "unknown"
    filter_rules: Optional[List[str]] = None
    include_ai_analysis: bool = False
    include_raw_report: bool = False
    extracted_rules: Optional[List[Dict[str, Any]]] = None
    ruleset_meta: Optional[RulesetMetaInput] = None
    merge_with_default_rules: bool = False


class GenerateReportResponse(BaseModel):
    report: AggregatedComplianceReport
    generated_at: datetime
    analysis_session_id: Optional[str] = None


class SummaryResponse(BaseModel):
    device_id: str
    summary: Dict[str, Any]
    critical_rules: List[str]
    high_rules: List[str]
    recommendation_count: int


@router.post("/reports/summary", response_model=SummaryResponse)
async def generate_compliance_summary(
    request: GenerateReportRequest
):
    """
    Generate a concise compliance summary from log data.
    
    Returns key metrics without full report details.
    """
    try:
        entries: List[Any] = []
        
        if request.raw_logs:
            parsed_entries, warnings = parse_raw_logs(request.raw_logs)
            entries.extend(parsed_entries)
        
        if request.entries:
            from app.models.logs import LogEntry as LogEntryModel, LogType
            for entry_dict in request.entries:
                try:
                    ts = datetime.fromisoformat(
                        entry_dict["timestamp"].replace('Z', '+00:00')
                    )
                    log_type = LogType(entry_dict["log_type"])
                    entry = LogEntryModel(
                        timestamp=ts,
                        log_type=log_type,
                        raw_value=entry_dict.get("raw_value", ""),
                        parsed_value=entry_dict.get("parsed_value"),
                        sensor_id=entry_dict.get("sensor_id"),
                        metadata={}
                    )
                    entries.append(entry)
                except (ValueError, KeyError) as e:
                    logger.warning(f"Skipping invalid entry: {e}")
        
        if not entries:
            raise HTTPException(
                status_code=400,
                detail="No valid log entries provided. Include 'raw_logs' or 'entries'."
            )
        
        def _parse_rules_for_summary(rules_data: Optional[List[Dict[str, Any]]]) -> Optional[List[Any]]:
            if not rules_data or not DYNAMIC_RULES_AVAILABLE:
                return None
            try:
                from app.models.dynamic_rules import ExtractedRule
                return [ExtractedRule(**r) for r in rules_data if isinstance(r, dict)]
            except Exception:
                return None
        
        extracted_rules = _parse_rules_for_summary(request.extracted_rules)
        
        engine = RegulatoryEngine()
        base_report = engine.validate(
            logs=entries,
            filter_rules=request.filter_rules,
            device_id=request.device_id,
            rule_set=extracted_rules,
            merge_with_default=request.merge_with_default_rules,
        )
        
        aggregator = ComplianceReportAggregator()
        aggregated = aggregator.aggregate(
            regulatory_report=base_report,
            logs=entries,
            include_raw_report=False
        )
        
        from app.models.findings import Severity
        
        critical_rules = [
            vs.rule_id
            for vs in aggregated.violations_by_rule.values()
            if vs.severity == Severity.CRITICAL
        ]
        
        high_rules = [
            vs.rule_id
            for vs in aggregated.violations_by_rule.values()
            if vs.severity == Severity.HIGH
        ]
        
        return SummaryResponse(
            device_id=aggregated.device_id,
            summary=aggregated.summary,
            critical_rules=critical_rules,
            high_rules=high_rules,
            recommendation_count=len(aggregated.recommendations)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Summary generation failed", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Summary generation failed: {str(e)}"
        )


@router.post("/reports/generate", response_model=GenerateReportResponse)
async def generate_compliance_report(
    request: GenerateReportRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Generate an aggregated compliance report from log data.
    
    This endpoint:
    1. Parses raw logs or uses pre-parsed entries
    2. Runs regulatory validation
    3. Aggregates findings with severity classification
    4. Performs temporal analysis
    5. Generates prioritized recommendations
    
    **Critical Violations Monitored:**
    - REG-TEMP-1: Temperature exceedances (>3 = CRITICAL)
    - REG-SENS-1: Dual sensor timeout = CRITICAL
    - REG-ALARM-1: Delayed alarm activation
    """
    def _parse_extracted_rules(rules_data: Optional[List[Dict[str, Any]]]) -> Optional[List[Any]]:
        if not rules_data or not DYNAMIC_RULES_AVAILABLE:
            return None
        
        try:
            from app.models.dynamic_rules import ExtractedRule
            parsed_rules = []
            for rule_dict in rules_data:
                try:
                    rule = ExtractedRule(**rule_dict)
                    parsed_rules.append(rule)
                except Exception:
                    pass
            return parsed_rules if parsed_rules else None
        except Exception:
            return None

    try:
        entries: List[Any] = []
        
        if request.raw_logs:
            parsed_entries, warnings = parse_raw_logs(request.raw_logs)
            entries.extend(parsed_entries)
            if warnings:
                logger.warning(
                    f"Log parsing warnings: {len(warnings)} issues"
                )
        
        if request.entries:
            from app.models.logs import LogEntry as LogEntryModel, LogType
            for entry_dict in request.entries:
                try:
                    ts = datetime.fromisoformat(
                        entry_dict["timestamp"].replace('Z', '+00:00')
                    )
                    log_type = LogType(entry_dict["log_type"])
                    entry = LogEntryModel(
                        timestamp=ts,
                        log_type=log_type,
                        raw_value=entry_dict.get("raw_value", ""),
                        parsed_value=entry_dict.get("parsed_value"),
                        sensor_id=entry_dict.get("sensor_id"),
                        metadata={}
                    )
                    entries.append(entry)
                except (ValueError, KeyError) as e:
                    logger.warning(f"Skipping invalid entry: {e}")
        
        if not entries:
            raise HTTPException(
                status_code=400,
                detail="No valid log entries provided. Include 'raw_logs' or 'entries'."
            )
        
        extracted_rules = _parse_extracted_rules(request.extracted_rules)
        
        engine = RegulatoryEngine()
        base_report = engine.validate(
            logs=entries,
            filter_rules=request.filter_rules,
            device_id=request.device_id,
            rule_set=extracted_rules,
            merge_with_default=request.merge_with_default_rules,
        )
        
        config_dict: Dict[str, Any] = {
            "filter_rules": request.filter_rules,
            "include_raw_report": request.include_raw_report,
            "merge_with_default_rules": request.merge_with_default_rules,
        }
        
        if request.extracted_rules:
            config_dict["_extracted_rules"] = request.extracted_rules
        
        if request.ruleset_meta:
            config_dict["_ruleset_meta"] = {
                "source": request.ruleset_meta.source,
                "filename": request.ruleset_meta.filename,
                "extracted_at": request.ruleset_meta.extracted_at,
                "model_used": request.ruleset_meta.model_used,
                "rule_count": request.ruleset_meta.rule_count,
                "average_confidence": request.ruleset_meta.average_confidence,
                "ruleset_name": request.ruleset_meta.ruleset_name or "Custom Rules",
            }
        
        persistence = PersistenceService(db)
        session = await persistence.save_analysis_session(
            device_id=request.device_id,
            logs=entries,
            report=base_report,
            config=config_dict,
            raw_logs=request.raw_logs,
        )
        
        from sqlalchemy.ext.asyncio import AsyncSession
        async_db: AsyncSession = db
        await async_db.refresh(session)
        
        session_id = session.id
        session_id_str = str(session_id)
        
        try:
            ai_analyst = AIAnalystEngine()
            ai_analysis = await ai_analyst.analyze_logs(
                logs=entries,
                report=base_report,
            )
            
            if ai_analysis:
                await persistence.update_analysis_with_ai(
                    session_id=session_id,
                    ai_analysis=ai_analysis,
                )
                logger.info(
                    "AI analysis completed and saved",
                    extra={
                        "session_id": session_id_str,
                        "insights_count": len(ai_analysis.insights),
                        "risk_level": ai_analysis.session_risk_overview.risk_level,
                    }
                )
        except Exception as ai_error:
            logger.warning(
                f"AI analysis failed (continuing without it): {ai_error}",
                exc_info=True,
            )
        
        aggregator = ComplianceReportAggregator()
        aggregated = aggregator.aggregate(
            regulatory_report=base_report,
            logs=entries,
            include_raw_report=request.include_raw_report
        )
        
        logger.info(
            "Compliance report generated",
            extra={
                "device_id": aggregated.device_id,
                "critical_count": aggregated.summary.get("critical_count", 0),
                "high_count": aggregated.summary.get("high_count", 0),
                "analysis_session_id": session_id_str,
            }
        )
        
        return GenerateReportResponse(
            report=aggregated,
            generated_at=base_report.analyzed_at,
            analysis_session_id=session_id_str,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Report generation failed", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {str(e)}"
        )


import uuid

from app.models.orm import ComplianceReport as ComplianceReportORM


class ReportListItem(BaseModel):
    id: str
    device_name: Optional[str]
    status: str
    period_start: Optional[str]
    period_end: Optional[str]
    compliance_score: Optional[float]
    generated_at: Optional[str]
    summary: Optional[Dict[str, Any]]


class ReportListResponse(BaseModel):
    items: List[ReportListItem]
    total: int
    limit: int
    offset: int


def _orm_report_to_list_item(report: ComplianceReportORM) -> dict:
    device_name = report.device.name if report.device else None
    return {
        "id": str(report.id),
        "device_name": device_name,
        "status": report.status.value if hasattr(report.status, 'value') else str(report.status),
        "period_start": report.period_start.isoformat() if report.period_start else None,
        "period_end": report.period_end.isoformat() if report.period_end else None,
        "compliance_score": report.compliance_score,
        "generated_at": report.generated_at.isoformat() if report.generated_at else None,
        "summary": report.summary,
    }


@router.get("/reports", response_model=ReportListResponse)
async def list_reports(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    device_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_db),
):
    persistence = PersistenceService(db)
    
    reports, total = await persistence.get_reports(
        limit=limit,
        offset=offset,
        device_id=device_id,
    )
    
    items = [_orm_report_to_list_item(r) for r in reports]
    
    return ReportListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/reports/{report_id}")
async def get_report_detail(
    report_id: str,
    db: AsyncSession = Depends(get_async_db),
):
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    try:
        report_uuid = uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid report ID format")
    
    query = select(ComplianceReportORM).options(
        selectinload(ComplianceReportORM.device),
    ).where(ComplianceReportORM.id == report_uuid)
    
    result = await db.execute(query)
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return _orm_report_to_list_item(report)
