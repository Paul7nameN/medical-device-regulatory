import pytest

from app.regulatory.log_parser import parse_raw_logs
from app.regulatory.rules.cool import RegCool1, RegCool2
from app.models.findings import Severity


class TestRegCool1:
    def test_returns_info(self):
        logs = [
            "2026-05-14 14:00:20 FAN_SPEED 2029RPM",
            "2026-05-14 14:01:30 COOLING_RECOVERY_START",
        ]
        entries, _ = parse_raw_logs(logs)
        rule = RegCool1()
        findings = rule.validate(entries, {})

        assert len(findings) == 1
        assert findings[0].severity == Severity.INFO
        assert "airflow" in findings[0].message.lower()


class TestRegCool2:
    def test_no_temp_readings(self):
        logs = [
            "2026-05-14 14:00:20 FAN_SPEED 2029RPM",
        ]
        entries, _ = parse_raw_logs(logs)
        rule = RegCool2()
        findings = rule.validate(entries, {})

        assert len(findings) == 1
        assert findings[0].passed is False
        assert findings[0].severity == Severity.LOW

    def test_compliant_temp(self):
        logs = [
            "2026-05-14 14:00:10 TEMP_READING 4.0C",
            "2026-05-14 14:00:40 TEMP_READING 5.0C",
            "2026-05-14 14:01:10 TEMP_READING 4.5C",
        ]
        entries, _ = parse_raw_logs(logs)
        rule = RegCool2()
        findings = rule.validate(entries, {})

        assert len(findings) == 1
        assert findings[0].passed is True
