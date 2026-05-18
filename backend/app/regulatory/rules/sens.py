from typing import List, Dict, Any
from datetime import datetime, timedelta

from app.regulatory.rules.base import BaseRule, register_rule, ValidationSource
from app.models.logs import LogEntry, LogType
from app.models.findings import Severity, Finding


@register_rule
class RegSens1(BaseRule):
    rule_id = "REG-SENS-1"
    description = "The system shall include at least one primary + one redundant secondary sensor. Failure of redundancy constitutes a critical violation."
    category = "sensor"
    default_severity = Severity.CRITICAL
    data_source = ValidationSource.LOGS
    confidence = 1.0

    def validate(self, logs: List[LogEntry], context: Dict[str, Any]) -> List[Finding]:
        sensor_timeouts = [
            log for log in logs
            if log.log_type == LogType.SENSOR_TIMEOUT
        ]

        primary_timeout = any(
            "PRIMARY" in log.raw_value.upper() or log.sensor_id == "PRIMARY"
            for log in sensor_timeouts
        )
        secondary_timeout = any(
            "SECONDARY" in log.raw_value.upper() or log.sensor_id == "SECONDARY"
            for log in sensor_timeouts
        )

        if not sensor_timeouts:
            return [self.create_pass_finding(
                "No sensor timeout events detected - redundancy appears intact"
            )]

        if primary_timeout and secondary_timeout:
            return [self.create_finding(
                passed=False,
                message="CRITICAL: Both PRIMARY and SECONDARY sensors experiencing timeouts - complete redundancy failure",
                evidence_logs=sensor_timeouts[:5],
                severity=Severity.CRITICAL,
                remediation_hint="Immediate action required. Check sensor wiring, power, and controller connectivity."
            )]

        if secondary_timeout:
            return [self.create_finding(
                passed=False,
                message="SECONDARY sensor experiencing timeouts - redundancy compromised",
                evidence_logs=sensor_timeouts[:5],
                severity=Severity.HIGH,
                remediation_hint="Investigate secondary sensor. Primary still functional but redundancy lost."
            )]

        if primary_timeout:
            return [self.create_finding(
                passed=False,
                message="PRIMARY sensor experiencing timeouts - operating on secondary only",
                evidence_logs=sensor_timeouts[:5],
                severity=Severity.HIGH,
                remediation_hint="Investigate primary sensor. Device functional but degraded redundancy."
            )]

        return [self.create_pass_finding(
            f"Sensor timeout events detected but both channels appear operational: {len(sensor_timeouts)} event(s)"
        )]


@register_rule
class RegSens2(BaseRule):
    rule_id = "REG-SENS-2"
    description = "Sensors must not be placed within d < 15 cm from airflow outlet to prevent airflow bias interference."
    category = "sensor"
    default_severity = Severity.INFO
    data_source = ValidationSource.INSPECTION
    confidence = 0.0
    inspection_hint = "Verify sensor placement ≥15cm from airflow outlets. Use blueprint analysis or physical measurement."

    def validate(self, logs: List[LogEntry], context: Dict[str, Any]) -> List[Finding]:
        return [self.create_info_finding(
            "REG-SENS-2 requires physical inspection or blueprint analysis to verify sensor placement relative to airflow outlets. "
            "Cannot validate from logs alone. Use VLLM integration for schematic analysis.",
            needs_visual=True
        )]


@register_rule
class RegSens3(BaseRule):
    rule_id = "REG-SENS-3"
    description = "Sensor readings must satisfy: |T1 - T2| ≤ 0.5°C"
    category = "sensor"
    default_severity = Severity.HIGH
    data_source = ValidationSource.COMBINED
    confidence = 0.7

    MAX_DISAGREEMENT = 0.5

    def validate(self, logs: List[LogEntry], context: Dict[str, Any]) -> List[Finding]:
        temp_readings = [
            log for log in logs
            if log.log_type == LogType.TEMP_READING and log.parsed_value is not None
        ]

        if len(temp_readings) < 2:
            return [self.create_finding(
                passed=False,
                message="Insufficient temperature readings to verify sensor agreement",
                severity=Severity.LOW
            )]

        sorted_readings = sorted(temp_readings, key=lambda x: x.timestamp)

        readings_by_time: Dict[datetime, List[float]] = {}
        for reading in sorted_readings:
            ts = reading.timestamp.replace(second=0, microsecond=0)
            if ts not in readings_by_time:
                readings_by_time[ts] = []
            val = reading.parsed_value
            if isinstance(val, (int, float)):
                readings_by_time[ts].append(float(val))

        has_dual_sensor_data = any(len(temps) >= 2 for temps in readings_by_time.values())

        if not has_dual_sensor_data:
            return [self.create_info_finding(
                "Only single sensor data available - cannot verify sensor agreement (REG-SENS-3). "
                "Need PRIMARY + SECONDARY readings at the same timestamp to validate |T1 - T2| ≤ 0.5°C requirement."
            )]

        disagreements = []
        for ts, temps in readings_by_time.items():
            if len(temps) >= 2:
                temps_sorted = sorted(temps)
                for i in range(len(temps_sorted)):
                    for j in range(i + 1, len(temps_sorted)):
                        diff = abs(temps_sorted[j] - temps_sorted[i])
                        if diff > self.MAX_DISAGREEMENT:
                            disagreements.append({
                                "timestamp": ts,
                                "readings": temps,
                                "max_diff": diff
                            })

        if not disagreements:
            return [self.create_pass_finding(
                f"Sensor agreement within ±{self.MAX_DISAGREEMENT}°C for all concurrent readings"
            )]

        max_diff = max(d["max_diff"] for d in disagreements)

        return [self.create_finding(
            passed=False,
            message=f"Found {len(disagreements)} instance(s) of sensor disagreement > {self.MAX_DISAGREEMENT}°C. "
                    f"Maximum disagreement: {max_diff:.2f}°C",
            severity=Severity.HIGH,
            remediation_hint="Check sensor calibration, verify both sensors are measuring same location, and inspect for sensor drift."
        )]
