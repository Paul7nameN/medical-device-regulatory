# Design: Compliance Report Aggregator

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         COMPLIANCE REPORT AGGREGATOR                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐  │
│  │                           INPUT SOURCES                                        │  │
│  │                                                                                │  │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐           │  │
│  │  │  Log Parser      │  │ Regulatory Engine│  │   AI Analysis    │           │  │
│  │  │                  │  │                  │  │                  │           │  │
│  │  │  • LogEntry[]   │  │  • Finding[]    │  │  • ChartAnalysis │           │  │
│  │  │  • ParseResult  │  │  • Compliance   │  │  • LogAnalysis   │           │  │
│  │  │  • Events       │  │    Report       │  │  • CrossValidation│           │  │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘           │  │
│  └──────────────────────────────────────────────────────────────────────────────┘  │
│                                            │                                         │
│                                            ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────────────┐  │
│  │                        AGGREGATION CORE                                        │  │
│  │                                                                                │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │  Findings    │  │   Severity   │  │  Temporal    │  │   AI Merge   │   │  │
│  │  │  Aggregator  │  │  Classifier  │  │  Analyzer    │  │               │   │  │
│  │  │              │  │              │  │              │  │               │   │  │
│  │  │  • Dedupe    │  │  • Normalize │  │  • Timeline  │  │  • Chart     │   │  │
│  │  │  • Group     │  │  • Override  │  │  • Gaps      │  │    Findings  │   │  │
│  │  │  • Merge     │  │  • Critical  │  │  • Sequences │  │  • Log       │   │  │
│  │  │              │  │    Detection │  │  • Recovery  │  │    Insights  │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────────────────┘  │
│                                            │                                         │
│                                            ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────────────┐  │
│  │                        RECOMMENDATION ENGINE                                   │  │
│  │                                                                                │  │
│  │  ┌──────────────────────────────────────────────────────────────────────┐   │  │
│  │  │  Priority: CRITICAL → HIGH → MEDIUM → LOW → INFO                     │   │  │
│  │  │                                                                         │   │  │
│  │  │  • Rule-specific remediation hints                                      │   │  │
│  │  │  • Temporal context (when did violations occur?)                       │   │  │
│  │  │  • Correlation analysis (related violations)                           │   │  │
│  │  │  • AI-enhanced insights (if available)                                 │   │  │
│  │  └──────────────────────────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────────────────┘  │
│                                            │                                         │
│                                            ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────────────┐  │
│  │                        OUTPUT: AGGREGATED REPORT                              │  │
│  │                                                                                │  │
│  │  • Summary (counts by severity)                                               │  │
│  │  • Violations by REG-* rule code                                              │  │
│  │  • Temporal analysis (timeline, gaps, recovery)                              │  │
│  │  • AI enhancements (chart findings, insights, confidence)                    │  │
│  │  • Prioritized recommendations                                                │  │
│  └──────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

## Module Structure

```
backend/app/
├── reports/
│   ├── __init__.py
│   ├── aggregator.py          # Main ComplianceReportAggregator class
│   ├── models.py              # Extended data models
│   ├── severity.py            # Severity classification logic
│   ├── temporal.py            # Temporal analysis functions
│   ├── recommendations.py     # Recommendation generation
│   └── exceptions.py          # Custom exceptions
│
├── api/
│   └── reports.py             # FastAPI endpoints for report generation
│
└── models/
    └── findings.py            # Existing models (extend if needed)
```

## Data Models

### Extended Models (models.py)

```python
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
```

## Severity Classification Logic (severity.py)

### Critical Violation Detection

