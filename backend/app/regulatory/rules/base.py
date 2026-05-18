from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Type
from datetime import datetime
from enum import Enum

from app.models.logs import LogEntry
from app.models.findings import Finding, Severity, Evidence


class ValidationSource(Enum):
    LOGS = "logs"
    IMAGES = "images"
    INSPECTION = "inspection"
    COMBINED = "combined"


class BaseRule(ABC):
    rule_id: str
    description: str
    category: str
    default_severity: Severity
    data_source: ValidationSource = ValidationSource.LOGS
    confidence: float = 1.0
    inspection_hint: Optional[str] = None

    @abstractmethod
    def validate(self, logs: List[LogEntry], context: Dict[str, Any]) -> List[Finding]:
        pass

    def create_finding(
        self,
        passed: bool,
        message: str,
        evidence_logs: Optional[List[LogEntry]] = None,
        severity: Optional[Severity] = None,
        remediation_hint: Optional[str] = None,
        needs_visual_verification: bool = False
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

        return Finding(
            rule_id=self.rule_id,
            rule_description=self.description,
            category=self.category,
            severity=severity or self.default_severity,
            passed=passed,
            message=message,
            evidence=evidence,
            timestamp=datetime.now(),
            remediation_hint=remediation_hint,
            needs_visual_verification=needs_visual_verification,
            data_source=self.data_source.value if hasattr(self.data_source, 'value') else self.data_source,
            confidence=self.confidence,
            inspection_hint=self.inspection_hint
        )

    def create_pass_finding(self, message: Optional[str] = None) -> Finding:
        msg = message or f"Rule {self.rule_id} passed: {self.description}"
        return self.create_finding(
            passed=True,
            message=msg
        )

    def create_info_finding(self, message: str, needs_visual: bool = False) -> Finding:
        return self.create_finding(
            passed=True,
            message=message,
            severity=Severity.INFO,
            needs_visual_verification=needs_visual
        )


class RuleRegistry:
    _rules: Dict[str, Type[BaseRule]] = {}
    _by_category: Dict[str, List[str]] = {}

    @classmethod
    def register(cls, rule_class: Type[BaseRule]) -> None:
        cls._rules[rule_class.rule_id] = rule_class

        if rule_class.category not in cls._by_category:
            cls._by_category[rule_class.category] = []
        if rule_class.rule_id not in cls._by_category[rule_class.category]:
            cls._by_category[rule_class.category].append(rule_class.rule_id)

    @classmethod
    def get(cls, rule_id: str) -> Optional[Type[BaseRule]]:
        return cls._rules.get(rule_id)

    @classmethod
    def get_all(cls) -> List[Type[BaseRule]]:
        return list(cls._rules.values())

    @classmethod
    def get_by_category(cls, category: str) -> List[Type[BaseRule]]:
        rule_ids = cls._by_category.get(category, [])
        return [cls._rules[rid] for rid in rule_ids if rid in cls._rules]

    @classmethod
    def get_categories(cls) -> List[str]:
        return list(cls._by_category.keys())

    @classmethod
    def get_by_source(cls, source: ValidationSource) -> List[Type[BaseRule]]:
        return [
            rule for rule in cls._rules.values()
            if rule.data_source == source
        ]

    @classmethod
    def get_sources(cls) -> List[ValidationSource]:
        sources = set()
        for rule in cls._rules.values():
            sources.add(rule.data_source)
        return list(sources)

    @classmethod
    def clear(cls) -> None:
        cls._rules = {}
        cls._by_category = {}


def register_rule(cls: Type[BaseRule]) -> Type[BaseRule]:
    RuleRegistry.register(cls)
    return cls
