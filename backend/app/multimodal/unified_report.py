from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from collections import defaultdict
import logging

from app.models.logs import LogEntry, LogType
from app.models.findings import Finding, ComplianceReport, Severity
from app.models.multimodal import (
    SourceFile,
    CorrelatedFinding,
    ConflictingFinding,
    CorrelationSummary,
    CorrelationInsight,
)
from app.ai.image.models import TemperatureReading, ChartViolation
from app.ai.image.converters import (
    CHART_VIOLATION_MAPPINGS, 
    chart_violation_to_finding,
    confidence_to_severity
)
from app.reports.models import (
    AggregatedComplianceReport,
    TimelineEvent,
    TemporalAnalysis,
)
from app.reports.aggregator import ComplianceReportAggregator, aggregate_report

logger = logging.getLogger(__name__)


def _temperature_to_severity(temp: float) -> Severity:
    """
    Map temperature excursion to severity based on MED-THERM-2026:
    - 8°C < T ≤ 10°C or 0°C ≤ T < 2°C → HIGH
    - T > 10°C or T < 0°C → CRITICAL
    """
    if temp > 10.0 or temp < 0.0:
        return Severity.CRITICAL
    elif temp > 8.0 or temp < 2.0:
        return Severity.HIGH
    return Severity.LOW


def _get_temperature_severity_label(temp: float) -> str:
    """Get human-readable severity label for temperature."""
    if temp > 10.0 or temp < 0.0:
        return "CRITICAL"
    elif temp > 8.5 or temp < 1.5:
        return "HIGH"
    elif temp > 8.0 or temp < 2.0:
        return "MEDIUM"
    return "LOW"