```python
class SeverityClassifier:
    
    CRITICAL_TRIGGERS = {
        "REG-TEMP-1": {
            "condition": "violation_count > 3",
            "base_severity": Severity.HIGH,
            "upgrade_threshold": 3
        },
        "REG-TEMP-2": {
            "condition": "any_excursion_exceeds_5min OR cumulative_exceeds_10min",
            "base_severity": Severity.CRITICAL,
            "upgrade_threshold": 0
        },
        "REG-SENS-1": {
            "condition": "both_primary_and_secondary_timeout",
            "base_severity": Severity.HIGH,
            "upgrade_condition": "dual_failure"
        },
    }
    
    def classify(
        self,
        finding: Finding,
        context: Dict[str, Any]
    ) -> Severity:
        rule_id = finding.rule_id
        
        if rule_id == "REG-TEMP-1":
            violation_count = context.get("temp_violation_count", 0)
            if violation_count > 3:
                return Severity.CRITICAL
            return Severity.HIGH
        
        elif rule_id == "REG-TEMP-2":
            return Severity.CRITICAL
        
        elif rule_id == "REG-SENS-1":
            if context.get("dual_sensor_failure", False):
                return Severity.CRITICAL
            return Severity.HIGH
        
        elif rule_id == "REG-ALARM-1":
            return Severity.HIGH
        
        elif rule_id in ["REG-TEMP-3", "REG-SENS-3"]:
            return Severity.HIGH
        
        elif rule_id in ["REG-TEMP-4", "REG-DATA-2", "REG-ALARM-2", "REG-ALARM-3"]:
            return Severity.MEDIUM
        
        elif rule_id in ["REG-SENS-2"]:
            return Severity.INFO
        
        return finding.severity
    
    def get_critical_rules(self) -> List[str]:
        return ["REG-TEMP-1", "REG-TEMP-2", "REG-SENS-1", "REG-ALARM-1"]
    
    def is_critical_violation(
        self,
        finding: Finding,
        context: Dict[str, Any]
    ) -> bool:
        classified = self.classify(finding, context)
        return classified == Severity.CRITICAL
```

### Severity Override Matrix

| Rule ID | Base Severity | Can be CRITICAL? | Trigger |
|---------|---------------|------------------|---------|
| REG-TEMP-1 | HIGH | Yes | >3 violations in analysis window |
| REG-TEMP-2 | CRITICAL | Always | Any excursion >5min or cumulative >10min |
| REG-SENS-1 | HIGH | Yes | Both PRIMARY + SECONDARY sensor timeouts |
| REG-ALARM-1 | HIGH | No | Always HIGH (but critical implications) |
| REG-TEMP-3 | HIGH | No | Always HIGH |
| REG-SENS-3 | HIGH | No | Always HIGH |
| REG-TEMP-4 | MEDIUM | No | Always MEDIUM |
| REG-DATA-2 | MEDIUM | No | Always MEDIUM |
| REG-ALARM-2 | MEDIUM | No | Always MEDIUM |
| REG-ALARM-3 | MEDIUM | No | Always MEDIUM |
| REG-SENS-2 | INFO | No | Always INFO (needs physical inspection) |

## Temporal Analysis (temporal.py)

### Timeline Construction

```python
def build_event_timeline(
    logs: List[LogEntry],
    findings: List[Finding],
    ai_chart_violations: Optional[List] = None
) -> List[TimelineEvent]:
    
    events: List[TimelineEvent] = []
    
    for log in logs:
        events.append(TimelineEvent(
            timestamp=log.timestamp,
            event_type=f"LOG_{log.log_type.value}",
            description=f"{log.log_type.value}: {log.raw_value}",
            details={"log_type": log.log_type.value, "raw_value": log.raw_value}
        ))
    
    for finding in findings:
        if not finding.passed:
            events.append(TimelineEvent(
                timestamp=finding.timestamp,
                event_type=f"VIOLATION_{finding.rule_id}",
                rule_id=finding.rule_id,
                severity=finding.severity,
                description=f"[{finding.rule_id}] {finding.message}",
                details={"severity": finding.severity.value, "category": finding.category}
            ))
    
    if ai_chart_violations:
        for v in ai_chart_violations:
            ts = v.get("timestamp_start", datetime.now())
            events.append(TimelineEvent(
                timestamp=ts,
                event_type=f"CHART_{v.get('violation_type', 'unknown')}",
                description=f"Chart: {v.get('description', '')}",
                details={"source": "ai_chart_analysis", "confidence": v.get("confidence")}
            ))
    
    return sorted(events, key=lambda e: e.timestamp)
```

### Critical Period Detection

