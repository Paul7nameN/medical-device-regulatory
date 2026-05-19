# Log Parser

> This file was moved from `docs/log-parser.md`.

---

## Overview

The **log-parser** is a Python module that parses raw medical device logs and extracts structured data for regulatory validation. It serves as the foundational parsing layer for the MED-THERM-2026 Compliance Engine.

### Purpose

The log-parser module:

1. **Parses** device logs in format: `YYYY-MM-DD HH:MM:SS EVENT_TYPE [VALUE]`
2. **Extracts** structured data: timestamps, event types, values with units
3. **Detects** key regulatory patterns for MED-THERM-2026 compliance
4. **Provides** streaming API support for large log files
5. **Enables** backward compatibility with existing parsing code

### Key Features

- **14 supported log types** - Comprehensive device event coverage
- **5 regulatory pattern detectors** - Direct mapping to MED-THERM-2026 rules
- **Streaming support** - Memory-efficient parsing of large files
- **Robust error handling** - Warnings for non-critical issues, errors for critical failures
- **Zero external dependencies** - Uses only Python standard library
- **Backward compatible** - Existing `parse_raw_logs()` signature preserved

---

## Module Location

```
backend/app/regulatory/log_parser/
├── __init__.py          # Public API exports
├── log_parser.py        # Core: LogParser class + pattern detection
├── patterns.py          # Regex patterns + value parsing functions
└── exceptions.py        # Custom exception classes
```

---

## What It Does

### Parsing Process

```
Raw Log Line
    │
    ▼
Regex Pattern Match (LOG_PATTERN)
    │
    ├─► Timestamp Parse (datetime.strptime)
    │
    ├─► Log Type Match (LogType enum)
    │
    ├─► Value Parse (type-specific parsers)
    │       │
    │       ├─► Temperature: 4.3C → 4.3 (float)
    │       ├─► Fan Speed: 2029RPM → 2029 (int)
    │       ├─► Voltage: 12.26V → 12.26 (float)
    │       ├─► Humidity: 77% → 77.0 (float)
    │       ├─► Battery: 99.9% → 99.9 (float)
    │       └─► Sensor ID: PRIMARY_SENSOR → "PRIMARY"
    │
    ▼
LogEntry Object
```

### Pattern Detection

After parsing, the module provides 5 pattern detection functions:

1. **Temperature Violations** - Detect readings outside 2-8°C range
2. **Telemetry Gaps** - Find gaps > 90 seconds between log entries
3. **Sensor Timeouts** - Track PRIMARY and SECONDARY sensor failures
4. **Alarm Sequences** - Identify ALARM_TRIGGERED events
5. **Door Events** - Match DOOR_OPEN/DOOR_CLOSE pairs with duration

---

## Inputs & Outputs

### Input Formats

| Input Type | Description | Example |
|------------|-------------|---------|
| **Single line** | String with timestamp, type, optional value | `"2026-05-14 14:00:10 TEMP_READING 4.3C"` |
| **Multiple lines** | List of log strings | `List[str]` with multiple log lines |
| **File path** | Path to log file (one line per entry) | `"path/to/device_logs.txt"` |

### Supported Log Types (14 Types)

| LogType | Description | Value Format | Example |
|---------|-------------|--------------|---------|
| `TEMP_READING` | Temperature measurement | `N°C` or `N` | `4.3C`, `5.2°C`, `-1.5` |
| `FAN_SPEED` | Cooling fan RPM | `NRPM` | `2029RPM` |
| `VOLTAGE` | Power voltage | `NV` | `12.26V` |
| `HUMIDITY` | Ambient humidity | `N%` | `77%` |
| `BATTERY_LEVEL` | Battery percentage | `N%` | `99.9%` |
| `DOOR_OPEN` | Door opened event | (no value) | `DOOR_OPEN` |
| `DOOR_CLOSE` | Door closed event | (no value) | `DOOR_CLOSE` |
| `DEVICE_START` | Device startup | (no value) | `DEVICE_START` |
| `ALARM_TRIGGERED` | Alarm activation | (no value) | `ALARM_TRIGGERED` |
| `TEMP_WARNING` | Temperature warning | (no value) | `TEMP_WARNING` |
| `SENSOR_TIMEOUT` | Sensor failure | `PRIMARY_SENSOR` or `SECONDARY_SENSOR` | `SENSOR_TIMEOUT SECONDARY_SENSOR` |
| `TELEMETRY_SYNC_FAILED` | Telemetry sync failure | (no value) | `TELEMETRY_SYNC_FAILED` |
| `COOLING_RECOVERY_START` | Cooling system recovery | (no value) | `COOLING_RECOVERY_START` |

### Output Models

#### LogEntry

```python
class LogParser:
    timestamp: datetime          # When the event occurred
    log_type: LogType          # Enum of supported log types
    raw_value: str             # Original value string from log line
    parsed_value: Optional[Any] # Parsed numeric value (float, int, etc.)
    sensor_id: Optional[str]   # "PRIMARY" or "SECONDARY" for SENSOR_TIMEOUT
    metadata: dict             # Additional context information
```

