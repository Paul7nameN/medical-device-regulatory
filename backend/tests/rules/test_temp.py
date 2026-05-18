import pytest
from datetime import datetime, timedelta

from app.regulatory.log_parser import parse_raw_logs
from app.regulatory.rules.temp import RegTemp1, RegTemp2, RegTemp3, RegTemp4
from app.models.findings import Severity


class TestRegTemp1:
    def test_pass_all_in_range(self):
        logs = [
            "2026-05-14 14:00:10 TEMP_READING 4.0C",
            "2026-05-14 14:00:40 TEMP_READING 5.0C",
            "2026-05-14 14:01:10 TEMP_READING 6.0C",
        ]
        entries, _ = parse_raw_logs(logs)
        rule = RegTemp1()
        findings = rule.validate(entries, {})

        assert len(findings) == 1
        assert findings[0].passed is True

    def test_fail_out_of_range(self):
        logs = [
            "2026-05-14 14:00:10 TEMP_READING 1.0C",
            "2026-05-14 14:00:40 TEMP_READING 5.0C",
            "2026-05-14 14:01:10 TEMP_READING 10.0C",
        ]
        entries, _ = parse_raw_logs(logs)
        rule = RegTemp1()
        findings = rule.validate(entries, {})

        assert len(findings) == 1
        assert findings[0].passed is False
        assert len(findings[0].evidence) >= 1

    def test_no_temp_readings(self):
        logs = [
            "2026-05-14 14:00:20 FAN_SPEED 2029RPM",
            "2026-05-14 14:01:00 VOLTAGE 12.26V",
        ]
        entries, _ = parse_raw_logs(logs)
        rule = RegTemp1()
        findings = rule.validate(entries, {})

        assert len(findings) == 1
        assert findings[0].passed is False
        assert findings[0].severity == Severity.MEDIUM


class TestRegTemp4:
    def test_pass_valid_intervals(self):
        base_time = datetime(2026, 5, 14, 14, 0, 0)
        logs = []
        for i in range(5):
            ts = base_time + timedelta(seconds=i * 20)
            logs.append(f"{ts.strftime('%Y-%m-%d %H:%M:%S')} TEMP_READING 5.0C")

        entries, _ = parse_raw_logs(logs)
        rule = RegTemp4()
        findings = rule.validate(entries, {})

        assert len(findings) == 1
        assert findings[0].passed is True

    def test_fail_large_gap(self):
        base_time = datetime(2026, 5, 14, 14, 0, 0)
        logs = [
            f"{(base_time).strftime('%Y-%m-%d %H:%M:%S')} TEMP_READING 5.0C",
            f"{(base_time + timedelta(seconds=60)).strftime('%Y-%m-%d %H:%M:%S')} TEMP_READING 5.0C",
        ]

        entries, _ = parse_raw_logs(logs)
        rule = RegTemp4()
        findings = rule.validate(entries, {})

        assert len(findings) == 1
        assert findings[0].passed is False
