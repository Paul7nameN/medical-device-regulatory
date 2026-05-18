from typing import List, Dict, Any
from datetime import datetime, timedelta

from app.regulatory.rules.base import BaseRule, register_rule, ValidationSource
from app.regulatory.rules.temp import RegTemp1
from app.models.logs import LogEntry, LogType
from app.models.findings import Severity, Finding


@register_rule
class RegCool1(BaseRule):
    rule_id = "REG-COOL-1"
    description = "Cooling system must include at least n ≥ 2 airflow paths"
    category = "cooling"
    default_severity = Severity.INFO
    data_source = ValidationSource.INSPECTION
    confidence = 0.0
    inspection_hint = "Verify ≥2 independent airflow paths. Check for redundant fans and separate cooling loops via blueprint or physical inspection."

    def validate(self, logs: List[LogEntry], context: Dict[str, Any]) -> List[Finding]:
        fan_readings = [
            log for log in logs
            if log.log_type == LogType.FAN_SPEED
        ]

        cooling_starts = [
            log for log in logs
            if log.log_type == LogType.COOLING_RECOVERY_START
        ]

        return [self.create_info_finding(
            "REG-COOL-1 requires verification of multiple airflow paths (n ≥ 2). "
            f"Logs show {len(fan_readings)} FAN_SPEED reading(s) and {len(cooling_starts)} COOLING_RECOVERY_START event(s). "
            "Cannot verify number of independent airflow paths from logs alone. "
            "Use VLLM to analyze schematics or inspect physical hardware for redundant fans/airflow paths."
        )]


@register_rule
class RegCool2(BaseRule):
    rule_id = "REG-COOL-2"
    description = "Single-point failure in cooling airflow shall not result in temperature excursion beyond allowed range for more than 3 minutes"
    category = "cooling"
    default_severity = Severity.HIGH
    data_source = ValidationSource.LOGS
    confidence = 0.8

    MAX_EXCURSION = timedelta(minutes=3)

    def validate(self, logs: List[LogEntry], context: Dict[str, Any]) -> List[Finding]:
        temp_readings = [
            log for log in logs
            if log.log_type == LogType.TEMP_READING and log.parsed_value is not None
        ]

        fan_readings = [
            log for log in logs
            if log.log_type == LogType.FAN_SPEED
        ]

        cooling_events = [
            log for log in logs
            if log.log_type in (LogType.COOLING_RECOVERY_START,)
        ]

        if not temp_readings:
            return [self.create_finding(
                passed=False,
                message="No temperature readings to verify cooling failure tolerance",
                severity=Severity.LOW
            )]

        sorted_temp = sorted(temp_readings, key=lambda x: x.timestamp)

        possible_failures: List[Dict[str, Any]] = []

        for i in range(1, len(sorted_temp)):
            prev_val = sorted_temp[i-1].parsed_value
            curr_val = sorted_temp[i].parsed_value

            if isinstance(prev_val, (int, float)) and isinstance(curr_val, (int, float)):
                temp_rise = curr_val - prev_val
                time_delta = sorted_temp[i].timestamp - sorted_temp[i-1].timestamp

                if temp_rise > 1.0 and time_delta.total_seconds() < 120:
                    possible_failures.append({
                        "time": sorted_temp[i].timestamp,
                        "temp_rise": temp_rise,
                        "log": sorted_temp[i]
                    })

        excursions: List[Dict[str, Any]] = []
        excursion_start: datetime = None
        excursion_logs: List[LogEntry] = []

        for reading in sorted_temp:
            val = reading.parsed_value
            if isinstance(val, (int, float)):
                in_range = RegTemp1.MIN_TEMP <= val <= RegTemp1.MAX_TEMP

                if not in_range:
                    if excursion_start is None:
                        excursion_start = reading.timestamp
                    excursion_logs.append(reading)
                else:
                    if excursion_start is not None:
                        duration = reading.timestamp - excursion_start
                        if duration > self.MAX_EXCURSION:
                            excursions.append({
                                "start": excursion_start,
                                "end": reading.timestamp,
                                "duration": duration,
                                "logs": excursion_logs
                            })
                        excursion_start = None
                        excursion_logs = []

        if excursion_start is not None and excursion_logs:
            end_time = excursion_logs[-1].timestamp
            duration = end_time - excursion_start
            if duration > self.MAX_EXCURSION:
                excursions.append({
                    "start": excursion_start,
                    "end": end_time,
                    "duration": duration,
                    "logs": excursion_logs
                })

        if excursions:
            max_duration = max(e["duration"] for e in excursions)
            violation_logs = []
            for e in excursions:
                violation_logs.extend(e["logs"][:2])

            return [self.create_finding(
                passed=False,
                message=f"Found {len(excursions)} temperature excursion(s) exceeding {self.MAX_EXCURSION.total_seconds()/60}min recovery window. "
                        f"Longest excursion: {max_duration.total_seconds()/60:.1f}min. "
                        "This may indicate cooling system single-point failure vulnerability.",
                evidence_logs=violation_logs[:5],
                severity=Severity.HIGH,
                remediation_hint="Investigate cooling system redundancy. Verify fans, refrigerant loops, and airflow paths have N+1 redundancy. "
                               "Test single-point failure scenarios to ensure compliance with 3-minute recovery requirement."
            )]

        return [self.create_pass_finding(
            f"REG-COOL-2: All temperature excursions (if any) recovered within {self.MAX_EXCURSION.total_seconds()/60}min window. "
            "Note: Single-point failure testing requires controlled failure injection for complete verification."
        )]
