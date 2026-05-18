import pytest
from datetime import datetime

from app.regulatory.log_parser import (
    LogParser,
    LogType,
    LogEntry,
    ParseResult,
    parse_raw_logs,
    detect_telemetry_gaps,
    detect_sensor_timeouts,
    detect_alarm_sequences,
    detect_door_events,
    detect_temp_violations,
)
from app.regulatory.log_parser.patterns import (
    LOG_PATTERN,
    TEMP_PATTERN,
    FAN_PATTERN,
    VOLTAGE_PATTERN,
    HUMIDITY_PATTERN,
    BATTERY_PATTERN,
    parse_temperature,
    parse_fan_speed,
    parse_voltage,
    parse_humidity,
    parse_battery_level,
    extract_sensor_id,
    parse_log_line,
)


class TestLogParserClass:
    def test_init(self):
        parser = LogParser()
        assert parser.warnings == []
        assert parser.errors == []
    
    def test_parse_temp_reading(self):
        line = "2026-05-14 14:00:10 TEMP_READING 4.3C"
        parser = LogParser()
        entry = parser.parse_line(line)
        
        assert entry is not None
        assert entry.log_type == LogType.TEMP_READING
        assert entry.parsed_value == 4.3
        assert entry.timestamp == datetime(2026, 5, 14, 14, 0, 10)
    
    def test_parse_fan_speed(self):
        line = "2026-05-14 14:00:20 FAN_SPEED 2029RPM"
        parser = LogParser()
        entry = parser.parse_line(line)
        
        assert entry is not None
        assert entry.log_type == LogType.FAN_SPEED
        assert entry.parsed_value == 2029
    
    def test_parse_voltage(self):
        line = "2026-05-14 14:01:00 VOLTAGE 12.26V"
        parser = LogParser()
        entry = parser.parse_line(line)
        
        assert entry is not None
        assert entry.log_type == LogType.VOLTAGE
        assert entry.parsed_value == 12.26
    
    def test_parse_humidity(self):
        line = "2026-05-14 14:02:10 HUMIDITY 77%"
        parser = LogParser()
        entry = parser.parse_line(line)
        
        assert entry is not None
        assert entry.log_type == LogType.HUMIDITY
        assert entry.parsed_value == 77.0
    
    def test_parse_battery_level(self):
        line = "2026-05-14 14:07:40 BATTERY_LEVEL 99.9%"
        parser = LogParser()
        entry = parser.parse_line(line)
        
        assert entry is not None
        assert entry.log_type == LogType.BATTERY_LEVEL
        assert entry.parsed_value == 99.9
    
    def test_parse_door_open(self):
        line = "2026-05-14 14:04:50 DOOR_OPEN"
        parser = LogParser()
        entry = parser.parse_line(line)
        
        assert entry is not None
        assert entry.log_type == LogType.DOOR_OPEN
        assert entry.raw_value == ""
    
    def test_parse_door_close(self):
        line = "2026-05-14 14:01:20 DOOR_CLOSE"
        parser = LogParser()
        entry = parser.parse_line(line)
        
        assert entry is not None
        assert entry.log_type == LogType.DOOR_CLOSE
    
    def test_parse_device_start(self):
        line = "2026-05-14 14:00:50 DEVICE_START"
        parser = LogParser()
        entry = parser.parse_line(line)
        
        assert entry is not None
        assert entry.log_type == LogType.DEVICE_START
    
    def test_parse_alarm_triggered(self):
        line = "2026-05-14 14:00:00 ALARM_TRIGGERED"
        parser = LogParser()
        entry = parser.parse_line(line)
        
        assert entry is not None
        assert entry.log_type == LogType.ALARM_TRIGGERED
    
    def test_parse_temp_warning(self):
        line = "2026-05-14 14:09:20 TEMP_WARNING"
        parser = LogParser()
        entry = parser.parse_line(line)
        
        assert entry is not None
        assert entry.log_type == LogType.TEMP_WARNING
    
    def test_parse_sensor_timeout_secondary(self):
        line = "2026-05-14 14:02:30 SENSOR_TIMEOUT SECONDARY_SENSOR"
        parser = LogParser()
        entry = parser.parse_line(line)
        
        assert entry is not None
        assert entry.log_type == LogType.SENSOR_TIMEOUT
        assert entry.sensor_id == "SECONDARY"
        assert entry.parsed_value is True
    
    def test_parse_sensor_timeout_primary(self):
        line = "2026-05-14 14:03:30 SENSOR_TIMEOUT PRIMARY_SENSOR"
        parser = LogParser()
        entry = parser.parse_line(line)
        
        assert entry is not None
        assert entry.sensor_id == "PRIMARY"
    
    def test_parse_telemetry_sync_failed(self):
        line = "2026-05-14 14:00:30 TELEMETRY_SYNC_FAILED"
        parser = LogParser()
        entry = parser.parse_line(line)
        
        assert entry is not None
        assert entry.log_type == LogType.TELEMETRY_SYNC_FAILED
    
    def test_parse_cooling_recovery_start(self):
        line = "2026-05-14 14:01:30 COOLING_RECOVERY_START"
        parser = LogParser()
        entry = parser.parse_line(line)
        
        assert entry is not None
        assert entry.log_type == LogType.COOLING_RECOVERY_START


