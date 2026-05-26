from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_serializer


class SourceFileType(str, Enum):
    LOG_FILE = "log_file"
    CHART_IMAGE = "chart_image"
    CONSTRAINTS_DOC = "constraints_doc"


class AlignmentMethod(str, Enum):
    PATTERN_MATCHED = "pattern_matched"
    LLM_EXTRACTED = "llm_extracted"
    MANUAL = "manual"


class ChartAlignment(BaseModel):
    method: AlignmentMethod
    confidence: float
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    uncertain: bool = False

    @field_serializer("start_time", "end_time")
    def serialize_datetime(self, dt: Optional[datetime], _info):
        return dt.isoformat() if dt else None


class SourceFile(BaseModel):
    id: str
    name: str
    type: SourceFileType
    entry_count: int = 0
    time_range_start: Optional[datetime] = None
    time_range_end: Optional[datetime] = None
    alignment: Optional[ChartAlignment] = None

    @field_serializer("time_range_start", "time_range_end")
    def serialize_datetime(self, dt: Optional[datetime], _info):
        return dt.isoformat() if dt else None


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CorrelatedFinding(BaseModel):
    finding_id: str
    rule_id: str
    timestamp: datetime
    sources: List[str]
    log_confidence: Optional[float] = None
    chart_confidence: Optional[float] = None
    alignment_confidence: Optional[float] = None
    combined_confidence: float
    confidence_level: ConfidenceLevel
    description: str
    evidence: Dict[str, Any] = {}

    @field_serializer("timestamp")
    def serialize_datetime(self, dt: datetime, _info):
        return dt.isoformat()


class ConflictType(str, Enum):
    LOG_OK_CHART_VIOLATION = "log_ok_chart_violation"
    LOG_VIOLATION_CHART_OK = "log_violation_chart_ok"
    VALUE_DISCREPANCY = "value_discrepancy"


class ConflictingFinding(BaseModel):
    finding_id: str
    rule_id: str
    timestamp: datetime
    conflict_type: ConflictType
    log_value: Optional[str] = None
    log_status: Optional[str] = None
    chart_value: Optional[str] = None
    chart_status: Optional[str] = None
    description: str
    for_human_review: bool = True

    @field_serializer("timestamp")
    def serialize_datetime(self, dt: datetime, _info):
        return dt.isoformat()


class CorrelationSummary(BaseModel):
    total_correlated: int = 0
    total_conflicting: int = 0
    avg_correlation_confidence: Optional[float] = None
    high_confidence_count: int = 0
    medium_confidence_count: int = 0
    low_confidence_count: int = 0


class CorrelationInsightType(str, Enum):
    DOOR_TEMPERATURE_CORRELATION = "door_temperature_correlation"
    RECOVERY_PATTERN = "recovery_pattern"
    ANOMALY_CLUSTER = "anomaly_cluster"
    TREND_INDICATOR = "trend_indicator"


class CorrelationInsight(BaseModel):
    type: CorrelationInsightType
    title: str
    description: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    supporting_evidence: List[str] = []
    confidence: float

    @field_serializer("start_time", "end_time")
    def serialize_datetime(self, dt: Optional[datetime], _info):
        return dt.isoformat() if dt else None


class MultiModalAnalysisResult(BaseModel):
    sources: List[SourceFile] = []
    correlated_findings: List[CorrelatedFinding] = []
    conflicting_findings: List[ConflictingFinding] = []
    correlation_summary: CorrelationSummary = CorrelationSummary()
    correlation_insights: List[CorrelationInsight] = []
    overall_alignment_confidence: Optional[float] = None
    alignment_uncertain: bool = False
