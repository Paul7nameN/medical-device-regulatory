import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from app.reports.aggregator import ComplianceReportAggregator, aggregate_report
from app.reports.severity import SeverityClassifier
from app.models.logs import LogEntry, LogType
from app.models.findings import (
    Finding, ComplianceReport, Severity, CategorySummary
)


class TestComplianceReportAggregator:
    def test_init(self):
        aggregator = ComplianceReportAggregator()
        assert aggregator is not None
        assert isinstance(aggregator.severity_classifier, SeverityClassifier)


class TestBuildClassificationContext:
    def test_empty_findings(self):
        aggregator = ComplianceReportAggregator()
        context = aggregator._build_classification_context([], [])
        
        assert context["temp_violation_count"] == 0
        assert context["dual_sensor_failure"] is False
    
    def test_temp_violations_count(self):
        aggregator = ComplianceReportAggregator()
        
        finding1 = MagicMock(spec=Finding)
        finding1.rule_id = "REG-TEMP-1"
        finding1.passed = False
        
        finding2 = MagicMock(spec=Finding)
        finding2.rule_id = "REG-TEMP-1"
        finding2.passed = False
        
        finding3 = MagicMock(spec=Finding)
        finding3.rule_id = "REG-OTHER"
        finding3.passed = False
        
        findings = [finding1, finding2, finding3]
        context = aggregator._build_classification_context(findings, [])
        
        assert context["temp_violation_count"] == 2
    
    def test_dual_sensor_failure_detection(self):
        aggregator = ComplianceReportAggregator()
        
        finding = MagicMock(spec=Finding)
        finding.rule_id = "REG-SENS-1"
        finding.passed = False
        finding.message = "CRITICAL: Both PRIMARY and SECONDARY sensors experiencing timeouts"
        
        findings = [finding]
        context = aggregator._build_classification_context(findings, [])
        
        assert context["dual_sensor_failure"] is True


class TestClassifyFindings:
    def test_classify_findings_empty(self):
        aggregator = ComplianceReportAggregator()
        counts = aggregator._classify_findings([], {})
        assert counts == {}


class TestGroupByRule:
    def test_group_by_rule_empty(self):
        aggregator = ComplianceReportAggregator()
        result = aggregator._group_by_rule([], {})
        assert result == {}


class TestAggregate:
    @pytest.fixture
    def mock_report(self):
        report = MagicMock(spec=ComplianceReport)
        report.device_id = "test-device-001"
        report.total_entries = 5
        report.time_range_start = datetime(2026, 5, 14, 14, 0, 0)
        report.time_range_end = datetime(2026, 5, 14, 14, 30, 0)
        report.passed_count = 3
        report.failed_count = 2
        report.critical_count = 0
        report.findings = []
        report.summary = {
            "TEMP": CategorySummary(passed=1, failed=1, total=2),
            "SENS": CategorySummary(passed=1, failed=1, total=2),
        }
        return report
    
    def test_aggregate_basic(self, mock_report):
        aggregator = ComplianceReportAggregator()
        result = aggregator.aggregate(
            regulatory_report=mock_report,
            logs=[],
            include_raw_report=False
        )
        
        assert result.device_id == "test-device-001"
        assert result.total_entries == 5
        assert result.executive_summary != ""
        assert result.raw_regulatory_report is None
    
    def test_aggregate_with_raw_report(self, mock_report):
        aggregator = ComplianceReportAggregator()
        result = aggregator.aggregate(
            regulatory_report=mock_report,
            logs=[],
            include_raw_report=True
        )
        
        assert result.raw_regulatory_report is not None
    
    def test_aggregate_with_temp_violations(self, mock_report):
        finding = MagicMock(spec=Finding)
        finding.rule_id = "REG-TEMP-1"
        finding.rule_description = "Temperature must be 2-8C"
        finding.category = "TEMP"
        finding.severity = Severity.HIGH
        finding.passed = False
        finding.message = "Temperature 9.1C exceeds 8C"
        finding.evidence = []
        finding.timestamp = datetime(2026, 5, 14, 14, 0, 0)
        
        mock_report.findings = [finding]
        
        aggregator = ComplianceReportAggregator()
        result = aggregator.aggregate(
            regulatory_report=mock_report,
            logs=[],
            include_raw_report=False
        )
        
        assert "REG-TEMP-1" in result.violations_by_rule
        assert len(result.recommendations) >= 1


class TestGenerateExecutiveSummary:
    def test_no_critical_or_high_violations(self):
        aggregator = ComplianceReportAggregator()
        
        summary = {
            "critical_count": 0,
            "high_count": 0,
        }
        
        result = aggregator._generate_executive_summary(summary, {}, MagicMock())
        
        assert "All regulatory checks passed" in result
    
    def test_with_critical_violations(self):
        aggregator = ComplianceReportAggregator()
        
        from app.reports.models import ViolationSummary
        
        summary = {
            "critical_count": 2,
            "high_count": 3,
        }
        
        vs_temp1 = MagicMock(spec=ViolationSummary)
        vs_temp1.rule_id = "REG-TEMP-1"
        vs_temp1.severity = Severity.CRITICAL
        
        vs_temp2 = MagicMock(spec=ViolationSummary)
        vs_temp2.rule_id = "REG-TEMP-2"
        vs_temp2.severity = Severity.CRITICAL
        
        vs_sens1 = MagicMock(spec=ViolationSummary)
        vs_sens1.rule_id = "REG-SENS-1"
        vs_sens1.severity = Severity.HIGH
        
        violations_by_rule = {
            "REG-TEMP-1": vs_temp1,
            "REG-TEMP-2": vs_temp2,
            "REG-SENS-1": vs_sens1,
        }
        
        temporal_analysis = MagicMock()
        temporal_analysis.critical_periods = []
        
        result = aggregator._generate_executive_summary(
            summary, violations_by_rule, temporal_analysis
        )
        
        assert "CRITICAL" in result
        assert "REG-TEMP-1" in result or "REG-TEMP-2" in result


class TestAggregateReportConvenience:
    def test_aggregate_report_convenience(self):
        report = MagicMock(spec=ComplianceReport)
        report.device_id = "test-001"
        report.total_entries = 3
        report.time_range_start = datetime(2026, 5, 14, 14, 0, 0)
        report.time_range_end = datetime(2026, 5, 14, 14, 30, 0)
        report.passed_count = 2
        report.failed_count = 1
        report.critical_count = 0
        report.findings = []
        report.summary = {}
        
        result = aggregate_report(
            regulatory_report=report,
            logs=[],
            include_raw_report=False
        )
        
        assert result.device_id == "test-001"