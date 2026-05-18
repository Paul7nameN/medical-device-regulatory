import pytest

from app.regulatory.log_parser import parse_raw_logs
from app.regulatory.rules.ins import RegIns1, RegIns2
from app.models.findings import Severity


class TestRegIns1:
    def test_returns_info_with_visual_flag(self):
        logs = [
            "2026-05-14 14:00:10 TEMP_READING 4.0C",
        ]
        entries, _ = parse_raw_logs(logs)
        rule = RegIns1()
        findings = rule.validate(entries, {})

        assert len(findings) == 1
        assert findings[0].severity == Severity.INFO
        assert findings[0].needs_visual_verification is True
        assert "insulation" in findings[0].message.lower() or "4 cm" in findings[0].message


class TestRegIns2:
    def test_returns_info(self):
        logs = [
            "2026-05-14 14:00:10 TEMP_READING 4.0C",
            "2026-05-14 14:07:40 BATTERY_LEVEL 99.9%",
            "2026-05-14 14:01:00 VOLTAGE 12.26V",
        ]
        entries, _ = parse_raw_logs(logs)
        rule = RegIns2()
        findings = rule.validate(entries, {})

        assert len(findings) == 1
        assert findings[0].severity == Severity.INFO
        assert findings[0].needs_visual_verification is True
        assert "battery" in findings[0].message.lower() or "isolat" in findings[0].message.lower()
