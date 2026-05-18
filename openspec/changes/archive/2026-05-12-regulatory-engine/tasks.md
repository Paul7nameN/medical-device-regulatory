# Tasks: Regulatory Engine

## Implementation Tasks

### Phase 1: Project Setup & Foundation

- [x] **1.1** Create backend project structure (`backend/` directory with Python package layout
  - Create `app/`, `app/api/`, `app/models/`, `app/regulatory/`, `app/regulatory/rules/`, `tests/`
  - Create `requirements.txt` with FastAPI, Pydantic, pytest, python-multipart
  - Create `pyproject.toml` with project configuration

- [x] **1.2** Implement core Pydantic models
  - `app/models/logs.py`: `LogType` enum, `LogEntry` model
  - `app/models/findings.py`: `Severity` enum, `Evidence`, `Finding`, `ComplianceReport`
  - `app/models/rules.py`: `RegulatoryCategory` helpers

- [x] **1.3** Create BaseRule abstract class
  - `app/regulatory/rules/base.py`: `BaseRule` with `validate()` abstract method
  - Implement `create_finding()` helper with evidence generation
  - Implement `create_pass_finding()` convenience method

- [x] **1.4** Implement RuleRegistry pattern
  - `app/regulatory/registry.py`: `RuleRegistry` class
  - `register_rule` decorator for auto-registration
  - Methods: `get()`, `get_all()`, `get_by_category()`, `get_categories()`

---

### Phase 2: Log Ingestion Pipeline

- [x] **2.1** Implement LogParser
  - `app/regulatory/parser.py`: `LogParser` class
  - Parse raw log lines from `docs/client/medical_device_logs_1000.txt` format
  - Handle all `2026-05-14 14:00:10 TEMP_READING 4.3C` → `LogEntry`
  - Parse values: temperature (float with °C), fan speed (RPM), voltage (V), humidity (%), battery (%)
  - Handle `SENSOR_TIMEOUT SECONDARY_SENSOR` → extract sensor_id

- [x] **2.2** Implement LogNormalizer
  - `app/regulatory/normalizer.py`: `LogNormalizer` class
  - Sort entries chronologically
  - Fill gaps identification (for REG-DATA-2 validation prep)
  - Build context: time range, door events per hour, sensor availability stats

- [x] **2.3** Build FastAPI log ingestion endpoint
  - `app/api/logs.py`: `POST /api/logs/ingest`
  - Accept `raw_logs` array or file upload
  - Return `{ingested, normalized, warnings}
  - Add input validation with Pydantic

---

### Phase 3: Validation Rules Implementation (25 Rules)

#### Category: Thermal Safety (REG-TEMP 1-4)

- [x] **3.1** REG-TEMP-1: Temperature range (2°C ≤ T ≤ 8°C)
  - `app/regulatory/rules/temp.py`: `RegTemp1`
  - Filter `LogType.TEMP_READING` entries
  - Check each reading in valid range
  - Generate evidence for violations, severity based on count

- [x] **3.2** REG-TEMP-2: Excursion limits
  - `RegTemp2`: max 5min per event, 10min cumulative/24h
  - Detect contiguous out-of-range periods
  - Track cumulative duration
  - Critical severity if exceeded

- [x] **3.3** REG-TEMP-3: Recovery time ≤ 3min
  - `RegTemp3`: After disturbance (door opening)
  - Detect door events, monitor recovery
  - Measure time to return to range
  - Flag if > 3min recovery

- [x] **3.4** REG-TEMP-4: Sampling frequency ≤ 30s
  - `RegTemp4`: Check interval between readings
  - Calculate time deltas between consecutive TEMP_READING
  - Flag gaps > 30 seconds

#### Category: Sensor Redundancy (REG-SENS 1-3)

- [x] **3.5** REG-SENS-1: Dual sensors present
  - `app/regulatory/rules/sens.py`: `RegSens1`
  - Check for PRIMARY + SECONDARY sensor presence
  - Detect `SENSOR_TIMEOUT` events
  - Critical if redundancy lost

- [x] **3.6** REG-SENS-2: Placement constraint (needs VLLM)
  - `RegSens2`: ≥15cm from airflow outlet
  - Note: This requires image analysis - for log-only PoC, mark as "needs_visual_verification"
  - Return INFO finding: "Requires schematic analysis"

- [x] **3.7** REG-SENS-3: Sensor agreement ±0.5°C
  - `RegSens3`: |T1 - T2| ≤ 0.5°C
  - Compare primary/secondary readings at same timestamps
  - Calculate differences, flag violations

#### Category: Alarm System (REG-ALARM 1-3)

- [x] **3.8** REG-ALARM-1: Activation delay ≥ 2min
  - `app/regulatory/rules/alarm.py`: `RegAlarm1`
  - Detect temp out of range, check if alarm triggered after 2min
  - If no `ALARM_TRIGGERED` within window, flag

- [x] **3.9** REG-ALARM-2: Notification latency ≤ 10s
  - `RegAlarm2`: Alarm to notification time
  - Note: Logs don't have notification timestamps
  - Info finding: "Limited log visibility - track `ALARM_TRIGGERED` to any response

- [x] **3.10** REG-ALARM-3: Three channels (audible + visual + mobile
  - `RegAlarm3`: Check alarm types present
  - Log-only: Can't fully verify from logs alone
  - Info: Logs show `ALARM_TRIGGERED` events only
  - Document limitation

#### Category: Data Integrity (REG-DATA 1-3)

- [x] **3.11** REG-DATA-1: Immutable audit log
  - `app/regulatory/rules/data.py`: `RegData1`
  - Conceptual - at app level, not log validation
  - Info: "System ensures immutability - log entries are append-only
  - No deletion/modification detected (design-level guarantee)

- [x] **3.12** REG-DATA-2: Data gaps ≤ 90s
  - `RegData2`: Telemetry continuity
  - Analyze all log entry time deltas
  - Flag gaps > 90 seconds
  - `TELEMETRY_SYNC_FAILED` counts

- [x] **3.13** REG-DATA-3: 72h retention
  - `RegData3`: Local data retention
  - Info-level: System design requirement
  - Check log time span if available
  - Otherwise: "Requires full device config verification

#### Category: Power System (REG-POWER 1-2)

- [x] **3.14** REG-POWER-1: ≥4h battery runtime
  - `app/regulatory/rules/power.py`: `RegPower1`
  - Note: Can't verify full runtime from short log sample
  - Track `BATTERY_LEVEL` drain rate
  - Info: Extrapolate if trend visible

- [x] **3.15** REG-POWER-2: Battery mode compliance
  - `RegPower2`: Temp compliance on battery
  - Check `VOLTAGE` drops (battery mode indicators)
  - Correlate with temp readings during those periods
  - Ensure REG-TEMP-1 holds

#### Category: Cooling System (REG-COOL 1-2)

- [x] **3.16** REG-COOL-1: ≥2 airflow paths
  - `app/regulatory/rules/cool.py`: `RegCool1`
  - `FAN_SPEED` readings indicate fans
  - Count distinct fan sources?
  - Info: Needs schematic for full verification

- [x] **3.17** REG-COOL-2: 3min failure tolerance
  - `RegCool2`: Single-point failure
  - Detect fan anomalies (if `FAN_SPEED`=0` or drops
  - Monitor temp during those periods
  - Flag if excursion > 3min

#### Category: Structural (REG-INS 1-2)

- [x] **3.18** REG-INS-1: ≥4cm insulation
  - `app/regulatory/rules/ins.py`: `RegIns1`
  - VLLM/blueprint only
  - Info: "Requires physical inspection or blueprint analysis

- [x] **3.19** REG-INS-2: Battery isolation
  - `RegIns2`: Thermal/physical isolation
  - Info: "Requires schematic analysis

#### Category: Operational (REG-OPS 1-2)

- [x] **3.20** REG-OPS-1: Door recovery ≤ 3min + ≤8°C
  - `app/regulatory/rules/ops.py`: `RegOps1`
  - `DOOR_OPEN` → `DOOR_CLOSE` events
  - Monitor temp during recovery
  - Check stabilization + temp max

- [x] **3.21** REG-OPS-2: ≤10 door events/hour warning
  - `RegOps2`: Access frequency
  - Count `DOOR_OPEN` per rolling hour
  - Warning if > 10

---

### Phase 4: Regulatory Engine Core

- [x] **4.1** Implement RegulatoryEngine
  - `app/regulatory/engine.py`: `RegulatoryEngine` class
  - `validate(logs, filter_rules=None)` method
  - Pre-process: sort, build context dict
  - Execute rules in order
  - Aggregate findings

- [x] **4.2** Implement rule auto-discovery/auto-registration
  - Import all rule classes in `app/regulatory/rules/__init__.py`
  - Decorate with `@register_rule`
  - 25 rules total

- [x] **4.3** Build validation endpoint
  - `app/api/validate.py`: `POST /api/validate`
  - Accept logs (or log entries or raw)
  - Optional `filter_rules`, `device_id`
  - Return `ComplianceReport` JSON

- [x] **4.4** Health endpoint
  - `app/api/health.py`: `GET /api/health`
  - Return `{status, rules_loaded, categories}`

---

### Phase 5: Testing

- [x] **5.1** Parser tests
  - `tests/test_parser.py`
  - Test sample log lines
  - Test edge cases: malformed lines, missing values

- [x] **5.2** Rule unit tests
  - `tests/rules/test_temp.py`: REG-TEMP 1-4
  - `tests/rules/test_sens.py`: REG-SENS 1-3
  - `tests/rules/test_alarm.py`: REG-ALARM 1-3
  - `tests/rules/test_data.py`: REG-DATA 1-3
  - `tests/rules/test_power.py`: REG-POWER 1-2
  - `tests/rules/test_cool.py`: REG-COOL 1-2
  - `tests/rules/test_ins.py`: REG-INS 1-2
  - `tests/rules/test_ops.py`: REG-OPS 1-2

- [x] **5.3** Engine integration tests
  - `tests/test_engine.py`
  - Use actual `docs/client/medical_device_logs_1000.txt`
  - End-to-end validation
  - Check expected findings

---

### Phase 6: App Entry & Polish

- [x] **6.1** FastAPI app factory
  - `app/main.py`: FastAPI instance
  - Include routers: logs, validate, health
  - CORS middleware
  - OpenAPI docs at `/docs`

- [x] **6.2** Configuration
  - `app/config.py`: Settings
  - Environment variables if needed

- [x] **6.3** README
  - Quick start: install, run, test
  - API endpoints docs

## Dependencies

| Task | Depends On |
|------|------------|
| All rule implementations | 1.1-1.4 (foundation |
| 2.1-2.3 (ingestion) | 1.2 (models) |
| 3.1-3.21 (rules) | 1.3 (BaseRule), 1.4 (Registry) |
| 4.1-4.4 (engine/api) | All rules, ingestion |
| 5.1-5.3 (tests) | All implementation |
| 6.1-6.3 (app) | All phases |

## Estimated Complexity

| Phase | Complexity | Notes |
|-------|----------|-------|
| Phase 1 | Low | Setup, models, base classes |
| Phase 2 | Low-Medium | Log parsing edge cases |
| Phase 3 | High | 25 rules, many with temporal logic |
| Phase 4 | Medium | Engine orchestration |
| Phase 5 | Medium | Comprehensive test coverage |
| Phase 6 | Low | App wiring |

## Notes

- **VLLM-dependent rules (REG-SENS-2, REG-INS-1, REG-INS-2):
  - These require visual/blueprint analysis
  - For PoC, return INFO findings explaining limitation
  - Indicate "needs_visual_verification"
  - Future: VLLM integration will fill these gaps

- **Log sample from `docs/client/medical_device_logs_1000.txt`**:
  - Has: TEMP_READING, FAN_SPEED, VOLTAGE, HUMIDITY, BATTERY_LEVEL
  - Has: DOOR_OPEN/DOOR_CLOSE, DEVICE_START
  - Has: ALARM_TRIGGERED, TEMP_WARNING
  - Has: SENSOR_TIMEOUT SECONDARY_SENSOR
  - Has: TELEMETRY_SYNC_FAILED
  - Use this as primary test fixture

- **Severity guide**:
  - CRITICAL: REG-TEMP-2 excursion exceed, REG-SENS-1 redundancy fail
  - HIGH: Most REG-TEMP violations, sensor agreement
  - MEDIUM: Missing data, gaps
  - LOW/INFO: Warnings, limitations, design checks
