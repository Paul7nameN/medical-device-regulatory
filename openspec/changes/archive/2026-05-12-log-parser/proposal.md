# Proposal: Log Parser

## What

Build a **Log Parser** Python module that:

1. **Parses** device logs with format: `TIMESTAMP EVENT_TYPE VALUE`
2. **Extracts** structured data: timestamps, event types, values
3. **Detects** key patterns for regulatory validation:
   - Telemetry gaps over 90 seconds (REG-DATA-2)
   - `SENSOR_TIMEOUT` events (REG-SENS-1)
   - `ALARM_TRIGGERED` sequences (REG-ALARM-1)
   - `DOOR_OPEN`/`DOOR_CLOSE` events (REG-OPS-1)
   - `TEMP_READING` values outside 2-8°C range (REG-TEMP-1)

## Why

**Problem Being Solved:**

The regulatory engine currently uses inline parsing logic. As the system scales, we need:

- **Better separation of concerns** - Dedicated parser module
- **Testability** - Isolated parsing logic easier to unit test
- **Error handling** - Comprehensive error messages for malformed lines
- **Extensibility** - Support for future log formats

**User Benefits:**

| Stakeholder | Benefit |
|-------------|---------|
| QA Team | Clear error messages for malformed log lines |
| Engineers | Isolated parser logic - easier to debug |
| Regulatory Team | Confidence in pattern detection accuracy |

## Goals

1. Parse `YYYY-MM-DD HH:MM:SS EVENT_TYPE VALUE` format
2. Extract 14 supported log types
3. Detect 5 key regulatory patterns
4. 100% parsing accuracy on sample log data
5. Comprehensive error handling

## Non-Goals

- **Database persistence** - Stateless parsing only
- **Network requests** - No external dependencies
- **Log validation** - Just parsing, not validation rules
- **Complex transformations** - Extract only, don't modify

## Success Metrics

| Metric | Target |
|--------|--------|
| Log Type Coverage | All 14 types |
| Pattern Detection | 5 key patterns |
| Error Handling | All malformed lines produce warnings |
| Test Coverage | 90%+ on parsing logic |

## Log Types Supported

| Type | Description | Example |
|------|-------------|---------|
| TEMP_READING | Temperature | `TEMP_READING 4.3C` |
| FAN_SPEED | Fan RPM | `FAN_SPEED 2029RPM` |
| VOLTAGE | Power voltage | `VOLTAGE 12.26V` |
| HUMIDITY | Humidity | `HUMIDITY 77%` |
| BATTERY_LEVEL | Battery | `BATTERY_LEVEL 99.9%` |
| DOOR_OPEN | Door open | `DOOR_OPEN` |
| DOOR_CLOSE | Door close | `DOOR_CLOSE` |
| DEVICE_START | Device start | `DEVICE_START` |
| ALARM_TRIGGERED | Alarm | `ALARM_TRIGGERED` |
| TEMP_WARNING | Temp warning | `TEMP_WARNING` |
| SENSOR_TIMEOUT | Sensor fail | `SENSOR_TIMEOUT SECONDARY_SENSOR` |
| TELEMETRY_SYNC_FAILED | Sync fail | `TELEMETRY_SYNC_FAILED` |
| COOLING_RECOVERY_START | Cooling start | `COOLING_RECOVERY_START` |

## Regulatory Patterns Detected

| Pattern | Rule | Description |
|---------|------|-------------|
| Telemetry gaps | REG-DATA-2 | Gaps > 90s between entries |
| Sensor timeouts | REG-SENS-1 | `SENSOR_TIMEOUT PRIMARY/SECONDARY` |
| Alarm sequences | REG-ALARM-1 | `ALARM_TRIGGERED` events |
| Door events | REG-OPS-1 | `DOOR_OPEN`/`DOOR_CLOSE` pairs |
| Temp violations | REG-TEMP-1 | `TEMP_READING` outside 2-8°C |

## Dependencies

- Python 3.11+
- `re` module (standard library)
- `datetime` module (standard library)
- Pydantic (existing in project)
