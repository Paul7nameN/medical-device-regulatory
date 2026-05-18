from typing import List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict

from app.regulatory.rules.base import BaseRule, register_rule, ValidationSource
from app.regulatory.rules.temp import RegTemp1
from app.models.logs import LogEntry, LogType
from app.models.findings import Severity, Finding


@register_rule
class RegOps1(BaseRule):
    rule_id = "REG-OPS-1"
    description = "After a door opening event, system must: stabilize within 3 minutes (REG-TEMP-3), not exceed 8°C during recovery window"
    category = "operational"
    default_severity = Severity.HIGH
    data_source = ValidationSource.LOGS
    confidence = 1.0

    MAX_RECOVERY = timedelta(minutes=3)
    MAX_TEMP_DURING_RECOVERY = 8.0

    def validate(self, logs: List[LogEntry], context: Dict[str, Any]) -> List[Finding]:
        door_open_events = [
            log for log in logs
            if log.log_type == LogType.DOOR_OPEN
        ]

        temp_readings = [
            log for log in logs
            if log.log_type == LogType.TEMP_READING and log.parsed_value is not None
        ]

        if not door_open_events:
            return [self.create_pass_finding("No door opening events - recovery not applicable")]

        if not temp_readings:
            return [self.create_finding(
                passed=False,
                message=f"{len(door_open_events)} door event(s) detected but no temperature readings to verify recovery",
                severity=Severity.MEDIUM
            )]

        sorted_temps = sorted(temp_readings, key=lambda x: x.timestamp)

        recovery_violations: List[Dict[str, Any]] = []
        temp_spike_violations: List[Dict[str, Any]] = []
        violation_logs: List[LogEntry] = []

        for door_open in door_open_events:
            temps_after = [
                t for t in sorted_temps
                if t.timestamp >= door_open.timestamp
            ]

            if not temps_after:
                continue

            recovery_window_end = door_open.timestamp + self.MAX_RECOVERY
            temps_in_window = [
                t for t in sorted_temps
                if door_open.timestamp <= t.timestamp <= recovery_window_end
            ]

            for temp in temps_in_window:
                val = temp.parsed_value
                if isinstance(val, (int, float)):
                    if val > self.MAX_TEMP_DURING_RECOVERY:
                        temp_spike_violations.append({
                            "door_open_at": door_open.timestamp,
                            "spike_at": temp.timestamp,
                            "temp": val
                        })
                        violation_logs.append(temp)

            stable_found = False
            stable_time: datetime = None
            consecutive_in_range = 0

            for temp in temps_after:
                val = temp.parsed_value
                if isinstance(val, (int, float)):
                    in_range = RegTemp1.MIN_TEMP <= val <= RegTemp1.MAX_TEMP

                    if in_range:
                        consecutive_in_range += 1
                        if consecutive_in_range >= 2:
                            stable_found = True
                            stable_time = temp.timestamp
                            break
                    else:
                        consecutive_in_range = 0

            if not stable_found:
                recovery_violations.append({
                    "door_open_at": door_open.timestamp,
                    "last_reading_at": temps_after[-1].timestamp if temps_after else None
                })
                violation_logs.extend(temps_after[-2:] if len(temps_after) >= 2 else temps_after)
            else:
                if stable_time:
                    recovery_time = stable_time - door_open.timestamp
                    if recovery_time > self.MAX_RECOVERY:
                        recovery_violations.append({
                            "door_open_at": door_open.timestamp,
                            "stable_at": stable_time,
                            "recovery_time": recovery_time
                        })
                        violation_logs.append(temps_after[-1])

        if not recovery_violations and not temp_spike_violations:
            return [self.create_pass_finding(
                f"All {len(door_open_events)} door opening event(s) recovered within {self.MAX_RECOVERY.total_seconds()/60}min "
                f"and maintained temperature ≤ {self.MAX_TEMP_DURING_RECOVERY}°C during recovery."
            )]

        messages = []
        if recovery_violations:
            messages.append(f"{len(recovery_violations)} recovery time violation(s) > {self.MAX_RECOVERY.total_seconds()/60}min")
        if temp_spike_violations:
            messages.append(f"{len(temp_spike_violations)} temperature spike(s) > {self.MAX_TEMP_DURING_RECOVERY}°C during recovery")

        return [self.create_finding(
            passed=False,
            message="; ".join(messages),
            evidence_logs=violation_logs[:5],
            severity=Severity.HIGH if len(recovery_violations) + len(temp_spike_violations) > 2 else Severity.MEDIUM,
            remediation_hint="Check door seal integrity, verify pre-cooling before access, review standard operating procedures for door access, "
                           "and ensure cooling capacity is sized for door opening recovery."
        )]


