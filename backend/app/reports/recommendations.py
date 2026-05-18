from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict

from app.models.findings import Severity
from app.reports.models import (
    ViolationSummary,
    TemporalAnalysis,
    AIEnhancements,
    Recommendation
)


RULE_REMEDIATION_HINTS: Dict[str, Dict[str, Any]] = {
    "REG-TEMP-1": {
        "title": "Investigate Temperature Excursions",
        "description": "Temperature readings outside valid range detected. Check cooling system and door access patterns.",
        "remediation_hint": "1. Verify cooling system is operating correctly\n2. Review door event frequency\n3. Check sensor calibration\n4. Verify thermal load hasn't changed",
    },
    "REG-TEMP-2": {
        "title": "Critical: Excursion Limits Exceeded",
        "description": "Temperature excursion duration exceeds MED-THERM-2026 limits. This is a CRITICAL violation requiring immediate action.",
        "remediation_hint": "1. IMMEDIATE: Check cooling system capacity\n2. Review door access logs for excessive openings\n3. Verify temperature sensor calibration\n4. Check for thermal insulation degradation\n5. Review alarm thresholds and activation",
    },
    "REG-TEMP-3": {
        "title": "Slow Recovery After Disturbance",
        "description": "System taking longer than 3 minutes to recover after door opening or other disturbance.",
        "remediation_hint": "1. Check cooling system capacity\n2. Verify door seals are intact\n3. Review door operation procedures\n4. Check for thermal load issues",
    },
    "REG-SENS-1": {
        "title": "Sensor Redundancy Compromised",
        "description": "One or both temperature sensors experiencing timeouts. Dual failure is CRITICAL.",
        "remediation_hint": "1. Check sensor wiring and connections\n2. Verify sensor power supply\n3. Test sensor replacement if failures persist\n4. For dual failure: IMMEDIATE investigation required",
    },
    "REG-ALARM-1": {
        "title": "Alarm Activation Failure",
        "description": "Temperature excursion >=2 minutes detected without corresponding alarm activation.",
        "remediation_hint": "1. Verify alarm system configuration\n2. Check alarm threshold settings\n3. Test alarm activation with simulated excursion\n4. Verify sensor-alarm integration",
    },
    "REG-DATA-2": {
        "title": "Telemetry Gaps Detected",
        "description": "Telemetry data gaps exceeding 90 seconds detected. May indicate communication or logging issues.",
        "remediation_hint": "1. Check network connectivity\n2. Verify logging service status\n3. Review telemetry sync configuration\n4. Check for power interruptions",
    },
    "REG-TEMP-4": {
        "title": "Sampling Interval Exceeded",
        "description": "Temperature sampling interval exceeds 30 seconds. May affect excursion detection.",
        "remediation_hint": "1. Review logging configuration\n2. Check sensor polling frequency\n3. Verify no network latency issues",
    },
    "REG-SENS-3": {
        "title": "Sensor Disagreement Detected",
        "description": "Primary and secondary sensors show temperature difference > 0.5°C.",
        "remediation_hint": "1. Check sensor calibration\n2. Verify both sensors measure same location\n3. Inspect for sensor drift",
    },
    "REG-ALARM-2": {
        "title": "Notification Latency Requires Verification",
        "description": "REG-ALARM-2 requires end-to-end notification timing verification.",
        "remediation_hint": "1. Test alarm trigger to notification timing\n2. Verify all notification channels are configured\n3. Check network latency for remote notifications",
    },
    "REG-ALARM-3": {
        "title": "Alarm Channels Need Physical Verification",
        "description": "REG-ALARM-3 requires verification of all three notification channels.",
        "remediation_hint": "1. Test audible alarm (speaker/buzzer)\n2. Verify visual dashboard alerts\n3. Test remote mobile notifications",
    },
    "REG-SENS-2": {
        "title": "Sensor Placement Needs Physical Inspection",
        "description": "REG-SENS-2 requires physical inspection or blueprint analysis to verify sensor placement.",
        "remediation_hint": "1. Inspect sensor placement relative to airflow outlets\n2. Verify minimum 15cm distance requirement\n3. Review device schematics if available",
    },
}


def generate_recommendations(
    violations_by_rule: Dict[str, ViolationSummary],
    temporal_analysis: TemporalAnalysis,
    ai_enhancements: AIEnhancements
) -> List[Recommendation]:
    
    recommendations: List[Recommendation] = []
    
    severity_order = [
        Severity.CRITICAL,
        Severity.HIGH,
        Severity.MEDIUM,
        Severity.LOW,
        Severity.INFO
    ]
    
    for severity in severity_order:
        for rule_id, vs in violations_by_rule.items():
            if vs.severity != severity:
                continue
            
            rule_info = RULE_REMEDIATION_HINTS.get(rule_id, {})
            
            temporal_context = _get_temporal_context(vs, temporal_analysis)
            
            rec = Recommendation(
                priority=vs.severity,
                rule_id=rule_id,
                rule_description=vs.rule_description,
                title=rule_info.get("title", f"Address {rule_id} Violations"),
                description=rule_info.get(
                    "description",
                    f"{vs.count} violation(s) detected for {rule_id}"
                ),
                remediation_hint=rule_info.get("remediation_hint"),
                temporal_context=temporal_context,
                evidence_count=vs.count,
                first_occurrence=vs.first_occurrence
            )
            
            recommendations.append(rec)
    
    if ai_enhancements and ai_enhancements.log_insights:
        ai_recs = ai_enhancements.log_insights.get("recommendations", [])
        for ai_rec in ai_recs[:2]:
            ai_rec_str = str(ai_rec)
            if ai_rec_str and ai_rec_str not in [r.description for r in recommendations]:
                recommendations.append(Recommendation(
                    priority=Severity.LOW,
                    rule_id="AI_INSIGHT",
                    rule_description="AI-generated insight",
                    title="Additional AI Insight",
                    description=ai_rec_str,
                    evidence_count=0
                ))
    
    return recommendations


def _get_temporal_context(
    vs: ViolationSummary,
    temporal_analysis: TemporalAnalysis
) -> str:
    
    context_parts = []
    
    if vs.first_occurrence and vs.last_occurrence:
        if vs.first_occurrence == vs.last_occurrence:
            context_parts.append(
                f"Occurred at {vs.first_occurrence.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        else:
            context_parts.append(
                f"First occurrence: {vs.first_occurrence.strftime('%Y-%m-%d %H:%M:%S')}, "
                f"Last occurrence: {vs.last_occurrence.strftime('%Y-%m-%d %H:%M:%S')}"
            )
    
    related_periods = [
        p for p in temporal_analysis.critical_periods
        if vs.first_occurrence and p.period_start <= vs.first_occurrence <= p.period_end
    ]
    
    if related_periods:
        context_parts.append(
            f"Part of {len(related_periods)} critical period(s) with clustered violations"
        )
    
    return " | ".join(context_parts) if context_parts else None