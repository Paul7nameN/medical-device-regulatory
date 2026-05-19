from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Body, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_async_db
from app.services.persistence import PersistenceService
from app.ai.client import (
    ModelArkClient,
    ImageFormat,
    AIError,
    AIValidationError,
    AIImageError,
    AIRateLimitError
)
from app.ai.image.models import ChartAnalysisResult, ChartViolation, CrossValidationResult
from app.ai.image.converters import (
    create_compliance_report_from_chart_result,
    convert_temperature_readings_to_data_points,
)
import uuid
from app.ai.analyst.engine import AIAnalystEngine
from app.ai.analyst.models import ChatMessage, ChatRequest, ChatResponse
from app.ai.text.models import LogAnalysisResult, GeneratedReport, AIErrorResponse
from app.ai.image.analyzer import ChartAnalyzer
from app.ai.text.analyzer import TextAnalyzer

router = APIRouter()
logger = logging.getLogger(__name__)


class LogEntryInput(BaseModel):
    timestamp: str
    log_type: str
    raw_value: str
    parsed_value: Optional[Any] = None
    sensor_id: Optional[str] = None


class FindingInput(BaseModel):
    rule_id: str
    rule_description: str
    category: str
    severity: str
    passed: bool
    message: str
    evidence: Optional[List[Dict]] = None
    remediation_hint: Optional[str] = None


class LogAnalysisRequest(BaseModel):
    logs: Optional[List[LogEntryInput]] = None
    findings: Optional[List[FindingInput]] = None
    raw_logs: Optional[List[str]] = None
    device_id: Optional[str] = None


class ReportGenerationRequest(BaseModel):
    device_id: str = "unknown"
    total_entries: int = 0
    time_range_start: Optional[str] = None
    time_range_end: Optional[str] = None
    passed_count: int = 0
    failed_count: int = 0
    critical_count: int = 0
    summary: Optional[Dict[str, Any]] = None
    findings: Optional[List[FindingInput]] = None
    report_type: str = "compliance_summary"


class ModelInfo(BaseModel):
    id: str
    name: str
    purpose: str
    status: str


class ModelsStatusResponse(BaseModel):
    models: List[ModelInfo]
    api_status: str
    config: Dict[str, Any]


class ChartAnalysisResponse(BaseModel):
    result: Optional[ChartAnalysisResult] = None
    error: Optional[AIErrorResponse] = None
    success: bool


class LogAnalysisResponse(BaseModel):
    result: Optional[LogAnalysisResult] = None
    error: Optional[AIErrorResponse] = None
    success: bool


class ReportGenerationResponse(BaseModel):
    report: Optional[GeneratedReport] = None
    error: Optional[AIErrorResponse] = None
    success: bool


def _format_error_response(exception: Exception) -> AIErrorResponse:
    error_type = "api_error"
    retry_available = False
    retry_after = None
    
    if isinstance(exception, AIValidationError):
        error_type = "validation_error"
    elif isinstance(exception, AIImageError):
        error_type = "image_error"
    elif isinstance(exception, AIRateLimitError):
        error_type = "rate_limit"
        retry_available = True
        retry_after = getattr(exception, 'retry_after', 60)
    elif isinstance(exception, TimeoutError):
        error_type = "timeout"
        retry_available = True
    
    return AIErrorResponse(
        error_type=error_type,
        message=str(exception),
        retry_available=retry_available,
        retry_after_seconds=retry_after
    )


@router.get("/ai/models", response_model=ModelsStatusResponse)
async def get_models_status():
    request_start = datetime.now()
    
    models = [
        ModelInfo(
            id=settings.model_chart_analysis,
            name="Dola-Seed-2.0-pro",
            purpose="chart_analysis",
            status="available" if settings.modelark_api_key else "not_configured"
        ),
        ModelInfo(
            id=settings.model_text_analysis,
            name="GLM-4.7",
            purpose="text_analysis",
            status="available" if settings.modelark_api_key else "not_configured"
        )
    ]
    
    api_status = "connected" if settings.ai_enabled else "not_configured"
    
    config = {
        "base_url": settings.modelark_base_url,
        "timeout": settings.modelark_timeout,
        "max_retries": settings.modelark_max_retries,
        "ai_enabled": settings.ai_enabled
    }
    
    duration = (datetime.now() - request_start).total_seconds()
    
    logger.info(
        "GET /ai/models request processed",
        extra={
            "duration_seconds": duration,
            "api_status": api_status,
            "models_count": len(models)
        }
    )
    
    return ModelsStatusResponse(
        models=models,
        api_status=api_status,
        config=config
    )


