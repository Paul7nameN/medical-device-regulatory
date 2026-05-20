from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from app.models.logs import LogEntry, LogType
from app.models.findings import Finding, Severity, Evidence
from app.models.dynamic_rules import (
    ExtractedRule,
    RuleType,
    RuleThresholds,
    DataSource,
)


CONFIDENCE_THRESHOLD_AUTO_EXECUTE = 0.7


def get_severity_enum(severity_str: str) -> Severity:
    mapping = {
        "critical": Severity.CRITICAL,
        "high": Severity.HIGH,
        "medium": Severity.MEDIUM,
        "low": Severity.LOW,
        "info": Severity.INFO,
    }
    return mapping.get(severity_str.lower(), Severity.MEDIUM)


class DynamicRuleEvaluator:
    def __init__(self):
        self._handlers = {
            RuleType.THRESHOLD_RANGE: self._handle_threshold_range,
            RuleType.DURATION_LIMIT: self._handle_duration_limit,
            RuleType.FREQUENCY_LIMIT: self._handle_frequency_limit,
            RuleType.PRESENCE_CHECK: self._handle_presence_check,
            RuleType.INSPECTION_ONLY: self._handle_inspection_only,
        }

    def validate(
        self,
        rule: ExtractedRule,
        logs: List[LogEntry],
        context: Dict[str, Any]
    ) -> List[Finding]:
        if not rule.is_auto_executable:
            return [self._create_needs_review_finding(rule)]

        handler = self._handlers.get(rule.type)
        if not handler:
            return [self._create_unsupported_type_finding(rule)]

        try:
            return handler(rule, logs, context)
        except Exception as e:
            return [self._create_execution_error_finding(rule, str(e))]

    def validate_all(
        self,
        rules: List[ExtractedRule],
        logs: List[LogEntry],
        context: Dict[str, Any]
    ) -> List[Finding]:
        all_findings: List[Finding] = []
        
        for rule in rules:
            findings = self.validate(rule, logs, context)
            all_findings.extend(findings)
        
        return all_findings

    def _create_finding(
        self,
        rule: ExtractedRule,
        passed: bool,
        message: str,
        evidence_logs: Optional[List[LogEntry]] = None,
        severity_override: Optional[Severity] = None,
        needs_visual_verification: bool = False,
    ) -> Finding:
        evidence = []
        if evidence_logs:
            for i, log in enumerate(evidence_logs[:10]):
                evidence.append(Evidence(
                    entry_index=i,
                    timestamp=log.timestamp,
                    log_type=log.log_type.value if hasattr(log.log_type, 'value') else str(log.log_type),
                    raw_value=log.raw_value,
                    explanation=f"Log entry: {log.raw_value}"
                ))

        severity = severity_override if severity_override else get_severity_enum(rule.severity.value if hasattr(rule.severity, 'value') else str(rule.severity))

        return Finding(
            rule_id=rule.id,
            rule_description=rule.description,
            category=rule.category,
            severity=severity,
            passed=passed,
            message=message,
            evidence=evidence,
            timestamp=datetime.now(),
            remediation_hint=rule.extraction_notes,
            needs_visual_verification=needs_visual_verification,
            data_source=rule.data_source.value if hasattr(rule.data_source, 'value') else str(rule.data_source),
            confidence=rule.confidence,
            inspection_hint=rule.inspection_hint,
        )

    def _create_needs_review_finding(self, rule: ExtractedRule) -> Finding:
        if rule.type == RuleType.INSPECTION_ONLY:
            return self._create_finding(
                rule=rule,
                passed=True,
                message=f"[Inspection Required] {rule.description}",
                severity_override=Severity.INFO,
                needs_visual_verification=True,
            )
        
        return self._create_finding(
            rule=rule,
            passed=True,
            message=f"[Needs Review] Rule has low confidence ({rule.confidence:.2f} < 0.7) and requires manual validation: {rule.description}",
            severity_override=Severity.LOW,
            needs_visual_verification=True,
        )

    def _create_unsupported_type_finding(self, rule: ExtractedRule) -> Finding:
        return self._create_finding(
            rule=rule,
            passed=False,
            message=f"Unsupported rule type: {rule.type}. Cannot validate automatically.",
            severity_override=Severity.MEDIUM,
        )

    def _create_execution_error_finding(self, rule: ExtractedRule, error: str) -> Finding:
        return self._create_finding(
            rule=rule,
            passed=False,
            message=f"Rule execution error: {error}",
            severity_override=Severity.MEDIUM,
        )

    def _get_field_logs(
        self,
        rule: ExtractedRule,
        logs: List[LogEntry]
    ) -> Tuple[List[LogEntry], str]:
        thresholds = rule.thresholds or RuleThresholds()
        field = thresholds.field or "temperature"
        
        field_lower = field.lower()
        
        if "temp" in field_lower:
            log_type = LogType.TEMP_READING
        elif "door" in field_lower:
            log_type = LogType.DOOR_OPEN
        elif "fan" in field_lower:
            log_type = LogType.FAN_SPEED
        elif "voltage" in field_lower or "power" in field_lower:
            log_type = LogType.VOLTAGE
        elif "humidity" in field_lower:
            log_type = LogType.HUMIDITY
        elif "battery" in field_lower:
            log_type = LogType.BATTERY_LEVEL
        elif "alarm" in field_lower:
            log_type = LogType.ALARM_TRIGGERED
        elif "sensor" in field_lower and "timeout" in field_lower:
            log_type = LogType.SENSOR_TIMEOUT
        elif "sync" in field_lower:
            log_type = LogType.TELEMETRY_SYNC_FAILED
        else:
            log_type = LogType.TEMP_READING
        
        filtered = [
            log for log in logs
            if log.log_type == log_type and log.parsed_value is not None
        ]
        
        return filtered, field

    def _handle_threshold_range(
        self,
        rule: ExtractedRule,
        logs: List[LogEntry],
        context: Dict[str, Any]
    ) -> List[Finding]:
        thresholds = rule.thresholds or RuleThresholds()
        min_val = thresholds.min
        max_val = thresholds.max
        
        field_logs, field_name = self._get_field_logs(rule, logs)
        
        if not field_logs:
            return [self._create_finding(
                rule=rule,
                passed=False,
                message=f"No {field_name} readings found - cannot validate {rule.id}",
                severity_override=Severity.MEDIUM,
            )]
        
        if min_val is None and max_val is None:
            return [self._create_finding(
                rule=rule,
                passed=False,
                message=f"No thresholds defined for rule {rule.id}",
                severity_override=Severity.MEDIUM,
            )]
        
        violations = []
        for log in field_logs:
            val = log.parsed_value
            if isinstance(val, (int, float)):
                is_violation = False
                if min_val is not None and val < min_val:
                    is_violation = True
                if max_val is not None and val > max_val:
                    is_violation = True
                if is_violation:
                    violations.append(log)
        
        if not violations:
            range_str = ""
            if min_val is not None:
                range_str += f"≥{min_val}"
            if max_val is not None:
                if range_str:
                    range_str += ", "
                range_str += f"≤{max_val}"
            if thresholds.unit:
                range_str += f" {thresholds.unit}"
            
            return [self._create_finding(
                rule=rule,
                passed=True,
                message=f"All {len(field_logs)} {field_name} readings within valid range [{range_str}]",
            )]
        
        violation_count = len(violations)
        
        if violation_count > len(field_logs) * 0.5:
            severity = Severity.CRITICAL
        elif violation_count > 3:
            severity = Severity.HIGH
        else:
            severity = None
        
        range_str = ""
        if min_val is not None:
            range_str += f"min={min_val}"
        if max_val is not None:
            if range_str:
                range_str += ", "
            range_str += f"max={max_val}"
        
        return [self._create_finding(
            rule=rule,
            passed=False,
            message=f"Found {violation_count} {field_name} reading(s) outside threshold ({range_str})",
            evidence_logs=violations,
            severity_override=severity,
        )]

    def _handle_duration_limit(
        self,
        rule: ExtractedRule,
        logs: List[LogEntry],
        context: Dict[str, Any]
    ) -> List[Finding]:
        thresholds = rule.thresholds or RuleThresholds()
        max_duration = thresholds.max_duration_seconds
        
        if max_duration is None:
            return [self._create_finding(
                rule=rule,
                passed=False,
                message=f"No duration threshold defined for rule {rule.id}",
                severity_override=Severity.MEDIUM,
            )]
        
        field_logs, field_name = self._get_field_logs(rule, logs)
        
        if len(field_logs) < 2:
            return [self._create_finding(
                rule=rule,
                passed=False,
                message=f"Insufficient {field_name} readings to analyze duration patterns",
                severity_override=Severity.LOW,
            )]
        
        min_val = thresholds.min
        max_val = thresholds.max
        
        sorted_logs = sorted(field_logs, key=lambda x: x.timestamp)
        
        excursion_events = []
        current_excursion: List[LogEntry] = []
        max_excursion_duration = timedelta(0)
        violation_logs: List[LogEntry] = []
        cumulative_violating_duration = timedelta(0)
        
        for log in sorted_logs:
            val = log.parsed_value
            in_range = True
            
            if isinstance(val, (int, float)):
                if min_val is not None and val < min_val:
                    in_range = False
                if max_val is not None and val > max_val:
                    in_range = False
            else:
                continue
            
            if not in_range:
                current_excursion.append(log)
            else:
                if current_excursion:
                    duration = current_excursion[-1].timestamp - current_excursion[0].timestamp
                    if duration > max_excursion_duration:
                        max_excursion_duration = duration
                    
                    if duration.total_seconds() > max_duration:
                        excursion_events.append({
                            "start": current_excursion[0].timestamp,
                            "end": current_excursion[-1].timestamp,
                            "duration": duration,
                        })
                        cumulative_violating_duration += duration
                        violation_logs.extend(current_excursion)
                    
                    current_excursion = []
        
        if current_excursion:
            duration = current_excursion[-1].timestamp - current_excursion[0].timestamp
            if duration > max_excursion_duration:
                max_excursion_duration = duration
            
            if duration.total_seconds() > max_duration:
                excursion_events.append({
                    "start": current_excursion[0].timestamp,
                    "end": current_excursion[-1].timestamp,
                    "duration": duration,
                })
                cumulative_violating_duration += duration
                violation_logs.extend(current_excursion)
        
        if not excursion_events:
            return [self._create_finding(
                rule=rule,
                passed=True,
                message=f"No {field_name} excursions exceeding {max_duration}s limit detected. "
                       f"Max observed: {max_excursion_duration.total_seconds():.1f}s",
            )]
        
        return [self._create_finding(
            rule=rule,
            passed=False,
            message=f"Found {len(excursion_events)} {field_name} excursion(s) exceeding {max_duration}s limit. "
                   f"Max: {max_excursion_duration.total_seconds():.1f}s, "
                   f"Cumulative violating: {cumulative_violating_duration.total_seconds():.1f}s",
            evidence_logs=violation_logs[:10],
            severity_override=Severity.HIGH,
        )]

    def _handle_frequency_limit(
        self,
        rule: ExtractedRule,
        logs: List[LogEntry],
        context: Dict[str, Any]
    ) -> List[Finding]:
        thresholds = rule.thresholds or RuleThresholds()
        max_count = thresholds.max_count
        time_window = thresholds.time_window_seconds
        
        if max_count is None:
            return [self._create_finding(
                rule=rule,
                passed=False,
                message=f"No frequency threshold (max_count) defined for rule {rule.id}",
                severity_override=Severity.MEDIUM,
            )]
        
        field_logs, field_name = self._get_field_logs(rule, logs)
        
        if not field_logs:
            return [self._create_finding(
                rule=rule,
                passed=True,
                message=f"No {field_name} events to analyze",
            )]
        
        sorted_logs = sorted(field_logs, key=lambda x: x.timestamp)
        
        violations = []
        violation_logs: List[LogEntry] = []
        
        if time_window:
            for i, event in enumerate(sorted_logs):
                window_end = event.timestamp + timedelta(seconds=time_window)
                count_in_window = 1
                
                for j in range(i + 1, len(sorted_logs)):
                    if sorted_logs[j].timestamp <= window_end:
                        count_in_window += 1
                    else:
                        break
                
                if count_in_window > max_count:
                    violations.append({
                        "window_start": event.timestamp,
                        "window_end": window_end,
                        "count": count_in_window,
                    })
                    if event not in violation_logs:
                        violation_logs.append(event)
        else:
            total_count = len(sorted_logs)
            if total_count > max_count:
                violations.append({
                    "count": total_count,
                    "max_allowed": max_count,
                })
                violation_logs = sorted_logs[:5]
        
        if not violations:
            window_str = f" in {time_window}s window" if time_window else ""
            return [self._create_finding(
                rule=rule,
                passed=True,
                message=f"{field_name} event frequency within limit: {len(sorted_logs)} events "
                       f"(max {max_count}{window_str})",
            )]
        
        window_str = f" per {time_window}s window" if time_window else ""
        return [self._create_finding(
            rule=rule,
            passed=False,
            message=f"{field_name} event frequency exceeded: max {max_count} allowed{window_str}, "
                   f"found {len(violations)} violation window(s)",
            evidence_logs=violation_logs[:5],
        )]

    def _handle_presence_check(
        self,
        rule: ExtractedRule,
        logs: List[LogEntry],
        context: Dict[str, Any]
    ) -> List[Finding]:
        thresholds = rule.thresholds or RuleThresholds()
        required_state = thresholds.required_state
        field = thresholds.field or "sensor"
        
        field_lower = field.lower()
        
        if "sensor" in field_lower:
            primary_available = context.get("sensor_availability", {}).get("primary", True)
            secondary_available = context.get("sensor_availability", {}).get("secondary", True)
            
            if "redundant" in rule.description.lower() or "dual" in rule.description.lower():
                if primary_available and secondary_available:
                    return [self._create_finding(
                        rule=rule,
                        passed=True,
                        message=f"Sensor redundancy verified: both PRIMARY and SECONDARY sensors available",
                    )]
                else:
                    missing = []
                    if not primary_available:
                        missing.append("PRIMARY")
                    if not secondary_available:
                        missing.append("SECONDARY")
                    return [self._create_finding(
                        rule=rule,
                        passed=False,
                        message=f"Sensor redundancy failure: {', '.join(missing)} sensor unavailable",
                        severity_override=Severity.CRITICAL,
                    )]
            
            if primary_available:
                return [self._create_finding(
                    rule=rule,
                    passed=True,
                    message=f"Sensor presence verified: PRIMARY sensor available",
                )]
            else:
                return [self._create_finding(
                    rule=rule,
                    passed=False,
                    message=f"Sensor unavailable: PRIMARY sensor timeout detected",
                    severity_override=Severity.HIGH,
                )]
        
        if "door" in field_lower:
            door_events = context.get("door_open_count", 0)
            if required_state and "close" in required_state.lower():
                return [self._create_finding(
                    rule=rule,
                    passed=True,
                    message=f"Door state check: {door_events} door open event(s) detected",
                )]
        
        field_logs, _ = self._get_field_logs(rule, logs)
        
        if field_logs:
            return [self._create_finding(
                rule=rule,
                passed=True,
                message=f"Presence verified: {len(field_logs)} {field} reading(s) found",
            )]
        
        return [self._create_finding(
            rule=rule,
            passed=False,
            message=f"Presence check failed: no {field} readings found",
        )]

    def _handle_inspection_only(
        self,
        rule: ExtractedRule,
        logs: List[LogEntry],
        context: Dict[str, Any]
    ) -> List[Finding]:
        return [self._create_finding(
            rule=rule,
            passed=True,
            message=f"[Inspection Required] {rule.description}",
            severity_override=Severity.INFO,
            needs_visual_verification=True,
        )]


def filter_executable_rules(rules: List[ExtractedRule]) -> Tuple[List[ExtractedRule], List[ExtractedRule]]:
    executable: List[ExtractedRule] = []
    needs_review: List[ExtractedRule] = []
    
    for rule in rules:
        if rule.is_auto_executable:
            executable.append(rule)
        else:
            needs_review.append(rule)
    
    return executable, needs_review
