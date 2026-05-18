import re
from typing import List, Optional, Tuple
from datetime import datetime

TIMESTAMP_PATTERN = re.compile(
    r'^(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})'
)

LOG_PATTERN = re.compile(
    r'^(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})\s+(\w+)(?:\s+(.*))?$'
)

TEMP_PATTERN = re.compile(r'(-?[\d.]+)\s*[°C]?')
FAN_PATTERN = re.compile(r'(\d+)\s*RPM')
VOLTAGE_PATTERN = re.compile(r'([\d.]+)\s*V')
HUMIDITY_PATTERN = re.compile(r'([\d.]+)\s*%')
BATTERY_PATTERN = re.compile(r'([\d.]+)\s*%')


def parse_temperature(raw_value: str) -> Optional[float]:
    match = TEMP_PATTERN.search(raw_value)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    return None


def parse_fan_speed(raw_value: str) -> Optional[int]:
    match = FAN_PATTERN.search(raw_value)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass
    return None


def parse_voltage(raw_value: str) -> Optional[float]:
    match = VOLTAGE_PATTERN.search(raw_value)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    return None


def parse_humidity(raw_value: str) -> Optional[float]:
    match = HUMIDITY_PATTERN.search(raw_value)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    return None


def parse_battery_level(raw_value: str) -> Optional[float]:
    match = BATTERY_PATTERN.search(raw_value)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    return None


def extract_sensor_id(raw_value: str, log_type: str) -> Optional[str]:
    if log_type == "SENSOR_TIMEOUT":
        parts = raw_value.split()
        if parts:
            sensor_id = parts[0].upper()
            if sensor_id.endswith("_SENSOR"):
                sensor_id = sensor_id[:-7]
            return sensor_id
    return None


def parse_log_line(line: str) -> Tuple[Optional[dict], Optional[str]]:
    line = line.strip()
    if not line:
        return None, None
    
    match = LOG_PATTERN.match(line)
    if not match:
        return None, f"Could not parse line: {line[:50]}..."
    
    date_str, time_str, log_type_str, raw_value = match.groups()
    raw_value = raw_value or ""
    
    try:
        timestamp_str = f"{date_str} {time_str}"
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None, f"Invalid timestamp: {timestamp_str}"
    
    parsed_value: Optional[any] = None
    sensor_id: Optional[str] = None
    
    if log_type_str == "TEMP_READING":
        parsed_value = parse_temperature(raw_value)
    elif log_type_str == "FAN_SPEED":
        parsed_value = parse_fan_speed(raw_value)
    elif log_type_str == "VOLTAGE":
        parsed_value = parse_voltage(raw_value)
    elif log_type_str == "HUMIDITY":
        parsed_value = parse_humidity(raw_value)
    elif log_type_str == "BATTERY_LEVEL":
        parsed_value = parse_battery_level(raw_value)
    elif log_type_str == "SENSOR_TIMEOUT":
        sensor_id = extract_sensor_id(raw_value, log_type_str)
        parsed_value = True
    
    entry = {
        "timestamp": timestamp,
        "log_type": log_type_str,
        "raw_value": raw_value,
        "parsed_value": parsed_value,
        "sensor_id": sensor_id,
        "metadata": {}
    }
    
    return entry, None