@register_rule
class RegOps2(BaseRule):
    rule_id = "REG-OPS-2"
    description = "Excessive access is defined as f_door > 10 events/hour and must trigger operational warning"
    category = "operational"
    default_severity = Severity.LOW
    data_source = ValidationSource.LOGS
    confidence = 1.0

    MAX_DOOR_EVENTS_PER_HOUR = 10

    def validate(self, logs: List[LogEntry], context: Dict[str, Any]) -> List[Finding]:
        door_events = [
            log for log in logs
            if log.log_type in (LogType.DOOR_OPEN, LogType.DOOR_CLOSE)
        ]

        if not door_events:
            return [self.create_pass_finding("No door events detected")]

        door_open_events = [
            log for log in logs
            if log.log_type == LogType.DOOR_OPEN
        ]

        if not door_open_events:
            return [self.create_pass_finding(f"No DOOR_OPEN events among {len(door_events)} door-related events")]

        sorted_events = sorted(door_open_events, key=lambda x: x.timestamp)

        hourly_counts: Dict[datetime, int] = defaultdict(int)
        for event in sorted_events:
            hour_key = event.timestamp.replace(minute=0, second=0, microsecond=0)
            hourly_counts[hour_key] += 1

        sliding_violations: List[Dict[str, Any]] = []
        violation_logs: List[LogEntry] = []

        for i, event in enumerate(sorted_events):
            window_start = event.timestamp
            window_end = window_start + timedelta(hours=1)

            events_in_window = [
                e for e in sorted_events
                if window_start <= e.timestamp <= window_end
            ]

            if len(events_in_window) > self.MAX_DOOR_EVENTS_PER_HOUR:
                sliding_violations.append({
                    "window_start": window_start,
                    "event_count": len(events_in_window)
                })
                violation_logs.extend(events_in_window[:3])
                break

        excessive_hours = {
            hour: count
            for hour, count in hourly_counts.items()
            if count > self.MAX_DOOR_EVENTS_PER_HOUR
        }

        if not sliding_violations and not excessive_hours:
            max_count = max(hourly_counts.values()) if hourly_counts else 0
            return [self.create_pass_finding(
                f"Door access frequency within limits: max {max_count} event(s)/hour "
                f"(threshold: {self.MAX_DOOR_EVENTS_PER_HOUR}). "
                f"Total DOOR_OPEN events: {len(door_open_events)}"
            )]

        messages = []
        if excessive_hours:
            messages.append(f"{len(excessive_hours)} hour(s) with > {self.MAX_DOOR_EVENTS_PER_HOUR} door events")
        if sliding_violations:
            messages.append(f"Sliding window analysis found {len(sliding_violations)} period(s) with excessive access")

        return [self.create_finding(
            passed=False,
            message="; ".join(messages),
            evidence_logs=violation_logs[:5],
            severity=Severity.LOW,
            remediation_hint="Operational warning: Excessive door access detected. "
                           "Review access procedures, batch access operations where possible, "
                           "and verify pre-cooling strategy handles frequent access patterns. "
                           "Consider warning escalation if correlated with temperature excursions."
        )]
