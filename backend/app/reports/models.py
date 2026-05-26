from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_serializer

from app.models.findings import Severity, Finding, ComplianceReport
from app.models.multimodal import (
    SourceFile,
    CorrelationInsight,
    ConflictingFinding,
    CorrelationSummary,
)


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
    
    data_sources: List[SourceFile] = []
    multi_modal_confidence: Optional[float] = None
    correlation_insights: List[CorrelationInsight] = []
    conflicting_findings: List[ConflictingFinding] = []
    correlation_summary: Optional[CorrelationSummary] = None
    alignment_uncertain: bool = False
    
    @field_serializer("generated_at", "time_range_start", "time_range_end")
    def serialize_datetime(self, dt: Optional[datetime], _info):
        return dt.isoformat() if dt else None

    @property
    def analyzed_at(self) -> datetime:
        """Compatibility with ComplianceReport.analyzed_at."""
        return self.generated_at

    @property
    def findings(self) -> List[Finding]:
        """Compatibility with ComplianceReport.findings. Flattens violations_by_severity."""
        all_findings: List[Finding] = []
        for severity, findings_list in self.violations_by_severity.items():
            all_findings.extend(findings_list)
        return all_findings

    @property
    def passed_count(self) -> int:
        """Compatibility with ComplianceReport.passed_count."""
        return self.summary.get("passed_count", 0)

    @property
    def failed_count(self) -> int:
        """Compatibility with ComplianceReport.failed_count."""
        return self.summary.get("failed_count", 0)

    @property
    def critical_count(self) -> int:
        """Compatibility with ComplianceReport.critical_count."""
        return self.summary.get("critical_count", 0)

    def to_dict(self, include_findings: bool = True) -> Dict[str, Any]:
        """
        Convert to dictionary for persistence.
        Compatible with ComplianceReport.to_dict() interface.
        """
        findings_list = self.findings

        category_summary: Dict[str, Dict[str, int]] = {}
        for finding in findings_list:
            category = finding.category
            if category not in category_summary:
                category_summary[category] = {"passed": 0, "failed": 0, "total": 0}
            category_summary[category]["total"] += 1
            if finding.passed:
                category_summary[category]["passed"] += 1
            else:
                category_summary[category]["failed"] += 1

        result: Dict[str, Any] = {
            "device_id": self.device_id,
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
            "total_entries": self.total_entries,
            "time_range_start": self.time_range_start.isoformat() if self.time_range_start else None,
            "time_range_end": self.time_range_end.isoformat() if self.time_range_end else None,
            "summary": category_summary,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "critical_count": self.critical_count,
        }

        if include_findings:
            findings_dicts = []
            for finding in findings_list:
                evidence_dicts = []
                for ev in finding.evidence:
                    evidence_dicts.append({
                        "entry_index": ev.entry_index,
                        "timestamp": ev.timestamp.isoformat() if ev.timestamp else None,
                        "log_type": ev.log_type,
                        "raw_value": ev.raw_value,
                        "explanation": ev.explanation
                    })

                findings_dicts.append({
                    "rule_id": finding.rule_id,
                    "rule_description": finding.rule_description,
                    "category": finding.category,
                    "severity": finding.severity.value if hasattr(finding.severity, 'value') else str(finding.severity),
                    "passed": finding.passed,
                    "message": finding.message,
                    "evidence": evidence_dicts,
                    "timestamp": finding.timestamp.isoformat() if finding.timestamp else None,
                    "remediation_hint": finding.remediation_hint,
                    "needs_visual_verification": finding.needs_visual_verification,
                    "data_source": finding.data_source,
                    "confidence": finding.confidence,
                    "inspection_hint": finding.inspection_hint
                })
            result["findings"] = findings_dicts

        if self.data_sources:
            result["data_sources"] = [s.model_dump(mode='json') for s in self.data_sources]

        if self.multi_modal_confidence is not None:
            result["multi_modal_confidence"] = self.multi_modal_confidence

        if self.correlation_insights:
            result["correlation_insights"] = [ci.model_dump(mode='json') for ci in self.correlation_insights]

        if self.conflicting_findings:
            result["conflicting_findings"] = [cf.model_dump(mode='json') for cf in self.conflicting_findings]

        if self.correlation_summary:
            result["correlation_summary"] = self.correlation_summary.model_dump(mode='json')

        result["alignment_uncertain"] = self.alignment_uncertain

        if self.temporal_analysis:
            result["temporal_analysis"] = self.temporal_analysis.model_dump(mode='json')

        if self.ai_enhancements:
            result["ai_enhancements"] = self.ai_enhancements.model_dump(mode='json')

        return result