```python
def detect_critical_periods(
    timeline: List[TimelineEvent],
    window_minutes: int = 15
) -> List[CriticalPeriod]:
    
    critical_periods: List[CriticalPeriod] = []
    
    if not timeline:
        return critical_periods
    
    critical_events = [
        e for e in timeline
        if e.severity in (Severity.CRITICAL, Severity.HIGH)
    ]
    
    if not critical_events:
        return critical_periods
    
    window = timedelta(minutes=window_minutes)
    
    for i, event in enumerate(critical_events):
        window_start = event.timestamp
        window_end = window_start + window
        
        events_in_window = [
            e for e in timeline
            if window_start <= e.timestamp <= window_end
        ]
        
        critical_count = sum(
            1 for e in events_in_window
            if e.severity == Severity.CRITICAL
        )
        high_count = sum(
            1 for e in events_in_window
            if e.severity == Severity.HIGH
        )
        
        if critical_count > 0 or high_count >= 3:
            critical_periods.append(CriticalPeriod(
                period_start=window_start,
                period_end=window_end,
                duration_seconds=window.total_seconds(),
                violations_count=len([e for e in events_in_window if e.rule_id]),
                critical_count=critical_count,
                high_count=high_count,
                triggering_rule=event.rule_id,
                description=f"Cluster of {critical_count} critical, {high_count} high severity events"
            ))
    
    merged = []
    for period in critical_periods:
        if not merged:
            merged.append(period)
        else:
            last = merged[-1]
            if period.period_start <= last.period_end + timedelta(minutes=5):
                last.period_end = max(last.period_end, period.period_end)
                last.critical_count += period.critical_count
                last.high_count += period.high_count
            else:
                merged.append(period)
    
    return merged
```

### Gap Detection

```python
def detect_gaps(
    timeline: List[TimelineEvent],
    max_expected_gap_seconds: float = 30.0
) -> List[GapAnalysis]:
    
    gaps: List[GapAnalysis] = []
    
    if len(timeline) < 2:
        return gaps
    
    sorted_events = sorted(timeline, key=lambda e: e.timestamp)
    
    for i in range(1, len(sorted_events)):
        gap = sorted_events[i].timestamp - sorted_events[i-1].timestamp
        gap_seconds = gap.total_seconds()
        
        if gap_seconds > max_expected_gap_seconds:
            gaps.append(GapAnalysis(
                gap_start=sorted_events[i-1].timestamp,
                gap_end=sorted_events[i].timestamp,
                gap_duration_seconds=gap_seconds,
                gap_type="telemetry_gap" if gap_seconds > 90 else "sampling_gap",
                preceding_event=sorted_events[i-1].event_type,
                following_event=sorted_events[i].event_type
            ))
    
    return gaps
```

## Aggregator Class (aggregator.py)

