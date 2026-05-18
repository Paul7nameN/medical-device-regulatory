from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.models.logs import LogEntry, LogType
from app.models.findings import Finding, Severity
from app.reports.models import (
    TimelineEvent,
    CriticalPeriod,
    GapAnalysis,
    RecoveryInterval,
    TemporalAnalysis
)


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


def detect_recovery_intervals(
    logs: List[LogEntry],
    max_recovery_seconds: float = 180.0
) -> List[RecoveryInterval]:
    
    recovery_intervals: List[RecoveryInterval] = []
    
    door_events = [
        log for log in logs
        if log.log_type in (LogType.DOOR_OPEN, LogType.DOOR_CLOSE)
    ]
    
    temp_readings = [
        log for log in logs
        if log.log_type == LogType.TEMP_READING and log.parsed_value is not None
    ]
    
    if not door_events or not temp_readings:
        return recovery_intervals
    
    sorted_door = sorted(door_events, key=lambda x: x.timestamp)
    sorted_temps = sorted(temp_readings, key=lambda x: x.timestamp)
    
    for i, door_event in enumerate(sorted_door):
        if door_event.log_type != LogType.DOOR_OPEN:
            continue
        
        door_open_time = door_event.timestamp
        
        temps_after = [
            t for t in sorted_temps
            if t.timestamp >= door_open_time
        ]
        
        if not temps_after:
            continue
        
        MIN_TEMP = 2.0
        MAX_TEMP = 8.0
        
        in_range_start: Optional[datetime] = None
        stable_count = 0
        recovery_complete: Optional[datetime] = None
        
        for temp in temps_after:
            temp_val = temp.parsed_value
            if isinstance(temp_val, (int, float)):
                in_range = MIN_TEMP <= temp_val <= MAX_TEMP
                
                if in_range:
                    if in_range_start is None:
                        in_range_start = temp.timestamp
                    stable_count += 1
                    
                    if stable_count >= 3:
                        recovery_complete = temp.timestamp
                        break
                else:
                    in_range_start = None
                    stable_count = 0
        
        if in_range_start and recovery_complete:
            recovery_duration = (recovery_complete - door_open_time).total_seconds()
            successful = recovery_duration <= max_recovery_seconds
            
            recovery_intervals.append(RecoveryInterval(
                disturbance_start=door_open_time,
                recovery_complete=recovery_complete,
                recovery_duration_seconds=recovery_duration,
                successful=successful,
                severity=Severity.HIGH if not successful else Severity.LOW,
                rule_id="REG-TEMP-3" if not successful else None
            ))
        elif in_range_start:
            recovery_duration = (in_range_start - door_open_time).total_seconds()
            successful = recovery_duration <= max_recovery_seconds
            
            recovery_intervals.append(RecoveryInterval(
                disturbance_start=door_open_time,
                recovery_complete=in_range_start,
                recovery_duration_seconds=recovery_duration,
                successful=successful,
                severity=Severity.HIGH if not successful else Severity.LOW,
                rule_id="REG-TEMP-3" if not successful else None
            ))
    
    return recovery_intervals


def build_temporal_analysis(
    logs: List[LogEntry],
    findings: List[Finding],
    ai_chart_analysis: Optional[Dict[str, Any]] = None
) -> TemporalAnalysis:
    
    chart_violations = None
    if ai_chart_analysis:
        chart_violations = ai_chart_analysis.get("violations", [])
    
    timeline = build_event_timeline(logs, findings, chart_violations)
    
    critical_periods = detect_critical_periods(timeline)
    gaps = detect_gaps(timeline)
    recovery_intervals = detect_recovery_intervals(logs)
    
    time_start = None
    time_end = None
    if timeline:
        sorted_timeline = sorted(timeline, key=lambda e: e.timestamp)
        time_start = sorted_timeline[0].timestamp
        time_end = sorted_timeline[-1].timestamp
    
    return TemporalAnalysis(
        event_timeline=timeline,
        critical_periods=critical_periods,
        recovery_intervals=recovery_intervals,
        gaps_detected=gaps,
        time_range_start=time_start,
        time_range_end=time_end
    )