@router.post("/ai/analyze-chart", response_model=ChartAnalysisResponse)
async def analyze_chart(
    file: UploadFile = File(...),
    device_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_db),
):
    request_start = datetime.now()
    request_log = {
        "endpoint": "/api/ai/analyze-chart",
        "file_name": file.filename,
        "device_id": device_id,
        "ai_enabled": settings.ai_enabled
    }
    
    logger.info(
        "Starting chart analysis request",
        extra=request_log
    )
    
    if not settings.ai_enabled:
        logger.warning(
            "Chart analysis request rejected: AI not enabled",
            extra=request_log
        )
        return ChartAnalysisResponse(
            result=None,
            error=AIErrorResponse(
                error_type="validation_error",
                message="AI analysis is not enabled. Set MODELARK_API_KEY environment variable.",
                retry_available=False
            ),
            success=False
        )
    
    try:
        if not file.filename:
            raise AIImageError("No filename provided")
        
        image_format = ModelArkClient.detect_image_format(file.filename)
        if not image_format:
            logger.warning(
                "Unsupported image format",
                extra={"file_name": file.filename}
            )
            raise AIImageError(
                "Unsupported image format. Only PNG and JPG/JPEG are supported."
            )
        
        image_bytes = await file.read()
        image_size_bytes = len(image_bytes)
        
        max_size_mb = 10
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if image_size_bytes > max_size_bytes:
            logger.warning(
                "Image exceeds size limit",
                extra={
                    "size_bytes": image_size_bytes,
                    "max_size_bytes": max_size_bytes
                }
            )
            raise AIImageError(
                f"Image exceeds maximum size of {max_size_mb}MB"
            )
        
        logger.info(
            "Processing image",
            extra={
                "format": image_format.value,
                "size_bytes": image_size_bytes,
                "size_mb": image_size_bytes / (1024 * 1024)
            }
        )
        
        analyzer = ChartAnalyzer()
        result = await analyzer.analyze(image_bytes, image_format)
        
        actual_device_id = device_id or file.filename or "unknown-device"
        
        try:
            compliance_report = create_compliance_report_from_chart_result(
                result,
                actual_device_id
            )
            
            temperature_data = convert_temperature_readings_to_data_points(
                result.data_points or []
            )
            
            persistence = PersistenceService(db)
            session = await persistence.save_analysis_session(
                device_id=actual_device_id,
                logs=[],
                report=compliance_report,
                config={
                    "_latest_analysis_data": {
                        "temperatureData": temperature_data,
                    }
                },
                raw_logs=[],
            )
            
            from sqlalchemy.ext.asyncio import AsyncSession
            async_db: AsyncSession = db
            await async_db.refresh(session)
            
            session_id = session.id
            session_id_str = str(session_id)
            
            try:
                ai_analyst = AIAnalystEngine()
                ai_analysis = await ai_analyst.analyze_chart(
                    chart_result=result,
                    report=compliance_report,
                )
                
                if ai_analysis:
                    await persistence.update_analysis_with_ai(
                        session_id=session_id,
                        ai_analysis=ai_analysis,
                    )
                    logger.info(
                        "AI chart analysis completed and saved",
                        extra={
                            "session_id": session_id_str,
                            "insights_count": len(ai_analysis.insights),
                            "risk_level": ai_analysis.session_risk_overview.risk_level,
                        }
                    )
            except Exception as ai_error:
                logger.warning(
                    f"AI chart analysis failed (continuing without it): {ai_error}",
                    exc_info=True,
                )
            
            logger.info(
                "Chart analysis saved to database",
                extra={
                    "device_id": actual_device_id,
                    "violations_count": len(result.violations) if result.violations else 0,
                    "temperature_points": len(temperature_data),
                    "analysis_session_id": session_id_str,
                }
            )
        except Exception as save_error:
            logger.error(
                "Failed to save chart analysis to database",
                extra={
                    "error": str(save_error),
                    "device_id": actual_device_id,
                },
                exc_info=True
            )
        
        duration = (datetime.now() - request_start).total_seconds()
        
        logger.info(
            "Chart analysis completed successfully",
            extra={
                "duration_seconds": duration,
                "violations_count": len(result.violations) if result and result.violations else 0,
                "confidence": result.confidence if result else None
            }
        )
        
        return ChartAnalysisResponse(
            result=result,
            error=None,
            success=True
        )
    
    except (AIError, HTTPException) as e:
        duration = (datetime.now() - request_start).total_seconds()
        logger.error(
            "Chart analysis failed",
            extra={
                "error": str(e),
                "duration_seconds": duration
            }
        )
        return ChartAnalysisResponse(
            result=None,
            error=_format_error_response(e),
            success=False
        )
    except Exception as e:
        duration = (datetime.now() - request_start).total_seconds()
        logger.error(
            "Unexpected error in chart analysis",
            extra={
                "error": str(e),
                "duration_seconds": duration
            },
            exc_info=True
        )
        return ChartAnalysisResponse(
            result=None,
            error=_format_error_response(e),
            success=False
        )


