from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, field_serializer, field_validator

from app.models.findings import Severity


class RuleType(str, Enum):
    THRESHOLD_RANGE = "threshold_range"
    DURATION_LIMIT = "duration_limit"
    FREQUENCY_LIMIT = "frequency_limit"
    PRESENCE_CHECK = "presence_check"
    INSPECTION_ONLY = "inspection_only"


class DataSource(str, Enum):
    LOGS = "logs"
    INSPECTION = "inspection"
    COMBINED = "combined"


class RuleThresholds(BaseModel):
    field: Optional[str] = None
    min: Optional[float] = None
    max: Optional[float] = None
    unit: Optional[str] = None
    max_duration_seconds: Optional[int] = None
    time_window_seconds: Optional[int] = None
    max_count: Optional[int] = None
    required_state: Optional[str] = None

    @field_validator("required_state", mode="before")
    @classmethod
    def coerce_required_state(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        if isinstance(v, str):
            return v
        if isinstance(v, int) or isinstance(v, float):
            return str(int(v)) if isinstance(v, float) and v.is_integer() else str(v)
        return str(v)


class RulesetMeta(BaseModel):
    source: str
    filename: Optional[str] = None
    extracted_at: Optional[datetime] = None
    model_used: Optional[str] = None
    rule_count: int = 0
    average_confidence: Optional[float] = None
    ruleset_name: str = "MED-THERM-2026"

    @field_serializer("extracted_at")
    def serialize_datetime(self, dt: Optional[datetime], _info):
        return dt.isoformat() if dt else None


class ExtractedRule(BaseModel):
    id: str
    name: str
    category: str
    description: str
    type: RuleType
    severity: Severity
    confidence: float
    thresholds: Optional[RuleThresholds] = None
    data_source: DataSource = DataSource.LOGS
    inspection_hint: Optional[str] = None
    extraction_notes: Optional[str] = None

    @property
    def is_auto_executable(self) -> bool:
        return self.confidence >= 0.7 and self.type != RuleType.INSPECTION_ONLY


class ExtractRulesRequest(BaseModel):
    document_text: str
    filename: Optional[str] = None


class ExtractRulesMeta(BaseModel):
    extracted_at: datetime
    model_used: str
    average_confidence: float
    rule_count: int

    @field_serializer("extracted_at")
    def serialize_datetime(self, dt: datetime, _info):
        return dt.isoformat()


class ExtractRulesResponse(BaseModel):
    success: bool
    rules: List[ExtractedRule]
    meta: Optional[ExtractRulesMeta] = None
    error: Optional[str] = None
