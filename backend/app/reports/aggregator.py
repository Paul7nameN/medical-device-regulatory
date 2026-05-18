from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict
import logging

from app.models.logs import LogEntry
from app.models.findings import (
    Finding, ComplianceReport, Severity, CategorySummary
)
from app.reports.models import (
    AggregatedComplianceReport, ViolationSummary, TemporalAnalysis,
    TimelineEvent, CriticalPeriod, GapAnalysis, RecoveryInterval,
    AIEnhancements, Recommendation
)
from app.reports.severity import SeverityClassifier
from app.reports.temporal import build_temporal_analysis
from app.reports.recommendations import generate_recommendations

logger = logging.getLogger(__name__)


class ComplianceReportAggregator:
    
    def __init__(self):
        self.severity_classifier = SeverityClassifier()
    
    def aggregate(
        self,
        regulatory_report: ComplianceReport,
        logs: Optional[List[LogEntry]] = None,
        ai_chart_analysis: Optional[Dict[str, Any]] = None,
        ai_log_analysis: Optional[Dict[str, Any]] = None,
        ai_cross_validation: Optional[Dict[str, Any]] = None,
        include_raw_report: bool = False
    ) -> AggregatedComplianceReport:
        
        logger.info("Starting compliance report aggregation")
        
        logs = logs or []
        findings = regulatory_report.findings
        
        classification_context = self._build_classification_context(
            findings, logs
        )
        
        severity_counts = self._classify_findings(
            findings, classification_context
        )
        
        violations_by_rule = self._group_by_rule(
            findings, classification_context
        )
        
        temporal_analysis = self._perform_temporal_analysis(
            logs, findings, ai_chart_analysis
        )
        
        ai_enhancements = self._merge_ai_analysis(
            ai_chart_analysis, ai_log_analysis, ai_cross_validation
        )
        
        recommendations = generate_recommendations(
            violations_by_rule, temporal_analysis, ai_enhancements
        )
        
        summary = {
            "total_findings": len(findings),
            "passed_count": regulatory_report.passed_count,
            "failed_count": regulatory_report.failed_count,
            "critical_count": severity_counts.get(Severity.CRITICAL, 0),
            "high_count": severity_counts.get(Severity.HIGH, 0),
            "medium_count": severity_counts.get(Severity.MEDIUM, 0),
            "low_count": severity_counts.get(Severity.LOW, 0),
            "info_count": severity_counts.get(Severity.INFO, 0),
        }
        
        executive_summary = self._generate_executive_summary(
            summary, violations_by_rule, temporal_analysis
        )
        
        aggregated = AggregatedComplianceReport(
            device_id=regulatory_report.device_id,
            generated_at=datetime.now(),
            time_range_start=regulatory_report.time_range_start,
            time_range_end=regulatory_report.time_range_end,
            total_entries=regulatory_report.total_entries,
            total_rules_evaluated=len(regulatory_report.summary),
            summary=summary,
            violations_by_rule=violations_by_rule,
            violations_by_severity=self._group_by_severity(findings, classification_context),
            temporal_analysis=temporal_analysis,
            ai_enhancements=ai_enhancements,
            recommendations=recommendations,
            executive_summary=executive_summary,
            raw_regulatory_report=(
                self._report_to_dict(regulatory_report, include_findings=False)
                if include_raw_report else None
            )
        )
        
        logger.info(
            "Compliance report aggregation complete",
            extra={
                "device_id": aggregated.device_id,
                "critical_count": summary["critical_count"],
                "high_count": summary["high_count"],
                "recommendation_count": len(recommendations)
            }
        )
        
        return aggregated
    
    def _build_classification_context(
        self,
        findings: List[Finding],
        logs: List[LogEntry]
    ) -> Dict[str, Any]:
        
        context = {}
        
        temp_violations = [
            f for f in findings
            if f.rule_id == "REG-TEMP-1" and not f.passed
        ]
        context["temp_violation_count"] = len(temp_violations)
        
        sensor_timeouts = [
            f for f in findings
            if f.rule_id == "REG-SENS-1" and not f.passed
        ]
        context["dual_sensor_failure"] = any(
            "both" in f.message.lower() or 
            ("primary" in f.message.lower() and "secondary" in f.message.lower())
            for f in sensor_timeouts
        )
        
        return context
    
    def _classify_findings(
        self,
        findings: List[Finding],
        context: Dict[str, Any]
    ) -> Dict[Severity, int]:
        
        counts: Dict[Severity, int] = defaultdict(int)
        
        for finding in findings:
            if not finding.passed:
                severity = self.severity_classifier.classify(finding, context)
                counts[severity] += 1
        
        return dict(counts)
    
    def _group_by_rule(
        self,
        findings: List[Finding],
        context: Dict[str, Any]
    ) -> Dict[str, ViolationSummary]:
        
        grouped: Dict[str, List[Finding]] = defaultdict(list)
        
        for finding in findings:
            grouped[finding.rule_id].append(finding)
        
        result: Dict[str, ViolationSummary] = {}
        
        for rule_id, rule_findings in grouped.items():
            failed_findings = [f for f in rule_findings if not f.passed]
            passed_findings = [f for f in rule_findings if f.passed]
            
            if not failed_findings and passed_findings:
                continue
            
            sample = failed_findings[:3] if failed_findings else []
            
            timestamps = [
                f.timestamp for f in failed_findings
                if hasattr(f, 'timestamp') and f.timestamp
            ]
            
            result[rule_id] = ViolationSummary(
                rule_id=rule_id,
                rule_description=rule_findings[0].rule_description if rule_findings else "",
                category=rule_findings[0].category if rule_findings else "unknown",
                severity=self.severity_classifier.classify(
                    rule_findings[0], context
                ) if rule_findings else Severity.LOW,
                count=len(failed_findings),
                first_occurrence=min(timestamps) if timestamps else None,
                last_occurrence=max(timestamps) if timestamps else None,
                sample_findings=sample
            )
        
        return result
    
    def _group_by_severity(
        self,
        findings: List[Finding],
        context: Dict[str, Any]
    ) -> Dict[Severity, List[Finding]]:
        
        grouped: Dict[Severity, List[Finding]] = defaultdict(list)
        
        for finding in findings:
            if not finding.passed:
                severity = self.severity_classifier.classify(finding, context)
                grouped[severity].append(finding)
        
        return dict(grouped)
    
    def _perform_temporal_analysis(
        self,
        logs: List[LogEntry],
        findings: List[Finding],
        ai_chart_analysis: Optional[Dict[str, Any]]
    ) -> TemporalAnalysis:
        
        return build_temporal_analysis(logs, findings, ai_chart_analysis)
    
    def _merge_ai_analysis(
        self,
        chart_analysis: Optional[Dict[str, Any]],
        log_analysis: Optional[Dict[str, Any]],
        cross_validation: Optional[Dict[str, Any]]
    ) -> Optional[AIEnhancements]:
        
        if not any([chart_analysis, log_analysis, cross_validation]):
            return None
        
        enhancements = AIEnhancements()
        
        if chart_analysis:
            enhancements.chart_violations = chart_analysis.get("violations", [])
        
        if log_analysis:
            enhancements.log_insights = {
                "summary": log_analysis.get("summary", ""),
                "key_findings": log_analysis.get("key_findings", []),
                "recommendations": log_analysis.get("recommendations", []),
                "risk_assessment": log_analysis.get("risk_assessment", "low")
            }
        
        if cross_validation:
            enhancements.cross_validation_confidence = cross_validation.get(
                "confidence_score"
            )
        
        return enhancements
    
    def _generate_executive_summary(
        self,
        summary: Dict[str, Any],
        violations_by_rule: Dict[str, ViolationSummary],
        temporal_analysis: TemporalAnalysis
    ) -> str:
        
        critical_count = summary.get("critical_count", 0)
        high_count = summary.get("high_count", 0)
        
        if critical_count == 0 and high_count == 0:
            return (
                "All regulatory checks passed. No critical or high severity "
                "violations detected. Device operating within MED-THERM-2026 "
                "compliance parameters."
            )
        
        critical_rules = [
            vs.rule_id
            for vs in violations_by_rule.values()
            if vs.severity == Severity.CRITICAL
        ]
        
        high_rules = [
            vs.rule_id
            for vs in violations_by_rule.values()
            if vs.severity == Severity.HIGH
        ]
        
        parts = []
        
        if critical_count > 0:
            parts.append(
                f"CRITICAL: {critical_count} violation(s) detected in rules: "
                f"{', '.join(critical_rules)}. "
                "Immediate investigation required."
            )
        
        if high_count > 0:
            parts.append(
                f"HIGH: {high_count} violation(s) detected in rules: "
                f"{', '.join(high_rules)}. "
                "Prioritize for next maintenance window."
            )
        
        if temporal_analysis.critical_periods:
            period_count = len(temporal_analysis.critical_periods)
            parts.append(
                f"Identified {period_count} critical time period(s) with "
                "clustered violations. Review temporal analysis for details."
            )
        
        return " ".join(parts)
    
    def _report_to_dict(self, report: ComplianceReport, include_findings: bool = False) -> Dict[str, Any]:
        if hasattr(report, 'to_dict') and callable(getattr(report, 'to_dict', None)):
            try:
                result = report.to_dict(include_findings=include_findings)
                if isinstance(result, dict):
                    return result
            except Exception:
                pass
        
        device_id = getattr(report, 'device_id', 'unknown')
        analyzed_at = getattr(report, 'analyzed_at', None)
        total_entries = getattr(report, 'total_entries', 0)
        time_range_start = getattr(report, 'time_range_start', None)
        time_range_end = getattr(report, 'time_range_end', None)
        passed_count = getattr(report, 'passed_count', 0)
        failed_count = getattr(report, 'failed_count', 0)
        critical_count = getattr(report, 'critical_count', 0)
        summary = getattr(report, 'summary', {})
        findings = getattr(report, 'findings', [])
        
        summary_dict = {}
        for cat, summary_item in summary.items():
            summary_dict[cat] = {
                "passed": getattr(summary_item, 'passed', 0),
                "failed": getattr(summary_item, 'failed', 0),
                "total": getattr(summary_item, 'total', 0)
            }
        
        result = {
            "device_id": device_id,
            "analyzed_at": analyzed_at.isoformat() if analyzed_at else None,
            "total_entries": total_entries,
            "time_range_start": time_range_start.isoformat() if time_range_start else None,
            "time_range_end": time_range_end.isoformat() if time_range_end else None,
            "summary": summary_dict,
            "passed_count": passed_count,
            "failed_count": failed_count,
            "critical_count": critical_count
        }
        
        if include_findings:
            findings_dicts = []
            for finding in findings:
                evidence_dicts = []
                evidence_list = getattr(finding, 'evidence', [])
                for ev in evidence_list:
                    ev_ts = getattr(ev, 'timestamp', None)
                    evidence_dicts.append({
                        "entry_index": getattr(ev, 'entry_index', 0),
                        "timestamp": ev_ts.isoformat() if ev_ts else None,
                        "log_type": getattr(ev, 'log_type', None),
                        "raw_value": getattr(ev, 'raw_value', None),
                        "explanation": getattr(ev, 'explanation', None)
                    })
                
                severity = getattr(finding, 'severity', None)
                finding_ts = getattr(finding, 'timestamp', None)
                finding_dict = {
                    "rule_id": getattr(finding, 'rule_id', None),
                    "rule_description": getattr(finding, 'rule_description', None),
                    "category": getattr(finding, 'category', None),
                    "severity": severity.value if hasattr(severity, 'value') else str(severity),
                    "passed": getattr(finding, 'passed', False),
                    "message": getattr(finding, 'message', None),
                    "evidence": evidence_dicts,
                    "timestamp": finding_ts.isoformat() if finding_ts else None,
                    "remediation_hint": getattr(finding, 'remediation_hint', None),
                    "needs_visual_verification": getattr(finding, 'needs_visual_verification', False),
                    "data_source": getattr(finding, 'data_source', None),
                    "confidence": getattr(finding, 'confidence', None),
                    "inspection_hint": getattr(finding, 'inspection_hint', None)
                }
                findings_dicts.append(finding_dict)
            result["findings"] = findings_dicts
        
        return result


def aggregate_report(
    regulatory_report: ComplianceReport,
    logs: Optional[List[LogEntry]] = None,
    ai_chart_analysis: Optional[Dict[str, Any]] = None,
    ai_log_analysis: Optional[Dict[str, Any]] = None,
    ai_cross_validation: Optional[Dict[str, Any]] = None,
    include_raw_report: bool = False
) -> AggregatedComplianceReport:
    
    aggregator = ComplianceReportAggregator()
    return aggregator.aggregate(
        regulatory_report=regulatory_report,
        logs=logs,
        ai_chart_analysis=ai_chart_analysis,
        ai_log_analysis=ai_log_analysis,
        ai_cross_validation=ai_cross_validation,
        include_raw_report=include_raw_report
    )
