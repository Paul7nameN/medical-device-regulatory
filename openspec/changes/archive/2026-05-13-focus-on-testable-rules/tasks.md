## 1. Core Infrastructure

- [x] 1.1 Add `ValidationSource` enum to `backend/app/regulatory/rules/base.py`
  - Values: LOGS, IMAGES, INSPECTION, COMBINED
  - Add `data_source: ValidationSource = ValidationSource.LOGS` to BaseRule
  - Add `confidence: float = 1.0` field for partial testability
  - Add `inspection_hint: Optional[str] = None` for inspection-only rules

- [x] 1.2 Update `backend/app/regulatory/engine.py` with source filtering
  - Add `include_sources` parameter to `validate()`
  - Add `exclude_sources` parameter for flexibility
  - Add `get_sources()` method to engine
  - Update `get_rule_info()` and `get_all_rules()` to return source info

## 2. Update Thermal Rules (temp.py)

- [x] 2.1 REG-TEMP-1: `data_source=ValidationSource.LOGS`, `confidence=1.0`
- [x] 2.2 REG-TEMP-2: `data_source=ValidationSource.LOGS`, `confidence=1.0`
- [x] 2.3 REG-TEMP-3: `data_source=ValidationSource.LOGS`, `confidence=1.0`
- [x] 2.4 REG-TEMP-4: `data_source=ValidationSource.LOGS`, `confidence=1.0`

## 3. Update Sensor Rules (sens.py)

- [x] 3.1 REG-SENS-1: `data_source=ValidationSource.LOGS`, `confidence=1.0`
- [x] 3.2 REG-SENS-2: `data_source=ValidationSource.INSPECTION`, `confidence=0.0`, `inspection_hint="Verify sensor placement ≥15cm from airflow outlets. Use blueprint analysis or physical measurement."`
- [x] 3.3 REG-SENS-3: `data_source=ValidationSource.COMBINED`, `confidence=0.7`
  - Enhancement: Detect if only single sensor readings available
  - Return INFO finding: "Only single sensor data - cannot verify sensor agreement."

## 4. Update Alarm Rules (alarm.py)

- [x] 4.1 REG-ALARM-1: `data_source=ValidationSource.LOGS`, `confidence=1.0`
- [x] 4.2 REG-ALARM-2: `data_source=ValidationSource.INSPECTION`, `confidence=0.0`, `inspection_hint="Requires end-to-end notification timing test: alarm trigger → mobile delivery ≤10s."`
- [x] 4.3 REG-ALARM-3: `data_source=ValidationSource.INSPECTION`, `confidence=0.0`, `inspection_hint="Verify all 3 notification channels: audible alarm, visual dashboard alert, remote mobile notification."`

## 5. Update Data Integrity Rules (data.py)

- [x] 5.1 REG-DATA-1: `data_source=ValidationSource.LOGS`, `confidence=1.0`
- [x] 5.2 REG-DATA-2: `data_source=ValidationSource.LOGS`, `confidence=1.0`
- [x] 5.3 REG-DATA-3: `data_source=ValidationSource.COMBINED`, `confidence=0.5`

## 6. Update Power Rules (power.py)

- [x] 6.1 REG-POWER-1: `data_source=ValidationSource.COMBINED`, `confidence=0.6`
- [x] 6.2 REG-POWER-2: `data_source=ValidationSource.LOGS`, `confidence=0.9`

## 7. Update Cooling Rules (cool.py)

- [x] 7.1 REG-COOL-1: `data_source=ValidationSource.INSPECTION`, `confidence=0.0`, `inspection_hint="Verify ≥2 independent airflow paths. Check for redundant fans and separate cooling loops via blueprint or physical inspection."`
- [x] 7.2 REG-COOL-2: `data_source=ValidationSource.LOGS`, `confidence=0.8`

## 8. Update Insulation Rules (ins.py)

- [x] 8.1 REG-INS-1: `data_source=ValidationSource.INSPECTION`, `confidence=0.0`, `inspection_hint="Measure insulation thickness on all chamber walls. Minimum 4cm required. Use caliper measurement or review engineering specifications."`
- [x] 8.2 REG-INS-2: `data_source=ValidationSource.INSPECTION`, `confidence=0.0`, `inspection_hint="Verify physical barrier between battery compartment and storage chamber. Check for thermal isolation features."`

## 9. Update Operational Rules (ops.py)

- [x] 9.1 REG-OPS-1: `data_source=ValidationSource.LOGS`, `confidence=1.0`
- [x] 9.2 REG-OPS-2: `data_source=ValidationSource.LOGS`, `confidence=1.0`

## 10. Report Enhancement (Optional - For Future)

- [ ] 10.1 Update `backend/app/reports/aggregator.py`
  - Add `group_by_source()` method
  - Create sections: verified_from_logs, partially_testable, needs_inspection
- [ ] 10.2 Update `backend/app/api/reports.py`
  - Add optional `sources` query parameter for filtering
  - Keep backward compatibility (default: all sources)
- [ ] 10.3 Update severity classifier for inspection rules
  - Inspection rules should return INFO (not PASS/FAIL)
  - Add "Action Required" flag for inspection-needed findings

## 11. Testing & Validation

- [ ] 11.1 Run existing pytest suite to ensure no regressions
- [x] 11.2 Test with `medical_device_logs_1000.txt`
  - ✅ Verify REG-SENS-1 detects SECONDARY_SENSOR timeout
  - ✅ Verify REG-DATA-2 detects TELEMETRY_SYNC_FAILED
  - ✅ Verify REG-OPS-2 checks door frequency
  - ✅ Detected 10 FAILED rules including CRITICAL temperature excursions
- [x] 11.3 Test filter functionality
  - ✅ `include_sources=[LOGS]` runs 12 rules
  - ✅ `exclude_sources=[INSPECTION]` excludes 6 rules
  - ✅ Total: 12 LOGS, 6 INSPECTION, 3 COMBINED

## Rezumat Implementare

**Completate:** 24/29 task-uri

**Rule Categorization:**
| Source | Count | Rules |
|--------|-------|-------|
| LOGS | 12 | TEMP-1/2/3/4, SENS-1, ALARM-1, DATA-1/2, POWER-2, COOL-2, OPS-1/2 |
| INSPECTION | 6 | SENS-2, ALARM-2/3, COOL-1, INS-1/2 |
| COMBINED | 3 | SENS-3, DATA-3, POWER-1 |

**Test Results on medical_device_logs_1000.txt:**
- 10 FAILED rules detected (including 2 CRITICAL)
- REG-SENS-1: SECONDARY sensor timeout detected
- REG-DATA-2: 68 telemetry sync failures
- REG-TEMP-1: 25 temperature readings outside [2-8°C] (max 11.8°C)
