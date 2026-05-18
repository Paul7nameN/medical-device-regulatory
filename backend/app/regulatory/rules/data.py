from typing import List, Dict, Any
from datetime import datetime, timedelta

from app.regulatory.rules.base import BaseRule, register_rule, ValidationSource
from app.models.logs import LogEntry, LogType
from app.models.findings import Severity, Finding


@register_rule
class RegData1(BaseRule):
    rule_id = "REG-DATA-1"
    description = "The system must maintain an immutable log of: temperature readings, alarms, configuration changes, sensor status events"
    category = "data"
    default_severity = Severity.INFO
    data_source = ValidationSource.LOGS
    confidence = 1.0

    def validate(self, logs: List[LogEntry], context: Dict[str, Any]) -> List[Finding]:
        required_types = {
            LogType.TEMP_READING: "temperature readings",
            LogType.ALARM_TRIGGERED: "alarms",
            LogType.SENSOR_TIMEOUT: "sensor status",
        }

        found_types = set()
        for log in logs:
            for req_type in required_types.keys():
                if log.log_type == req_type:
                    found_types.add(req_type)

        missing = [
            name for log_type, name in required_types.items()
            if log_type not in found_types
        ]

        if missing:
            return [self.create_finding(
                passed=False,
                message=f"Immutable log missing required event types: {', '.join(missing)}. "
                        f"REG-DATA-1 requires: temperature, alarms, config changes, sensor status.",
                severity=Severity.MEDIUM,
                remediation_hint="Verify logging configuration captures all required event types: temp readings, alarms, config changes, sensor status."
            )]

        return [self.create_pass_finding(
            "Immutable log contains all required event types (temp, alarms, sensor status). "
            "Note: Configuration changes not separately identifiable in this log format."
        )]


@register_rule
class RegData2(BaseRule):
    rule_id = "REG-DATA-2"
    description = "Data gaps in telemetry must not exceed: Δt_gap ≤ 90 seconds"
    category = "data"
    default_severity = Severity.MEDIUM
    data_source = ValidationSource.LOGS
    confidence = 1.0

    MAX_GAP = timedelta(seconds=90)

    def validate(self, logs: List[LogEntry], context: Dict[str, Any]) -> List[Finding]:
        if len(logs) < 2:
            return [self.create_finding(
                passed=False,
                message="Insufficient log entries to verify telemetry continuity",
                severity=Severity.LOW
            )]

        sorted_logs = sorted(logs, key=lambda x: x.timestamp)

        sync_failures = [
            log for log in logs
            if log.log_type == LogType.TELEMETRY_SYNC_FAILED
        ]

        gaps = []
        violation_logs: List[LogEntry] = []

        for i in range(1, len(sorted_logs)):
            gap = sorted_logs[i].timestamp - sorted_logs[i-1].timestamp
            if gap > self.MAX_GAP:
                gaps.append({
                    "from": sorted_logs[i-1].timestamp,
                    "to": sorted_logs[i].timestamp,
                    "gap": gap
                })
                violation_logs.append(sorted_logs[i])

        if not gaps and not sync_failures:
            return [self.create_pass_finding(
                f"Telemetry continuity verified: all {len(sorted_logs)-1} intervals ≤ {self.MAX_GAP.total_seconds()}s, no sync failures"
            )]

        messages = []
        if gaps:
            max_gap = max(g["gap"] for g in gaps)
            messages.append(f"{len(gaps)} gap(s) > {self.MAX_GAP.total_seconds()}s, largest: {max_gap.total_seconds():.1f}s")
        if sync_failures:
            messages.append(f"{len(sync_failures)} telemetry sync failure(s)")

        return [self.create_finding(
            passed=False,
            message="; ".join(messages),
            evidence_logs=violation_logs[:5] + sync_failures[:5],
            severity=Severity.MEDIUM if len(gaps) < 3 else Severity.HIGH,
            remediation_hint="Investigate telemetry sync issues, check network connectivity, verify logging service health, and review power stability."
        )]


@register_rule
class RegData3(BaseRule):
    rule_id = "REG-DATA-3"
    description = "Local data must be retained for at least t_retention ≥ 72 hours in case of cloud sync failure."
    category = "data"
    default_severity = Severity.INFO
    data_source = ValidationSource.COMBINED
    confidence = 0.5

    MIN_RETENTION = timedelta(hours=72)

    def validate(self, logs: List[LogEntry], context: Dict[str, Any]) -> List[Finding]:
        if len(logs) < 2:
            return [self.create_info_finding(
                "REG-DATA-3 requires 72h local data retention verification. "
                "Insufficient logs to measure time span. Verify device storage capacity and retention policy configuration."
            )]

        sorted_logs = sorted(logs, key=lambda x: x.timestamp)
        time_span = sorted_logs[-1].timestamp - sorted_logs[0].timestamp

        if time_span >= self.MIN_RETENTION:
            return [self.create_pass_finding(
                f"Log sample spans {time_span.total_seconds()/3600:.1f} hours, meeting ≥ {self.MIN_RETENTION.total_seconds()/3600}h retention requirement. "
                f"Verify device storage configuration maintains this retention during cloud sync failures."
            )]

        return [self.create_info_finding(
            f"REG-DATA-3 requires {self.MIN_RETENTION.total_seconds()/3600}h local data retention. "
            f"Current log sample spans {time_span.total_seconds()/3600:.1f} hours. "
            f"This does NOT indicate non-compliance - verify device storage capacity and retention policy configuration."
        )]
