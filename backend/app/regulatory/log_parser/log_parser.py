from datetime import datetime, timedelta
from typing import List, Optional, Any, Dict, Iterator, Tuple
from pathlib import Path

from app.models.logs import LogType, LogEntry

from app.regulatory.log_parser.patterns import (
    parse_log_line,
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
)


class ParseResult:
    def __init__(
        self,
        entries: List[LogEntry],
        warnings: List[str],
        errors: List[str],
        total_lines: int
    ):
        self.entries = entries
        self.warnings = warnings
        self.errors = errors
        self.total_lines = total_lines
        self.success_rate = len(entries) / total_lines if total_lines > 0 else 0.0


class LogParser:
    def __init__(self):
        self.warnings: List[str] = []
        self.errors: List[str] = []
    
    def parse_line(self, line: str) -> Optional[LogEntry]:
        entry_dict, warning = parse_log_line(line)
        
        if warning:
            self.warnings.append(warning)
            return None
        
        if not entry_dict:
            return None
        
        try:
            log_type = LogType(entry_dict["log_type"])
        except ValueError:
            self.errors.append(f"Unknown log type: {entry_dict['log_type']} in line: {line[:50]}...")
            return None
        
        return LogEntry(
            timestamp=entry_dict["timestamp"],
            log_type=log_type,
            raw_value=entry_dict["raw_value"],
            parsed_value=entry_dict["parsed_value"],
            sensor_id=entry_dict["sensor_id"],
            metadata=entry_dict["metadata"]
        )
    
    def parse_lines(self, lines: List[str]) -> ParseResult:
        self.warnings = []
        self.errors = []
        entries: List[LogEntry] = []
        
        for line in lines:
            entry = self.parse_line(line)
            if entry:
                entries.append(entry)
        
        return ParseResult(
            entries=entries,
            warnings=list(self.warnings),
            errors=list(self.errors),
            total_lines=len(lines)
        )
    
    def parse_file(self, filepath: str) -> ParseResult:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            return self.parse_lines(lines)
        except FileNotFoundError:
            self.errors.append(f"File not found: {filepath}")
            return ParseResult(entries=[], warnings=[], errors=list(self.errors), total_lines=0)
        except Exception as e:
            self.errors.append(f"Error reading file: {str(e)}")
            return ParseResult(entries=[], warnings=[], errors=list(self.errors), total_lines=0)
    
    def parse_stream(self, filepath: str) -> Iterator[LogEntry]:
        self.warnings = []
        self.errors = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    entry = self.parse_line(line.strip())
                    if entry:
                        yield entry
        except FileNotFoundError:
            self.errors.append(f"File not found: {filepath}")
        except Exception as e:
            self.errors.append(f"Error reading file: {str(e)}")


def detect_telemetry_gaps(
    entries: List[LogEntry],
    max_gap_seconds: float = 90.0
) -> List[Dict]:
    gaps = []
    sorted_entries = sorted(entries, key=lambda x: x.timestamp)
    
    for i in range(1, len(sorted_entries)):
        gap_seconds = (sorted_entries[i].timestamp - 
                       sorted_entries[i-1].timestamp).total_seconds()
        if gap_seconds > max_gap_seconds:
            gaps.append({
                "from": sorted_entries[i-1].timestamp,
                "to": sorted_entries[i].timestamp,
                "gap_seconds": gap_seconds
            })
    
    return gaps


def detect_sensor_timeouts(entries: List[LogEntry]) -> Dict[str, List[Dict]]:
    timeouts = {
        "primary": [],
        "secondary": []
    }
    
    for entry in entries:
        if entry.log_type == LogType.SENSOR_TIMEOUT:
            if entry.sensor_id == "PRIMARY":
                timeouts["primary"].append({
                    "timestamp": entry.timestamp
                })
            elif entry.sensor_id == "SECONDARY":
                timeouts["secondary"].append({
                    "timestamp": entry.timestamp
                })
    
    return timeouts


def detect_alarm_sequences(entries: List[LogEntry]) -> List[Dict]:
    alarms = []
    
    for entry in entries:
        if entry.log_type == LogType.ALARM_TRIGGERED:
            alarms.append({
                "timestamp": entry.timestamp
            })
    
    return alarms


def detect_door_events(entries: List[LogEntry]) -> List[Dict]:
    events = []
    sorted_entries = sorted(entries, key=lambda x: x.timestamp)
    open_time: Optional[datetime] = None
    
    for entry in sorted_entries:
        if entry.log_type == LogType.DOOR_OPEN:
            open_time = entry.timestamp
        elif entry.log_type == LogType.DOOR_CLOSE and open_time:
            duration_seconds = (entry.timestamp - open_time).total_seconds()
            events.append({
                "opened_at": open_time,
                "closed_at": entry.timestamp,
                "duration_seconds": duration_seconds
            })
            open_time = None
    
    return events


def detect_temp_violations(
    entries: List[LogEntry],
    min_temp: float = 2.0,
    max_temp: float = 8.0
) -> List[Dict]:
    violations = []
    
    for entry in entries:
        if entry.log_type == LogType.TEMP_READING:
            val = entry.parsed_value
            if val is not None:
                if val < min_temp or val > max_temp:
                    violations.append({
                        "timestamp": entry.timestamp,
                        "value": val,
                        "min": min_temp,
                        "max": max_temp
                    })
    
    return violations


def parse_raw_logs(raw_logs: List[str]) -> Tuple[List[LogEntry], List[str]]:
    parser = LogParser()
    result = parser.parse_lines(raw_logs)
    return result.entries, result.warnings