```python
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict
import logging

from app.models.logs import LogEntry
from app.models.findings import (
    Finding, ComplianceReport, Severity, CategorySummary
)
from app.reports.models import (
    AggregatedComplianceReport, ViolationSummary, TemporalAnalysis,
    TimelineEvent, CriticalPeriod, GapAnalysis, RecoveryInterval,
    AIEnhancements, Recommendation
)
from app.reports.severity import SeverityClassifier
from app.reports.temporal import (
    build_event_timeline, detect_critical_periods, detect_gaps
)
from app.reports.recommendations import generate_recommendations

logger = logging.getLogger(__name__)


class ComplianceReportAggregator:
    
    def __init__(self):
        self.severity_classifier = SeverityClassifier()
    
    def aggregate(
        self,
        regulatory_report: ComplianceReport,
        logs: Optional[List[LogEntry]] = None,
        ai_chart_analysis: Optional[Dict[str, Any]] = None,
        ai_log_analysis: Optional[Dict[str, Any]] = None,
        ai_cross_validation: Optional[Dict[str, Any]] = None,
        include_raw_report: bool = False
    ) -> AggregatedComplianceReport:
        
        logger.info("Starting compliance report aggregation")
        
        logs = logs or []
        findings = regulatory_report.findings
        
        classification_context = self._build_classification_context(
            findings, logs
        )
        
        severity_counts = self._classify_findings(
            findings, classification_context
        )
        
        violations_by_rule = self._group_by_rule(
            findings, classification_context
        )
        
        temporal_analysis = self._perform_temporal_analysis(
            logs, findings, ai_chart_analysis
        )
        
        ai_enhancements = self._merge_ai_analysis(
            ai_chart_analysis, ai_log_analysis, ai_cross_validation
        )
        
        recommendations = generate_recommendations(
            violations_by_rule, temporal_analysis, ai_enhancements
        )
        
        summary = {
            "total_findings": len(findings),
            "passed_count": regulatory_report.passed_count,
            "failed_count": regulatory_report.failed_count,
            "critical_count": severity_counts.get(Severity.CRITICAL, 0),
            "high_count": severity_counts.get(Severity.HIGH, 0),
            "medium_count": severity_counts.get(Severity.MEDIUM, 0),
            "low_count": severity_counts.get(Severity.LOW, 0),
            "info_count": severity_counts.get(Severity.INFO, 0),
        }
        
        executive_summary = self._generate_executive_summary(
            summary, violations_by_rule, temporal_analysis
        )
        
        aggregated = AggregatedComplianceReport(
            device_id=regulatory_report.device_id,
            generated_at=datetime.now(),
            time_range_start=regulatory_report.time_range_start,
            time_range_end=regulatory_report.time_range_end,
            total_entries=regulatory_report.total_entries,
            total_rules_evaluated=len(regulatory_report.summary),
            summary=summary,
            violations_by_rule=violations_by_rule,
            violations_by_severity=self._group_by_severity(findings, classification_context),
            temporal_analysis=temporal_analysis,
            ai_enhancements=ai_enhancements,
            recommendations=recommendations,
            executive_summary=executive_summary,
            raw_regulatory_report=(
                self._report_to_dict(regulatory_report)
                if include_raw_report else None
            )
        )
        
        logger.info(
            "Compliance report aggregation complete",
            extra={
                "device_id": aggregated.device_id,
                "critical_count": summary["critical_count"],
                "high_count": summary["high_count"],
                "recommendation_count": len(recommendations)
            }
        )
        
        return aggregated
    
    def _build_classification_context(
        self,
        findings: List[Finding],
        logs: List[LogEntry]
    ) -> Dict[str, Any]:
        
        context = {}
        
        temp_violations = [
            f for f in findings
            if f.rule_id == "REG-TEMP-1" and not f.passed
        ]
        context["temp_violation_count"] = len(temp_violations)
        
        sensor_timeouts = [
            f for f in findings
            if f.rule_id == "REG-SENS-1" and not f.passed
        ]
        context["dual_sensor_failure"] = any(
            "both" in f.message.lower() or "primary" in f.message.lower() and "secondary" in f.message.lower()
            for f in sensor_timeouts
        )
        
        return context
    
    def _classify_findings(
        self,
        findings: List[Finding],
        context: Dict[str, Any]
    ) -> Dict[Severity, int]:
        
        counts: Dict[Severity, int] = defaultdict(int)
        
        for finding in findings:
            if not finding.passed:
                severity = self.severity_classifier.classify(finding, context)
                counts[severity] += 1
        
        return dict(counts)
    
    def _group_by_rule(
        self,
        findings: List[Finding],
        context: Dict[str, Any]
    ) -> Dict[str, ViolationSummary]:
        
        grouped: Dict[str, List[Finding]] = defaultdict(list)
        
        for finding in findings:
            grouped[finding.rule_id].append(finding)
        
        result: Dict[str, ViolationSummary] = {}
        
        for rule_id, rule_findings in grouped.items():
            failed_findings = [f for f in rule_findings if not f.passed]
            passed_findings = [f for f in rule_findings if f.passed]
            
            if not failed_findings and passed_findings:
                continue
            
            sample = failed_findings[:3] if failed_findings else []
            
            timestamps = [
                f.timestamp for f in failed_findings
                if hasattr(f, 'timestamp') and f.timestamp
            ]
            
            result[rule_id] = ViolationSummary(
                rule_id=rule_id,
                rule_description=rule_findings[0].rule_description if rule_findings else "",
                category=rule_findings[0].category if rule_findings else "unknown",
                severity=self.severity_classifier.classify(
                    rule_findings[0], context
                ) if rule_findings else Severity.LOW,
                count=len(failed_findings),
                first_occurrence=min(timestamps) if timestamps else None,
                last_occurrence=max(timestamps) if timestamps else None,
                sample_findings=sample
            )
        
        return result
    
    def _group_by_severity(
        self,
        findings: List[Finding],
        context: Dict[str, Any]
    ) -> Dict[Severity, List[Finding]]:
        
        grouped: Dict[Severity, List[Finding]] = defaultdict(list)
        
        for finding in findings:
            if not finding.passed:
                severity = self.severity_classifier.classify(finding, context)
                grouped[severity].append(finding)
        
        return dict(grouped)
    
    def _perform_temporal_analysis(
        self,
        logs: List[LogEntry],
        findings: List[Finding],
        ai_chart_analysis: Optional[Dict[str, Any]]
    ) -> TemporalAnalysis:
        
        chart_violations = None
        if ai_chart_analysis:
            chart_violations = ai_chart_analysis.get("violations", [])
        
        timeline = build_event_timeline(logs, findings, chart_violations)
        
        critical_periods = detect_critical_periods(timeline)
        gaps = detect_gaps(timeline)
        
        time_start = None
        time_end = None
        if timeline:
            sorted_timeline = sorted(timeline, key=lambda e: e.timestamp)
            time_start = sorted_timeline[0].timestamp
            time_end = sorted_timeline[-1].timestamp
        
        return TemporalAnalysis(
            event_timeline=timeline,
            critical_periods=critical_periods,
            recovery_intervals=[],
            gaps_detected=gaps,
            time_range_start=time_start,
            time_range_end=time_end
        )
    
    def _merge_ai_analysis(
        self,
        chart_analysis: Optional[Dict[str, Any]],
        log_analysis: Optional[Dict[str, Any]],
        cross_validation: Optional[Dict[str, Any]]
    ) -> Optional[AIEnhancements]:
        
        if not any([chart_analysis, log_analysis, cross_validation]):
            return None
        
        enhancements = AIEnhancements()
        
        if chart_analysis:
            enhancements.chart_violations = chart_analysis.get("violations", [])
        
        if log_analysis:
            enhancements.log_insights = {
                "summary": log_analysis.get("summary", ""),
                "key_findings": log_analysis.get("key_findings", []),
                "recommendations": log_analysis.get("recommendations", []),
                "risk_assessment": log_analysis.get("risk_assessment", "low")
            }
        
        if cross_validation:
            enhancements.cross_validation_confidence = cross_validation.get(
                "confidence_score"
            )
        
        return enhancements
    
    def _generate_executive_summary(
        self,
        summary: Dict[str, Any],
        violations_by_rule: Dict[str, ViolationSummary],
        temporal_analysis: TemporalAnalysis
    ) -> str:
        
        critical_count = summary.get("critical_count", 0)
        high_count = summary.get("high_count", 0)
        
        if critical_count == 0 and high_count == 0:
            return (
                "All regulatory checks passed. No critical or high severity "
                "violations detected. Device operating within MED-THERM-2026 "
                "compliance parameters."
            )
        
        critical_rules = [
            vs.rule_id
            for vs in violations_by_rule.values()
            if vs.severity == Severity.CRITICAL
        ]
        
        high_rules = [
            vs.rule_id
            for vs in violations_by_rule.values()
            if vs.severity == Severity.HIGH
        ]
        
        parts = []
        
        if critical_count > 0:
            parts.append(
                f"CRITICAL: {critical_count} violation(s) detected in rules: "
                f"{', '.join(critical_rules)}. "
                "Immediate investigation required."
            )
        
        if high_count > 0:
            parts.append(
                f"HIGH: {high_count} violation(s) detected in rules: "
                f"{', '.join(high_rules)}. "
                "Prioritize for next maintenance window."
            )
        
        if temporal_analysis.critical_periods:
            period_count = len(temporal_analysis.critical_periods)
            parts.append(
                f"Identified {period_count} critical time period(s) with "
                "clustered violations. Review temporal analysis for details."
            )
        
        return " ".join(parts)
    
    def _report_to_dict(self, report: ComplianceReport) -> Dict[str, Any]:
        return {
            "device_id": report.device_id,
            "analyzed_at": report.analyzed_at.isoformat() if report.analyzed_at else None,
            "total_entries": report.total_entries,
            "time_range_start": (
                report.time_range_start.isoformat()
                if report.time_range_start else None
            ),
            "time_range_end": (
                report.time_range_end.isoformat()
                if report.time_range_end else None
            ),
            "summary": {
                k: {"passed": v.passed, "failed": v.failed, "total": v.total}
                for k, v in report.summary.items()
            },
            "passed_count": report.passed_count,
            "failed_count": report.failed_count,
            "critical_count": report.critical_count
        }
```