class TestLogParserEdgeCases:
    def test_empty_line(self):
        parser = LogParser()
        entry = parser.parse_line("")
        assert entry is None
        assert len(parser.warnings) == 0
    
    def test_whitespace_line(self):
        parser = LogParser()
        entry = parser.parse_line("   ")
        assert entry is None
    
    def test_malformed_timestamp(self):
        line = "invalid-date 14:00:10 TEMP_READING 4.3C"
        parser = LogParser()
        entry = parser.parse_line(line)
        
        assert entry is None
        assert len(parser.errors) >= 1 or len(parser.warnings) >= 1
    
    def test_unknown_log_type(self):
        line = "2026-05-14 14:00:10 UNKNOWN_TYPE 4.3C"
        parser = LogParser()
        entry = parser.parse_line(line)
        
        assert entry is None
        assert len(parser.errors) >= 1


class TestParseLines:
    def test_parse_multiple_lines(self):
        lines = [
            "2026-05-14 14:00:10 TEMP_READING 4.3C",
            "2026-05-14 14:00:20 FAN_SPEED 2029RPM",
            "2026-05-14 14:00:30 TELEMETRY_SYNC_FAILED",
        ]
        parser = LogParser()
        result = parser.parse_lines(lines)
        
        assert len(result.entries) == 3
        assert result.entries[0].log_type == LogType.TEMP_READING
        assert result.entries[1].log_type == LogType.FAN_SPEED
        assert result.entries[2].log_type == LogType.TELEMETRY_SYNC_FAILED
        assert result.total_lines == 3


class TestParseRawLogsConvenience:
    def test_parse_raw_logs(self):
        raw_logs = [
            "2026-05-14 14:00:10 TEMP_READING 4.3C",
            "2026-05-14 14:00:40 TEMP_READING 9.1C",
        ]
        entries, warnings = parse_raw_logs(raw_logs)
        
        assert len(entries) == 2
        assert entries[0].parsed_value == 4.3
        assert entries[1].parsed_value == 9.1


class TestPatternDetection:
    def test_detect_telemetry_gaps(self):
        base_time = datetime(2026, 5, 14, 14, 0, 0)
        parser = LogParser()
        
        entries = [
            LogEntry(
                timestamp=base_time,
                log_type=LogType.TEMP_READING,
                raw_value="4.3C",
                parsed_value=4.3
            ),
            LogEntry(
                timestamp=base_time,
                log_type=LogType.TEMP_READING,
                raw_value="5.0C",
                parsed_value=5.0
            ),
        ]
        
        gaps = detect_telemetry_gaps(entries, max_gap_seconds=90.0)
        assert len(gaps) == 0
    
    def test_detect_sensor_timeouts(self):
        parser = LogParser()
        entries = [
            LogEntry(
                timestamp=datetime(2026, 5, 14, 14, 0, 0),
                log_type=LogType.SENSOR_TIMEOUT,
                raw_value="SECONDARY_SENSOR",
                sensor_id="SECONDARY",
                parsed_value=True
            ),
        ]
        
        timeouts = detect_sensor_timeouts(entries)
        assert len(timeouts["secondary"]) == 1
        assert len(timeouts["primary"]) == 0
    
    def test_detect_alarm_sequences(self):
        parser = LogParser()
        entries = [
            LogEntry(
                timestamp=datetime(2026, 5, 14, 14, 0, 0),
                log_type=LogType.ALARM_TRIGGERED,
                raw_value="",
                parsed_value=None
            ),
        ]
        
        alarms = detect_alarm_sequences(entries)
        assert len(alarms) == 1
    
    def test_detect_temp_violations(self):
        parser = LogParser()
        entries = [
            LogEntry(
                timestamp=datetime(2026, 5, 14, 14, 0, 0),
                log_type=LogType.TEMP_READING,
                raw_value="4.3C",
                parsed_value=4.3
            ),
            LogEntry(
                timestamp=datetime(2026, 5, 14, 14, 0, 1),
                log_type=LogType.TEMP_READING,
                raw_value="9.1C",
                parsed_value=9.1
            ),
            LogEntry(
                timestamp=datetime(2026, 5, 14, 14, 0, 2),
                log_type=LogType.TEMP_READING,
                raw_value="1.5C",
                parsed_value=1.5
            ),
        ]
        
        violations = detect_temp_violations(entries, min_temp=2.0, max_temp=8.0)
        assert len(violations) == 2
        assert violations[0]["value"] == 9.1
        assert violations[1]["value"] == 1.5


class TestValueParsers:
    def test_parse_temperature_with_unit(self):
        assert parse_temperature("4.3C") == 4.3
    
    def test_parse_temperature_without_unit(self):
        assert parse_temperature("4.3") == 4.3
    
    def test_parse_temperature_negative(self):
        assert parse_temperature("-1.5C") == -1.5
    
    def test_parse_fan_speed(self):
        assert parse_fan_speed("2029RPM") == 2029
    
    def test_parse_voltage(self):
        assert parse_voltage("12.26V") == 12.26
    
    def test_parse_humidity(self):
        assert parse_humidity("77%") == 77.0
    
    def test_parse_battery_level(self):
        assert parse_battery_level("99.9%") == 99.9
    
    def test_extract_sensor_id_secondary(self):
        assert extract_sensor_id("SECONDARY_SENSOR", "SENSOR_TIMEOUT") == "SECONDARY"
    
    def test_extract_sensor_id_primary(self):
        assert extract_sensor_id("PRIMARY_SENSOR", "SENSOR_TIMEOUT") == "PRIMARY"


class TestParseLogLine:
    def test_parse_log_line_valid(self):
        line = "2026-05-14 14:00:10 TEMP_READING 4.3C"
        entry_dict, warning = parse_log_line(line)
        
        assert entry_dict is not None
        assert warning is None
        assert entry_dict["log_type"] == "TEMP_READING"
        assert entry_dict["parsed_value"] == 4.3
    
    def test_parse_log_line_invalid(self):
        line = "invalid line format"
        entry_dict, warning = parse_log_line(line)
        
        assert entry_dict is None
        assert warning is not None
