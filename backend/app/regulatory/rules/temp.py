from typing import List, Dict, Any
from datetime import datetime, timedelta

from app.regulatory.rules.base import BaseRule, register_rule, ValidationSource
from app.models.logs import LogEntry, LogType
from app.models.findings import Severity, Finding


@register_rule
class RegTemp1(BaseRule):
    rule_id = "REG-TEMP-1"
    description = "Maintain internal temperature: 2°C ≤ T ≤ 8°C at all times during active operation"
    category = "TEMP"
    default_severity = Severity.HIGH
    data_source = ValidationSource.LOGS
    confidence = 1.0

    MIN_TEMP = 2.0
    MAX_TEMP = 8.0

    def validate(self, logs: List[LogEntry], context: Dict[str, Any]) -> List[Finding]:
        temp_readings = [
            log for log in logs
            if log.log_type == LogType.TEMP_READING and log.parsed_value is not None
        ]

        if not temp_readings:
            return [self.create_finding(
                passed=False,
                message="No temperature readings found - cannot verify REG-TEMP-1",
                severity=Severity.MEDIUM,
                remediation_hint="Ensure device is configured to log temperature readings at REG-TEMP-4 intervals (≤30s)"
            )]

        violations = []
        for reading in temp_readings:
            temp = reading.parsed_value
            if isinstance(temp, (int, float)):
                if temp < self.MIN_TEMP or temp > self.MAX_TEMP:
                    violations.append(reading)

        if not violations:
            return [self.create_pass_finding(
                f"All {len(temp_readings)} temperature readings within valid range [{self.MIN_TEMP}°C, {self.MAX_TEMP}°C]"
            )]

        severity = Severity.CRITICAL if len(violations) > 3 else Severity.HIGH

        return [self.create_finding(
            passed=False,
            message=f"Found {len(violations)} temperature reading(s) outside range [{self.MIN_TEMP}°C, {self.MAX_TEMP}°C]",
            evidence_logs=violations,
            severity=severity,
            remediation_hint="Check cooling system performance, review door event patterns, and verify sensor calibration"
        )]


@register_rule
class RegTemp2(BaseRule):
    rule_id = "REG-TEMP-2"
    description = "Temperature excursion limits: max 5min per event, 10min cumulative per 24h. Any exceedance is critical."
    category = "TEMP"
    default_severity = Severity.CRITICAL
    data_source = ValidationSource.LOGS
    confidence = 1.0

    MAX_SINGLE_EXCURSION = timedelta(minutes=5)
    MAX_CUMULATIVE_24H = timedelta(minutes=10)

    def validate(self, logs: List[LogEntry], context: Dict[str, Any]) -> List[Finding]:
        temp_readings = [
            log for log in logs
            if log.log_type == LogType.TEMP_READING and log.parsed_value is not None
        ]

        if len(temp_readings) < 2:
            return [self.create_finding(
                passed=False,
                message="Insufficient temperature readings to analyze excursion patterns",
                severity=Severity.MEDIUM
            )]

        sorted_readings = sorted(temp_readings, key=lambda x: x.timestamp)

        excursion_events = []
        current_excursion: List[LogEntry] = []
        cumulative_duration = timedelta(0)
        max_single_excursion = timedelta(0)
        violation_logs: List[LogEntry] = []

        for reading in sorted_readings:
            temp = reading.parsed_value
            if isinstance(temp, (int, float)):
                in_range = RegTemp1.MIN_TEMP <= temp <= RegTemp1.MAX_TEMP

                if not in_range:
                    current_excursion.append(reading)
                else:
                    if current_excursion:
                        duration = current_excursion[-1].timestamp - current_excursion[0].timestamp
                        cumulative_duration += duration
                        if duration > max_single_excursion:
                            max_single_excursion = duration

                        if duration > self.MAX_SINGLE_EXCURSION:
                            excursion_events.append({
                                "start": current_excursion[0].timestamp,
                                "end": current_excursion[-1].timestamp,
                                "duration": duration,
                                "readings": current_excursion
                            })
                            violation_logs.extend(current_excursion)

                        current_excursion = []

        if current_excursion:
            duration = current_excursion[-1].timestamp - current_excursion[0].timestamp
            cumulative_duration += duration
            if duration > max_single_excursion:
                max_single_excursion = duration

            if duration > self.MAX_SINGLE_EXCURSION:
                excursion_events.append({
                    "start": current_excursion[0].timestamp,
                    "end": current_excursion[-1].timestamp,
                    "duration": duration,
                    "readings": current_excursion
                })
                violation_logs.extend(current_excursion)

        cumulative_exceeded = cumulative_duration > self.MAX_CUMULATIVE_24H
        single_exceeded = max_single_excursion > self.MAX_SINGLE_EXCURSION

        if not cumulative_exceeded and not single_exceeded:
            return [self.create_pass_finding(
                f"Temperature excursions within limits: max single={max_single_excursion.total_seconds()/60:.1f}min, "
                f"cumulative={cumulative_duration.total_seconds()/60:.1f}min"
            )]

        messages = []
        if single_exceeded:
            messages.append(f"Single excursion exceeded limit: {max_single_excursion.total_seconds()/60:.1f}min > {self.MAX_SINGLE_EXCURSION.total_seconds()/60}min")
        if cumulative_exceeded:
            messages.append(f"Cumulative excursion exceeded limit: {cumulative_duration.total_seconds()/60:.1f}min > {self.MAX_CUMULATIVE_24H.total_seconds()/60}min")

        return [self.create_finding(
            passed=False,
            message="; ".join(messages),
            evidence_logs=violation_logs[:10],
            severity=Severity.CRITICAL,
            remediation_hint="CRITICAL: Immediate investigation required. Check cooling system, door access patterns, and thermal load."
        )]


