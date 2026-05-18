from typing import List, Dict, Any
from datetime import datetime, timedelta

from app.regulatory.rules.base import BaseRule, register_rule, ValidationSource
from app.regulatory.rules.temp import RegTemp1
from app.models.logs import LogEntry, LogType
from app.models.findings import Severity, Finding


@register_rule
class RegPower1(BaseRule):
    rule_id = "REG-POWER-1"
    description = "Battery backup must support continuous operation for t_battery ≥ 4 hours"
    category = "power"
    default_severity = Severity.MEDIUM
    data_source = ValidationSource.COMBINED
    confidence = 0.6

    MIN_RUNTIME = timedelta(hours=4)

    def validate(self, logs: List[LogEntry], context: Dict[str, Any]) -> List[Finding]:
        battery_readings = [
            log for log in logs
            if log.log_type == LogType.BATTERY_LEVEL and log.parsed_value is not None
        ]

        voltage_readings = [
            log for log in logs
            if log.log_type == LogType.VOLTAGE and log.parsed_value is not None
        ]

        if not battery_readings and not voltage_readings:
            return [self.create_info_finding(
                "REG-POWER-1 requires battery runtime verification. "
                "No battery level or voltage readings found in logs. "
                f"Verify battery capacity supports {self.MIN_RUNTIME.total_seconds()/3600}h continuous operation."
            )]

        if len(battery_readings) >= 2:
            sorted_battery = sorted(battery_readings, key=lambda x: x.timestamp)

            drain_rates = []
            for i in range(1, len(sorted_battery)):
                start_val = sorted_battery[i-1].parsed_value
                end_val = sorted_battery[i].parsed_value
                time_delta = sorted_battery[i].timestamp - sorted_battery[i-1].timestamp

                if isinstance(start_val, (int, float)) and isinstance(end_val, (int, float)):
                    drain = start_val - end_val
                    if drain > 0 and time_delta.total_seconds() > 0:
                        rate_per_hour = (drain / time_delta.total_seconds()) * 3600
                        drain_rates.append(rate_per_hour)

            if drain_rates:
                avg_rate = sum(drain_rates) / len(drain_rates)
                first_val = sorted_battery[0].parsed_value

                if isinstance(first_val, (int, float)):
                    estimated_runtime_hours = first_val / avg_rate if avg_rate > 0 else float('inf')

                    if estimated_runtime_hours >= self.MIN_RUNTIME.total_seconds() / 3600:
                        return [self.create_pass_finding(
                            f"Estimated battery runtime: {estimated_runtime_hours:.1f}h based on {len(drain_rates)} drain sample(s). "
                            f"Meets ≥ {self.MIN_RUNTIME.total_seconds()/3600}h requirement."
                        )]

                    return [self.create_finding(
                        passed=False,
                        message=f"Estimated battery runtime: {estimated_runtime_hours:.1f}h < required {self.MIN_RUNTIME.total_seconds()/3600}h. "
                                f"Average drain rate: {avg_rate:.2f}% per hour based on observed samples.",
                        severity=Severity.HIGH,
                        remediation_hint="Verify battery capacity, check for excessive power drain, and ensure backup system is properly sized."
                    )]

        return [self.create_info_finding(
            "REG-POWER-1: Insufficient battery drain data to estimate runtime. "
            "Verify battery capacity through full discharge test or device specifications. "
            f"Requirement: {self.MIN_RUNTIME.total_seconds()/3600}h minimum backup runtime."
        )]


@register_rule
class RegPower2(BaseRule):
    rule_id = "REG-POWER-2"
    description = "Even in battery mode, temperature must remain compliant with REG-TEMP-1 (2°C ≤ T ≤ 8°C)"
    category = "power"
    default_severity = Severity.HIGH
    data_source = ValidationSource.LOGS
    confidence = 0.9

    def validate(self, logs: List[LogEntry], context: Dict[str, Any]) -> List[Finding]:
        temp_readings = [
            log for log in logs
            if log.log_type == LogType.TEMP_READING and log.parsed_value is not None
        ]

        voltage_readings = [
            log for log in logs
            if log.log_type == LogType.VOLTAGE and log.parsed_value is not None
        ]

        if not temp_readings:
            return [self.create_finding(
                passed=False,
                message="No temperature readings to verify battery mode compliance",
                severity=Severity.LOW
            )]

        if not voltage_readings:
            return [self.create_info_finding(
                "REG-POWER-2: No voltage readings to identify battery mode operation. "
                "Cannot correlate temperature compliance with power source. "
                "Verify cooling system maintains temperature during battery-only operation."
            )]

        sorted_voltage = sorted(voltage_readings, key=lambda x: x.timestamp)
        sorted_temp = sorted(temp_readings, key=lambda x: x.timestamp)

        battery_mode_periods: List[Dict[str, Any]] = []
        device_starts = [log for log in logs if log.log_type == LogType.DEVICE_START]

        temp_violations_in_battery_mode: List[LogEntry] = []

        for voltage in sorted_voltage:
            val = voltage.parsed_value
            if isinstance(val, (int, float)):
                if val < 12.0:
                    temps_nearby = [
                        t for t in sorted_temp
                        if abs((t.timestamp - voltage.timestamp).total_seconds()) < 60
                    ]

                    for temp in temps_nearby:
                        t_val = temp.parsed_value
                        if isinstance(t_val, (int, float)):
                            if t_val < RegTemp1.MIN_TEMP or t_val > RegTemp1.MAX_TEMP:
                                temp_violations_in_battery_mode.append(temp)

        if temp_violations_in_battery_mode:
            return [self.create_finding(
                passed=False,
                message=f"Found {len(temp_violations_in_battery_mode)} temperature violation(s) during apparent battery mode (low voltage). "
                        "REG-POWER-2 requires temperature compliance even on battery backup.",
                evidence_logs=temp_violations_in_battery_mode[:5],
                severity=Severity.HIGH,
                remediation_hint="Critical: Verify cooling system runs on battery power, check power management configuration, and ensure sufficient battery capacity for cooling load."
            )]

        return [self.create_pass_finding(
            "REG-POWER-2: No temperature violations detected during periods of low voltage (battery mode). "
            "Temperature compliance maintained during apparent backup operation."
        )]