## Recommendation Engine (recommendations.py)

```python
from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict

from app.models.findings import Severity
from app.reports.models import (
    ViolationSummary, TemporalAnalysis, AIEnhancements, Recommendation
)


RULE_REMEDIATION_HINTS: Dict[str, Dict[str, Any]] = {
    "REG-TEMP-1": {
        "title": "Investigate Temperature Excursions",
        "description": "Temperature readings outside valid range detected. Check cooling system and door access patterns.",
        "remediation_hint": "1. Verify cooling system is operating correctly\n2. Review door event frequency\n3. Check sensor calibration\n4. Verify thermal load hasn't changed",
    },
    "REG-TEMP-2": {
        "title": "Critical: Excursion Limits Exceeded",
        "description": "Temperature excursion duration exceeds MED-THERM-2026 limits. This is a CRITICAL violation requiring immediate action.",
        "remediation_hint": "1. IMMEDIATE: Check cooling system capacity\n2. Review door access logs for excessive openings\n3. Verify temperature sensor calibration\n4. Check for thermal insulation degradation\n5. Review alarm thresholds and activation",
    },
    "REG-TEMP-3": {
        "title": "Slow Recovery After Disturbance",
        "description": "System taking longer than 3 minutes to recover after door opening or other disturbance.",
        "remediation_hint": "1. Check cooling system capacity\n2. Verify door seals are intact\n3. Review door operation procedures\n4. Check for thermal load issues",
    },
    "REG-SENS-1": {
        "title": "Sensor Redundancy Compromised",
        "description": "One or both temperature sensors experiencing timeouts. Dual failure is CRITICAL.",
        "remediation_hint": "1. Check sensor wiring and connections\n2. Verify sensor power supply\n3. Test sensor replacement if failures persist\n4. For dual failure: IMMEDIATE investigation required",
    },
    "REG-ALARM-1": {
        "title": "Alarm Activation Failure",
        "description": "Temperature excursion ≥2 minutes detected without corresponding alarm activation.",
        "remediation_hint": "1. Verify alarm system configuration\n2. Check alarm threshold settings\n3. Test alarm activation with simulated excursion\n4. Verify sensor-alarm integration",
    },
    "REG-DATA-2": {
        "title": "Telemetry Gaps Detected",
        "description": "Telemetry data gaps exceeding 90 seconds detected. May indicate communication or logging issues.",
        "remediation_hint": "1. Check network connectivity\n2. Verify logging service status\n3. Review telemetry sync configuration\n4. Check for power interruptions",
    },
}


def generate_recommendations(
    violations_by_rule: Dict[str, ViolationSummary],
    temporal_analysis: TemporalAnalysis,
    ai_enhancements: AIEnhancements
) -> List[Recommendation]:
    
    recommendations: List[Recommendation] = []
    
    severity_order = [
        Severity.CRITICAL,
        Severity.HIGH,
        Severity.MEDIUM,
        Severity.LOW,
        Severity.INFO
    ]
    
    for severity in severity_order:
        for rule_id, vs in violations_by_rule.items():
            if vs.severity != severity:
                continue
            
            rule_info = RULE_REMEDIATION_HINTS.get(rule_id, {})
            
            temporal_context = _get_temporal_context(vs, temporal_analysis)
            
            rec = Recommendation(
                priority=vs.severity,
                rule_id=rule_id,
                rule_description=vs.rule_description,
                title=rule_info.get("title", f"Address {rule_id} Violations"),
                description=rule_info.get(
                    "description",
                    f"{vs.count} violation(s) detected for {rule_id}"
                ),
                remediation_hint=rule_info.get("remediation_hint"),
                temporal_context=temporal_context,
                evidence_count=vs.count,
                first_occurrence=vs.first_occurrence
            )
            
            recommendations.append(rec)
    
    if ai_enhancements and ai_enhancements.log_insights:
        ai_recs = ai_enhancements.log_insights.get("recommendations", [])
        for ai_rec in ai_recs[:2]:
            if ai_rec and ai_rec not in [r.description for r in recommendations]:
                recommendations.append(Recommendation(
                    priority=Severity.LOW,
                    rule_id="AI_INSIGHT",
                    rule_description="AI-generated insight",
                    title="Additional AI Insight",
                    description=str(ai_rec),
                    evidence_count=0
                ))
    
    return recommendations


def _get_temporal_context(
    vs: ViolationSummary,
    temporal_analysis: TemporalAnalysis
) -> str:
    
    context_parts = []
    
    if vs.first_occurrence and vs.last_occurrence:
        if vs.first_occurrence == vs.last_occurrence:
            context_parts.append(
                f"Occurred at {vs.first_occurrence.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        else:
            context_parts.append(
                f"First occurrence: {vs.first_occurrence.strftime('%Y-%m-%d %H:%M:%S')}, "
                f"Last occurrence: {vs.last_occurrence.strftime('%Y-%m-%d %H:%M:%S')}"
            )
    
    related_periods = [
        p for p in temporal_analysis.critical_periods
        if vs.first_occurrence and p.period_start <= vs.first_occurrence <= p.period_end
    ]
    
    if related_periods:
        context_parts.append(
            f"Part of {len(related_periods)} critical period(s) with clustered violations"
        )
    
    return " | ".join(context_parts) if context_parts else None
```

