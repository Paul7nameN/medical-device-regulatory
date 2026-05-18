from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_serializer

from app.models.findings import Severity, Finding, ComplianceReport


class ViolationSummary(BaseModel):
    rule_id: str
    rule_description: str
    category: str
    severity: Severity
    count: int
    first_occurrence: Optional[datetime] = None
    last_occurrence: Optional[datetime] = None
    sample_findings: List[Finding] = []
    
    @field_serializer("first_occurrence", "last_occurrence")
    def serialize_datetime(self, dt: Optional[datetime], _info):
        return dt.isoformat() if dt else None


class TimelineEvent(BaseModel):
    timestamp: datetime
    event_type: str
    rule_id: Optional[str] = None
    severity: Optional[Severity] = None
    description: str
    details: Dict[str, Any] = {}
    
    @field_serializer("timestamp")
    def serialize_datetime(self, dt: datetime, _info):
        return dt.isoformat()


class GapAnalysis(BaseModel):
    gap_start: datetime
    gap_end: datetime
    gap_duration_seconds: float
    gap_type: str
    preceding_event: Optional[str] = None
    following_event: Optional[str] = None
    
    @field_serializer("gap_start", "gap_end")
    def serialize_datetime(self, dt: datetime, _info):
        return dt.isoformat()


class RecoveryInterval(BaseModel):
    disturbance_start: datetime
    recovery_complete: datetime
    recovery_duration_seconds: float
    successful: bool
    severity: Severity
    rule_id: Optional[str] = None


class CriticalPeriod(BaseModel):
    period_start: datetime
    period_end: datetime
    duration_seconds: float
    violations_count: int
    critical_count: int
    high_count: int
    triggering_rule: Optional[str] = None
    description: str
    
    @field_serializer("period_start", "period_end")
    def serialize_datetime(self, dt: datetime, _info):
        return dt.isoformat()


class TemporalAnalysis(BaseModel):
    event_timeline: List[TimelineEvent] = []
    critical_periods: List[CriticalPeriod] = []
    recovery_intervals: List[RecoveryInterval] = []
    gaps_detected: List[GapAnalysis] = []
    time_range_start: Optional[datetime] = None
    time_range_end: Optional[datetime] = None
    
    @field_serializer("time_range_start", "time_range_end")
    def serialize_datetime(self, dt: Optional[datetime], _info):
        return dt.isoformat() if dt else None


class AIEnhancements(BaseModel):
    chart_violations: List[Dict[str, Any]] = []
    log_insights: Dict[str, Any] = {}
    cross_validation_confidence: Optional[float] = None
    generated_report_summary: Optional[str] = None


class Recommendation(BaseModel):
    priority: Severity
    rule_id: str
    rule_description: str
    title: str
    description: str
    remediation_hint: Optional[str] = None
    temporal_context: Optional[str] = None
    evidence_count: int = 0
    first_occurrence: Optional[datetime] = None
    
    @field_serializer("first_occurrence")
    def serialize_datetime(self, dt: Optional[datetime], _info):
        return dt.isoformat() if dt else None


class AggregatedComplianceReport(BaseModel):
    device_id: str = "unknown"
    generated_at: datetime
    time_range_start: Optional[datetime] = None
    time_range_end: Optional[datetime] = None
    
    total_entries: int = 0
    total_rules_evaluated: int = 0
    
    summary: Dict[str, int] = {}
    
    violations_by_rule: Dict[str, ViolationSummary] = {}
    violations_by_severity: Dict[Severity, List[Finding]] = {}
    
    temporal_analysis: TemporalAnalysis
    ai_enhancements: Optional[AIEnhancements] = None
    
    recommendations: List[Recommendation] = []
    executive_summary: str = ""
    
    raw_regulatory_report: Optional[Dict[str, Any]] = None
    
    @field_serializer("generated_at", "time_range_start", "time_range_end")
    def serialize_datetime(self, dt: Optional[datetime], _info):
        return dt.isoformat() if dt else None