@router.post("/ai/analyze-logs", response_model=LogAnalysisResponse)
async def analyze_logs(request: LogAnalysisRequest):
    request_start = datetime.now()
    
    logs_count = len(request.logs) if request.logs else 0
    findings_count = len(request.findings) if request.findings else 0
    raw_logs_count = len(request.raw_logs) if request.raw_logs else 0
    
    request_log = {
        "endpoint": "/api/ai/analyze-logs",
        "device_id": request.device_id,
        "logs_count": logs_count,
        "findings_count": findings_count,
        "raw_logs_count": raw_logs_count,
        "ai_enabled": settings.ai_enabled
    }
    
    logger.info(
        "Starting log analysis request",
        extra=request_log
    )
    
    if not settings.ai_enabled:
        logger.warning(
            "Log analysis request rejected: AI not enabled",
            extra=request_log
        )
        return LogAnalysisResponse(
            result=None,
            error=AIErrorResponse(
                error_type="validation_error",
                message="AI analysis is not enabled. Set MODELARK_API_KEY environment variable.",
                retry_available=False
            ),
            success=False
        )
    
    try:
        logs_list = []
        if request.logs:
            logs_list = request.logs
        
        findings_list = []
        if request.findings:
            findings_list = request.findings
        
        analyzer = TextAnalyzer()
        
        result = await analyzer.analyze_logs(logs_list, findings_list)
        
        duration = (datetime.now() - request_start).total_seconds()
        
        logger.info(
            "Log analysis completed successfully",
            extra={
                "duration_seconds": duration,
                "risk_assessment": result.risk_assessment if result else None,
                "key_findings_count": len(result.key_findings) if result and result.key_findings else 0
            }
        )
        
        return LogAnalysisResponse(
            result=result,
            error=None,
            success=True
        )
    
    except AIError as e:
        duration = (datetime.now() - request_start).total_seconds()
        logger.error(
            "Log analysis failed",
            extra={
                "error": str(e),
                "duration_seconds": duration
            }
        )
        return LogAnalysisResponse(
            result=None,
            error=_format_error_response(e),
            success=False
        )
    except Exception as e:
        duration = (datetime.now() - request_start).total_seconds()
        logger.error(
            "Unexpected error in log analysis",
            extra={
                "error": str(e),
                "duration_seconds": duration
            },
            exc_info=True
        )
        return LogAnalysisResponse(
            result=None,
            error=_format_error_response(e),
            success=False
        )


