from fastapi import (
    APIRouter, 
    UploadFile, 
    File, 
    HTTPException, 
    Query, 
    Depends, 
    Form,
    BackgroundTasks,
)
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from collections import defaultdict
import logging
import uuid
import json

from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.config import settings
from app.database import get_async_db
from app.services.persistence import PersistenceService

from app.ai.client import ModelArkClient, ImageFormat, AIError, AIValidationError
from app.ai.image.analyzer import ChartAnalyzer
from app.ai.text.analyzer import TextAnalyzer

from app.regulatory.engine import RegulatoryEngine
from app.regulatory.log_parser import parse_raw_logs

from app.multimodal.ingestion import MultiModalIngestionService
from app.multimodal.chart_alignment import ChartAlignmentService
from app.multimodal.correlation import TemporalCorrelationEngine
from app.multimodal.unified_report import UnifiedReportGenerator
from app.multimodal.prompts import extract_log_patterns

from app.models.multimodal import (
    SourceFile,
    SourceFileType,
    ChartAlignment,
    CorrelatedFinding,
    ConflictingFinding,
    CorrelationSummary,
    CorrelationInsight,
)
from app.reports.models import AggregatedComplianceReport
from app.ai.image.models import ChartAnalysisResult, TemperatureReading

router = APIRouter()
logger = logging.getLogger(__name__)