**Methods:**
- `to_dict()` - Convert to dictionary for JSON serialization

#### ParseResult

```python
class ParseResult:
    entries: List[LogEntry]    # Successfully parsed log entries
    warnings: List[str]          # Non-critical issues (unknown types, parse failures)
    errors: List[str]            # Critical failures (invalid timestamps, file not found)
    total_lines: int             # Total number of lines processed
    success_rate: float          # entries / total_lines (0.0 to 1.0)
```

---

## API Endpoints

The log-parser is exposed via FastAPI endpoints in `backend/app/api/`:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/logs/ingest` | Parse raw log lines from JSON request body |
| `POST` | `/api/logs/ingest/file` | Parse uploaded log file |
| `POST` | `/api/validate` | Parse logs + run full regulatory validation |
| `GET` | `/api/validate/quick-test` | Test endpoint with pre-configured sample data |
| `GET` | `/docs` | Interactive OpenAPI/Swagger documentation |

---

## Mapping to MED-THERM-2026 Regulations

The log-parser provides 5 pattern detection functions that map directly to MED-THERM-2026 regulatory rules:

| Pattern Detector | MED-THERM Rule | Regulation Description | What It Validates |
|------------------|----------------|----------------------|-------------------|
| `detect_temp_violations()` | **REG-TEMP-1** | Maintain internal temperature: 2°C ≤ T ≤ 8°C | Temperature readings outside 2-8°C range |
| `detect_sensor_timeouts()` | **REG-SENS-1** | Dual sensor redundancy: PRIMARY + SECONDARY | Sensor timeout events for PRIMARY/SECONDARY sensors |
| `detect_alarm_sequences()` | **REG-ALARM-1** | Alarm activation for excursions ≥ 2 minutes | ALARM_TRIGGERED events in logs |
| `detect_door_events()` | **REG-OPS-1** | Door opening recovery + temperature stability | DOOR_OPEN/DOOR_CLOSE pairs with duration |
| `detect_telemetry_gaps()` | **REG-DATA-2** | Data gaps in telemetry ≤ 90 seconds | Time gaps > 90s between consecutive log entries |

---

## Public API

### LogParser Class

Main parser class for processing device logs.

```python
from app.regulatory.log_parser import LogParser

parser = LogParser()
```

#### Methods

**parse_line(line: str) → Optional[LogEntry]**

Parse a single log line.

```python
entry = parser.parse_line("2026-05-14 14:00:10 TEMP_READING 4.3C")
# Returns LogEntry object or None if parsing fails
```

**parse_lines(lines: List[str]) → ParseResult**

Parse multiple log lines.

```python
result = parser.parse_lines(list_of_logs)
print(f"Parsed {len(result.entries)} entries")
print(f"Success rate: {result.success_rate:.1%}")
print(f"Warnings: {result.warnings}")
print(f"Errors: {result.errors}")
```

**parse_file(filepath: str) → ParseResult**

Parse log file from disk.

```python
result = parser.parse_file("path/to/device_logs.txt")
```

**parse_stream(filepath: str) → Iterator[LogEntry]**

Stream entries from file for memory-efficient processing of large files.

```python
for entry in parser.parse_stream("large_file.txt"):
    # Process one entry at a time
    if entry.log_type == LogType.TEMP_READING:
        process_temperature(entry.parsed_value)
```

### Pattern Detection Functions

Standalone functions for detecting regulatory patterns in parsed log entries.

```python
from app.regulatory.log_parser import (
    detect_telemetry_gaps,
    detect_sensor_timeouts,
    detect_alarm_sequences,
    detect_door_events,
    detect_temp_violations,
)
```

### Convenience Function (Backward Compatible)

**parse_raw_logs(raw_logs: List[str]) → Tuple[List[LogEntry], List[str]]**

Convenience function for backward compatibility with existing code.

```python
from app.regulatory.log_parser import parse_raw_logs

entries, warnings = parse_raw_logs(raw_logs_list)
# Returns: (List[LogEntry], List[str])
```

---

## Important Implementation Decisions

### 1. Plain Python Classes (Not Pydantic)

**Decision:** `LogEntry` and `ParseResult` use plain Python classes instead of Pydantic models.

**Rationale:**
- Simpler serialization without Pydantic dependencies
- Faster instantiation for high-volume parsing
- Direct control over `to_dict()` method

### 2. Reusable Pattern Detection Functions

**Decision:** Pattern detectors are standalone functions, not methods on `LogParser`.

**Rationale:**
- Functions accept `List[LogEntry]` from any source
- Can be used independently of LogParser class
- Easier to test in isolation
- Configurable thresholds (e.g., `max_gap_seconds=90.0`)

### 3. Streaming Support for Large Files

**Decision:** `parse_stream()` yields entries one at a time using generator pattern.

**Rationale:**
- Critical for handling very large log files (>10K entries)
- Avoids loading entire file into memory
- Enables real-time processing of incoming logs

### 4. Error Handling Strategy

**Decision:** Three-level error handling: warnings, errors, exceptions.

| Level | Handling | Examples | Action |
|-------|----------|----------|--------|
| **Warnings** | Collected, line skipped | Unknown log type, value parse fail | Continue processing |
| **Errors** | Collected, processing continues | File not found, I/O error | Return empty result |
| **Exceptions** | Raised for critical issues | Invalid timestamp format | Propagate to caller |

---

## Usage Examples

### Basic Parsing

```python
from app.regulatory.log_parser import LogParser