@register_rule
class RegTemp3(BaseRule):
    rule_id = "REG-TEMP-3"
    description = "After any disturbance (e.g., door opening), system must return to stable range within ≤ 3 minutes"
    category = "TEMP"
    default_severity = Severity.HIGH
    data_source = ValidationSource.LOGS
    confidence = 1.0

    MAX_RECOVERY = timedelta(minutes=3)

    def validate(self, logs: List[LogEntry], context: Dict[str, Any]) -> List[Finding]:
        door_events = [
            log for log in logs
            if log.log_type in (LogType.DOOR_OPEN, LogType.DOOR_CLOSE)
        ]

        temp_readings = [
            log for log in logs
            if log.log_type == LogType.TEMP_READING and log.parsed_value is not None
        ]

        if not door_events:
            return [self.create_pass_finding("No door disturbance events detected - recovery not applicable")]

        if not temp_readings:
            return [self.create_finding(
                passed=False,
                message="Door events detected but no temperature readings to verify recovery",
                severity=Severity.MEDIUM
            )]

        door_open_events = [log for log in door_events if log.log_type == LogType.DOOR_OPEN]
        sorted_temps = sorted(temp_readings, key=lambda x: x.timestamp)

        recovery_violations = []
        violation_logs: List[LogEntry] = []

        for door_open in door_open_events:
            temps_after = [
                t for t in sorted_temps
                if t.timestamp >= door_open.timestamp
            ]

            if not temps_after:
                continue

            recovery_time: timedelta = timedelta(0)
            stable_found = False
            in_range_start: datetime = temps_after[0].timestamp

            for temp in temps_after:
                temp_val = temp.parsed_value
                if isinstance(temp_val, (int, float)):
                    in_range = RegTemp1.MIN_TEMP <= temp_val <= RegTemp1.MAX_TEMP

                    if in_range:
                        if not stable_found:
                            in_range_start = temp.timestamp
                            stable_found = True
                        else:
                            recovery_time = temp.timestamp - door_open.timestamp
                            if recovery_time > self.MAX_RECOVERY:
                                recovery_violations.append({
                                    "door_open_at": door_open.timestamp,
                                    "recovery_time": recovery_time,
                                    "first_stable_at": in_range_start
                                })
                                violation_logs.append(temp)
                            break
                    else:
                        stable_found = False

        if not recovery_violations:
            return [self.create_pass_finding(
                f"All {len(door_open_events)} door disturbance(s) recovered within {self.MAX_RECOVERY.total_seconds()/60} minutes"
            )]

        return [self.create_finding(
            passed=False,
            message=f"Found {len(recovery_violations)} recovery violation(s) exceeding {self.MAX_RECOVERY.total_seconds()/60}min limit",
            evidence_logs=violation_logs,
            severity=Severity.HIGH,
            remediation_hint="Check cooling system capacity, insulation integrity, and door operation procedures"
        )]


@register_rule
class RegTemp4(BaseRule):
    rule_id = "REG-TEMP-4"
    description = "Temperature must be recorded at intervals of Δt ≤ 30 seconds"
    category = "TEMP"
    default_severity = Severity.MEDIUM
    data_source = ValidationSource.LOGS
    confidence = 1.0

    MAX_INTERVAL = timedelta(seconds=30)

    def validate(self, logs: List[LogEntry], context: Dict[str, Any]) -> List[Finding]:
        temp_readings = [
            log for log in logs
            if log.log_type == LogType.TEMP_READING
        ]

        if len(temp_readings) < 2:
            return [self.create_finding(
                passed=False,
                message="Insufficient temperature readings to verify sampling frequency",
                severity=Severity.LOW
            )]

        sorted_readings = sorted(temp_readings, key=lambda x: x.timestamp)

        gaps = []
        violation_logs: List[LogEntry] = []

        for i in range(1, len(sorted_readings)):
            interval = sorted_readings[i].timestamp - sorted_readings[i-1].timestamp
            if interval > self.MAX_INTERVAL:
                gaps.append({
                    "from": sorted_readings[i-1].timestamp,
                    "to": sorted_readings[i].timestamp,
                    "interval": interval
                })
                violation_logs.append(sorted_readings[i])

        if not gaps:
            return [self.create_pass_finding(
                f"All {len(sorted_readings)-1} sampling intervals ≤ {self.MAX_INTERVAL.total_seconds()} seconds"
            )]

        max_gap = max(g["interval"] for g in gaps)

        return [self.create_finding(
            passed=False,
            message=f"Found {len(gaps)} sampling gap(s) > {self.MAX_INTERVAL.total_seconds()}s. "
                    f"Largest gap: {max_gap.total_seconds():.1f} seconds",
            evidence_logs=violation_logs[:5],
            severity=Severity.MEDIUM,
            remediation_hint="Check sensor connectivity, logging configuration, and telemetry sync status"
        )]
