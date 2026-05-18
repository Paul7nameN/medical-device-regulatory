from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

from app.models.findings import Severity, Finding, ComplianceReport, CategorySummary, Evidence
from app.ai.image.models import ChartViolation, ChartViolationType, TemperatureReading, ChartAnalysisResult


CHART_VIOLATION_MAPPINGS: Dict[str, Dict[str, Any]] = {
    "excursion": {
        "rule_id": "REG-TEMP-1",
        "category": "TEMP",
        "default_severity": Severity.HIGH,
    },
    "gap": {
        "rule_id": "REG-DATA-1",
        "category": "DATA",
        "default_severity": Severity.MEDIUM,
    },
    "slow_recovery": {
        "rule_id": "REG-TEMP-3",
        "category": "TEMP",
        "default_severity": Severity.HIGH,
    },
    "frequent_access": {
        "rule_id": "REG-OPS-2",
        "category": "OPS",
        "default_severity": Severity.LOW,
    },
}


def confidence_to_severity(confidence: float) -> Severity:
    if confidence > 0.8:
        return Severity.CRITICAL
    if confidence > 0.6:
        return Severity.HIGH
    if confidence > 0.3:
        return Severity.MEDIUM
    return Severity.LOW


def chart_violation_to_finding(
    violation: ChartViolation,
    parent_confidence: float = 0.5,
    parent_analyzed_at: Optional[datetime] = None,
) -> Finding:
    violation_type_value = violation.violation_type.value if isinstance(violation.violation_type, Enum) else str(violation.violation_type)
    
    mapping = CHART_VIOLATION_MAPPINGS.get(violation_type_value, {
        "rule_id": "REG-TEMP-1",
        "category": "TEMP",
        "default_severity": Severity.LOW,
    })
    
    violation_confidence = violation.confidence if violation.confidence is not None else parent_confidence
    severity = confidence_to_severity(violation_confidence)
    
    timestamp = parent_analyzed_at or datetime.utcnow()
    if violation.timestamp_start:
        timestamp = violation.timestamp_start
    elif violation.timestamp_end:
        timestamp = violation.timestamp_end
    
    description = violation.description or "Chart analysis violation"
    
    message = description
    if violation.extracted_value is not None:
        message = f"{description} (Value: {violation.extracted_value})"
    
    rule_description = f"[{violation_type_value.upper()}] {mapping['category']} violation from chart analysis"
    
    return Finding(
        rule_id=mapping["rule_id"],
        rule_description=rule_description,
        category=mapping["category"],
        severity=severity,
        passed=False,
        message=message,
        evidence=[],
        timestamp=timestamp,
        needs_visual_verification=True,
        data_source="images",
        confidence=violation_confidence,
    )


def convert_chart_violations_to_findings(
    violations: List[ChartViolation],
    parent_confidence: float = 0.5,
    parent_analyzed_at: Optional[datetime] = None,
) -> List[Finding]:
    return [
        chart_violation_to_finding(v, parent_confidence, parent_analyzed_at)
        for v in violations
    ]


def temperature_reading_to_dict(reading: TemperatureReading) -> Dict[str, Any]:
    timestamp: str
    if reading.timestamp:
        timestamp = reading.timestamp.isoformat()
    else:
        try:
            parsed_time = datetime.strptime(reading.time, "%H:%M")
            now = datetime.now()
            combined = now.replace(hour=parsed_time.hour, minute=parsed_time.minute, second=0, microsecond=0)
            timestamp = combined.isoformat()
        except ValueError:
            timestamp = datetime.utcnow().isoformat()
    
    result: Dict[str, Any] = {
        "timestamp": timestamp,
        "time": reading.time,
        "sensorA": reading.sensor_a,
        "source": reading.source or "chart_image",
    }
    
    if reading.sensor_b is not None:
        result["sensorB"] = reading.sensor_b
    
    return result


def convert_temperature_readings_to_data_points(
    readings: List[TemperatureReading]
) -> List[Dict[str, Any]]:
    points = [temperature_reading_to_dict(r) for r in readings]
    
    return sorted(
        points,
        key=lambda p: datetime.fromisoformat(p["timestamp"]) if p.get("timestamp") else datetime.min
    )


def create_compliance_report_from_chart_result(
    result: ChartAnalysisResult,
    device_id: str,
) -> ComplianceReport:
    findings = convert_chart_violations_to_findings(
        result.violations,
        parent_confidence=result.confidence,
        parent_analyzed_at=result.analyzed_at,
    )
    
    failed_count = len(findings)
    critical_count = sum(1 for f in findings if f.severity == Severity.CRITICAL)
    passed_count = 0
    
    total_entries = len(result.data_points) if result.data_points else 0
    
    categories: Dict[str, CategorySummary] = {}
    for finding in findings:
        cat = finding.category
        if cat not in categories:
            categories[cat] = CategorySummary(passed=0, failed=0, total=0)
        
        if finding.passed:
            categories[cat].passed += 1
        else:
            categories[cat].failed += 1
        categories[cat].total += 1
    
    return ComplianceReport(
        device_id=device_id,
        analyzed_at=result.analyzed_at,
        total_entries=total_entries,
        time_range_start=result.time_range_start,
        time_range_end=result.time_range_end,
        summary=categories,
        findings=findings,
        passed_count=passed_count,
        failed_count=failed_count,
        critical_count=critical_count,
    )
