import pytest
from datetime import datetime, timedelta

from app.regulatory.log_parser import parse_raw_logs
from app.regulatory.rules.ops import RegOps1, RegOps2
from app.models.findings import Severity


class TestRegOps1:
    def test_no_door_events(self):
        logs = [
            "2026-05-14 14:00:10 TEMP_READING 4.0C",
        ]
        entries, _ = parse_raw_logs(logs)
        rule = RegOps1()
        findings = rule.validate(entries, {})

        assert len(findings) == 1
        assert findings[0].passed is True

    def test_door_events_no_temp(self):
        logs = [
            "2026-05-14 14:06:30 DOOR_OPEN",
            "2026-05-14 14:10:50 DOOR_CLOSE",
        ]
        entries, _ = parse_raw_logs(logs)
        rule = RegOps1()
        findings = rule.validate(entries, {})

        assert len(findings) == 1
        assert findings[0].passed is False
        assert findings[0].severity == Severity.MEDIUM


class TestRegOps2:
    def test_no_door_events(self):
        logs = [
            "2026-05-14 14:00:10 TEMP_READING 4.0C",
        ]
        entries, _ = parse_raw_logs(logs)
        rule = RegOps2()
        findings = rule.validate(entries, {})

        assert len(findings) == 1
        assert findings[0].passed is True

    def test_normal_access_frequency(self):
        base_time = datetime(2026, 5, 14, 14, 0, 0)
        logs = []
        for i in range(5):
            ts = base_time + timedelta(minutes=i * 15)
            logs.append(f"{ts.strftime('%Y-%m-%d %H:%M:%S')} DOOR_OPEN")

        entries, _ = parse_raw_logs(logs)
        rule = RegOps2()
        findings = rule.validate(entries, {})

        assert len(findings) == 1
        assert findings[0].passed is True

    def test_excessive_access(self):
        base_time = datetime(2026, 5, 14, 14, 0, 0)
        logs = []
        for i in range(12):
            ts = base_time + timedelta(minutes=i * 4)
            logs.append(f"{ts.strftime('%Y-%m-%d %H:%M:%S')} DOOR_OPEN")

        entries, _ = parse_raw_logs(logs)
        rule = RegOps2()
        findings = rule.validate(entries, {})

        assert len(findings) == 1
