from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_serializer


class LogAnalysisResult(BaseModel):
    model_used: str
    analyzed_at: datetime
    duration_seconds: float

    summary: str
    key_findings: List[str]
    recommendations: List[str]
    risk_assessment: str

    raw_response: Optional[Dict[str, Any]] = None

    @field_serializer("analyzed_at")
    def serialize_datetime(self, dt: datetime, _info):
        return dt.isoformat()


class ComplianceReportSection(BaseModel):
    title: str
    content: str
    bullet_points: Optional[List[str]] = None


class GeneratedReport(BaseModel):
    model_used: str
    generated_at: datetime
    duration_seconds: float

    report_type: str
    device_id: str
    title: str

    sections: List[ComplianceReportSection]
    executive_summary: str
    recommendations: str
    conclusion: str

    raw_response: Optional[Dict[str, Any]] = None

    @field_serializer("generated_at")
    def serialize_datetime(self, dt: datetime, _info):
        return dt.isoformat()


class AIErrorResponse(BaseModel):
    error_type: str
    message: str
    retry_available: bool = False
    retry_after_seconds: Optional[int] = None