@router.post("/ai/generate-report", response_model=ReportGenerationResponse)
async def generate_report(request: ReportGenerationRequest):
    request_start = datetime.now()
    
    request_log = {
        "endpoint": "/api/ai/generate-report",
        "device_id": request.device_id,
        "total_entries": request.total_entries,
        "passed_count": request.passed_count,
        "failed_count": request.failed_count,
        "critical_count": request.critical_count,
        "report_type": request.report_type,
        "ai_enabled": settings.ai_enabled
    }
    
    logger.info(
        "Starting report generation request",
        extra=request_log
    )
    
    if not settings.ai_enabled:
        logger.warning(
            "Report generation request rejected: AI not enabled",
            extra=request_log
        )
        return ReportGenerationResponse(
            report=None,
            error=AIErrorResponse(
                error_type="validation_error",
                message="AI analysis is not enabled. Set MODELARK_API_KEY environment variable.",
                retry_available=False
            ),
            success=False
        )
    
    try:
        class MinimalReport:
            def __init__(self, req: ReportGenerationRequest):
                self.device_id = req.device_id
                self.total_entries = req.total_entries
                self.time_range_start = None
                self.time_range_end = None
                if req.time_range_start:
                    try:
                        self.time_range_start = datetime.fromisoformat(
                            req.time_range_start.rstrip('Z').rstrip('+00:00')
                        )
                    except (ValueError, TypeError):
                        pass
                if req.time_range_end:
                    try:
                        self.time_range_end = datetime.fromisoformat(
                            req.time_range_end.rstrip('Z').rstrip('+00:00')
                        )
                    except (ValueError, TypeError):
                        pass
                self.summary = req.summary or {}
                self.findings = []
                self.passed_count = req.passed_count
                self.failed_count = req.failed_count
                self.critical_count = req.critical_count
        
        minimal_report = MinimalReport(request)
        
        analyzer = TextAnalyzer()
        
        report = await analyzer.generate_report(
            minimal_report,
            request.report_type
        )
        
        duration = (datetime.now() - request_start).total_seconds()
        
        logger.info(
            "Report generation completed successfully",
            extra={
                "duration_seconds": duration,
                "report_type": request.report_type,
                "sections_count": len(report.sections) if report and report.sections else 0
            }
        )
        
        return ReportGenerationResponse(
            report=report,
            error=None,
            success=True
        )
    
    except AIError as e:
        duration = (datetime.now() - request_start).total_seconds()
        logger.error(
            "Report generation failed",
            extra={
                "error": str(e),
                "duration_seconds": duration
            }
        )
        return ReportGenerationResponse(
            report=None,
            error=_format_error_response(e),
            success=False
        )
    except Exception as e:
        duration = (datetime.now() - request_start).total_seconds()
        logger.error(
            "Unexpected error in report generation",
            extra={
                "error": str(e),
                "duration_seconds": duration
            },
            exc_info=True
        )
        return ReportGenerationResponse(
            report=None,
            error=_format_error_response(e),
            success=False
        )


@router.post("/ai/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Chat with AI about analysis data.
    
    Provide context from an analysis session for more relevant responses.
    """
    request_start = datetime.now()
    
    request_log = {
        "endpoint": "/api/ai/chat",
        "has_analysis_session_id": bool(request.analysis_session_id),
        "message_length": len(request.message) if request.message else 0,
        "history_length": len(request.chat_history) if request.chat_history else 0,
        "ai_enabled": settings.ai_enabled,
    }
    
    logger.info(
        "Starting AI chat request",
        extra=request_log
    )
    
    if not settings.ai_enabled:
        logger.warning(
            "AI chat request rejected: AI not enabled",
            extra=request_log
        )
        return ChatResponse(
            message="AI analysis is not enabled. Set MODELARK_API_KEY environment variable.",
            sources=[],
            suggested_actions=[],
        )
    
    try:
        ai_analysis_dict = None
        
        if request.analysis_session_id:
            try:
                session_uuid = uuid.UUID(request.analysis_session_id)
                persistence = PersistenceService(db)
                session = await persistence.get_analysis_session(session_uuid)
                
                if session and session.config:
                    ai_analysis_dict = session.config.get("_ai_analysis")
                    logger.info(
                        "Loaded AI analysis from session",
                        extra={"session_id": request.analysis_session_id}
                    )
            except ValueError:
                logger.warning(f"Invalid session ID format: {request.analysis_session_id}")
            except Exception as e:
                logger.warning(f"Failed to load analysis session: {e}")
        
        ai_analyst = AIAnalystEngine()
        
        response_message = await ai_analyst.chat(
            message=request.message,
            ai_analysis=ai_analysis_dict,
            chat_history=request.chat_history,
        )
        
        duration = (datetime.now() - request_start).total_seconds()
        
        logger.info(
            "AI chat completed successfully",
            extra={
                "duration_seconds": duration,
                "response_length": len(response_message) if response_message else 0,
            }
        )
        
        return ChatResponse(
            message=response_message,
            sources=[],
            suggested_actions=[],
        )
    
    except AIError as e:
        duration = (datetime.now() - request_start).total_seconds()
        logger.error(
            "AI chat failed",
            extra={
                "error": str(e),
                "duration_seconds": duration
            }
        )
        return ChatResponse(
            message=f"Sorry, I encountered an error: {str(e)}",
            sources=[],
            suggested_actions=[],
        )
    except Exception as e:
        duration = (datetime.now() - request_start).total_seconds()
        logger.error(
            "Unexpected error in AI chat",
            extra={
                "error": str(e),
                "duration_seconds": duration
            },
            exc_info=True
        )
        return ChatResponse(
            message="Sorry, I encountered an unexpected error. Please try again.",
            sources=[],
            suggested_actions=[],
        )
