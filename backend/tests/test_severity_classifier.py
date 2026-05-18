import pytest
from datetime import datetime
from unittest.mock import MagicMock

from app.reports.severity import SeverityClassifier
from app.models.findings import Severity, Finding


class TestSeverityClassifier:
    def test_init(self):
        classifier = SeverityClassifier()
        assert classifier is not None
    
    def test_get_critical_rules(self):
        classifier = SeverityClassifier()
        rules = classifier.get_critical_rules()
        assert "REG-TEMP-1" in rules
        assert "REG-TEMP-2" in rules
        assert "REG-SENS-1" in rules
        assert "REG-ALARM-1" in rules
    
    def test_classify_reg_temp2_always_critical(self):
        classifier = SeverityClassifier()
        finding = MagicMock(spec=Finding)
        finding.rule_id = "REG-TEMP-2"
        finding.severity = Severity.HIGH
        
        severity = classifier.classify(finding, {})
        assert severity == Severity.CRITICAL
    
    def test_classify_reg_temp1_few_violations_high(self):
        classifier = SeverityClassifier()
        finding = MagicMock(spec=Finding)
        finding.rule_id = "REG-TEMP-1"
        finding.severity = Severity.HIGH
        
        severity = classifier.classify(finding, {"temp_violation_count": 1})
        assert severity == Severity.HIGH
        
        severity = classifier.classify(finding, {"temp_violation_count": 3})
        assert severity == Severity.HIGH
    
    def test_classify_reg_temp1_many_violations_critical(self):
        classifier = SeverityClassifier()
        finding = MagicMock(spec=Finding)
        finding.rule_id = "REG-TEMP-1"
        finding.severity = Severity.HIGH
        
        severity = classifier.classify(finding, {"temp_violation_count": 4})
        assert severity == Severity.CRITICAL
        
        severity = classifier.classify(finding, {"temp_violation_count": 10})
        assert severity == Severity.CRITICAL
    
    def test_classify_reg_sens1_single_failure_high(self):
        classifier = SeverityClassifier()
        finding = MagicMock(spec=Finding)
        finding.rule_id = "REG-SENS-1"
        finding.severity = Severity.HIGH
        
        severity = classifier.classify(finding, {"dual_sensor_failure": False})
        assert severity == Severity.HIGH
    
    def test_classify_reg_sens1_dual_failure_critical(self):
        classifier = SeverityClassifier()
        finding = MagicMock(spec=Finding)
        finding.rule_id = "REG-SENS-1"
        finding.severity = Severity.HIGH
        
        severity = classifier.classify(finding, {"dual_sensor_failure": True})
        assert severity == Severity.CRITICAL
    
    def test_classify_reg_alarm1_always_high(self):
        classifier = SeverityClassifier()
        finding = MagicMock(spec=Finding)
        finding.rule_id = "REG-ALARM-1"
        finding.severity = Severity.MEDIUM
        
        severity = classifier.classify(finding, {})
        assert severity == Severity.HIGH
    
    def test_classify_reg_temp3_always_high(self):
        classifier = SeverityClassifier()
        finding = MagicMock(spec=Finding)
        finding.rule_id = "REG-TEMP-3"
        finding.severity = Severity.MEDIUM
        
        severity = classifier.classify(finding, {})
        assert severity == Severity.HIGH
    
    def test_classify_reg_sens3_always_high(self):
        classifier = SeverityClassifier()
        finding = MagicMock(spec=Finding)
        finding.rule_id = "REG-SENS-3"
        finding.severity = Severity.MEDIUM
        
        severity = classifier.classify(finding, {})
        assert severity == Severity.HIGH
    
    def test_classify_reg_temp4_always_medium(self):
        classifier = SeverityClassifier()
        finding = MagicMock(spec=Finding)
        finding.rule_id = "REG-TEMP-4"
        finding.severity = Severity.HIGH
        
        severity = classifier.classify(finding, {})
        assert severity == Severity.MEDIUM
    
    def test_classify_reg_data2_always_medium(self):
        classifier = SeverityClassifier()
        finding = MagicMock(spec=Finding)
        finding.rule_id = "REG-DATA-2"
        finding.severity = Severity.HIGH
        
        severity = classifier.classify(finding, {})
        assert severity == Severity.MEDIUM
    
    def test_classify_reg_alarm2_always_medium(self):
        classifier = SeverityClassifier()
        finding = MagicMock(spec=Finding)
        finding.rule_id = "REG-ALARM-2"
        finding.severity = Severity.HIGH
        
        severity = classifier.classify(finding, {})
        assert severity == Severity.MEDIUM
    
    def test_classify_reg_alarm3_always_medium(self):
        classifier = SeverityClassifier()
        finding = MagicMock(spec=Finding)
        finding.rule_id = "REG-ALARM-3"
        finding.severity = Severity.HIGH
        
        severity = classifier.classify(finding, {})
        assert severity == Severity.MEDIUM
    
    def test_classify_reg_sens2_always_info(self):
        classifier = SeverityClassifier()
        finding = MagicMock(spec=Finding)
        finding.rule_id = "REG-SENS-2"
        finding.severity = Severity.HIGH
        
        severity = classifier.classify(finding, {})
        assert severity == Severity.INFO
    
    def test_classify_unknown_rule_uses_finding_severity(self):
        classifier = SeverityClassifier()
        finding = MagicMock(spec=Finding)
        finding.rule_id = "REG-UNKNOWN-999"
        finding.severity = Severity.LOW
        
        severity = classifier.classify(finding, {})
        assert severity == Severity.LOW
    
    def test_is_critical_violation_true(self):
        classifier = SeverityClassifier()
        finding = MagicMock(spec=Finding)
        finding.rule_id = "REG-TEMP-2"
        
        result = classifier.is_critical_violation(finding, {})
        assert result is True
    
    def test_is_critical_violation_false(self):
        classifier = SeverityClassifier()
        finding = MagicMock(spec=Finding)
        finding.rule_id = "REG-TEMP-4"
        
        result = classifier.is_critical_violation(finding, {})
        assert result is False
    
    def test_get_severity_order(self):
        classifier = SeverityClassifier()
        order = classifier.get_severity_order()
        
        assert order[0] == Severity.CRITICAL
        assert order[1] == Severity.HIGH
        assert order[2] == Severity.MEDIUM
        assert order[3] == Severity.LOW
        assert order[4] == Severity.INFO