from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_serializer


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Evidence(BaseModel):
    entry_index: int
    timestamp: datetime
    log_type: str
    raw_value: str
    explanation: str

    @field_serializer("timestamp")
    def serialize_datetime(self, dt: datetime, _info):
        return dt.isoformat()


class Finding(BaseModel):
    rule_id: str
    rule_description: str
    category: str
    severity: Severity
    passed: bool
    message: str
    evidence: List[Evidence] = []
    timestamp: datetime
    remediation_hint: Optional[str] = None
    needs_visual_verification: bool = False
    data_source: Optional[str] = None
    confidence: Optional[float] = None
    inspection_hint: Optional[str] = None

    @field_serializer("timestamp")
    def serialize_datetime(self, dt: datetime, _info):
        return dt.isoformat()


class CategorySummary(BaseModel):
    passed: int
    failed: int
    total: int


class ComplianceReport(BaseModel):
    device_id: str = "unknown"
    analyzed_at: datetime
    total_entries: int
    time_range_start: Optional[datetime] = None
    time_range_end: Optional[datetime] = None

    summary: Dict[str, CategorySummary]
    findings: List[Finding]
    passed_count: int
    failed_count: int
    critical_count: int

    @field_serializer("analyzed_at", "time_range_start", "time_range_end")
    def serialize_datetime(self, dt: Optional[datetime], _info):
        return dt.isoformat() if dt else None

    def get_findings_by_severity(self, severity: Severity) -> List[Finding]:
        return [f for f in self.findings if f.severity == severity]

    def get_findings_by_rule(self, rule_id: str) -> List[Finding]:
        return [f for f in self.findings if f.rule_id == rule_id]

    def get_findings_by_category(self, category: str) -> List[Finding]:
        return [f for f in self.findings if f.category == category]

    def to_dict(self, include_findings: bool = True) -> Dict[str, Any]:
        summary_dict: Dict[str, Any] = {}
        for cat, summary in self.summary.items():
            summary_dict[cat] = {
                "passed": summary.passed,
                "failed": summary.failed,
                "total": summary.total
            }

        result: Dict[str, Any] = {
            "device_id": self.device_id,
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
            "total_entries": self.total_entries,
            "time_range_start": self.time_range_start.isoformat() if self.time_range_start else None,
            "time_range_end": self.time_range_end.isoformat() if self.time_range_end else None,
            "summary": summary_dict,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "critical_count": self.critical_count
        }

        if include_findings:
            findings_dicts = []
            for finding in self.findings:
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

        return result
