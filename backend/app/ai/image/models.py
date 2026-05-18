from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_serializer


class ImageFormat(str, Enum):
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"


class ChartViolationType(str, Enum):
    EXCURSION = "excursion"
    GAP = "gap"
    SLOW_RECOVERY = "slow_recovery"
    FREQUENT_ACCESS = "frequent_access"


class ChartViolation(BaseModel):
    violation_type: ChartViolationType
    timestamp_start: Optional[datetime] = None
    timestamp_end: Optional[datetime] = None
    description: str
    confidence: float = 0.5
    extracted_value: Optional[float] = None

    @field_serializer("timestamp_start", "timestamp_end")
    def serialize_datetime(self, dt: Optional[datetime], _info):
        return dt.isoformat() if dt else None


class TemperatureReading(BaseModel):
    time: str
    timestamp: Optional[datetime] = None
    sensor_a: float
    sensor_b: Optional[float] = None
    source: str = "chart_image"

    @field_serializer("timestamp")
    def serialize_timestamp(self, dt: Optional[datetime], _info):
        return dt.isoformat() if dt else None


class ChartAnalysisResult(BaseModel):
    model_used: str
    analyzed_at: datetime
    duration_seconds: float

    chart_type: Optional[str] = None
    time_range_start: Optional[datetime] = None
    time_range_end: Optional[datetime] = None
    temp_range_min: Optional[float] = None
    temp_range_max: Optional[float] = None

    violations: List[ChartViolation] = []
    data_points: List[TemperatureReading] = []
    summary: str = ""

    raw_response: Optional[Dict[str, Any]] = None
    confidence: float = 0.5

    @field_serializer("analyzed_at", "time_range_start", "time_range_end")
    def serialize_datetime(self, dt: Optional[datetime], _info):
        return dt.isoformat() if dt else None


class CrossValidationResult(BaseModel):
    log_findings_count: int
    chart_findings_count: int
    matching_violations: int
    conflicting_findings: int

    confidence_score: float
    summary: str