class UnifiedReportGenerator:
    def __init__(self):
        self.base_aggregator = ComplianceReportAggregator()

    def enhance_findings_with_sources(
        self,
        findings: List[Finding],
        correlated_findings: List[CorrelatedFinding],
        sources: List[SourceFile],
    ) -> List[Finding]:
        """
        Add source tracking information to findings.
        
        Each finding gets a data_sources list indicating which sources support it.
        """
        source_map = {s.id: s for s in sources}
        
        enhanced_findings = []
        
        for finding in findings:
            matching_correlated = [
                cf for cf in correlated_findings
                if cf.rule_id == finding.rule_id
                and abs((cf.timestamp - finding.timestamp).total_seconds()) < 300
            ]
            
            data_sources: List[str] = []
            if hasattr(finding, 'data_source') and finding.data_source:
                data_sources = [finding.data_source]
            else:
                data_sources = ["logs"]
            
            if matching_correlated:
                best_match = max(
                    matching_correlated,
                    key=lambda x: x.combined_confidence
                )
                data_sources = list(set(data_sources + best_match.sources))
                
                if hasattr(finding, 'confidence') and finding.confidence:
                    finding.confidence = min(
                        finding.confidence,
                        best_match.combined_confidence
                    )
                else:
                    finding.confidence = best_match.combined_confidence

            enhanced_findings.append(finding)
        
        return enhanced_findings

    def build_unified_timeline(
        self,
        log_entries: List[LogEntry],
        findings: List[Finding],
        correlated_findings: List[CorrelatedFinding],
        aligned_chart_points: List[TemperatureReading],
        chart_violations: Optional[List[ChartViolation]] = None,
    ) -> List[TimelineEvent]:
        """
        Build a unified timeline combining:
        - Log events (door opens, alarms, etc.)
        - Violations/findings
        - Chart-derived events (both analyzed violations and raw data points)
        - Correlation markers
        """
        events: List[TimelineEvent] = []

        for entry in log_entries:
            event_type = self._log_type_to_event_type(entry.log_type)
            
            if event_type in ["door_open", "door_close", "alarm_triggered", 
                            "sensor_timeout", "device_start"]:
                details: Dict[str, Any] = {
                    "source": "logs",
                    "log_type": entry.log_type.value if hasattr(entry.log_type, 'value') else str(entry.log_type),
                    "raw_value": entry.raw_value,
                }
                if entry.parsed_value is not None:
                    details["parsed_value"] = entry.parsed_value
                
                events.append(TimelineEvent(
                    timestamp=entry.timestamp,
                    event_type=event_type,
                    description=self._log_entry_to_description(entry),
                    details=details,
                ))

        for finding in findings:
            if not finding.passed:
                severity_value = (
                    finding.severity.value 
                    if hasattr(finding.severity, 'value') 
                    else str(finding.severity)
                )
                
                finding_source: str = "logs"
                if hasattr(finding, 'data_source') and finding.data_source:
                    finding_source = finding.data_source
                
                events.append(TimelineEvent(
                    timestamp=finding.timestamp,
                    event_type="violation",
                    rule_id=finding.rule_id,
                    severity=finding.severity,
                    description=f"{finding.rule_id}: {finding.message}",
                    details={
                        "source": finding_source,
                        "severity": severity_value,
                        "evidence_count": len(finding.evidence),
                    },
                ))

        if chart_violations:
            for violation in chart_violations:
                finding = chart_violation_to_finding(violation)
                severity_value = (
                    finding.severity.value 
                    if hasattr(finding.severity, 'value') 
                    else str(finding.severity)
                )
                
                violation_type_value = (
                    violation.violation_type.value
                    if hasattr(violation.violation_type, 'value')
                    else str(violation.violation_type)
                )
                
                events.append(TimelineEvent(
                    timestamp=finding.timestamp,
                    event_type="violation",
                    rule_id=finding.rule_id,
                    severity=finding.severity,
                    description=f"{finding.rule_id}: {finding.message} [Chart]",
                    details={
                        "source": "images",
                        "severity": severity_value,
                        "violation_type": violation_type_value,
                        "confidence": violation.confidence,
                        "extracted_value": violation.extracted_value,
                    },
                ))

        for cf in correlated_findings:
            if len(cf.sources) > 1:
                events.append(TimelineEvent(
                    timestamp=cf.timestamp,
                    event_type="correlation_marker",
                    rule_id=cf.rule_id,
                    description=f"Multi-modal confirmation: {cf.description[:100]}...",
                    details={
                        "sources": cf.sources,
                        "combined_confidence": cf.combined_confidence,
                        "confidence_level": (
                            cf.confidence_level.value 
                            if hasattr(cf.confidence_level, 'value')
                            else str(cf.confidence_level)
                        ),
                        "evidence": cf.evidence,
                    },
                ))

        for point in aligned_chart_points:
            if point.timestamp:
                temp = point.sensor_a
                if temp < 2.0 or temp > 8.0:
                    severity = _temperature_to_severity(temp)
                    severity_label = _get_temperature_severity_label(temp)
                    
                    events.append(TimelineEvent(
                        timestamp=point.timestamp,
                        event_type="chart_anomaly",
                        severity=severity,
                        description=f"[{severity_label}] Chart: {temp}°C outside range [2-8°C]",
                        details={
                            "source": "images",
                            "temperature": temp,
                            "severity": severity_label,
                            "time_label": point.time,
                            "sensor_b": point.sensor_b,
                            "range_min": 2.0,
                            "range_max": 8.0,
                            "deviation": round(temp - 8.0 if temp > 8.0 else 2.0 - temp, 2),
                        },
                    ))

        return sorted(events, key=lambda e: e.timestamp)

    def generate_unified_report(
        self,
        regulatory_report: ComplianceReport,
        log_entries: List[LogEntry],
        sources: List[SourceFile],
        correlated_findings: List[CorrelatedFinding],
        conflicting_findings: List[ConflictingFinding],
        correlation_summary: CorrelationSummary,
        correlation_insights: List[CorrelationInsight],
        aligned_chart_points: List[TemperatureReading],
        chart_violations: Optional[List[ChartViolation]] = None,
        alignment_confidence: float = 1.0,
        alignment_uncertain: bool = False,
        include_raw_report: bool = False,
    ) -> AggregatedComplianceReport:
        """
        Generate a unified multi-modal compliance report.
        
        Workflow:
        1. Enhance findings with source information
        2. Build unified timeline
        3. Aggregate base report
        4. Add multi-modal fields
        """
        logger.info("Starting unified multi-modal report generation")

        enhanced_findings = self.enhance_findings_with_sources(
            findings=regulatory_report.findings,
            correlated_findings=correlated_findings,
            sources=sources,
        )

        original_findings = regulatory_report.findings
        regulatory_report.findings = enhanced_findings

        try:
            base_report = aggregate_report(
                regulatory_report=regulatory_report,
                logs=log_entries,
                include_raw_report=include_raw_report,
            )
        finally:
            regulatory_report.findings = original_findings

        unified_timeline = self.build_unified_timeline(
            log_entries=log_entries,
            findings=enhanced_findings,
            correlated_findings=correlated_findings,
            aligned_chart_points=aligned_chart_points,
            chart_violations=chart_violations,
        )

        base_report.temporal_analysis.event_timeline = unified_timeline

        base_report.data_sources = sources
        base_report.correlation_insights = correlation_insights
        base_report.conflicting_findings = conflicting_findings
        base_report.correlation_summary = correlation_summary
        base_report.alignment_uncertain = alignment_uncertain

        if correlation_summary.avg_correlation_confidence is not None:
            base_report.multi_modal_confidence = correlation_summary.avg_correlation_confidence
        elif aligned_chart_points:
            base_report.multi_modal_confidence = alignment_confidence * 0.8

        base_report.executive_summary = self._enhance_executive_summary(
            base_report.executive_summary,
            correlation_summary,
            alignment_uncertain,
        )

        logger.info(
            "Unified report generation complete",
            extra={
                "sources_count": len(sources),
                "correlated_findings": len(correlated_findings),
                "conflicting_findings": len(conflicting_findings),
                "alignment_uncertain": alignment_uncertain,
            }
        )

        return base_report

    def _log_type_to_event_type(self, log_type: LogType) -> str:
        """Convert LogType to timeline event type string."""
        mapping = {
            LogType.DOOR_OPEN: "door_open",
            LogType.DOOR_CLOSE: "door_close",
            LogType.ALARM_TRIGGERED: "alarm_triggered",
            LogType.SENSOR_TIMEOUT: "sensor_timeout",
            LogType.DEVICE_START: "device_start",
            LogType.TEMP_WARNING: "temp_warning",
            LogType.COOLING_RECOVERY_START: "recovery_start",
            LogType.TELEMETRY_SYNC_FAILED: "sync_failed",
        }
        return mapping.get(log_type, "telemetry")

    def _log_entry_to_description(self, entry: LogEntry) -> str:
        """Generate human-readable description for a log entry."""
        if entry.log_type == LogType.DOOR_OPEN:
            return "Door opened"
        elif entry.log_type == LogType.DOOR_CLOSE:
            return "Door closed"
        elif entry.log_type == LogType.ALARM_TRIGGERED:
            return f"Alarm triggered: {entry.raw_value}"
        elif entry.log_type == LogType.SENSOR_TIMEOUT:
            return f"Sensor timeout: {entry.raw_value}"
        elif entry.log_type == LogType.TEMP_READING and entry.parsed_value is not None:
            return f"Temperature reading: {entry.parsed_value}°C"
        elif entry.log_type == LogType.TEMP_WARNING:
            return f"Temperature warning: {entry.raw_value}"
        else:
            return f"{entry.log_type.value if hasattr(entry.log_type, 'value') else entry.log_type}: {entry.raw_value}"

    def _enhance_executive_summary(
        self,
        base_summary: str,
        correlation_summary: CorrelationSummary,
        alignment_uncertain: bool,
    ) -> str:
        """Enhance executive summary with multi-modal information."""
        enhancements = []

        if correlation_summary.total_correlated > 0:
            enhancements.append(
                f"Multi-modal analysis correlated {correlation_summary.total_correlated} "
                f"findings across sources. "
                f"High confidence: {correlation_summary.high_confidence_count}, "
                f"Medium: {correlation_summary.medium_confidence_count}."
            )

        if correlation_summary.total_conflicting > 0:
            enhancements.append(
                f"Note: {correlation_summary.total_conflicting} "
                f"discrepancies detected between log data and chart analysis. "
                f"These are flagged for human review."
            )

        if alignment_uncertain:
            enhancements.append(
                "IMPORTANT: Chart time alignment is uncertain. "
                "Review the 'Alignment Uncertain' banner for details and "
                "consider manual verification of chart-derived data points."
            )

        if enhancements:
            return base_summary + " " + " ".join(enhancements)
        
        return base_summary
