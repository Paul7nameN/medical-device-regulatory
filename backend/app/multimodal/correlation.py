from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from collections import defaultdict
import logging

from app.models.logs import LogEntry, LogType
from app.models.findings import Finding, Severity
from app.models.multimodal import (
    CorrelatedFinding,
    ConflictingFinding,
    CorrelationSummary,
    CorrelationInsight,
    CorrelationInsightType,
    ConfidenceLevel,
    ConflictType,
)
from app.ai.image.models import TemperatureReading, ChartViolation, ChartViolationType

logger = logging.getLogger(__name__)


class CorrelationResult:
    def __init__(
        self,
        correlated_findings: List[CorrelatedFinding],
        conflicting_findings: List[ConflictingFinding],
        correlation_summary: CorrelationSummary,
        correlation_insights: List[CorrelationInsight],
        warnings: List[str],
    ):
        self.correlated_findings = correlated_findings
        self.conflicting_findings = conflicting_findings
        self.correlation_summary = correlation_summary
        self.correlation_insights = correlation_insights
        self.warnings = warnings


class TemporalCorrelationEngine:
    def __init__(self, window_seconds: float = 60.0):
        self.window_seconds = window_seconds
        self.warnings: List[str] = []

    def create_sliding_windows(
        self,
        entries: List[Any],
        window_seconds: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Create sliding time windows from timestamped entries.
        
        Args:
            entries: List of objects with 'timestamp' attribute
            window_seconds: Window size in seconds (default: self.window_seconds)
        
        Returns:
            List of windows with start_time, end_time, and entries
        """
        window_sec = window_seconds or self.window_seconds
        
        if not entries:
            return []
        
        sorted_entries = sorted(entries, key=lambda x: x.timestamp)
        
        windows = []
        current_window_entries: List[Any] = []
        window_start: Optional[datetime] = None
        
        for entry in sorted_entries:
            if window_start is None:
                window_start = entry.timestamp
                current_window_entries = [entry]
            else:
                elapsed = (entry.timestamp - window_start).total_seconds()
                
                if elapsed > window_sec:
                    windows.append({
                        "start_time": window_start,
                        "end_time": window_start + timedelta(seconds=window_sec),
                        "entries": list(current_window_entries),
                    })
                    
                    overlap_threshold = window_sec * 0.5
                    while (window_start and 
                           (entry.timestamp - window_start).total_seconds() > overlap_threshold):
                        window_start += timedelta(seconds=window_sec * 0.5)
                    
                    current_window_entries = [e for e in current_window_entries
                        if (e.timestamp - window_start).total_seconds() >= -window_sec * 0.25]
                    current_window_entries.append(entry)
                else:
                    current_window_entries.append(entry)
        
        if current_window_entries and window_start:
            windows.append({
                "start_time": window_start,
                "end_time": window_start + timedelta(seconds=window_sec),
                "entries": current_window_entries,
            })
        
        return windows

    def detect_matching_violations(
        self,
        log_findings: List[Finding],
        chart_violations: List[ChartViolation],
        aligned_chart_points: List[TemperatureReading],
        alignment_confidence: float = 1.0,
    ) -> Tuple[List[CorrelatedFinding], List[ConflictingFinding]]:
        """
        Detect matching and conflicting violations between logs and chart data.
        
        Conflict resolution priority:
        - Logs are ground truth
        - Chart disagreements flagged for human review
        
        Returns:
            Tuple of (correlated_findings, conflicting_findings)
        """
        correlated: List[CorrelatedFinding] = []
        conflicting: List[ConflictingFinding] = []

        failed_log_findings = [f for f in log_findings if not f.passed]

        for log_finding in failed_log_findings:
            finding_id = f"corr_{len(correlated) + len(conflicting)}"
            
            matching_chart_violations = self._find_nearby_chart_violations(
                log_finding.timestamp,
                chart_violations,
            )
            
            matching_chart_points = self._find_nearby_chart_points(
                log_finding.timestamp,
                aligned_chart_points,
            )

            log_confidence = getattr(log_finding, 'confidence', None) or 0.9
            
            chart_confidence: Optional[float] = None
            if matching_chart_violations:
                chart_confidence = max(v.confidence for v in matching_chart_violations)
            elif matching_chart_points:
                chart_confidence = 0.7

            combined_confidence = self.calculate_multimodal_confidence(
                log_confidence=log_confidence,
                chart_confidence=chart_confidence,
                alignment_confidence=alignment_confidence,
            )

            confidence_level = self._confidence_to_level(combined_confidence)

            sources = ["logs"]
            if matching_chart_violations or matching_chart_points:
                sources.append("chart")

            evidence: Dict[str, Any] = {
                "log_evidence": self._build_log_evidence(log_finding),
            }
            if matching_chart_violations:
                evidence["chart_violations"] = [
                    {"type": v.violation_type.value, "description": v.description}
                    for v in matching_chart_violations
                ]
            if matching_chart_points:
                evidence["chart_temperatures"] = [
                    {"time": p.time, "temp": p.sensor_a, "source": p.source}
                    for p in matching_chart_points
                ]

            if matching_chart_violations:
                correlated.append(CorrelatedFinding(
                    finding_id=finding_id,
                    rule_id=log_finding.rule_id,
                    timestamp=log_finding.timestamp,
                    sources=sources,
                    log_confidence=log_confidence,
                    chart_confidence=chart_confidence,
                    alignment_confidence=alignment_confidence,
                    combined_confidence=combined_confidence,
                    confidence_level=confidence_level,
                    description=f"Multi-modal confirmed: {log_finding.message}",
                    evidence=evidence,
                ))
            elif matching_chart_points:
                temps = [p.sensor_a for p in matching_chart_points]
                avg_temp = sum(temps) / len(temps) if temps else 5.0
                
                if 2.0 <= avg_temp <= 8.0:
                    conflicting.append(ConflictingFinding(
                        finding_id=finding_id,
                        rule_id=log_finding.rule_id,
                        timestamp=log_finding.timestamp,
                        conflict_type=ConflictType.LOG_VIOLATION_CHART_OK,
                        log_status="VIOLATION",
                        log_value=str(log_finding.message[:100]) if log_finding.message else None,
                        chart_status="OK",
                        chart_value=f"avg {avg_temp:.1f}°C in range",
                        description=f"Log reports violation but chart shows temperature in range at this time",
                        for_human_review=True,
                    ))
                else:
                    correlated.append(CorrelatedFinding(
                        finding_id=finding_id,
                        rule_id=log_finding.rule_id,
                        timestamp=log_finding.timestamp,
                        sources=sources,
                        log_confidence=log_confidence,
                        chart_confidence=0.6,
                        alignment_confidence=alignment_confidence,
                        combined_confidence=self.calculate_multimodal_confidence(
                            log_confidence, 0.6, alignment_confidence
                        ),
                        confidence_level=self._confidence_to_level(
                            self.calculate_multimodal_confidence(log_confidence, 0.6, alignment_confidence)
                        ),
                        description=f"Log violation supported by chart temperature pattern",
                        evidence=evidence,
                    ))
            else:
                correlated.append(CorrelatedFinding(
                    finding_id=finding_id,
                    rule_id=log_finding.rule_id,
                    timestamp=log_finding.timestamp,
                    sources=["logs"],
                    log_confidence=log_confidence,
                    chart_confidence=None,
                    alignment_confidence=None,
                    combined_confidence=log_confidence * 0.9,
                    confidence_level=self._confidence_to_level(log_confidence * 0.9),
                    description=f"Log finding (no chart data at this time): {log_finding.message}",
                    evidence=evidence,
                ))

        for chart_violation in chart_violations:
            if chart_violation.timestamp_start:
                matching_logs = [
                    f for f in failed_log_findings
                    if self._is_timestamp_in_window(
                        f.timestamp,
                        chart_violation.timestamp_start,
                        chart_violation.timestamp_end or chart_violation.timestamp_start,
                    )
                ]
                
                if not matching_logs:
                    finding_id = f"conflict_{len(conflicting)}"
                    conflicting.append(ConflictingFinding(
                        finding_id=finding_id,
                        rule_id="CHART-DETECTED",
                        timestamp=chart_violation.timestamp_start,
                        conflict_type=ConflictType.LOG_OK_CHART_VIOLATION,
                        log_status="OK",
                        chart_status="VIOLATION",
                        chart_value=str(chart_violation.description[:100]) if chart_violation.description else None,
                        description=f"Chart suggests potential issue but logs do not show violation at this time",
                        for_human_review=True,
                    ))

        return correlated, conflicting

    def calculate_multimodal_confidence(
        self,
        log_confidence: Optional[float],
        chart_confidence: Optional[float],
        alignment_confidence: Optional[float],
    ) -> float:
        """
        Calculate combined multi-modal confidence.
        
        Formula:
        - If only logs: log_confidence
        - If only chart: chart_confidence * 0.8 (chart has inherent uncertainty)
        - If both: min(log_confidence, chart_confidence * 0.9) * (alignment_confidence or 0.7) * 1.1 boost
        
        Note: 1.1 boost capped at 1.0
        """
        log_c = log_confidence if log_confidence is not None else 0.0
        chart_c = chart_confidence if chart_confidence is not None else 0.0
        align_c = alignment_confidence if alignment_confidence is not None else 0.7

        if chart_c == 0.0:
            return log_c

        if log_c == 0.0:
            return chart_c * 0.8

        base = min(log_c, chart_c * 0.9)
        with_alignment = base * align_c
        with_boost = with_alignment * 1.1

        return min(with_boost, 1.0)

    def generate_correlation_insights(
        self,
        log_entries: List[LogEntry],
        correlated_findings: List[CorrelatedFinding],
    ) -> List[CorrelationInsight]:
        """
        Generate narrative insights from multi-modal data:
        - Door → temperature correlation
        - Recovery patterns
        - Anomaly clusters
        - Trend indicators
        """
        insights: List[CorrelationInsight] = []

        door_events = [e for e in log_entries if e.log_type in [LogType.DOOR_OPEN, LogType.DOOR_CLOSE]]
        
        if door_events:
            door_insights = self._analyze_door_temperature_correlation(log_entries, door_events)
            insights.extend(door_insights)

        recovery_insights = self._analyze_recovery_patterns(log_entries, correlated_findings)
        insights.extend(recovery_insights)

        cluster_insights = self._find_anomaly_clusters(correlated_findings)
        insights.extend(cluster_insights)

        return insights

    def correlate(
        self,
        log_entries: List[LogEntry],
        log_findings: List[Finding],
        chart_violations: List[ChartViolation],
        aligned_chart_points: List[TemperatureReading],
        alignment_confidence: float = 1.0,
        alignment_uncertain: bool = False,
    ) -> CorrelationResult:
        """
        Main correlation workflow:
        1. Detect matching and conflicting findings
        2. Generate correlation insights
        3. Build summary
        """
        self.warnings = []

        if alignment_uncertain:
            self.warnings.append(
                "Chart alignment is uncertain - correlation confidence may be reduced"
            )

        correlated, conflicting = self.detect_matching_violations(
            log_findings=log_findings,
            chart_violations=chart_violations,
            aligned_chart_points=aligned_chart_points,
            alignment_confidence=alignment_confidence,
        )

        insights = self.generate_correlation_insights(
            log_entries=log_entries,
            correlated_findings=correlated,
        )

        summary = self._build_correlation_summary(correlated, conflicting)

        return CorrelationResult(
            correlated_findings=correlated,
            conflicting_findings=conflicting,
            correlation_summary=summary,
            correlation_insights=insights,
            warnings=list(self.warnings),
        )

    def _find_nearby_chart_violations(
        self,
        timestamp: datetime,
        chart_violations: List[ChartViolation],
    ) -> List[ChartViolation]:
        """Find chart violations near a given timestamp."""
        matches = []
        
        for violation in chart_violations:
            if not violation.timestamp_start:
                continue
            
            if self._is_timestamp_in_window(
                timestamp,
                violation.timestamp_start - timedelta(seconds=self.window_seconds),
                (violation.timestamp_end or violation.timestamp_start) + timedelta(seconds=self.window_seconds),
            ):
                matches.append(violation)
        
        return matches

    def _find_nearby_chart_points(
        self,
        timestamp: datetime,
        chart_points: List[TemperatureReading],
    ) -> List[TemperatureReading]:
        """Find chart temperature points near a given timestamp."""
        matches = []
        
        for point in chart_points:
            if not point.timestamp:
                continue
            
            elapsed = abs((point.timestamp - timestamp).total_seconds())
            if elapsed <= self.window_seconds:
                matches.append(point)
        
        return sorted(matches, key=lambda p: abs(
            (p.timestamp - timestamp).total_seconds() if p.timestamp else 99999
        ))

    def _is_timestamp_in_window(
        self,
        ts: datetime,
        window_start: datetime,
        window_end: datetime,
    ) -> bool:
        """Check if a timestamp falls within a time window."""
        return window_start <= ts <= window_end

    def _confidence_to_level(self, confidence: float) -> ConfidenceLevel:
        """Convert numeric confidence to enum level."""
        if confidence >= 0.85:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.70:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    def _build_log_evidence(self, finding: Finding) -> Dict[str, Any]:
        """Build evidence dict from a log finding."""
        return {
            "rule_id": finding.rule_id,
            "rule_description": finding.rule_description,
            "category": finding.category,
            "severity": finding.severity.value if hasattr(finding.severity, 'value') else str(finding.severity),
            "message": finding.message,
            "evidence_count": len(finding.evidence),
            "data_source": getattr(finding, 'data_source', None),
            "confidence": getattr(finding, 'confidence', None),
        }

    def _analyze_door_temperature_correlation(
        self,
        log_entries: List[LogEntry],
        door_events: List[LogEntry],
    ) -> List[CorrelationInsight]:
        """Analyze correlation between door events and temperature changes."""
        insights: List[CorrelationInsight] = []

        temp_readings = [
            e for e in log_entries 
            if e.log_type == LogType.TEMP_READING and e.parsed_value is not None
        ]

        for door_event in door_events:
            if door_event.log_type == LogType.DOOR_OPEN:
                temps_after = [
                    t for t in temp_readings
                    if t.timestamp > door_event.timestamp
                    and t.timestamp <= door_event.timestamp + timedelta(minutes=15)
                ]
                
                if temps_after:
                    temps_sorted = sorted(temps_after, key=lambda x: x.timestamp)
                    initial_temp = temps_sorted[0].parsed_value if temps_sorted[0].parsed_value else 5.0
                    max_temp = max(t.parsed_value or 5.0 for t in temps_sorted)
                    
                    if max_temp > initial_temp + 1.0:
                        insights.append(CorrelationInsight(
                            type=CorrelationInsightType.DOOR_TEMPERATURE_CORRELATION,
                            title="Door access caused temperature rise",
                            description=f"Door opened at {door_event.timestamp.strftime('%H:%M')}. "
                                       f"Temperature rose from {initial_temp:.1f}°C to {max_temp:.1f}°C "
                                       f"within 15 minutes after door access.",
                            start_time=door_event.timestamp,
                            end_time=door_event.timestamp + timedelta(minutes=15),
                            supporting_evidence=[
                                f"Door open event at {door_event.timestamp}",
                                f"Initial temperature: {initial_temp:.1f}°C",
                                f"Peak temperature: {max_temp:.1f}°C",
                            ],
                            confidence=0.85,
                        ))

        return insights

    def _analyze_recovery_patterns(
        self,
        log_entries: List[LogEntry],
        correlated_findings: List[CorrelatedFinding],
    ) -> List[CorrelationInsight]:
        """Analyze temperature recovery patterns after disturbances."""
        insights: List[CorrelationInsight] = []

        temp_readings = [
            e for e in log_entries 
            if e.log_type == LogType.TEMP_READING and e.parsed_value is not None
        ]

        if not temp_readings:
            return insights

        sorted_temps = sorted(temp_readings, key=lambda x: x.timestamp)
        
        in_excursion = False
        excursion_start: Optional[datetime] = None
        excursion_peak: float = 0.0

        for i, reading in enumerate(sorted_temps):
            temp = reading.parsed_value or 5.0
            
            if temp < 2.0 or temp > 8.0:
                if not in_excursion:
                    in_excursion = True
                    excursion_start = reading.timestamp
                    excursion_peak = temp
                else:
                    excursion_peak = max(excursion_peak, abs(temp - 5.0))
            elif in_excursion:
                in_excursion = False
                if excursion_start:
                    recovery_duration = (reading.timestamp - excursion_start).total_seconds()
                    
                    if recovery_duration > 180:
                        insights.append(CorrelationInsight(
                            type=CorrelationInsightType.RECOVERY_PATTERN,
                            title="Slow temperature recovery detected",
                            description=f"After temperature excursion starting at {excursion_start.strftime('%H:%M')}, "
                                       f"system took {recovery_duration/60:.1f} minutes to return to safe range. "
                                       f"Target recovery time is 3 minutes per REG-TEMP-3.",
                            start_time=excursion_start,
                            end_time=reading.timestamp,
                            supporting_evidence=[
                                f"Excursion started: {excursion_start}",
                                f"Recovery duration: {recovery_duration/60:.1f} minutes",
                                f"Peak deviation: {excursion_peak:.1f}°C from target",
                            ],
                            confidence=0.9,
                        ))

        return insights

    def _find_anomaly_clusters(
        self,
        correlated_findings: List[CorrelatedFinding],
    ) -> List[CorrelationInsight]:
        """Find clusters of correlated findings in time."""
        insights: List[CorrelationInsight] = []

        if len(correlated_findings) < 2:
            return insights

        sorted_findings = sorted(correlated_findings, key=lambda x: x.timestamp)

        clusters: List[List[CorrelatedFinding]] = []
        current_cluster: List[CorrelatedFinding] = [sorted_findings[0]]

        for finding in sorted_findings[1:]:
            last_in_cluster = current_cluster[-1]
            elapsed = (finding.timestamp - last_in_cluster.timestamp).total_seconds()

            if elapsed <= 3600:
                current_cluster.append(finding)
            else:
                if len(current_cluster) >= 2:
                    clusters.append(current_cluster)
                current_cluster = [finding]

        if len(current_cluster) >= 2:
            clusters.append(current_cluster)

        for i, cluster in enumerate(clusters):
            if len(cluster) >= 3:
                start_time = cluster[0].timestamp
                end_time = cluster[-1].timestamp
                duration = (end_time - start_time).total_seconds()

                rule_ids = [f.rule_id for f in cluster]
                unique_rules = set(rule_ids)

                insights.append(CorrelationInsight(
                    type=CorrelationInsightType.ANOMALY_CLUSTER,
                    title=f"Anomaly cluster detected ({len(cluster)} findings)",
                    description=f"Between {start_time.strftime('%H:%M')} and {end_time.strftime('%H:%M')}, "
                               f"there were {len(cluster)} correlated findings involving "
                               f"{len(unique_rules)} unique rules. This cluster lasted {duration/60:.1f} minutes.",
                    start_time=start_time,
                    end_time=end_time,
                    supporting_evidence=[
                        f"Total findings in cluster: {len(cluster)}",
                        f"Unique rules involved: {', '.join(unique_rules)}",
                        f"Cluster duration: {duration/60:.1f} minutes",
                    ],
                    confidence=0.95,
                ))

        return insights

    def _build_correlation_summary(
        self,
        correlated: List[CorrelatedFinding],
        conflicting: List[ConflictingFinding],
    ) -> CorrelationSummary:
        """Build summary statistics from correlation results."""
        high_count = sum(1 for f in correlated if f.confidence_level == ConfidenceLevel.HIGH)
        medium_count = sum(1 for f in correlated if f.confidence_level == ConfidenceLevel.MEDIUM)
        low_count = sum(1 for f in correlated if f.confidence_level == ConfidenceLevel.LOW)

        if correlated:
            avg_confidence = sum(f.combined_confidence for f in correlated) / len(correlated)
        else:
            avg_confidence = None

        return CorrelationSummary(
            total_correlated=len(correlated),
            total_conflicting=len(conflicting),
            avg_correlation_confidence=avg_confidence,
            high_confidence_count=high_count,
            medium_confidence_count=medium_count,
            low_confidence_count=low_count,
        )
