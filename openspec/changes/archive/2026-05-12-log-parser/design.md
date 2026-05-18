# Design: Log Parser

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Log Parser Module                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────┐                   │
│  │    INPUT     │      │    OUTPUT    │                   │
│  │              │      │              │                   │
│  │ Raw log lines│─────▶│  LogEntry    │                   │
│  │    or file   │      │  ParseResult │                   │
│  └──────────────┘      └──────────────┘                   │
│         │                     │                           │
│         └─────────────────────┘                           │
│                        ▼                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Core Parsing Components                │   │
│  │                                                     │   │
│  │  ┌──────────┐  ┌──────────┐  ┌────────────────┐ │   │
│  │  │ Patterns │  │  Values  │  │  LogParser     │ │   │
│  │  │  (regex) │  │ (parsers)│  │   (orchestrator)│ │   │
│  │  └──────────┘  └──────────┘  └────────────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Module Structure

```
backend/app/regulatory/
├── log_parser/
│   ├── __init__.py
│   ├── log_parser.py      # Main LogParser class
│   ├── patterns.py        # Regex pattern definitions
│   ├── value_parsers.py   # Value extraction functions
│   ├── exceptions.py      # Custom exception classes
│   └── models.py          # LogEntry, LogType, ParseResult
└── parser.py              # Existing - imports from log_parser
```

## Regex Patterns

### Main Log Pattern

```python
LOG_PATTERN = re.compile(
    r'^(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})\s+(\w+)(?:\s+(.*))?$'
)
```

**Captures:**
1. Date: `YYYY-MM-DD`
2. Time: `HH:MM:SS`
3. Event type: `WORD`
4. Raw value (optional): `anything after`

### Value Patterns

```python
TEMP_PATTERN = re.compile(r'(-?[\d.]+)\s*[°C]?')
FAN_PATTERN = re.compile(r'(\d+)\s*RPM')
VOLTAGE_PATTERN = re.compile(r'([\d.]+)\s*V')
HUMIDITY_PATTERN = re.compile(r'([\d.]+)\s*%')
BATTERY_PATTERN = re.compile(r'([\d.]+)\s*%')
```

## Data Models

### LogEntry

```python
class LogEntry(BaseModel):
    timestamp: datetime
    log_type: LogType
    raw_value: str
    parsed_value: Optional[Any] = None
    sensor_id: Optional[str] = None
    metadata: dict = {}
```

### LogType Enum

```python
class LogType(str, Enum):
    TEMP_READING = "TEMP_READING"
    FAN_SPEED = "FAN_SPEED"
    VOLTAGE = "VOLTAGE"
    HUMIDITY = "HUMIDITY"
    BATTERY_LEVEL = "BATTERY_LEVEL"
    DOOR_OPEN = "DOOR_OPEN"
    DOOR_CLOSE = "DOOR_CLOSE"
    DEVICE_START = "DEVICE_START"
    ALARM_TRIGGERED = "ALARM_TRIGGERED"
    TEMP_WARNING = "TEMP_WARNING"
    SENSOR_TIMEOUT = "SENSOR_TIMEOUT"
    TELEMETRY_SYNC_FAILED = "TELEMETRY_SYNC_FAILED"
    COOLING_RECOVERY_START = "COOLING_RECOVERY_START"
```

### ParseResult

```python
class ParseResult(BaseModel):
    entries: List[LogEntry]
    warnings: List[str]
    errors: List[str]
    total_lines: int
    success_rate: float
```

## LogParser Class

```python
class LogParser:
    def __init__(self):
        self.warnings: List[str] = []
        self.errors: List[str] = []

    def parse_line(self, line: str) -> Optional[LogEntry]:
        """Parse a single log line."""
        pass

    def parse_lines(self, lines: List[str]) -> ParseResult:
        """Parse multiple log lines."""
        pass

    def parse_file(self, filepath: str) -> ParseResult:
        """Parse log file."""
        pass

    def parse_stream(self, filepath: str) -> Iterator[LogEntry]:
        """Stream entries from file for memory efficiency."""
        pass
```

## Value Parsing Functions

```python
def parse_temperature(raw_value: str) -> Optional[float]:
    """Parse temperature value (handles °C unit)."""
    pass

def parse_fan_speed(raw_value: str) -> Optional[int]:
    """Parse fan speed (handles RPM unit)."""
    pass

def parse_voltage(raw_value: str) -> Optional[float]:
    """Parse voltage (handles V unit)."""
    pass

def parse_humidity(raw_value: str) -> Optional[float]:
    """Parse humidity (handles % unit)."""
    pass

def parse_battery_level(raw_value: str) -> Optional[float]:
    """Parse battery level (handles % unit)."""
    pass

def extract_sensor_id(raw_value: str, log_type: str) -> Optional[str]:
    """Extract sensor ID from SENSOR_TIMEOUT events."""
    pass
```

## Error Handling

### Warnings (Non-critical)

