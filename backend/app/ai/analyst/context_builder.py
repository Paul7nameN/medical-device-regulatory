from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from collections import defaultdict
import logging

from app.models.logs import LogEntry, LogType
from app.models.findings import ComplianceReport, Finding
from app.ai.image.models import ChartAnalysisResult, ChartViolation, TemperatureReading
from app.ai.analyst.models import (
    Thresholds,
    DEFAULT_THRESHOLDS,
)

logger = logging.getLogger(__name__)


def _safe_get_value(log_entry: LogEntry) -> Optional[float]:
    if log_entry.parsed_value is not None:
        if isinstance(log_entry.parsed_value, (int, float)):
            return float(log_entry.parsed_value)
    try:
        import re
        match = re.search(r'[\d.]+', log_entry.raw_value)
        if match:
            return float(match.group())
    except (ValueError, TypeError):
        pass
    return None


def build_analysis_context(
    logs: Optional[List[LogEntry]] = None,
    report: Optional[ComplianceReport] = None,
    chart_result: Optional[ChartAnalysisResult] = None,
    thresholds: Thresholds = DEFAULT_THRESHOLDS,
) -> Dict[str, Any]:
    context: Dict[str, Any] = {
        "thresholds": {
            "safe_temp_range": thresholds.safe_temp_range,
            "max_single_excursion_min": thresholds.max_single_excursion_min,
            "max_cumulative_excursion_24h": thresholds.max_cumulative_excursion_24h,
            "max_recovery_min": thresholds.max_recovery_min,
            "sensor_disagreement_max_celsius": thresholds.sensor_disagreement_max_celsius,
            "max_door_events_per_hour": thresholds.max_door_events_per_hour,
            "battery_backup_required_hours": thresholds.battery_backup_required_hours,
            "max_sampling_interval_sec": thresholds.max_sampling_interval_sec,
            "max_telemetry_gap_sec": thresholds.max_telemetry_gap_sec,
        }
    }
    
    if logs is not None and len(logs) > 0:
        context.update(_build_context_from_logs(logs, report, thresholds))
    elif chart_result is not None:
        context.update(_build_context_from_chart(chart_result, report, thresholds))
    else:
        context["session_overview"] = {
            "total_log_entries": 0,
            "duration_hours": 0,
            "message": "No log or chart data provided",
        }
    
    return context


def _build_context_from_logs(
    logs: List[LogEntry],
    report: Optional[ComplianceReport],
    thresholds: Thresholds,
) -> Dict[str, Any]:
    sorted_logs = sorted(logs, key=lambda x: x.timestamp)
    
    total_entries = len(sorted_logs)
    time_range_start = sorted_logs[0].timestamp
    time_range_end = sorted_logs[-1].timestamp
    duration_seconds = (time_range_end - time_range_start).total_seconds()
    duration_hours = duration_seconds / 3600 if duration_seconds > 0 else 0
    
    systems_status = _extract_systems_status(sorted_logs, thresholds)
    operational_patterns = _extract_operational_patterns(sorted_logs, duration_hours, thresholds)
    timeline = _build_timeline(sorted_logs, thresholds)
    rule_findings = _extract_rule_findings(report)
    
    return {
        "session_overview": {
            "total_log_entries": total_entries,
            "time_range_start": time_range_start.isoformat() if time_range_start else None,
            "time_range_end": time_range_end.isoformat() if time_range_end else None,
            "duration_hours": round(duration_hours, 2),
        },
        "systems_status": systems_status,
        "operational_patterns": operational_patterns,
        "timeline_critical_events": timeline,
        "rule_based_findings": rule_findings,
    }


