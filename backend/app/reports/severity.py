from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models.findings import Severity, Finding


class SeverityClassifier:
    
    CRITICAL_TRIGGERS = {
        "REG-TEMP-1": {
            "condition": "violation_count > 3",
            "base_severity": Severity.HIGH,
            "upgrade_threshold": 3
        },
        "REG-TEMP-2": {
            "condition": "any_excursion_exceeds_5min OR cumulative_exceeds_10min",
            "base_severity": Severity.CRITICAL,
            "upgrade_threshold": 0
        },
        "REG-SENS-1": {
            "condition": "both_primary_and_secondary_timeout",
            "base_severity": Severity.HIGH,
            "upgrade_condition": "dual_failure"
        },
    }
    
    def classify(
        self,
        finding: Finding,
        context: Dict[str, Any]
    ) -> Severity:
        rule_id = finding.rule_id
        
        if rule_id == "REG-TEMP-1":
            violation_count = context.get("temp_violation_count", 0)
            if violation_count > 3:
                return Severity.CRITICAL
            return Severity.HIGH
        
        elif rule_id == "REG-TEMP-2":
            return Severity.CRITICAL
        
        elif rule_id == "REG-SENS-1":
            if context.get("dual_sensor_failure", False):
                return Severity.CRITICAL
            return Severity.HIGH
        
        elif rule_id == "REG-ALARM-1":
            return Severity.HIGH
        
        elif rule_id in ["REG-TEMP-3", "REG-SENS-3"]:
            return Severity.HIGH
        
        elif rule_id in ["REG-TEMP-4", "REG-DATA-2", "REG-ALARM-2", "REG-ALARM-3"]:
            return Severity.MEDIUM
        
        elif rule_id in ["REG-SENS-2"]:
            return Severity.INFO
        
        return finding.severity
    
    def get_critical_rules(self) -> List[str]:
        return ["REG-TEMP-1", "REG-TEMP-2", "REG-SENS-1", "REG-ALARM-1"]
    
    def is_critical_violation(
        self,
        finding: Finding,
        context: Dict[str, Any]
    ) -> bool:
        classified = self.classify(finding, context)
        return classified == Severity.CRITICAL
    
    def get_severity_order(self) -> List[Severity]:
        return [
            Severity.CRITICAL,
            Severity.HIGH,
            Severity.MEDIUM,
            Severity.LOW,
            Severity.INFO
        ]