## API Endpoints (api/reports.py)

```python
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.models.logs import LogEntry
from app.models.findings import ComplianceReport
from app.regulatory.engine import RegulatoryEngine
from app.regulatory.parser import parse_raw_logs
from app.reports.aggregator import ComplianceReportAggregator
from app.reports.models import AggregatedComplianceReport

router = APIRouter()
logger = logging.getLogger(__name__)


class GenerateReportRequest(BaseModel):
    raw_logs: Optional[List[str]] = None
    entries: Optional[List[Dict[str, Any]]] = None
    device_id: str = "unknown"
    filter_rules: Optional[List[str]] = None
    include_ai_analysis: bool = False
    include_raw_report: bool = False


class GenerateReportResponse(BaseModel):
    report: AggregatedComplianceReport
    generated_at: datetime


class SummaryResponse(BaseModel):
    device_id: str
    summary: Dict[str, Any]
    critical_rules: List[str]
    high_rules: List[str]
    recommendation_count: int


@router.post("/reports/generate", response_model=GenerateReportResponse)
async def generate_compliance_report(
    request: GenerateReportRequest
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
        
        engine = RegulatoryEngine()
        base_report = engine.validate(
            logs=entries,
            filter_rules=request.filter_rules,
            device_id=request.device_id
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
                "high_count": aggregated.summary.get("high_count", 0)
            }
        )
        
        return GenerateReportResponse(
            report=aggregated,
            generated_at=datetime.now()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Report generation failed", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {str(e)}"
        )


@router.get("/reports/summary/{device_id}", response_model=SummaryResponse)
async def get_report_summary(
    device_id: str,
    report_data: Optional[Dict[str, Any]] = Query(None)
):
    """
    Get a concise summary of compliance status for a device.
    
    Returns key metrics:
    - Critical/high severity rule violations
    - Summary counts
    - Recommendation count
    """
    pass
```