def _build_context_from_chart(
    chart_result: ChartAnalysisResult,
    report: Optional[ComplianceReport],
    thresholds: Thresholds,
) -> Dict[str, Any]:
    temp_readings = chart_result.data_points or []
    violations = chart_result.violations or []
    
    temp_values = [r.sensor_a for r in temp_readings]
    temp_b_values = [r.sensor_b for r in temp_readings if r.sensor_b is not None]
    
    min_temp = min(temp_values) if temp_values else None
    max_temp = max(temp_values) if temp_values else None
    
    excursions_count = len([v for v in violations if v.violation_type.value == "excursion"])
    gaps_count = len([v for v in violations if v.violation_type.value == "gap"])
    
    sensor_disagreement = 0.0
    for reading in temp_readings:
        if reading.sensor_b is not None:
            diff = abs(reading.sensor_a - reading.sensor_b)
            if diff > sensor_disagreement:
                sensor_disagreement = diff
    
    max_disagreement_warning = sensor_disagreement > thresholds.sensor_disagreement_max_celsius
    
    excursion_violations = [v for v in violations if v.violation_type.value == "excursion"]
    
    return {
        "session_overview": {
            "total_data_points": len(temp_readings),
            "chart_type": chart_result.chart_type,
            "analyzed_at": chart_result.analyzed_at.isoformat() if chart_result.analyzed_at else None,
            "confidence": chart_result.confidence,
            "temp_range_observed": {
                "min": min_temp,
                "max": max_temp,
                "safe_range": thresholds.safe_temp_range,
            },
        },
        "systems_status": {
            "sensors": {
                "primary_available": len(temp_values) > 0,
                "secondary_available": len(temp_b_values) > 0,
                "max_disagreement_observed": round(sensor_disagreement, 2) if sensor_disagreement else None,
                "disagreement_exceeds_threshold": max_disagreement_warning,
            },
            "thermal": {
                "excursions_count": excursions_count,
                "gaps_count": gaps_count,
                "excursion_details": [
                    {
                        "timestamp_start": v.timestamp_start.isoformat() if v.timestamp_start else None,
                        "timestamp_end": v.timestamp_end.isoformat() if v.timestamp_end else None,
                        "description": v.description,
                        "extracted_value": v.extracted_value,
                        "confidence": v.confidence,
                    }
                    for v in excursion_violations[:5]
                ],
            },
        },
        "operational_patterns": {
            "message": "Limited operational data from chart image only",
        },
        "timeline_critical_events": [
            {
                "time": v.timestamp_start.isoformat() if v.timestamp_start else "unknown",
                "type": f"chart_{v.violation_type.value}",
                "context": v.description,
                "value": v.extracted_value,
            }
            for v in violations[:10]
        ],
        "rule_based_findings": _extract_rule_findings(report),
    }


