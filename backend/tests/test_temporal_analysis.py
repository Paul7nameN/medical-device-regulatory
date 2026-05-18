import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from app.reports.temporal import (
    build_event_timeline,
    detect_critical_periods,
    detect_gaps,
    detect_recovery_intervals,
    build_temporal_analysis
)
from app.models.logs import LogEntry, LogType
from app.models.findings import Finding, Severity
from app.reports.models import TimelineEvent, CriticalPeriod, GapAnalysis, RecoveryInterval


class TestBuildEventTimeline:
    def test_empty_inputs(self):
        timeline = build_event_timeline([], [])
        assert timeline == []
    
    def test_only_logs(self):
        base_time = datetime(2026, 5, 14, 14, 0, 0)
        logs = [
            LogEntry(
                timestamp=base_time,
                log_type=LogType.TEMP_READING,
                raw_value="4.3C",
                parsed_value=4.3
            ),
            LogEntry(
                timestamp=base_time + timedelta(seconds=30),
                log_type=LogType.DOOR_OPEN,
                raw_value="",
                parsed_value=None
            ),
        ]
        
        timeline = build_event_timeline(logs, [])
        
        assert len(timeline) == 2
        assert timeline[0].event_type == "LOG_TEMP_READING"
        assert timeline[1].event_type == "LOG_DOOR_OPEN"
    
    def test_only_findings(self):
        base_time = datetime(2026, 5, 14, 14, 0, 0)
        findings = [
            Finding(
                rule_id="REG-TEMP-1",
                rule_description="Temperature must be 2-8C",
                category="thermal",
                severity=Severity.HIGH,
                passed=False,
                message="Temperature 9.1C exceeds 8C",
                evidence=[],
                timestamp=base_time
            ),
        ]
        
        timeline = build_event_timeline([], findings)
        
        assert len(timeline) == 1
        assert timeline[0].event_type == "VIOLATION_REG-TEMP-1"
        assert timeline[0].severity == Severity.HIGH
    
    def test_combined_logs_and_findings(self):
        base_time = datetime(2026, 5, 14, 14, 0, 0)
        logs = [
            LogEntry(
                timestamp=base_time + timedelta(seconds=30),
                log_type=LogType.TEMP_READING,
                raw_value="9.1C",
                parsed_value=9.1
            ),
        ]
        findings = [
            Finding(
                rule_id="REG-TEMP-1",
                rule_description="Temperature must be 2-8C",
                category="thermal",
                severity=Severity.HIGH,
                passed=False,
                message="Temperature 9.1C exceeds 8C",
                evidence=[],
                timestamp=base_time
            ),
        ]
        
        timeline = build_event_timeline(logs, findings)
        
        assert len(timeline) == 2
        assert timeline[0].event_type == "VIOLATION_REG-TEMP-1"
        assert timeline[1].event_type == "LOG_TEMP_READING"
    
    def test_ai_chart_violations(self):
        base_time = datetime(2026, 5, 14, 14, 0, 0)
        logs = [
            LogEntry(
                timestamp=base_time,
                log_type=LogType.TEMP_READING,
                raw_value="4.3C",
                parsed_value=4.3
            ),
        ]
        ai_violations = [
            {
                "violation_type": "excursion",
                "timestamp_start": base_time + timedelta(seconds=30),
                "description": "Temperature exceeded 8C",
                "confidence": 0.95
            }
        ]
        
        timeline = build_event_timeline(logs, [], ai_violations)
        
        assert len(timeline) == 2
        assert timeline[1].event_type == "CHART_excursion"