## Integration With Existing API

The existing `/validate` endpoint returns a basic `ComplianceReport`. The new `/reports/generate` endpoint:

1. Accepts the same input format (`raw_logs` or `entries`)
2. Runs the same regulatory validation
3. Adds aggregation, temporal analysis, and recommendations
4. Returns the richer `AggregatedComplianceReport`

**Backward Compatibility:**
- Existing `/validate` endpoint remains unchanged
- New `/reports` endpoints are additive
- Both use the same `RegulatoryEngine` for validation

## Testing Strategy

### Unit Tests

| Test Category | What to Test |
|---------------|--------------|
| Severity Classification | REG-TEMP-1 with 1, 3, 4+ violations |
| | REG-SENS-1 with single vs dual sensor failure |
| | REG-TEMP-2 always returns CRITICAL |
| Temporal Analysis | Timeline construction from logs + findings |
| | Critical period detection (windowing logic) |
| | Gap detection (30s, 90s thresholds) |
| Aggregation | Deduplication of findings |
| | Grouping by rule ID |
| | Executive summary generation |
| Recommendations | Priority ordering (CRITICAL first) |
| | Rule-specific remediation hints |
| | Temporal context inclusion |

### Integration Tests

| Test Scenario | Description |
|---------------|-------------|
| Happy Path | Valid logs → full report generation |
| Critical Violations | 4+ REG-TEMP-1 violations → CRITICAL classification |
| Dual Sensor Failure | Both PRIMARY + SECONDARY timeout → CRITICAL |
| No Violations | All rules pass → positive summary |
| Edge Cases | Empty logs, single log, malformed entries |

