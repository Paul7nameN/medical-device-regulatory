import pytest
from datetime import datetime

from app.regulatory.log_parser import LogParser, parse_raw_logs
from app.models.logs import LogType


class TestLogParser:
    def test_parse_temp_reading(self):
        parser = LogParser()
        line = "2026-05-14 14:00:10 TEMP_READING 4.3C"
        entry = parser.parse_line(line)

        assert entry is not None
        assert entry.log_type == LogType.TEMP_READING
        assert entry.parsed_value == 4.3
        assert entry.timestamp == datetime(2026, 5, 14, 14, 0, 10)

    def test_parse_fan_speed(self):
        parser = LogParser()
        line = "2026-05-14 14:00:20 FAN_SPEED 2029RPM"
        entry = parser.parse_line(line)

        assert entry is not None
        assert entry.log_type == LogType.FAN_SPEED
        assert entry.parsed_value == 2029

    def test_parse_voltage(self):
        parser = LogParser()
        line = "2026-05-14 14:01:00 VOLTAGE 12.26V"
        entry = parser.parse_line(line)

        assert entry is not None
        assert entry.log_type == LogType.VOLTAGE
        assert entry.parsed_value == 12.26

    def test_parse_humidity(self):
        parser = LogParser()
        line = "2026-05-14 14:02:10 HUMIDITY 77%"
        entry = parser.parse_line(line)

        assert entry is not None
        assert entry.log_type == LogType.HUMIDITY
        assert entry.parsed_value == 77.0

    def test_parse_battery(self):
        parser = LogParser()
        line = "2026-05-14 14:07:40 BATTERY_LEVEL 99.9%"
        entry = parser.parse_line(line)

        assert entry is not None
        assert entry.log_type == LogType.BATTERY_LEVEL
        assert entry.parsed_value == 99.9

    def test_parse_door_events(self):
        parser = LogParser()

        open_entry = parser.parse_line("2026-05-14 14:04:50 DOOR_OPEN")
        close_entry = parser.parse_line("2026-05-14 14:01:20 DOOR_CLOSE")

        assert open_entry is not None
        assert open_entry.log_type == LogType.DOOR_OPEN
        assert close_entry is not None
        assert close_entry.log_type == LogType.DOOR_CLOSE

    def test_parse_sensor_timeout(self):
        parser = LogParser()
        line = "2026-05-14 14:02:30 SENSOR_TIMEOUT SECONDARY_SENSOR"
        entry = parser.parse_line(line)

        assert entry is not None
        assert entry.log_type == LogType.SENSOR_TIMEOUT
        assert "SECONDARY" in entry.raw_value.upper()

    def test_parse_alarm_triggered(self):
        parser = LogParser()
        line = "2026-05-14 14:00:00 ALARM_TRIGGERED"
        entry = parser.parse_line(line)

        assert entry is not None
        assert entry.log_type == LogType.ALARM_TRIGGERED

    def test_parse_lines_multiple(self):
        lines = [
            "2026-05-14 14:00:10 TEMP_READING 4.3C",
            "2026-05-14 14:00:20 FAN_SPEED 2029RPM",
            "2026-05-14 14:00:30 TELEMETRY_SYNC_FAILED",
            "invalid line format",
            "2026-05-14 14:00:40 ALARM_TRIGGERED",
        ]

        entries, warnings = parse_raw_logs(lines)

        assert len(entries) == 4
        assert len(warnings) >= 1

    def test_empty_line(self):
        parser = LogParser()
        entry = parser.parse_line("")
        assert entry is None

        entry = parser.parse_line("   ")
        assert entry is None

    def test_invalid_timestamp(self):
        parser = LogParser()
        line = "invalid-date 14:00:10 TEMP_READING 4.3C"
        entry = parser.parse_line(line)
        assert entry is None
        assert len(parser.warnings) >= 1

    def test_unknown_log_type(self):
        parser = LogParser()
        line = "2026-05-14 14:00:10 UNKNOWN_TYPE some value"
        entry = parser.parse_line(line)
        assert entry is None
        assert len(parser.warnings) >= 1

    def test_cooling_recovery_start(self):
        parser = LogParser()
        line = "2026-05-14 14:01:30 COOLING_RECOVERY_START"
        entry = parser.parse_line(line)

        assert entry is not None
        assert entry.log_type == LogType.COOLING_RECOVERY_START

    def test_device_start(self):
        parser = LogParser()
        line = "2026-05-14 14:00:50 DEVICE_START"
        entry = parser.parse_line(line)

        assert entry is not None
        assert entry.log_type == LogType.DEVICE_START

    def test_temp_warning(self):
        parser = LogParser()
        line = "2026-05-14 14:09:20 TEMP_WARNING"
        entry = parser.parse_line(line)

        assert entry is not None
        assert entry.log_type == LogType.TEMP_WARNING

    def test_telemetry_sync_failed(self):
        parser = LogParser()
        line = "2026-05-14 14:00:30 TELEMETRY_SYNC_FAILED"
        entry = parser.parse_line(line)

        assert entry is not None
        assert entry.log_type == LogType.TELEMETRY_SYNC_FAILED
