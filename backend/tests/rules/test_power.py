import pytest

from app.regulatory.log_parser import parse_raw_logs
from app.regulatory.rules.power import RegPower1, RegPower2
from app.models.findings import Severity


class TestRegPower1:
    def test_no_battery_readings(self):
        logs = [
            "2026-05-14 14:00:10 TEMP_READING 4.0C",
        ]
        entries, _ = parse_raw_logs(logs)
        rule = RegPower1()
        findings = rule.validate(entries, {})

        assert len(findings) == 1
        assert findings[0].severity == Severity.INFO

    def test_with_battery_readings(self):
        logs = [
            "2026-05-14 14:00:10 BATTERY_LEVEL 99.9%",
            "2026-05-14 14:08:10 BATTERY_LEVEL 99.1%",
        ]
        entries, _ = parse_raw_logs(logs)
        rule = RegPower1()
        findings = rule.validate(entries, {})

        assert len(findings) == 1


class TestRegPower2:
    def test_no_temp_readings(self):
        logs = [
            "2026-05-14 14:00:10 VOLTAGE 12.26V",
        ]
        entries, _ = parse_raw_logs(logs)
        rule = RegPower2()
        findings = rule.validate(entries, {})

        assert len(findings) == 1
        assert findings[0].passed is False
        assert findings[0].severity == Severity.LOW

    def test_no_voltage_readings(self):
        logs = [
            "2026-05-14 14:00:10 TEMP_READING 4.0C",
        ]
        entries, _ = parse_raw_logs(logs)
        rule = RegPower2()
        findings = rule.validate(entries, {})

        assert len(findings) == 1
        assert findings[0].severity == Severity.INFO

    def test_compliant_in_battery_mode(self):
        logs = [
            "2026-05-14 14:00:00 VOLTAGE 11.5V",
            "2026-05-14 14:00:10 TEMP_READING 4.0C",
            "2026-05-14 14:00:40 TEMP_READING 5.0C",
            "2026-05-14 14:01:10 TEMP_READING 4.5C",
        ]
        entries, _ = parse_raw_logs(logs)
        rule = RegPower2()
        findings = rule.validate(entries, {})

        assert len(findings) == 1