def _extract_systems_status(
    logs: List[LogEntry],
    thresholds: Thresholds,
) -> Dict[str, Any]:
    temp_readings = [l for l in logs if l.log_type == LogType.TEMP_READING]
    fan_readings = [l for l in logs if l.log_type == LogType.FAN_SPEED]
    voltage_readings = [l for l in logs if l.log_type == LogType.VOLTAGE]
    humidity_readings = [l for l in logs if l.log_type == LogType.HUMIDITY]
    battery_readings = [l for l in logs if l.log_type == LogType.BATTERY_LEVEL]
    sensor_timeouts = [l for l in logs if l.log_type == LogType.SENSOR_TIMEOUT]
    recovery_events = [l for l in logs if l.log_type == LogType.COOLING_RECOVERY_START]
    
    temp_values = [_safe_get_value(l) for l in temp_readings]
    temp_values = [v for v in temp_values if v is not None]
    
    voltage_values = [_safe_get_value(l) for l in voltage_readings]
    voltage_values = [v for v in voltage_values if v is not None]
    
    battery_values = [_safe_get_value(l) for l in battery_readings]
    battery_values = [v for v in battery_values if v is not None]
    
    humidity_values = [_safe_get_value(l) for l in humidity_readings]
    humidity_values = [v for v in humidity_values if v is not None]
    
    primary_timeout = any(l.sensor_id == "PRIMARY" or "PRIMARY" in (l.raw_value or "") for l in sensor_timeouts)
    secondary_timeout = any(l.sensor_id == "SECONDARY" or "SECONDARY" in (l.raw_value or "") for l in sensor_timeouts)
    
    battery_mode = False
    if voltage_values:
        avg_voltage = sum(voltage_values) / len(voltage_values)
        battery_mode = avg_voltage < 12.4
    
    min_temp = min(temp_values) if temp_values else None
    max_temp = max(temp_values) if temp_values else None
    avg_temp = sum(temp_values) / len(temp_values) if temp_values else None
    
    excursions = []
    safe_min, safe_max = thresholds.safe_temp_range
    for l in temp_readings:
        val = _safe_get_value(l)
        if val is not None and (val < safe_min or val > safe_max):
            excursions.append({
                "time": l.timestamp.isoformat(),
                "value": round(val, 2),
            })
    
    battery_hours_remaining = None
    if len(battery_values) >= 2:
        first = battery_values[0]
        last = battery_values[-1]
        if len(logs) >= 2:
            sorted_logs = sorted(logs, key=lambda x: x.timestamp)
            duration_hours = (sorted_logs[-1].timestamp - sorted_logs[0].timestamp).total_seconds() / 3600
            if duration_hours > 0 and first > last:
                drain_per_hour = (first - last) / duration_hours
                if drain_per_hour > 0:
                    battery_hours_remaining = last / drain_per_hour
    
    return {
        "sensors": {
            "primary_available": not primary_timeout,
            "secondary_available": not secondary_timeout,
            "primary_timeout_count": sum(1 for l in sensor_timeouts if l.sensor_id == "PRIMARY" or "PRIMARY" in (l.raw_value or "")),
            "secondary_timeout_count": sum(1 for l in sensor_timeouts if l.sensor_id == "SECONDARY" or "SECONDARY" in (l.raw_value or "")),
        },
        "power": {
            "voltage_range": {
                "min": round(min(voltage_values), 2) if voltage_values else None,
                "max": round(max(voltage_values), 2) if voltage_values else None,
                "avg": round(sum(voltage_values) / len(voltage_values), 2) if voltage_values else None,
            },
            "battery_mode": battery_mode,
            "battery_level_range": {
                "start": round(battery_values[0], 2) if battery_values else None,
                "end": round(battery_values[-1], 2) if len(battery_values) >= 2 else (battery_values[0] if battery_values else None),
            },
            "battery_drain_rate_per_hour": (
                round((battery_values[0] - battery_values[-1]) / (
                    (sorted(logs, key=lambda x: x.timestamp)[-1].timestamp - 
                     sorted(logs, key=lambda x: x.timestamp)[0].timestamp).total_seconds() / 3600
                ), 2)
                if len(battery_values) >= 2 and len(logs) >= 2 else None
            ),
            "estimated_battery_hours_remaining": (
                round(battery_hours_remaining, 1) if battery_hours_remaining else None
            ),
            "battery_below_required": (
                battery_hours_remaining is not None and battery_hours_remaining < thresholds.battery_backup_required_hours
            ),
        },
        "cooling": {
            "fan_speed_range": {
                "min": int(min([_safe_get_value(l) for l in fan_readings if _safe_get_value(l) is not None])) if fan_readings else None,
                "max": int(max([_safe_get_value(l) for l in fan_readings if _safe_get_value(l) is not None])) if fan_readings else None,
                "readings_count": len(fan_readings),
            },
            "recovery_activations_count": len(recovery_events),
            "cooling_struggling": len(recovery_events) >= 3,
        },
        "environmental": {
            "humidity_range": {
                "min": round(min(humidity_values), 1) if humidity_values else None,
                "max": round(max(humidity_values), 1) if humidity_values else None,
                "avg": round(sum(humidity_values) / len(humidity_values), 1) if humidity_values else None,
            },
        },
        "thermal": {
            "temp_range_observed": {
                "min": round(min_temp, 2) if min_temp is not None else None,
                "max": round(max_temp, 2) if max_temp is not None else None,
                "avg": round(avg_temp, 2) if avg_temp is not None else None,
                "safe_range": thresholds.safe_temp_range,
            },
            "excursions_count": len(excursions),
            "excursions_sample": excursions[:10],
            "excursions_exceed_threshold": len(excursions) > 0,
        },
    }


