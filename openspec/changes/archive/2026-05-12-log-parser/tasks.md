# Tasks: Log Parser

## Implementation Tasks

### Phase 1: Project Setup

- [x] **1.1** Create log_parser module structure
  - Create `backend/app/regulatory/log_parser/` directory
  - Create `__init__.py` for package

- [x] **1.2** Create Pydantic models
  - `models.py`: `LogType` enum, `LogEntry`, `ParseResult` classes
  - Uses existing Pydantic from project

---

### Phase 2: Core Parsing Logic

- [x] **2.1** Implement regex patterns
  - `patterns.py`: Define all regex patterns
  - `LOG_PATTERN`: Main log line pattern
  - Value patterns: `TEMP_PATTERN`, `FAN_PATTERN`, `VOLTAGE_PATTERN`, `HUMIDITY_PATTERN`, `BATTERY_PATTERN`

- [x] **2.2** Implement value parsers
  - `value_parsers.py`: Parsing functions
  - `parse_temperature()`: Handle °C unit
  - `parse_fan_speed()`: Handle RPM unit
  - `parse_voltage()`: Handle V unit
  - `parse_humidity()`: Handle % unit
  - `parse_battery_level()`: Handle % unit

- [x] **2.3** Implement sensor ID extraction
  - `value_parsers.py`: `extract_sensor_id()`
  - Handle `SENSOR_TIMEOUT PRIMARY_SENSOR` → `sensor_id: "PRIMARY"`
  - Handle `SENSOR_TIMEOUT SECONDARY_SENSOR` → `sensor_id: "SECONDARY"`

---

### Phase 3: LogParser Class

- [x] **3.1** Implement LogParser class
  - `log_parser.py`: Main parser class
  - `__init__()`: Initialize warning/error lists
  - `parse_line()`: Parse single line → `Optional[LogEntry]`
  - `parse_lines()`: Parse multiple lines → `ParseResult`
  - `parse_file()`: Read and parse file → `ParseResult`
  - `parse_stream()`: Stream entries from file → `Iterator[LogEntry]`

- [x] **3.2** Implement error handling
  - `exceptions.py`: Custom exception classes
  - `ParseError`: Base exception
  - `InvalidTimestampError`: Invalid timestamp format
  - `UnknownLogTypeError`: Unknown log event type
  - Collect warnings for non-critical issues
  - Collect errors for critical failures

---

### Phase 4: Pattern Detection

- [x] **4.1** Implement telemetry gap detection
  - `patterns.py` or new detection module
  - `detect_telemetry_gaps()`: Find gaps > 90s
  - Returns list of gap objects with timestamps

- [x] **4.2** Implement sensor timeout detection
  - `detect_sensor_timeouts()`: Find PRIMARY/SECONDARY timeouts
  - Returns dict with primary/secondary timeout lists

- [x] **4.3** Implement alarm sequence detection
  - `detect_alarm_sequences()`: Find ALARM_TRIGGERED events
  - Returns list of alarm timestamps

- [x] **4.4** Implement door event detection
  - `detect_door_events()`: Match DOOR_OPEN/DOOR_CLOSE pairs
  - Returns list of door events with duration

- [x] **4.5** Implement temperature violation detection
  - `detect_temp_violations()`: Find readings outside 2-8°C
  - Returns list of violation objects

---

### Phase 5: Integration

- [x] **5.1** Update existing parser module
  - Update `app/regulatory/parser.py`
  - Import from `log_parser` module
  - Maintain backward compatible `parse_raw_logs()` signature
  - Returns tuple: `(entries, warnings)`

- [x] **5.2** Add module exports
  - Update `log_parser/__init__.py`
  - Export `LogParser`, `LogType`, `LogEntry`, `ParseResult`
  - Export convenience functions

---

### Phase 6: Testing

- [x] **6.1** Create unit tests
  - `tests/test_log_parser.py`: Test suite
  - Test all 14 log types
  - Test edge cases (empty lines, malformed data)
  - Test value parsing (negative temps, decimals)
  - Test error handling (unknown types, invalid timestamps)

- [x] **6.2** Create pattern detection tests
  - Test telemetry gap detection
  - Test sensor timeout detection
  - Test alarm sequence detection
  - Test door event detection
  - Test temperature violation detection

- [x] **6.3** Create integration tests
  - Use `docs/client/medical_device_logs_1000.txt`
  - Verify parsing accuracy
  - Verify pattern detection works on real data

---

### Phase 7: Documentation

- [x] **7.1** Update module documentation
  - `README.md` or `docs/log-parser.md`
  - Document supported log types
  - Document pattern detection functions
  - Provide usage examples

## Dependencies

| Task | Depends On |
|------|------------|
| 1.2 | 1.1 (module structure) |
| 2.1 | 1.2 (models) |
| 2.2 | 1.2 (models) |
| 2.3 | 1.2 (models) |
| 3.1 | 2.1, 2.2, 2.3 (patterns + parsers) |
| 3.2 | 3.1 (LogParser) |
| 4.1 | 3.1 (LogParser) |
| 4.2 | 3.1 (LogParser) |
| 4.3 | 3.1 (LogParser) |
| 4.4 | 3.1 (LogParser) |
| 4.5 | 3.1 (LogParser) |
| 5.1 | 3.1 (LogParser) |
| 5.2 | 3.1 (LogParser) |
| 6.1 | 3.1, 4.x (LogParser + pattern detection) |
| 6.2 | 4.x (pattern detection) |
| 6.3 | 3.1, 4.x (LogParser + pattern detection) |
| 7.1 | 3.1, 4.x, 5.x (implementation) |

## Estimated Complexity

| Phase | Complexity | Notes |
|-------|------------|-------|
| Phase 1 | Low | Module structure and models |
| Phase 2 | Low | Regex patterns and value parsing |
| Phase 3 | Low-Medium | Main LogParser class |
| Phase 4 | Low | Pattern detection functions |
| Phase 5 | Low | Integration with existing code |
| Phase 6 | Medium | Comprehensive test coverage |
| Phase 7 | Low | Documentation |

## Notes

- **Backward Compatibility:** Must maintain existing `parse_raw_logs()` function signature
- **Performance:** Regex patterns compiled at initialization
- **Sample Data:** Use `docs/client/medical_device_logs_1000.txt` for testing
- **14 Log Types:** All types must be supported
- **5 Regulatory Patterns:** All patterns must be detectable

## Checkpoints

- [x] All models defined
- [x] All regex patterns implemented
- [x] All value parsers working
- [x] LogParser class complete
- [x] All 5 pattern detection functions implemented
- [x] Backward compatibility maintained
- [x] All tests passing
- [x] Documentation updated