| Situation | Example | Handling |
|-----------|---------|----------|
| Unknown log type | `UNKNOWN_TYPE value` | Warning, skip |
| Value parse fail | `bad-value` | Warning, use raw |
| Empty line | `""` | Skip silently |

### Errors (Critical)

| Situation | Example | Handling |
|-----------|---------|----------|
| Invalid timestamp | `invalid-date` | Error, skip |
| File not found | `nonexistent.txt` | Error, return empty |

### Custom Exceptions

```python
class ParseError(Exception):
    """Base exception for parsing errors."""
    pass

class InvalidTimestampError(ParseError):
    """Invalid timestamp format."""
    pass

class UnknownLogTypeError(ParseError):
    """Unknown log event type."""
    pass
```

## Pattern Detection Logic

### Telemetry Gaps (REG-DATA-2)

```python
def detect_telemetry_gaps(entries: List[LogEntry], 
                           max_gap_seconds: float = 90.0
                           ) -> List[Dict]:
    """Detect gaps > max_gap_seconds between consecutive entries."""
    gaps = []
    for i in range(1, len(entries)):
        gap_seconds = (entries[i].timestamp - 
                      entries[i-1].timestamp).total_seconds()
        if gap_seconds > max_gap_seconds:
            gaps.append({
                "from": entries[i-1].timestamp,
                "to": entries[i].timestamp,
                "gap_seconds": gap_seconds
            })
    return gaps
```

### Sensor Timeouts (REG-SENS-1)

```python
def detect_sensor_timeouts(entries: List[LogEntry]
                           ) -> Dict[str, List[Dict]]:
    """Detect PRIMARY/SECONDARY sensor timeout events."""
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
```

### Alarm Sequences (REG-ALARM-1)

```python
def detect_alarm_sequences(entries: List[LogEntry]
                           ) -> List[Dict]:
    """Detect ALARM_TRIGGERED event sequences."""
    alarms = []
    for entry in entries:
        if entry.log_type == LogType.ALARM_TRIGGERED:
            alarms.append({
                "timestamp": entry.timestamp
            })
    return alarms
```

### Door Events (REG-OPS-1)

```python
def detect_door_events(entries: List[LogEntry]
                       ) -> List[Dict]:
    """Detect DOOR_OPEN/DOOR_CLOSE event pairs."""
    events = []
    open_time: Optional[datetime] = None
    
    for entry in entries:
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
```

### Temperature Violations (REG-TEMP-1)

```python
def detect_temp_violations(entries: List[LogEntry],
                            min_temp: float = 2.0,
                            max_temp: float = 8.0
                            ) -> List[Dict]:
    """Detect TEMP_READING outside valid range."""
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
```

## Integration With Existing Code

### Backward Compatibility

The existing `parse_raw_logs()` function in `regulatory/parser.py` should be updated to use the new LogParser:

```python
# In app/regulatory/parser.py

from app.regulatory.log_parser import LogParser

def parse_raw_logs(raw_logs: List[str]) -> Tuple[List[LogEntry], List[str]]:
    """Convenience function for backward compatibility."""
    parser = LogParser()
    result = parser.parse_lines(raw_logs)
    return result.entries, result.warnings
```

## Performance Considerations

### Pattern Compilation

Compile regex patterns once at initialization for ~10x performance:

```python
class LogParser:
    def __init__(self):
        self.log_pattern = re.compile(LOG_PATTERN)
        self.temp_pattern = re.compile(TEMP_PATTERN)
        # ... compile all patterns
```

### Streaming for Large Files

For files > 10K entries, use streaming to avoid loading all into memory:

```python
def parse_stream(self, filepath: str) -> Iterator[LogEntry]:
    with open(filepath, 'r') as f:
        for line in f:
            entry = self.parse_line(line.strip())
            if entry:
                yield entry
```

## Testing Strategy

### Unit Tests

| Test Category | What to Test |
|---------------|--------------|
| Happy paths | All 14 log types with valid data |
| Edge cases | Empty lines, whitespace, malformed timestamps |
| Value parsing | Negative temps, decimals, boundary values |
| Error handling | Unknown types, invalid formats |

### Test Data

Use `docs/client/medical_device_logs_1000.txt` as primary test fixture.

### Example Tests

```python
def test_parse_temp_reading():
    line = "2026-05-14 14:00:10 TEMP_READING 4.3C"
    entry = parser.parse_line(line)
    assert entry.log_type == LogType.TEMP_READING
    assert entry.parsed_value == 4.3

def test_sensor_timeout():
    line = "2026-05-14 14:02:30 SENSOR_TIMEOUT SECONDARY_SENSOR"
    entry = parser.parse_line(line)
    assert entry.log_type == LogType.SENSOR_TIMEOUT
    assert entry.sensor_id == "SECONDARY"

def test_malformed_timestamp():
    line = "invalid-date 14:00:10 TEMP_READING 4.3C"
    entry = parser.parse_line(line)
    assert entry is None
    assert len(parser.warnings) >= 1
```