### Test Data

Use existing sample data:
- `docs/client/medical_device_logs_1000.txt` for realistic logs
- Synthetic critical violation sequences for testing severity logic

## Performance Considerations

### Complexity Analysis

| Operation | Complexity | Notes |
|-----------|------------|-------|
| Finding Aggregation | O(n) | n = number of findings |
| Timeline Construction | O(n log n) | Sorting by timestamp |
| Critical Period Detection | O(m * k) | m = critical events, k = window |
| Gap Detection | O(n) | Single pass through sorted events |
| Report Generation | O(n + m) | n = logs, m = findings |

### Memory Usage

- All operations in-memory (no disk I/O)
- Timeline stored as list of events
- Recommendations stored in priority order
- Typical memory: < 50MB for 10,000 log entries

### Optimization Strategies

1. **Lazy Timeline Construction** - Only build timeline if temporal analysis requested
2. **Event Filtering** - Filter out INFO severity for critical path analysis
3. **Caching** - Cache aggregated reports for identical input
4. **Streaming** - For very large datasets, process in batches

## Error Handling

### Custom Exceptions

```python
class ReportError(Exception):
    """Base exception for report generation errors."""
    pass


class AggregationError(ReportError):
    """Error during finding aggregation."""
    pass


class TemporalAnalysisError(ReportError):
    """Error during temporal analysis."""
    pass


class InvalidInputError(ReportError):
    """Invalid input data provided."""
    def __init__(self, message: str, field: str):
        self.field = field
        super().__init__(message)
```

### Error Response Schema

```python
{
    "error": {
        "type": "InvalidInputError",
        "message": "No valid log entries provided",
        "field": "raw_logs",
        "timestamp": "2026-05-12T17:30:00"
    }
}
```

## Module Exports (`reports/__init__.py`)

```python
from app.reports.aggregator import ComplianceReportAggregator
from app.reports.models import (
    AggregatedComplianceReport,
    ViolationSummary,
    TemporalAnalysis,
    TimelineEvent,
    CriticalPeriod,
    GapAnalysis,
    RecoveryInterval,
    AIEnhancements,
    Recommendation
)
from app.reports.severity import SeverityClassifier
from app.reports.exceptions import (
    ReportError,
    AggregationError,
    TemporalAnalysisError,
    InvalidInputError
)

__all__ = [
    "ComplianceReportAggregator",
    "AggregatedComplianceReport",
    "ViolationSummary",
    "TemporalAnalysis",
    "TimelineEvent",
    "CriticalPeriod",
    "GapAnalysis",
    "RecoveryInterval",
    "AIEnhancements",
    "Recommendation",
    "SeverityClassifier",
    "ReportError",
    "AggregationError",
    "TemporalAnalysisError",
    "InvalidInputError",
]
```