## Why

The MED-THERM Compliance Platform currently validates ALL 25 regulatory rules from MED-THERM-2026, but many of these rules CANNOT be verified with the available data types:

**Available Data:**
- System logs (`medical_device_logs_1000.txt`) with: TEMP_READING, VOLTAGE, BATTERY_LEVEL, FAN_SPEED, HUMIDITY, DOOR_OPEN/DOOR_CLOSE, ALARM_TRIGGERED, TEMP_WARNING, SENSOR_TIMEOUT, TELEMETRY_SYNC_FAILED, DEVICE_START, COOLING_RECOVERY_START
- Temperature profile images (`compliant_temperature_profile.png`, `noncompliant_temperature_profile.png`)

**Data NOT Available:**
- Physical inspection data (sensor placement, insulation thickness)
- Blueprint/schematic images
- End-to-end notification timing data
- 72-hour retention test data
- Multi-channel alarm verification

**Current Problem:**
Rules that require physical inspection return `INFO` findings, but users may confuse these with actual test results. The engine should clearly separate:
1. Rules that can be FULLY validated from logs
2. Rules that need additional data (images via AI)
3. Rules that need physical inspection

## What Changes

### Categorization of Rules by Data Source

| Source | Rules | Count |
|--------|-------|-------|
| **Logs (Fully Testable)** | REG-TEMP-1, REG-TEMP-2, REG-TEMP-3, REG-TEMP-4, REG-SENS-1, REG-ALARM-1, REG-DATA-1, REG-DATA-2, REG-POWER-2, REG-COOL-2, REG-OPS-1, REG-OPS-2 | 12 |
| **Logs (Partially Testable)** | REG-SENS-3, REG-DATA-3, REG-POWER-1 | 3 |
| **Images (AI/VLM Required)** | REG-TEMP-1 (chart), REG-TEMP-2 (chart), REG-TEMP-3 (chart), REG-OPS-1 (chart) | 4 |
| **Physical Inspection Only** | REG-SENS-2, REG-ALARM-2, REG-ALARM-3, REG-COOL-1, REG-INS-1, REG-INS-2 | 6 |

### Technical Changes

1. **Add `data_source` field to each rule** - explicit categorization
2. **Add `ValidationSource` enum** - LOGS, IMAGES, INSPECTION, COMBINED
3. **Engine filter option** - run only rules from specific sources
4. **Report enhancement** - clearly separate "Tested" vs "Needs Inspection" sections
5. **REG-SENS-3 enhancement** - detect if we have dual-sensor data or just single-sensor

## Capabilities

### New Capabilities
- `rule-categorization`: Explicit data source tagging for all rules
- `engine-filtering`: Run only testable rules based on available data
- `report-sections`: Clear separation of verified vs inspection-needed findings

### Modified Capabilities
- `regulatory-engine`: Updated to support source filtering and categorization
- `compliance-reporting`: Enhanced to show data source for each finding

## Impact

- Backend: `backend/app/regulatory/rules/` - each rule file updated
- Backend: `backend/app/regulatory/engine.py` - add filter support
- Backend: `backend/app/reports/` - enhanced report sections
- No breaking changes - existing behavior preserved with new opt-in filtering