raw_logs = [
    "2026-05-14 14:00:10 TEMP_READING 4.3C",
    "2026-05-14 14:00:20 FAN_SPEED 2029RPM",
    "2026-05-14 14:00:30 VOLTAGE 12.26V",
]

parser = LogParser()
result = parser.parse_lines(raw_logs)

print(f"Parsed {len(result.entries)} entries ({result.success_rate:.1%} success)")

for entry in result.entries:
    print(f"{entry.timestamp} | {entry.log_type.value} | {entry.parsed_value}")
```

### Pattern Detection

```python
from app.regulatory.log_parser import (
    LogParser,
    detect_temp_violations,
    detect_telemetry_gaps,
    detect_sensor_timeouts,
)

raw_logs = [
    "2026-05-14 14:00:10 TEMP_READING 4.3C",
    "2026-05-14 14:00:40 TEMP_READING 9.1C",  # Violation
    "2026-05-14 14:05:00 TEMP_READING 5.0C",  # Gap > 90s
    "2026-05-14 14:02:30 SENSOR_TIMEOUT SECONDARY_SENSOR",
]

parser = LogParser()
result = parser.parse_lines(raw_logs)

# Detect temperature violations (REG-TEMP-1)
violations = detect_temp_violations(result.entries)
print(f"Temperature violations: {len(violations)}")

# Detect telemetry gaps (REG-DATA-2)
gaps = detect_telemetry_gaps(result.entries, max_gap_seconds=90.0)
print(f"Telemetry gaps > 90s: {len(gaps)}")

# Detect sensor timeouts (REG-SENS-1)
timeouts = detect_sensor_timeouts(result.entries)
print(f"Sensor timeouts - Primary: {len(timeouts['primary'])}, Secondary: {len(timeouts['secondary'])}")
```

---

## Testing

### Test Coverage

The log-parser module has comprehensive test coverage:

- **Unit tests:** All 14 log types with valid and invalid data
- **Edge cases:** Empty lines, whitespace, malformed timestamps, unknown types
- **Value parsing:** Negative temperatures, decimals, boundary values, unit variations
- **Pattern detection:** All 5 regulatory pattern detectors
- **Integration:** End-to-end parsing with sample log file

### Running Tests

```bash
cd backend
pytest tests/test_log_parser.py -v
```

### Test Data

Primary test fixture: `docs/client/medical_device_logs_1000.txt`

---

## Performance Considerations

### Performance Characteristics

| Metric | Performance | Notes |
|--------|-------------|-------|
| Parsing throughput | ~10,000 lines/second | Depends on CPU and log complexity |
| Memory usage | ~1MB per 10K entries | In-memory processing |
| Pattern detection | O(n) linear scan | Single pass through entries |
| Streaming memory | Constant | Generator pattern, O(1) memory |

### Optimization Strategies

1. **Regex compilation** - Patterns compiled once at module load
2. **Early filtering** - Skip irrelevant log types per rule
3. **Streaming** - Use `parse_stream()` for large files
4. **Batch processing** - Process logs in chunks for very large datasets

---

## Troubleshooting

### Common Issues

**Issue:** "Could not parse line"
- **Cause:** Log format doesn't match `YYYY-MM-DD HH:MM:SS TYPE VALUE`
- **Fix:** Verify log format, check for extra spaces or missing fields

**Issue:** "Invalid timestamp"
- **Cause:** Timestamp format incorrect or invalid date/time values
- **Fix:** Ensure timestamp matches `YYYY-MM-DD HH:MM:SS` format

**Issue:** "Unknown log type"
- **Cause:** Log type not in supported 14 types
- **Fix:** Check log type spelling, verify against supported types list

**Issue:** "File not found"
- **Cause:** Incorrect file path or file doesn't exist
- **Fix:** Verify file path, check file permissions

---

## References

- **OpenSpec Change:** `openspec/changes/archive/2026-05-12-log-parser/`
- **Regulatory Engine:** `docs/architecture/regulatory-engine.md`
- **MED-THERM-2026 Spec:** `docs/user-guide/examples/Medical Device Regulatory Constraints.md`
- **Sample Logs:** `docs/user-guide/examples/medical_device_logs_1000.txt`
- **API Documentation:** http://localhost:8000/docs (when running)