def _extract_operational_patterns(
    logs: List[LogEntry],
    duration_hours: float,
    thresholds: Thresholds,
) -> Dict[str, Any]:
    door_open_events = [l for l in logs if l.log_type == LogType.DOOR_OPEN]
    door_close_events = [l for l in logs if l.log_type == LogType.DOOR_CLOSE]
    alarm_events = [l for l in logs if l.log_type == LogType.ALARM_TRIGGERED]
    temp_warnings = [l for l in logs if l.log_type == LogType.TEMP_WARNING]
    sync_failures = [l for l in logs if l.log_type == LogType.TELEMETRY_SYNC_FAILED]
    
    door_open_count = len(door_open_events)
    door_close_count = len(door_close_events)
    
    door_events_per_hour = door_open_count / duration_hours if duration_hours > 0 else 0
    unclosed_doors = door_open_count > door_close_count
    
    suspicious_gaps = []
    sorted_logs = sorted(logs, key=lambda x: x.timestamp)
    
    for i, open_event in enumerate(door_open_events):
        next_close = None
        for close_event in door_close_events:
            if close_event.timestamp > open_event.timestamp:
                if next_close is None or close_event.timestamp < next_close.timestamp:
                    next_close = close_event
        
        if next_close:
            recovery_time = (next_close.timestamp - open_event.timestamp).total_seconds() / 60
            temp_after_door = []
            for temp in [l for l in sorted_logs if l.log_type == LogType.TEMP_READING]:
                if temp.timestamp > open_event.timestamp and temp.timestamp < next_close.timestamp:
                    val = _safe_get_value(temp)
                    if val is not None:
                        temp_after_door.append(val)
            
            if temp_after_door:
                max_after = max(temp_after_door)
                safe_max = thresholds.safe_temp_range[1]
                spike_detected = max_after > safe_max + 1.0
                
                if recovery_time > thresholds.max_recovery_min or spike_detected:
                    suspicious_gaps.append({
                        "door_open_time": open_event.timestamp.isoformat(),
                        "door_close_time": next_close.timestamp.isoformat(),
                        "recovery_time_min": round(recovery_time, 1),
                        "max_temp_after_open": round(max_after, 2) if temp_after_door else None,
                        "spike_detected": spike_detected,
                        "recovery_too_slow": recovery_time > thresholds.max_recovery_min,
                    })
    
    return {
        "door_events": {
            "open_count": door_open_count,
            "close_count": door_close_count,
            "unclosed_doors": unclosed_doors,
            "events_per_hour": round(door_events_per_hour, 1),
            "exceeds_threshold": door_events_per_hour > thresholds.max_door_events_per_hour,
        },
        "suspicious_patterns": {
            "door_recovery_issues_count": len(suspicious_gaps),
            "door_recovery_issues_sample": suspicious_gaps[:5],
            "has_pattern": len(suspicious_gaps) > 0,
            "message": f"Detected {len(suspicious_gaps)} instances where door opening correlated with slow recovery or temperature spike." if suspicious_gaps else "No suspicious door-temp correlation patterns detected.",
        },
        "alarms_and_warnings": {
            "alarm_count": len(alarm_events),
            "temp_warning_count": len(temp_warnings),
            "sync_failure_count": len(sync_failures),
        },
    }


def _build_timeline(
    logs: List[LogEntry],
    thresholds: Thresholds,
) -> List[Dict[str, Any]]:
    critical_types = [
        LogType.ALARM_TRIGGERED,
        LogType.SENSOR_TIMEOUT,
        LogType.TELEMETRY_SYNC_FAILED,
        LogType.COOLING_RECOVERY_START,
        LogType.TEMP_WARNING,
        LogType.DEVICE_START,
    ]
    
    sorted_logs = sorted(logs, key=lambda x: x.timestamp)
    
    critical_events = []
    for log in sorted_logs:
        if log.log_type in critical_types:
            critical_events.append({
                "time": log.timestamp.isoformat(),
                "type": log.log_type.value,
                "raw_value": log.raw_value,
                "sensor_id": log.sensor_id,
            })
    
    safe_min, safe_max = thresholds.safe_temp_range
    for log in sorted_logs:
        if log.log_type == LogType.TEMP_READING:
            val = _safe_get_value(log)
            if val is not None and (val < safe_min or val > safe_max):
                critical_events.append({
                    "time": log.timestamp.isoformat(),
                    "type": "TEMP_EXCURSION",
                    "value": round(val, 2),
                    "safe_range": [safe_min, safe_max],
                })
    
    critical_events.sort(key=lambda x: x.get("time", ""))
    
    return critical_events[:20]


def _extract_rule_findings(report: Optional[ComplianceReport]) -> List[Dict[str, Any]]:
    if report is None:
        return []
    
    findings = []
    for finding in report.findings or []:
        if not finding.passed:
            findings.append({
                "rule_id": finding.rule_id,
                "rule_description": finding.rule_description,
                "category": finding.category,
                "severity": finding.severity.value if hasattr(finding.severity, 'value') else str(finding.severity),
                "message": finding.message,
                "needs_visual_verification": getattr(finding, 'needs_visual_verification', False),
                "data_source": getattr(finding, 'data_source', None),
            })
    
    summary = {
        "device_id": report.device_id,
        "total_entries": report.total_entries,
        "passed_count": report.passed_count,
        "failed_count": report.failed_count,
        "critical_count": report.critical_count,
    }
    
    return [
        {"summary": summary},
        {"findings": findings},
    ]


def build_context_from_logs(
    logs: List[LogEntry],
    report: Optional[ComplianceReport] = None,
    thresholds: Thresholds = DEFAULT_THRESHOLDS,
) -> Dict[str, Any]:
    return build_analysis_context(logs=logs, report=report, thresholds=thresholds)


def build_context_from_chart(
    chart_result: ChartAnalysisResult,
    report: Optional[ComplianceReport] = None,
    thresholds: Thresholds = DEFAULT_THRESHOLDS,
) -> Dict[str, Any]:
    return build_analysis_context(chart_result=chart_result, report=report, thresholds=thresholds)