class TestDetectCriticalPeriods:
    def test_empty_timeline(self):
        periods = detect_critical_periods([])
        assert periods == []
    
    def test_no_critical_or_high_events(self):
        timeline = [
            TimelineEvent(
                timestamp=datetime(2026, 5, 14, 14, 0, 0),
                event_type="LOG_TEMP_READING",
                severity=Severity.LOW,
                description="Normal reading"
            ),
        ]
        periods = detect_critical_periods(timeline)
        assert periods == []
    
    def test_critical_event_creates_period(self):
        timeline = [
            TimelineEvent(
                timestamp=datetime(2026, 5, 14, 14, 0, 0),
                event_type="VIOLATION_REG-TEMP-1",
                rule_id="REG-TEMP-1",
                severity=Severity.CRITICAL,
                description="Critical violation"
            ),
        ]
        periods = detect_critical_periods(timeline)
        
        assert len(periods) == 1
        assert periods[0].critical_count == 1
        assert periods[0].triggering_rule == "REG-TEMP-1"
    
    def test_three_high_events_creates_period(self):
        base_time = datetime(2026, 5, 14, 14, 0, 0)
        timeline = [
            TimelineEvent(
                timestamp=base_time,
                event_type="VIOLATION_REG-TEMP-1",
                rule_id="REG-TEMP-1",
                severity=Severity.HIGH,
                description="High violation 1"
            ),
            TimelineEvent(
                timestamp=base_time + timedelta(seconds=10),
                event_type="VIOLATION_REG-TEMP-3",
                rule_id="REG-TEMP-3",
                severity=Severity.HIGH,
                description="High violation 2"
            ),
            TimelineEvent(
                timestamp=base_time + timedelta(seconds=20),
                event_type="VIOLATION_REG-SENS-1",
                rule_id="REG-SENS-1",
                severity=Severity.HIGH,
                description="High violation 3"
            ),
        ]
        periods = detect_critical_periods(timeline)
        
        assert len(periods) >= 1
        assert periods[0].high_count >= 3


class TestDetectGaps:
    def test_fewer_than_two_events(self):
        gaps = detect_gaps([])
        assert gaps == []
        
        gaps = detect_gaps([
            TimelineEvent(
                timestamp=datetime(2026, 5, 14, 14, 0, 0),
                event_type="LOG_TEMP_READING",
                description="Test"
            )
        ])
        assert gaps == []
    
    def test_no_gaps(self):
        base_time = datetime(2026, 5, 14, 14, 0, 0)
        timeline = [
            TimelineEvent(
                timestamp=base_time,
                event_type="LOG_TEMP_READING",
                description="Test 1"
            ),
            TimelineEvent(
                timestamp=base_time + timedelta(seconds=20),
                event_type="LOG_TEMP_READING",
                description="Test 2"
            ),
        ]
        gaps = detect_gaps(timeline, max_expected_gap_seconds=30.0)
        assert gaps == []
    
    def test_sampling_gap(self):
        base_time = datetime(2026, 5, 14, 14, 0, 0)
        timeline = [
            TimelineEvent(
                timestamp=base_time,
                event_type="LOG_TEMP_READING",
                description="Test 1"
            ),
            TimelineEvent(
                timestamp=base_time + timedelta(seconds=45),
                event_type="LOG_TEMP_READING",
                description="Test 2"
            ),
        ]
        gaps = detect_gaps(timeline, max_expected_gap_seconds=30.0)
        
        assert len(gaps) == 1
        assert gaps[0].gap_type == "sampling_gap"
        assert gaps[0].gap_duration_seconds == 45.0
    
    def test_telemetry_gap(self):
        base_time = datetime(2026, 5, 14, 14, 0, 0)
        timeline = [
            TimelineEvent(
                timestamp=base_time,
                event_type="LOG_TEMP_READING",
                description="Test 1"
            ),
            TimelineEvent(
                timestamp=base_time + timedelta(seconds=120),
                event_type="LOG_TEMP_READING",
                description="Test 2"
            ),
        ]
        gaps = detect_gaps(timeline, max_expected_gap_seconds=30.0)
        
        assert len(gaps) == 1
        assert gaps[0].gap_type == "telemetry_gap"


