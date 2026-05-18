import pytest

from app.regulatory.log_parser import parse_raw_logs
from app.regulatory.rules.alarm import RegAlarm1, RegAlarm2, RegAlarm3
from app.models.findings import Severity


class TestRegAlarm1:
    def test_no_temp_readings(self):
        logs = [
            "2026-05-14 14:00:00 ALARM_TRIGGERED",
        ]
        entries, _ = parse_raw_logs(logs)
        rule = RegAlarm1()
        findings = rule.validate(entries, {})

        assert len(findings) == 1
        assert findings[0].severity == Severity.MEDIUM

    def test_no_excursions(self):
        logs = [
            "2026-05-14 14:00:10 TEMP_READING 4.0C",
            "2026-05-14 14:02:10 TEMP_READING 5.0C",
            "2026-05-14 14:04:10 TEMP_READING 6.0C",
        ]
        entries, _ = parse_raw_logs(logs)
        rule = RegAlarm1()
        findings = rule.validate(entries, {})

        assert len(findings) == 1
        assert findings[0].passed is True


class TestRegAlarm2:
    def test_no_alarm_events(self):
        logs = [
            "2026-05-14 14:00:10 TEMP_READING 4.0C",
        ]
        entries, _ = parse_raw_logs(logs)
        rule = RegAlarm2()
        findings = rule.validate(entries, {})

        assert len(findings) == 1
        assert findings[0].passed is True

    def test_with_alarms_returns_info(self):
        logs = [
            "2026-05-14 14:00:00 ALARM_TRIGGERED",
            "2026-05-14 14:02:00 ALARM_TRIGGERED",
        ]
        entries, _ = parse_raw_logs(logs)
        rule = RegAlarm2()
        findings = rule.validate(entries, {})

        assert len(findings) == 1
        assert findings[0].severity == Severity.INFO


class TestRegAlarm3:
    def test_returns_info(self):
        logs = [
            "2026-05-14 14:00:00 ALARM_TRIGGERED",
            "2026-05-14 14:00:10 TEMP_WARNING",
        ]
        entries, _ = parse_raw_logs(logs)
        rule = RegAlarm3()
        findings = rule.validate(entries, {})

        assert len(findings) == 1
        assert findings[0].severity == Severity.INFO
