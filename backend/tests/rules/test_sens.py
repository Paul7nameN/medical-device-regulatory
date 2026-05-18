import pytest

from app.regulatory.log_parser import parse_raw_logs
from app.regulatory.rules.sens import RegSens1, RegSens2, RegSens3
from app.models.findings import Severity


class TestRegSens1:
    def test_pass_no_timeouts(self):
        logs = [
            "2026-05-14 14:00:10 TEMP_READING 4.3C",
            "2026-05-14 14:00:20 FAN_SPEED 2029RPM",
        ]
        entries, _ = parse_raw_logs(logs)
        rule = RegSens1()
        findings = rule.validate(entries, {})

        assert len(findings) == 1
        assert findings[0].passed is True

    def test_fail_secondary_timeout(self):
        logs = [
            "2026-05-14 14:02:30 SENSOR_TIMEOUT SECONDARY_SENSOR",
            "2026-05-14 14:00:10 TEMP_READING 4.3C",
        ]
        entries, _ = parse_raw_logs(logs)
        rule = RegSens1()
        findings = rule.validate(entries, {})

        assert len(findings) == 1
        assert findings[0].passed is False
        assert findings[0].severity == Severity.HIGH

    def test_fail_both_timeouts(self):
        logs = [
            "2026-05-14 14:02:30 SENSOR_TIMEOUT SECONDARY_SENSOR",
            "2026-05-14 14:03:30 SENSOR_TIMEOUT PRIMARY_SENSOR",
        ]
        entries, _ = parse_raw_logs(logs)
        rule = RegSens1()
        findings = rule.validate(entries, {})

        assert len(findings) == 1
        assert findings[0].passed is False
        assert findings[0].severity == Severity.CRITICAL


class TestRegSens2:
    def test_returns_info(self):
        logs = [
            "2026-05-14 14:00:10 TEMP_READING 4.3C",
        ]
        entries, _ = parse_raw_logs(logs)
        rule = RegSens2()
        findings = rule.validate(entries, {})

        assert len(findings) == 1
        assert findings[0].severity == Severity.INFO
        assert findings[0].needs_visual_verification is True


class TestRegSens3:
    def test_insufficient_data(self):
        logs = [
            "2026-05-14 14:00:10 TEMP_READING 4.3C",
        ]
        entries, _ = parse_raw_logs(logs)
        rule = RegSens3()
        findings = rule.validate(entries, {})

        assert len(findings) == 1
