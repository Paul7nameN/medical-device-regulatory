from typing import List, Dict, Any
from datetime import datetime, timedelta

from app.regulatory.rules.base import BaseRule, register_rule, ValidationSource
from app.models.logs import LogEntry, LogType
from app.models.findings import Severity, Finding


@register_rule
class RegIns1(BaseRule):
    rule_id = "REG-INS-1"
    description = "All chamber walls must have insulation thickness: t_insulation ≥ 4 cm"
    category = "insulation"
    default_severity = Severity.INFO
    data_source = ValidationSource.INSPECTION
    confidence = 0.0
    inspection_hint = "Measure insulation thickness on all chamber walls. Minimum 4cm required. Use caliper measurement or review engineering specifications."

    MIN_THICKNESS_CM = 4.0

    def validate(self, logs: List[LogEntry], context: Dict[str, Any]) -> List[Finding]:
        return [self.create_info_finding(
            f"REG-INS-1 requires physical inspection or blueprint analysis to verify "
            f"insulation thickness ≥ {self.MIN_THICKNESS_CM} cm on ALL chamber walls. "
            "Cannot validate from logs alone - this is a structural requirement.\n\n"
            "Verification methods:\n"
            "  1. VLLM analysis of engineering blueprints/schematics\n"
            "  2. Physical measurement with caliper\n"
            "  3. Review of device specifications and test reports\n\n"
            "Insufficient insulation can cause:\n"
            "  - Poor temperature stability\n"
            "  - Increased energy consumption\n"
            "  - Longer recovery times after door events\n"
            "  - Potential non-compliance with REG-TEMP during high ambient temperatures",
            needs_visual=True
        )]


@register_rule
class RegIns2(BaseRule):
    rule_id = "REG-INS-2"
    description = "Battery compartment must be physically and thermally isolated from storage chamber"
    category = "insulation"
    default_severity = Severity.INFO
    data_source = ValidationSource.INSPECTION
    confidence = 0.0
    inspection_hint = "Verify physical barrier between battery compartment and storage chamber. Check for thermal isolation features."

    def validate(self, logs: List[LogEntry], context: Dict[str, Any]) -> List[Finding]:
        battery_readings = [
            log for log in logs
            if log.log_type in (LogType.BATTERY_LEVEL, LogType.VOLTAGE)
        ]

        temp_readings = [
            log for log in logs
            if log.log_type == LogType.TEMP_READING and log.parsed_value is not None
        ]

        correlation_notes = ""
        if battery_readings and temp_readings:
            correlation_notes = (
                f"Logs show {len(battery_readings)} battery/voltage reading(s) and {len(temp_readings)} temp reading(s). "
                "No direct thermal correlation can be established without additional sensors in battery compartment."
            )

        return [self.create_info_finding(
            "REG-INS-2 requires verification that battery compartment is physically and thermally isolated from storage chamber.\n\n"
            "Purpose of this requirement:\n"
            "  1. Prevent battery heat from warming plasma storage chamber\n"
            "  2. Contain any battery thermal runaway risk\n"
            "  3. Maintain separate environmental zones\n\n"
            "Verification methods:\n"
            "  1. VLLM analysis of CAD/engineering schematics\n"
            "  2. Physical inspection of barrier/wall between compartments\n"
            "  3. Review of thermal simulation test data\n"
            "  4. Temperature sensor comparison (battery compartment vs. storage)\n\n"
            f"{correlation_notes}",
            needs_visual=True
        )]