class TestDetectRecoveryIntervals:
    def test_no_door_events(self):
        base_time = datetime(2026, 5, 14, 14, 0, 0)
        logs = [
            LogEntry(
                timestamp=base_time,
                log_type=LogType.TEMP_READING,
                raw_value="4.3C",
                parsed_value=4.3
            ),
            LogEntry(
                timestamp=base_time + timedelta(seconds=30),
                log_type=LogType.TEMP_READING,
                raw_value="5.0C",
                parsed_value=5.0
            ),
        ]
        
        intervals = detect_recovery_intervals(logs)
        assert intervals == []
    
    def test_door_event_with_successful_recovery(self):
        base_time = datetime(2026, 5, 14, 14, 0, 0)
        logs = [
            LogEntry(
                timestamp=base_time,
                log_type=LogType.DOOR_OPEN,
                raw_value="",
                parsed_value=None
            ),
            LogEntry(
                timestamp=base_time + timedelta(seconds=10),
                log_type=LogType.TEMP_READING,
                raw_value="10.0C",
                parsed_value=10.0
            ),
            LogEntry(
                timestamp=base_time + timedelta(seconds=30),
                log_type=LogType.TEMP_READING,
                raw_value="8.0C",
                parsed_value=8.0
            ),
            LogEntry(
                timestamp=base_time + timedelta(seconds=40),
                log_type=LogType.TEMP_READING,
                raw_value="5.0C",
                parsed_value=5.0
            ),
            LogEntry(
                timestamp=base_time + timedelta(seconds=50),
                log_type=LogType.TEMP_READING,
                raw_value="4.0C",
                parsed_value=4.0
            ),
        ]
        
        intervals = detect_recovery_intervals(logs, max_recovery_seconds=180.0)
        
        assert len(intervals) == 1
        assert intervals[0].successful is True
    
    def test_door_event_with_slow_recovery(self):
        base_time = datetime(2026, 5, 14, 14, 0, 0)
        logs = [
            LogEntry(
                timestamp=base_time,
                log_type=LogType.DOOR_OPEN,
                raw_value="",
                parsed_value=None
            ),
            LogEntry(
                timestamp=base_time + timedelta(minutes=1),
                log_type=LogType.TEMP_READING,
                raw_value="10.0C",
                parsed_value=10.0
            ),
            LogEntry(
                timestamp=base_time + timedelta(minutes=2),
                log_type=LogType.TEMP_READING,
                raw_value="9.0C",
                parsed_value=9.0
            ),
            LogEntry(
                timestamp=base_time + timedelta(minutes=3),
                log_type=LogType.TEMP_READING,
                raw_value="8.5C",
                parsed_value=8.5
            ),
            LogEntry(
                timestamp=base_time + timedelta(minutes=4),
                log_type=LogType.TEMP_READING,
                raw_value="7.5C",
                parsed_value=7.5
            ),
        ]
        
        intervals = detect_recovery_intervals(logs, max_recovery_seconds=180.0)
        
        assert len(intervals) == 1
        assert intervals[0].successful is False
        assert intervals[0].severity == Severity.HIGH
        assert intervals[0].rule_id == "REG-TEMP-3"


class TestBuildTemporalAnalysis:
    def test_empty_inputs(self):
        result = build_temporal_analysis([], [])
        
        assert len(result.event_timeline) == 0
        assert len(result.critical_periods) == 0
        assert len(result.recovery_intervals) == 0
        assert len(result.gaps_detected) == 0
    
    def test_with_logs_and_findings(self):
        base_time = datetime(2026, 5, 14, 14, 0, 0)
        logs = [
            LogEntry(
                timestamp=base_time,
                log_type=LogType.TEMP_READING,
                raw_value="9.1C",
                parsed_value=9.1
            ),
            LogEntry(
                timestamp=base_time + timedelta(seconds=30),
                log_type=LogType.TEMP_READING,
                raw_value="9.5C",
                parsed_value=9.5
            ),
        ]
        findings = [
            Finding(
                rule_id="REG-TEMP-1",
                rule_description="Temperature must be 2-8C",
                category="thermal",
                severity=Severity.HIGH,
                passed=False,
                message="Temperature exceeds 8C",
                evidence=[],
                timestamp=base_time
            ),
        ]
        
        result = build_temporal_analysis(logs, findings)
        
        assert len(result.event_timeline) == 3
        assert result.time_range_start is not None
        assert result.time_range_end is not None