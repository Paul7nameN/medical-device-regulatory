from typing import List, Dict, Any
from datetime import datetime, timedelta

from app.regulatory.rules.base import BaseRule, register_rule, ValidationSource
from app.regulatory.rules.temp import RegTemp1
from app.models.logs import LogEntry, LogType
from app.models.findings import Severity, Finding


@register_rule
class RegAlarm1(BaseRule):
    rule_id = "REG-ALARM-1"
    description = "Alarm shall activate if temperature remains outside range for t ≥ 2 minutes"
    category = "ALARM"
    default_severity = Severity.HIGH
    data_source = ValidationSource.LOGS
    confidence = 1.0

    ACTIVATION_THRESHOLD = timedelta(minutes=2)

    def validate(self, logs: List[LogEntry], context: Dict[str, Any]) -> List[Finding]:
        temp_readings = [
            log for log in logs
            if log.log_type == LogType.TEMP_READING and log.parsed_value is not None
        ]
        alarm_events = [
            log for log in logs
            if log.log_type == LogType.ALARM_TRIGGERED
        ]

        if not temp_readings:
            return [self.create_finding(
                passed=False,
                message="No temperature readings - cannot verify alarm activation timing",
                severity=Severity.MEDIUM
            )]

        sorted_readings = sorted(temp_readings, key=lambda x: x.timestamp)
        sorted_alarms = sorted(alarm_events, key=lambda x: x.timestamp)

        excursions: List[Dict[str, Any]] = []
        current_excursion_start: datetime = None
        current_excursion_logs: List[LogEntry] = []

        for reading in sorted_readings:
            temp = reading.parsed_value
            if isinstance(temp, (int, float)):
                in_range = RegTemp1.MIN_TEMP <= temp <= RegTemp1.MAX_TEMP

                if not in_range:
                    if current_excursion_start is None:
                        current_excursion_start = reading.timestamp
                    current_excursion_logs.append(reading)
                else:
                    if current_excursion_start is not None:
                        duration = reading.timestamp - current_excursion_start
                        excursions.append({
                            "start": current_excursion_start,
                            "end": reading.timestamp,
                            "duration": duration,
                            "logs": current_excursion_logs
                        })
                        current_excursion_start = None
                        current_excursion_logs = []

        if current_excursion_start is not None and current_excursion_logs:
            end_time = current_excursion_logs[-1].timestamp
            duration = end_time - current_excursion_start
            excursions.append({
                "start": current_excursion_start,
                "end": end_time,
                "duration": duration,
                "logs": current_excursion_logs
            })

        long_excursions = [
            e for e in excursions
            if e["duration"] >= self.ACTIVATION_THRESHOLD
        ]

        if not long_excursions:
            if excursions:
                return [self.create_pass_finding(
                    f"All {len(excursions)} excursion(s) < {self.ACTIVATION_THRESHOLD.total_seconds()/60}min - no alarm required"
                )]
            return [self.create_pass_finding("No temperature excursions detected")]

        missing_alarms = []
        violation_logs: List[LogEntry] = []

        for excursion in long_excursions:
            alarm_during = [
                a for a in sorted_alarms
                if excursion["start"] <= a.timestamp <= excursion["end"]
            ]

            if not alarm_during:
                expected_alarm_time = excursion["start"] + self.ACTIVATION_THRESHOLD
                missing_alarms.append({
                    "excursion_start": excursion["start"],
                    "duration": excursion["duration"],
                    "expected_alarm_by": expected_alarm_time
                })
                violation_logs.extend(excursion["logs"][:3])

        if not missing_alarms:
            return [self.create_pass_finding(
                f"Alarm triggered for all {len(long_excursions)} excursion(s) ≥ {self.ACTIVATION_THRESHOLD.total_seconds()/60}min"
            )]

        return [self.create_finding(
            passed=False,
            message=f"Found {len(missing_alarms)} excursion(s) ≥ {self.ACTIVATION_THRESHOLD.total_seconds()/60}min without alarm activation. "
                    f"Check alarm configuration and sensor triggering logic.",
            evidence_logs=violation_logs[:5],
            severity=Severity.HIGH,
            remediation_hint="CRITICAL: Verify alarm system is properly configured to trigger after temperature threshold violations. "
                           "Check alarm thresholds, sensor integration, and notification system health."
        )]


@register_rule
class RegAlarm2(BaseRule):
    rule_id = "REG-ALARM-2"
    description = "System notifications must be delivered within t_notify ≤ 10 seconds"
    category = "ALARM"
    default_severity = Severity.MEDIUM
    data_source = ValidationSource.INSPECTION
    confidence = 0.0
    inspection_hint = "Requires end-to-end notification timing test: alarm trigger → mobile delivery ≤10s."

    MAX_NOTIFICATION_LATENCY = timedelta(seconds=10)

    def validate(self, logs: List[LogEntry], context: Dict[str, Any]) -> List[Finding]:
        alarm_events = [
            log for log in logs
            if log.log_type == LogType.ALARM_TRIGGERED
        ]

        if not alarm_events:
            return [self.create_pass_finding("No alarm events to verify notification latency")]

        return [self.create_info_finding(
            f"REG-ALARM-2 requires end-to-end notification timing verification. "
            f"Logs show {len(alarm_events)} ALARM_TRIGGERED event(s) but do not contain notification delivery timestamps. "
            f"Verify end-to-end: alarm trigger → dashboard display → mobile push → max {self.MAX_NOTIFICATION_LATENCY.total_seconds()}s latency."
        )]


@register_rule
class RegAlarm3(BaseRule):
    rule_id = "REG-ALARM-3"
    description = "The system must support: audible alarm, visual dashboard alert, remote mobile notification. Failure to support any channel is non-compliant."
    category = "ALARM"
    default_severity = Severity.MEDIUM
    data_source = ValidationSource.INSPECTION
    confidence = 0.0
    inspection_hint = "Verify all 3 notification channels: audible alarm, visual dashboard alert, remote mobile notification."

    def validate(self, logs: List[LogEntry], context: Dict[str, Any]) -> List[Finding]:
        alarm_events = [
            log for log in logs
            if log.log_type in (LogType.ALARM_TRIGGERED, LogType.TEMP_WARNING)
        ]

        return [self.create_info_finding(
            "REG-ALARM-3 requires verification of all three notification channels:\n"
            "  1. Audible alarm - physical speaker/buzzer test\n"
            "  2. Visual dashboard alert - HMI display verification\n"
            "  3. Remote mobile notification - push notification test\n\n"
            f"Logs show {len(alarm_events)} alarm-related event(s) but cannot verify channel presence or functionality. "
            f"Run comprehensive alarm system test to validate all three channels."
        )]
