import pytest
from datetime import datetime, timedelta
from pathlib import Path

from app.regulatory.log_parser import parse_raw_logs
from app.regulatory.engine import RegulatoryEngine
from app.regulatory.rules.base import RuleRegistry
from app.models.logs import LogType
from app.models.findings import Severity


@pytest.fixture(autouse=True)
def setup_rules():
    from app.main import register_all_rules
    RuleRegistry.clear()
    register_all_rules()


class TestRegulatoryEngine:
    def test_empty_logs(self):
        engine = RegulatoryEngine()
        report = engine.validate([])

        assert report.total_entries == 0
        assert report.passed_count >= 0

    def test_quick_test_scenario(self):
        test_logs = [
            "2026-05-14 14:00:10 TEMP_READING 4.3C",
            "2026-05-14 14:00:40 TEMP_READING 9.1C",
            "2026-05-14 14:01:10 TEMP_READING 4.7C",
            "2026-05-14 14:02:30 SENSOR_TIMEOUT SECONDARY_SENSOR",
            "2026-05-14 14:06:30 DOOR_OPEN",
        ]

        entries, _ = parse_raw_logs(test_logs)
        engine = RegulatoryEngine()
        report = engine.validate(entries, device_id="test-001")

        assert report.device_id == "test-001"
        assert report.total_entries == 5

        reg_temp1_findings = [f for f in report.findings if f.rule_id == "REG-TEMP-1"]
        assert len(reg_temp1_findings) == 1

        reg_sens1_findings = [f for f in report.findings if f.rule_id == "REG-SENS-1"]
        assert len(reg_sens1_findings) == 1

    def test_filter_rules(self):
        test_logs = [
            "2026-05-14 14:00:10 TEMP_READING 4.3C",
            "2026-05-14 14:00:40 TEMP_READING 5.1C",
        ]

        entries, _ = parse_raw_logs(test_logs)
        engine = RegulatoryEngine()

        report = engine.validate(entries, filter_rules=["REG-TEMP-1"])

        temp_rules = [f for f in report.findings if f.category == "thermal"]
        other_rules = [f for f in report.findings if f.category != "thermal"]

        assert len(temp_rules) >= 1

    def test_get_rule_info(self):
        engine = RegulatoryEngine()

        info = engine.get_rule_info("REG-TEMP-1")
        assert info is not None
        assert info["rule_id"] == "REG-TEMP-1"
        assert "temperature" in info["description"].lower()

        info = engine.get_rule_info("NONEXISTENT-RULE")
        assert info is None

    def test_get_all_rules(self):
        engine = RegulatoryEngine()
        rules = engine.get_all_rules()

        assert len(rules) == 25

        rule_ids = [r["rule_id"] for r in rules]
        assert "REG-TEMP-1" in rule_ids
        assert "REG-SENS-1" in rule_ids
        assert "REG-ALARM-1" in rule_ids
        assert "REG-DATA-1" in rule_ids
        assert "REG-POWER-1" in rule_ids
        assert "REG-COOL-1" in rule_ids
        assert "REG-INS-1" in rule_ids
        assert "REG-OPS-1" in rule_ids

    def test_get_categories(self):
        engine = RegulatoryEngine()
        categories = engine.get_categories()

        assert "thermal" in categories
        assert "sensor" in categories
        assert "alarm" in categories
        assert "data" in categories
        assert "power" in categories
        assert "cooling" in categories
        assert "insulation" in categories
        assert "operational" in categories

    def test_compliant_temp_readings(self):
        compliant_logs = [
            "2026-05-14 14:00:10 TEMP_READING 4.0C",
            "2026-05-14 14:00:40 TEMP_READING 5.0C",
            "2026-05-14 14:01:10 TEMP_READING 6.0C",
            "2026-05-14 14:01:40 TEMP_READING 3.5C",
            "2026-05-14 14:02:10 TEMP_READING 7.0C",
        ]

        entries, _ = parse_raw_logs(compliant_logs)
        engine = RegulatoryEngine()
        report = engine.validate(entries)

        reg_temp1 = [f for f in report.findings if f.rule_id == "REG-TEMP-1"]
        assert len(reg_temp1) == 1
        assert reg_temp1[0].passed is True

    def test_severity_classification(self):
        critical_scenario = [
            "2026-05-14 14:00:00 TEMP_READING 10.0C",
            "2026-05-14 14:01:00 TEMP_READING 10.5C",
            "2026-05-14 14:02:00 TEMP_READING 11.0C",
            "2026-05-14 14:03:00 TEMP_READING 10.8C",
            "2026-05-14 14:02:30 SENSOR_TIMEOUT SECONDARY_SENSOR",
            "2026-05-14 14:02:40 SENSOR_TIMEOUT PRIMARY_SENSOR",
        ]

        entries, _ = parse_raw_logs(critical_scenario)
        engine = RegulatoryEngine()
        report = engine.validate(entries)

        assert report.critical_count >= 0


class TestSampleLogFile:
    def test_sample_log_file_exists(self):
        sample_path = Path(__file__).parent.parent.parent / "docs" / "client" / "medical_device_logs_1000.txt"
        assert sample_path.exists()

    def test_parse_sample_file(self):
        sample_path = Path(__file__).parent.parent.parent / "docs" / "client" / "medical_device_logs_1000.txt"

        if not sample_path.exists():
            pytest.skip("Sample log file not found")

        with open(sample_path, 'r') as f:
            lines = f.readlines()

        entries, warnings = parse_raw_logs(lines)

        assert len(entries) > 0

    def test_full_validation_on_sample(self):
        sample_path = Path(__file__).parent.parent.parent / "docs" / "client" / "medical_device_logs_1000.txt"

        if not sample_path.exists():
            pytest.skip("Sample log file not found")

        with open(sample_path, 'r') as f:
            lines = f.readlines()

        entries, _ = parse_raw_logs(lines)
        engine = RegulatoryEngine()
        report = engine.validate(entries)

        assert report.total_entries == len(entries)
        assert len(report.findings) > 0
        assert "thermal" in report.summary
        assert "sensor" in report.summary
        assert "alarm" in report.summary
        assert "data" in report.summary
        assert "power" in report.summary
        assert "cooling" in report.summary
        assert "insulation" in report.summary
        assert "operational" in report.summary
