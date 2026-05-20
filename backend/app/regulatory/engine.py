from typing import List, Dict, Any, Optional, Type, Union, Tuple
from datetime import datetime
from collections import defaultdict

from app.models.logs import LogEntry
from app.models.findings import Finding, ComplianceReport, CategorySummary, Severity
from app.regulatory.rules.base import RuleRegistry, BaseRule, ValidationSource
from app.regulatory.normalizer import LogNormalizer

try:
    from app.models.dynamic_rules import ExtractedRule
    from app.regulatory.dynamic_evaluator import (
        DynamicRuleEvaluator,
        filter_executable_rules,
        CONFIDENCE_THRESHOLD_AUTO_EXECUTE,
    )
    DYNAMIC_EVALUATOR_AVAILABLE = True
except ImportError:
    DYNAMIC_EVALUATOR_AVAILABLE = False
    ExtractedRule = Any


class RegulatoryEngine:
    RULE_ORDER = [
        "TEMP",
        "SENS",
        "ALARM",
        "DATA",
        "POWER",
        "COOL",
        "INS",
        "OPS"
    ]

    def __init__(self):
        self.normalizer = LogNormalizer()

    def validate(
        self,
        logs: List[LogEntry],
        filter_rules: Optional[List[str]] = None,
        device_id: str = "unknown",
        include_sources: Optional[List[Union[ValidationSource, str]]] = None,
        exclude_sources: Optional[List[Union[ValidationSource, str]]] = None,
        rule_set: Optional[List[ExtractedRule]] = None,
        merge_with_default: bool = False,
    ) -> ComplianceReport:
        if not logs:
            return self._create_empty_report(device_id)

        def to_source_enum(s: Union[ValidationSource, str]) -> ValidationSource:
            if isinstance(s, ValidationSource):
                return s
            return ValidationSource(s)

        include_sources_enum: Optional[List[ValidationSource]] = None
        exclude_sources_enum: Optional[List[ValidationSource]] = None

        if include_sources:
            include_sources_enum = [to_source_enum(s) for s in include_sources]
        if exclude_sources:
            exclude_sources_enum = [to_source_enum(s) for s in exclude_sources]

        normalizer_result = self.normalizer.normalize(logs)
        sorted_logs = normalizer_result["sorted_logs"]
        context = normalizer_result["context"]

        all_findings: List[Finding] = []

        use_default_rules = True
        if rule_set is not None and DYNAMIC_EVALUATOR_AVAILABLE:
            use_default_rules = merge_with_default
            dynamic_findings = self._validate_with_dynamic_rules(
                rule_set, sorted_logs, context
            )
            all_findings.extend(dynamic_findings)

        if use_default_rules:
            for category in self.RULE_ORDER:
                rules = RuleRegistry.get_by_category(category)

                for rule_class in rules:
                    if filter_rules and rule_class.rule_id not in filter_rules:
                        continue

                    if include_sources_enum and rule_class.data_source not in include_sources_enum:
                        continue

                    if exclude_sources_enum and rule_class.data_source in exclude_sources_enum:
                        continue

                    rule_instance = rule_class()
                    try:
                        findings = rule_instance.validate(sorted_logs, context)
                        all_findings.extend(findings)
                    except Exception as e:
                        error_finding = Finding(
                            rule_id=rule_class.rule_id,
                            rule_description=rule_class.description,
                            category=category,
                            severity=Severity.MEDIUM,
                            passed=False,
                            message=f"Rule execution error: {str(e)}",
                            evidence=[],
                            timestamp=datetime.now()
                        )
                        all_findings.append(error_finding)

        return self._create_report(
            findings=all_findings,
            logs=sorted_logs,
            context=context,
            device_id=device_id
        )

    def _validate_with_dynamic_rules(
        self,
        rule_set: List[ExtractedRule],
        logs: List[LogEntry],
        context: Dict[str, Any]
    ) -> List[Finding]:
        if not DYNAMIC_EVALUATOR_AVAILABLE:
            return []
        
        evaluator = DynamicRuleEvaluator()
        
        executable, needs_review = filter_executable_rules(rule_set)
        
        all_findings: List[Finding] = []
        
        for rule in executable:
            try:
                findings = evaluator.validate(rule, logs, context)
                all_findings.extend(findings)
            except Exception as e:
                error_finding = Finding(
                    rule_id=rule.id,
                    rule_description=rule.description,
                    category=rule.category,
                    severity=Severity.MEDIUM,
                    passed=False,
                    message=f"Dynamic rule execution error: {str(e)}",
                    evidence=[],
                    timestamp=datetime.now(),
                    confidence=rule.confidence,
                )
                all_findings.append(error_finding)
        
        for rule in needs_review:
            findings = evaluator.validate(rule, logs, context)
            all_findings.extend(findings)
        
        return all_findings

    def _create_empty_report(self, device_id: str) -> ComplianceReport:
        return ComplianceReport(
            device_id=device_id,
            analyzed_at=datetime.now(),
            total_entries=0,
            time_range_start=None,
            time_range_end=None,
            summary={},
            findings=[],
            passed_count=0,
            failed_count=0,
            critical_count=0
        )

    def _create_report(
        self,
        findings: List[Finding],
        logs: List[LogEntry],
        context: Dict[str, Any],
        device_id: str
    ) -> ComplianceReport:
        passed_count = sum(1 for f in findings if f.passed)
        failed_count = sum(1 for f in findings if not f.passed)
        critical_count = sum(
            1 for f in findings
            if not f.passed and f.severity == Severity.CRITICAL
        )

        summary: Dict[str, CategorySummary] = {}

        for category in self.RULE_ORDER:
            category_findings = [f for f in findings if f.category == category]
            if category_findings:
                cat_passed = sum(1 for f in category_findings if f.passed)
                cat_failed = len(category_findings) - cat_passed
                summary[category] = CategorySummary(
                    passed=cat_passed,
                    failed=cat_failed,
                    total=len(category_findings)
                )

        time_start = context.get("time_range_start")
        time_end = context.get("time_range_end")

        return ComplianceReport(
            device_id=device_id,
            analyzed_at=datetime.now(),
            total_entries=len(logs),
            time_range_start=time_start,
            time_range_end=time_end,
            summary=summary,
            findings=findings,
            passed_count=passed_count,
            failed_count=failed_count,
            critical_count=critical_count
        )

    def get_rule_info(self, rule_id: str) -> Optional[Dict[str, Any]]:
        rule_class = RuleRegistry.get(rule_id)
        if not rule_class:
            return None

        return {
            "rule_id": rule_class.rule_id,
            "description": rule_class.description,
            "category": rule_class.category,
            "default_severity": rule_class.default_severity.value,
            "data_source": rule_class.data_source.value,
            "confidence": rule_class.confidence,
            "inspection_hint": rule_class.inspection_hint
        }

    def get_all_rules(self) -> List[Dict[str, Any]]:
        rules = RuleRegistry.get_all()
        return [
            {
                "rule_id": r.rule_id,
                "description": r.description,
                "category": r.category,
                "default_severity": r.default_severity.value,
                "data_source": r.data_source.value,
                "confidence": r.confidence,
                "inspection_hint": r.inspection_hint
            }
            for r in rules
        ]

    def get_categories(self) -> List[str]:
        return self.RULE_ORDER

    def get_sources(self) -> List[str]:
        sources = RuleRegistry.get_sources()
        return [s.value for s in sources]


def validate_logs(
    logs: List[LogEntry],
    filter_rules: Optional[List[str]] = None,
    device_id: str = "unknown",
    include_sources: Optional[List[Union[ValidationSource, str]]] = None,
    exclude_sources: Optional[List[Union[ValidationSource, str]]] = None,
    rule_set: Optional[List[ExtractedRule]] = None,
    merge_with_default: bool = False,
) -> ComplianceReport:
    engine = RegulatoryEngine()
    return engine.validate(
        logs, filter_rules, device_id, include_sources, exclude_sources,
        rule_set=rule_set, merge_with_default=merge_with_default
    )