def _to_json_safe(obj: Any) -> Any:
    """Recursively convert objects to JSON-safe format."""
    if obj is None:
        return None
    elif isinstance(obj, dict):
        return {k: _to_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_to_json_safe(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(_to_json_safe(item) for item in obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, timedelta):
        return obj.total_seconds()
    elif hasattr(obj, 'value'):
        return obj.value
    elif hasattr(obj, 'model_dump'):
        try:
            dumped = obj.model_dump(mode='json')
            return _to_json_safe(dumped)
        except Exception:
            return _to_json_safe(dict(getattr(obj, '__dict__', {})))
    elif hasattr(obj, 'to_dict'):
        try:
            return _to_json_safe(obj.to_dict())
        except Exception:
            return _to_json_safe(dict(getattr(obj, '__dict__', {})))
    elif hasattr(obj, '__dict__'):
        return _to_json_safe(dict(obj.__dict__))
    else:
        try:
            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            return str(obj)


analysis_sessions: Dict[str, Dict[str, Any]] = {}


class AnalysisStatus(str):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalyzeOptions(BaseModel):
    merge_logs: bool = True
    extract_rules: bool = True
    align_charts: bool = True
    correlate_findings: bool = True


class MultiModalAnalyzeResponse(BaseModel):
    success: bool
    session_id: str
    status: str
    message: Optional[str] = None
    estimated_time_seconds: Optional[int] = None


class MultiModalStatusResponse(BaseModel):
    success: bool
    session_id: str
    status: str
    progress: Optional[float] = None
    current_step: Optional[str] = None
    steps_total: Optional[int] = None
    message: Optional[str] = None


class MultiModalResultsResponse(BaseModel):
    success: bool
    session_id: str
    report: Optional[AggregatedComplianceReport] = None
    error: Optional[str] = None


def _update_session_status(
    session_id: str,
    status: str,
    step: str,
    progress: float,
    steps_total: int = 6,
):
    """Update analysis session status."""
    if session_id in analysis_sessions:
        analysis_sessions[session_id].update({
            "status": status,
            "current_step": step,
            "progress": progress,
            "steps_total": steps_total,
        })
        logger.info(
            f"Analysis {session_id}: {step} ({progress:.0%})",
            extra={"status": status, "step": step, "progress": progress}
        )


async def run_multi_modal_analysis(
    session_id: str,
    log_files_data: List[Tuple[str, bytes, str]],
    chart_files_data: List[Tuple[str, bytes, str]],
    constraints_files_data: List[Tuple[str, bytes, str]],
    options: AnalyzeOptions,
    db: AsyncSession,
):
    """
    Full multi-modal analysis workflow:
    1. Ingest logs (merge, dedupe, source tracking)
    2. Parallel: rule extraction (if constraints) + chart analysis
    3. Chart time alignment
    4. Regulatory validation
    5. Temporal correlation
    6. Unified report generation
    """
    try:
        analysis_sessions[session_id] = {
            "status": AnalysisStatus.PROCESSING,
            "started_at": datetime.now(),
            "current_step": "Initializing",
            "progress": 0.0,
            "steps_total": 6,
        }

        ingestion_service = MultiModalIngestionService()
        alignment_service = ChartAlignmentService()
        correlation_engine = TemporalCorrelationEngine()
        report_generator = UnifiedReportGenerator()
        regulatory_engine = RegulatoryEngine()

        merged_entries: List[Any] = []
        sources: List[SourceFile] = []
        extracted_rules: Optional[List[Dict[str, Any]]] = None
        ruleset_meta: Optional[Dict[str, Any]] = None
        chart_violations: List[Any] = []
        aligned_chart_points: List[TemperatureReading] = []
        alignment_confidence: float = 1.0
        alignment_uncertain: bool = False
        chart_analysis_results: List[ChartAnalysisResult] = []

        _update_session_status(session_id, AnalysisStatus.PROCESSING, "Ingesting log files", 0.10)

        if log_files_data:
            ingestion_result = ingestion_service.ingest_logs_from_upload(log_files_data)
            
            if ingestion_result.errors:
                logger.warning(
                    f"Ingestion warnings: {ingestion_result.warnings}",
                    extra={"errors": ingestion_result.errors}
                )
            
            merged_entries = ingestion_result.merged_entries
            sources.extend(ingestion_result.sources)
            
            logger.info(
                f"Ingested {len(log_files_data)} log files: {len(merged_entries)} entries after dedup",
                extra={"dedup_stats": ingestion_result.dedup_stats}
            )

        _update_session_status(session_id, AnalysisStatus.PROCESSING, "Extracting rules from constraints", 0.20)

        if constraints_files_data and options.extract_rules and settings.ai_enabled:
            try:
                all_doc_texts = []
                constraints_filenames = []
                for file_id, file_bytes, filename in constraints_files_data:
                    try:
                        text = file_bytes.decode('utf-8')
                        all_doc_texts.append(text)
                        constraints_filenames.append(filename)
                        sources.append(SourceFile(
                            id=file_id,
                            name=filename,
                            type=SourceFileType.CONSTRAINTS_DOC,
                            entry_count=len(text.splitlines()),
                        ))
                    except UnicodeDecodeError:
                        logger.warning(f"Could not decode constraints file: {filename}")
                
                if all_doc_texts:
                    combined_text = "\n\n---\n\n".join(all_doc_texts)
                    ruleset_filename = (
                        constraints_filenames[0] 
                        if len(constraints_filenames) == 1 
                        else f"{len(constraints_filenames)} constraints documents"
                    )
                    
                    text_analyzer = TextAnalyzer()
                    
                    rules_result = await text_analyzer.extract_rules(
                        document_text=combined_text,
                        filename=ruleset_filename,
                    )
                    
                    if rules_result.get("success") and rules_result.get("rules"):
                        extracted_rules = rules_result["rules"]
                        ruleset_meta = rules_result.get("meta")
                        logger.info(f"Extracted {len(extracted_rules)} rules from constraints documents: {ruleset_filename}")
            
            except Exception as e:
                logger.warning(f"Rule extraction failed: {e}")

        _update_session_status(session_id, AnalysisStatus.PROCESSING, "Analyzing chart images", 0.35)

        if chart_files_data and settings.ai_enabled:
            chart_analyzer = ChartAnalyzer()
            
            for file_id, file_bytes, filename in chart_files_data:
                try:
                    image_format = ModelArkClient.detect_image_format(filename)
                    if not image_format:
                        logger.warning(f"Unsupported chart format: {filename}")
                        continue
                    
                    chart_result = await chart_analyzer.analyze(file_bytes, image_format)
                    chart_analysis_results.append(chart_result)
                    
                    chart_source = SourceFile(
                        id=file_id,
                        name=filename,
                        type=SourceFileType.CHART_IMAGE,
                        entry_count=len(chart_result.data_points),
                        time_range_start=chart_result.time_range_start,
                        time_range_end=chart_result.time_range_end,
                    )
                    
                    if merged_entries and options.align_charts:
                        _update_session_status(session_id, AnalysisStatus.PROCESSING, f"Aligning {filename}", 0.40)

                        alignment_result = await alignment_service.align_chart(
                            log_entries=merged_entries,
                            chart_result=chart_result,
                        )
                        
                        chart_source.alignment = alignment_result.alignment
                        aligned_chart_points.extend(alignment_result.aligned_data_points)
                        
                        if alignment_result.alignment.confidence < alignment_confidence:
                            alignment_confidence = alignment_result.alignment.confidence
                        if alignment_result.alignment.uncertain:
                            alignment_uncertain = True
                        
                        logger.info(
                            f"Chart {filename} aligned: confidence={alignment_result.alignment.confidence:.2f}, "
                            f"uncertain={alignment_result.alignment.uncertain}"
                        )
                    else:
                        chart_source.alignment = ChartAlignment(
                            method="llm_extracted" if hasattr(chart_result, 'confidence') else "unknown",
                            confidence=chart_result.confidence if hasattr(chart_result, 'confidence') else 0.5,
                            start_time=chart_result.time_range_start,
                            end_time=chart_result.time_range_end,
                            uncertain=chart_result.confidence < 0.7 if hasattr(chart_result, 'confidence') else True,
                        )
                        
                        if chart_result.data_points:
                            aligned_chart_points.extend(chart_result.data_points)
                    
                    sources.append(chart_source)
                    
                    if chart_result.violations:
                        chart_violations.extend(chart_result.violations)
                    
                    logger.info(
                        f"Analyzed chart {filename}: {len(chart_result.data_points)} data points, "
                        f"{len(chart_result.violations) if chart_result.violations else 0} violations"
                    )
                    
                except Exception as e:
                    logger.error(f"Chart analysis failed for {filename}: {e}")

        _update_session_status(session_id, AnalysisStatus.PROCESSING, "Running regulatory validation", 0.55)

        if not merged_entries and not chart_violations and not chart_analysis_results:
            raise HTTPException(
                status_code=400,
                detail="No valid data to analyze. Provide log files and/or chart images."
            )

        base_report = None
        if merged_entries:
            try:
                rule_set = None
                if extracted_rules:
                    from app.models.dynamic_rules import ExtractedRule
                    rule_set = [ExtractedRule(**r) for r in extracted_rules if isinstance(r, dict)]
                
                base_report = regulatory_engine.validate(
                    logs=merged_entries,
                    device_id="multi-modal-analysis",
                    rule_set=rule_set,
                    merge_with_default=False,
                )
                
                logger.info(
                    f"Regulatory validation complete: {len(base_report.findings)} findings, "
                    f"{base_report.failed_count} failed"
                )
            except Exception as e:
                logger.error(f"Regulatory validation failed: {e}")
                raise
        elif chart_analysis_results:
            try:
                from app.ai.image.converters import (
                    create_compliance_report_from_chart_result, 
                    convert_chart_violations_to_findings
                )
                from app.models.findings import CategorySummary
                
                if len(chart_analysis_results) == 1:
                    base_report = create_compliance_report_from_chart_result(
                        chart_analysis_results[0],
                        device_id="multi-modal-analysis",
                    )
                else:
                    all_findings = []
                    total_entries = 0
                    time_range_starts = []
                    time_range_ends = []
                    categories: Dict[str, CategorySummary] = {}
                    
                    for result in chart_analysis_results:
                        findings = convert_chart_violations_to_findings(
                            result.violations,
                            parent_confidence=result.confidence,
                            parent_analyzed_at=result.analyzed_at,
                        )
                        all_findings.extend(findings)
                        total_entries += len(result.data_points) if result.data_points else 0
                        if result.time_range_start:
                            time_range_starts.append(result.time_range_start)
                        if result.time_range_end:
                            time_range_ends.append(result.time_range_end)
                        
                        for finding in findings:
                            cat = finding.category
                            if cat not in categories:
                                categories[cat] = CategorySummary(passed=0, failed=0, total=0)
                            if finding.passed:
                                categories[cat].passed += 1
                            else:
                                categories[cat].failed += 1
                            categories[cat].total += 1
                    
                    failed_count = len(all_findings)
                    critical_count = sum(1 for f in all_findings if f.severity == Severity.CRITICAL)
                    passed_count = 0
                    
                    base_report = ComplianceReport(
                        device_id="multi-modal-analysis",
                        analyzed_at=datetime.now(),
                        total_entries=total_entries,
                        time_range_start=min(time_range_starts) if time_range_starts else None,
                        time_range_end=max(time_range_ends) if time_range_ends else None,
                        summary=categories,
                        findings=all_findings,
                        passed_count=passed_count,
                        failed_count=failed_count,
                        critical_count=critical_count,
                    )
                
                logger.info(
                    f"Chart-based regulatory validation complete: {len(base_report.findings)} findings, "
                    f"{base_report.failed_count} failed"
                )
            except Exception as e:
                logger.error(f"Chart-based regulatory validation failed: {e}")
                raise

        _update_session_status(session_id, AnalysisStatus.PROCESSING, "Performing temporal correlation", 0.70)

        correlation_result = None
        if base_report and (chart_violations or aligned_chart_points):
            try:
                correlation_result = correlation_engine.correlate(
                    log_entries=merged_entries,
                    log_findings=base_report.findings,
                    chart_violations=chart_violations,
                    aligned_chart_points=aligned_chart_points,
                    alignment_confidence=alignment_confidence,
                    alignment_uncertain=alignment_uncertain,
                )
                
                logger.info(
                    f"Correlation complete: {len(correlation_result.correlated_findings)} correlated, "
                    f"{len(correlation_result.conflicting_findings)} conflicting"
                )
            except Exception as e:
                logger.warning(f"Correlation skipped: {e}")

        _update_session_status(session_id, AnalysisStatus.PROCESSING, "Generating unified report", 0.85)

        chart_violations_for_report = chart_violations
        if not merged_entries:
            chart_violations_for_report = []
            logger.info("Not using chart_violations separately - they are already in base_report (chart-only mode)")

        if base_report:
            try:
                if correlation_result or chart_violations_for_report or aligned_chart_points:
                    from app.models.multimodal import CorrelationSummary
                    
                    final_report = report_generator.generate_unified_report(
                        regulatory_report=base_report,
                        log_entries=merged_entries,
                        sources=sources,
                        correlated_findings=correlation_result.correlated_findings if correlation_result else [],
                        conflicting_findings=correlation_result.conflicting_findings if correlation_result else [],
                        correlation_summary=correlation_result.correlation_summary if correlation_result else CorrelationSummary(),
                        correlation_insights=correlation_result.correlation_insights if correlation_result else [],
                        aligned_chart_points=aligned_chart_points,
                        chart_violations=chart_violations_for_report,
                        alignment_confidence=alignment_confidence,
                        alignment_uncertain=alignment_uncertain,
                    )
                else:
                    from app.reports.aggregator import aggregate_report
                    final_report = aggregate_report(
                        regulatory_report=base_report,
                        logs=merged_entries,
                    )
                    final_report.data_sources = sources
                    final_report.alignment_uncertain = alignment_uncertain

                config_dict: Dict[str, Any] = {
                    "_sources": [s.model_dump(mode='json') for s in sources],
                }

                if correlation_result:
                    config_dict["_correlation"] = {
                        "correlated_findings": [cf.model_dump(mode='json') for cf in correlation_result.correlated_findings],
                        "conflicting_findings": [cf.model_dump(mode='json') for cf in correlation_result.conflicting_findings],
                        "summary": correlation_result.correlation_summary.model_dump(mode='json') if correlation_result.correlation_summary else None,
                        "alignment_uncertain": alignment_uncertain,
                    }
                else:
                    config_dict["_correlation"] = {
                        "alignment_uncertain": alignment_uncertain,
                    }

                if extracted_rules:
                    config_dict["_extracted_rules"] = _to_json_safe(extracted_rules)
                    if ruleset_meta:
                        config_dict["_ruleset_meta"] = _to_json_safe(ruleset_meta)

                if aligned_chart_points:
                    from app.ai.image.converters import convert_temperature_readings_to_data_points
                    
                    temp_data = convert_temperature_readings_to_data_points(aligned_chart_points)
                    if "_latest_analysis_data" not in config_dict:
                        config_dict["_latest_analysis_data"] = {}
                    config_dict["_latest_analysis_data"]["temperatureData"] = temp_data

                config_dict = _to_json_safe(config_dict)

                config_dict["_api_session_id"] = session_id

                config_json = json.dumps(config_dict, default=str)
                config_dict = json.loads(config_json)

                persistence = PersistenceService(db)
                session = await persistence.save_analysis_session(
                    device_id="multi-modal-analysis",
                    logs=merged_entries,
                    report=final_report,
                    config=config_dict,
                )

                from sqlalchemy.ext.asyncio import AsyncSession
                async_db: AsyncSession = db
                await async_db.refresh(session)

                db_session_id = session.id
                db_session_id_str = str(db_session_id)

                logger.info(f"Analysis saved to database: {db_session_id_str}")

                if settings.ai_enabled:
                    try:
                        from app.ai.analyst.engine import AIAnalystEngine
                        ai_analyst = AIAnalystEngine()
                        ai_analysis = None

                        if merged_entries:
                            ai_analysis = await ai_analyst.analyze_logs(
                                logs=merged_entries,
                                report=final_report,
                            )
                        elif chart_analysis_results:
                            ai_analysis = await ai_analyst.analyze_chart(
                                chart_result=chart_analysis_results[0],
                                report=final_report,
                            )

                        if ai_analysis:
                            await persistence.update_analysis_with_ai(
                                session_id=db_session_id,
                                ai_analysis=ai_analysis,
                            )
                            logger.info(
                                "AI analysis completed and saved for multi-modal session",
                                extra={
                                    "session_id": db_session_id_str,
                                    "insights_count": len(ai_analysis.insights),
                                }
                            )
                    except Exception as ai_error:
                        logger.warning(
                            f"AI analysis failed (continuing without it): {ai_error}",
                            exc_info=True,
                        )

                analysis_sessions[session_id].update({
                    "status": AnalysisStatus.COMPLETED,
                    "report": final_report,
                    "completed_at": datetime.now(),
                    "db_session_id": db_session_id_str,
                    "progress": 1.0,
                })

                logger.info(f"Multi-modal analysis {session_id} completed successfully")

            except Exception as e:
                logger.error(f"Report generation failed: {e}", exc_info=True)
                analysis_sessions[session_id].update({
                    "status": AnalysisStatus.FAILED,
                    "error": str(e),
                })
                raise
        else:
            analysis_sessions[session_id].update({
                "status": AnalysisStatus.FAILED,
                "error": "No log data for regulatory validation",
            })

    except Exception as e:
        logger.error(f"Analysis {session_id} failed: {e}", exc_info=True)
        analysis_sessions[session_id].update({
            "status": AnalysisStatus.FAILED,
            "error": str(e),
        })


@router.post("/multimodal/analyze", response_model=MultiModalAnalyzeResponse)
async def analyze_multimodal(
    background_tasks: BackgroundTasks,
    log_files: Optional[List[UploadFile]] = File(None, description="Log files to analyze"),
    chart_images: Optional[List[UploadFile]] = File(None, description="Chart images to analyze"),
    constraints_docs: Optional[List[UploadFile]] = File(None, description="Constraints documents for rule extraction"),
    options_json: Optional[str] = Form(None, description="Analysis options as JSON"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Unified multi-modal analysis endpoint.
    
    Accepts multiple file types and orchestrates:
    - Log ingestion (merge, dedupe)
    - Rule extraction from constraints
    - Chart analysis and time alignment
    - Regulatory validation
    - Temporal correlation
    - Unified report generation
    
    Returns a session ID for status polling.
    """
    request_start = datetime.now()
    session_id = str(uuid.uuid4())

    try:
        options = AnalyzeOptions()
        if options_json:
            try:
                options_dict = json.loads(options_json)
                options = AnalyzeOptions(**options_dict)
            except json.JSONDecodeError:
                logger.warning("Invalid options JSON, using defaults")

        log_files_data: List[Tuple[str, bytes, str]] = []
        if log_files:
            for i, file in enumerate(log_files):
                file_bytes = await file.read()
                file_id = f"log_{i}_{uuid.uuid4().hex[:8]}"
                filename = file.filename or f"log_{i}.log"
                log_files_data.append((file_id, file_bytes, filename))

        chart_files_data: List[Tuple[str, bytes, str]] = []
        if chart_images:
            for i, file in enumerate(chart_images):
                file_bytes = await file.read()
                file_id = f"chart_{i}_{uuid.uuid4().hex[:8]}"
                filename = file.filename or f"chart_{i}.png"
                chart_files_data.append((file_id, file_bytes, filename))

        constraints_files_data: List[Tuple[str, bytes, str]] = []
        if constraints_docs:
            for i, file in enumerate(constraints_docs):
                file_bytes = await file.read()
                file_id = f"constraints_{i}_{uuid.uuid4().hex[:8]}"
                filename = file.filename or f"constraints_{i}.txt"
                constraints_files_data.append((file_id, file_bytes, filename))

        if not log_files_data and not chart_files_data:
            raise HTTPException(
                status_code=400,
                detail="No files provided. Please provide at least log files or chart images."
            )

        total_files = len(log_files_data) + len(chart_files_data) + len(constraints_files_data)
        estimated_time = 15 + (total_files * 5) + (len(chart_files_data) * 10)

        analysis_sessions[session_id] = {
            "status": AnalysisStatus.PENDING,
            "started_at": datetime.now(),
            "current_step": "Queued",
            "progress": 0.0,
            "steps_total": 6,
        }

        background_tasks.add_task(
            run_multi_modal_analysis,
            session_id=session_id,
            log_files_data=log_files_data,
            chart_files_data=chart_files_data,
            constraints_files_data=constraints_files_data,
            options=options,
            db=db,
        )

        logger.info(
            f"Multi-modal analysis queued: {session_id}",
            extra={
                "log_files": len(log_files_data),
                "chart_files": len(chart_files_data),
                "constraints_files": len(constraints_files_data),
                "estimated_time_seconds": estimated_time,
            }
        )

        return MultiModalAnalyzeResponse(
            success=True,
            session_id=session_id,
            status=AnalysisStatus.PENDING,
            message=f"Analysis queued with {total_files} files. Poll /api/multimodal/status/{session_id} for progress.",
            estimated_time_seconds=estimated_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to queue analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue analysis: {str(e)}"
        )


async def _find_db_session_by_api_id(session_id: str, db: AsyncSession) -> Optional[Any]:
    """
    Find a database session by the API session ID stored in config._api_session_id.
    """
    from app.models.orm import AnalysisSession
    from sqlalchemy import select, text

    logger.info(f"[_find_db_session_by_api_id] Looking for session: {session_id}")

    try:
        stmt = select(AnalysisSession).where(
            text("config->>'_api_session_id' = :session_id")
        ).params(session_id=session_id)

        result = await db.execute(stmt)
        db_session = result.scalar_one_or_none()

        if db_session:
            logger.info(f"[_find_db_session_by_api_id] Found DB session: {db_session.id}, status: {db_session.status}")
        else:
            logger.warning(f"[_find_db_session_by_api_id] No DB session found for api_session_id: {session_id}")

        return db_session
    except Exception as e:
        logger.error(f"[_find_db_session_by_api_id] Query error: {e}", exc_info=True)
        return None


def _map_db_status_to_api_status(db_status: Any) -> str:
    """Map database AnalysisSessionStatus to API AnalysisStatus."""
    status_str = str(db_status.value) if hasattr(db_status, 'value') else str(db_status)
    if status_str == "completed":
        return AnalysisStatus.COMPLETED
    elif status_str == "failed":
        return AnalysisStatus.FAILED
    elif status_str == "pending":
        return AnalysisStatus.PENDING
    return status_str


@router.get("/multimodal/status/{session_id}", response_model=MultiModalStatusResponse)
async def get_analysis_status(
    session_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Poll the status of an ongoing multi-modal analysis.
    Falls back to database query if in-memory session not found.
    """
    logger.info(f"[get_analysis_status] Polling for session: {session_id}")
    logger.info(f"[get_analysis_status] In-memory sessions: {list(analysis_sessions.keys())}")

    if session_id in analysis_sessions:
        session_data = analysis_sessions[session_id]
        status = session_data.get("status", AnalysisStatus.PENDING)
        logger.info(f"[get_analysis_status] Found in memory, status: {status}, progress: {session_data.get('progress')}")
        return MultiModalStatusResponse(
            success=True,
            session_id=session_id,
            status=status,
            progress=session_data.get("progress"),
            current_step=session_data.get("current_step"),
            steps_total=session_data.get("steps_total"),
            message=session_data.get("error"),
        )

    logger.info(f"[get_analysis_status] Not in memory, checking database...")
    db_session = await _find_db_session_by_api_id(session_id, db)
    if db_session:
        api_status = _map_db_status_to_api_status(db_session.status)
        logger.info(f"[get_analysis_status] Found in DB, status: {api_status}")

        if api_status == AnalysisStatus.PENDING:
            if db_session.started_at:
                elapsed = (datetime.now() - db_session.started_at).total_seconds()
                logger.info(f"[get_analysis_status] Session pending for {elapsed:.1f}s")

                if elapsed > 300:
                    logger.warning(f"[get_analysis_status] Session pending for >5min, likely killed by backend reload")
                    return MultiModalStatusResponse(
                        success=True,
                        session_id=session_id,
                        status=AnalysisStatus.FAILED,
                        progress=0.0,
                        current_step="Failed",
                        steps_total=6,
                        message="Analiza a fost întreruptă. În modul de dezvoltare, modificările în cod opresc task-urile de background. Te rog reîncearcă.",
                    )

        return MultiModalStatusResponse(
            success=True,
            session_id=session_id,
            status=api_status,
            progress=1.0 if api_status == AnalysisStatus.COMPLETED else 0.0,
            current_step="Completed" if api_status == AnalysisStatus.COMPLETED else "In progress",
            steps_total=6,
            message=None,
        )

    logger.warning(f"[get_analysis_status] Session NOT FOUND in memory or DB: {session_id}")
    raise HTTPException(
        status_code=404,
        detail=f"Analysis session {session_id} not found. It may have been interrupted by a backend reload."
    )


@router.get("/multimodal/results/{session_id}", response_model=MultiModalResultsResponse)
async def get_analysis_results(
    session_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get the final results of a completed multi-modal analysis.
    Falls back to database query if in-memory session not found.
    """
    if session_id in analysis_sessions:
        session_data = analysis_sessions[session_id]
        status = session_data.get("status", AnalysisStatus.PENDING)

        if status == AnalysisStatus.PENDING or status == AnalysisStatus.PROCESSING:
            raise HTTPException(
                status_code=202,
                detail=f"Analysis still in progress: {status}. Poll /api/multimodal/status/{session_id} for updates."
            )

        if status == AnalysisStatus.FAILED:
            return MultiModalResultsResponse(
                success=False,
                session_id=session_id,
                report=None,
                error=session_data.get("error", "Analysis failed"),
            )

        report = session_data.get("report")

        return MultiModalResultsResponse(
            success=True,
            session_id=session_id,
            report=report,
            error=None,
        )

    db_session = await _find_db_session_by_api_id(session_id, db)
    if not db_session:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis session {session_id} not found"
        )

    api_status = _map_db_status_to_api_status(db_session.status)

    if api_status == AnalysisStatus.PENDING or api_status == AnalysisStatus.PROCESSING:
        raise HTTPException(
            status_code=202,
            detail=f"Analysis still in progress: {api_status}. Poll /api/multimodal/status/{session_id} for updates."
        )

    if api_status == AnalysisStatus.FAILED:
        return MultiModalResultsResponse(
            success=False,
            session_id=session_id,
            report=None,
            error="Analysis failed (status from database)",
        )

    report_dict = None
    if db_session.config and "_latest_analysis_data" in db_session.config:
        report_dict = db_session.config["_latest_analysis_data"].get("validationResult")

    return MultiModalResultsResponse(
        success=True,
        session_id=session_id,
        report=report_dict,
        error=None,
    )
