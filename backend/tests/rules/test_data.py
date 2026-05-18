import pytest
from datetime import datetime, timedelta

from app.regulatory.log_parser import parse_raw_logs
from app.regulatory.rules.data import RegData1, RegData2, RegData3
from app.models.findings import Severity


class TestRegData1:
    def test_with_all_required_types(self):
        logs = [
            "2026-05-14 14:00:10 TEMP_READING 4.0C",
            "2026-05-14 14:00:00 ALARM_TRIGGERED",
            "2026-05-14 14:02:30 SENSOR_TIMEOUT SECONDARY_SENSOR",
        ]
        entries, _ = parse_raw_logs(logs)
        rule = RegData1()
        findings = rule.validate(entries, {})

        assert len(findings) == 1


class TestRegData2:
    def test_insufficient_entries(self):
        logs = [
            "2026-05-14 14:00:10 TEMP_READING 4.0C",
        ]
        entries, _ = parse_raw_logs(logs)
        rule = RegData2()
        findings = rule.validate(entries, {})

        assert len(findings) == 1
        assert findings[0].severity == Severity.LOW

    def test_with_sync_failures(self):
        logs = [
            "2026-05-14 14:00:30 TELEMETRY_SYNC_FAILED",
            "2026-05-14 14:02:20 TELEMETRY_SYNC_FAILED",
        ]
        entries, _ = parse_raw_logs(logs)
        rule = RegData2()
        findings = rule.validate(entries, {})

        assert len(findings) == 1


class TestRegData3:
    def test_insufficient_entries(self):
        logs = [
            "2026-05-14 14:00:10 TEMP_READING 4.0C",
        ]
        entries, _ = parse_raw_logs(logs)
        rule = RegData3()
        findings = rule.validate(entries, {})

        assert len(findings) == 1
        assert findings[0].severity == Severity.INFO

    def test_with_multiple_entries(self):
        base_time = datetime(2026, 5, 14, 14, 0, 0)
        logs = []
        for i in range(5):
            ts = base_time + timedelta(hours=i)
            logs.append(f"{ts.strftime('%Y-%m-%d %H:%M:%S')} TEMP_READING 5.0C")

        entries, _ = parse_raw_logs(logs)
        rule = RegData3()
        findings = rule.validate(entries, {})

        assert len(findings) == 1
        assert findings[0].severity == Severity.INFO
