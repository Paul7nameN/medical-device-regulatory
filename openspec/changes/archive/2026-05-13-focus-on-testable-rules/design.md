## Context

The MED-THERM Compliance Engine validates 25 rules across 8 categories. Analysis of the sample data (`medical_device_logs_1000.txt`, temperature images) reveals that only **12-15 rules** can be actually tested with the available data types.

**Sample Log Analysis (medical_device_logs_1000.txt):**
- 1000 lines over ~16 minutes
- Temperature readings: 4.3°C → 5.2°C (all within 2-8°C range)
- **PROBLEMS DETECTED:**
  - `SENSOR_TIMEOUT SECONDARY_SENSOR` (multiple times!) → REG-SENS-1 violation
  - `TELEMETRY_SYNC_FAILED` (multiple times) → REG-DATA-2 violation
  - `ALARM_TRIGGERED` events present but temps in-range → needs investigation
  - `DOOR_OPEN` events frequent → REG-OPS-2 check

**Constraints:**
- Python + FastAPI backend
- SQLAlchemy ORM
- Existing rule structure uses `@register_rule` decorator
- Reports aggregate findings with severity classification

## Goals / Non-Goals

**Goals:**
1. Explicitly tag each rule with its required data source
2. Allow engine to filter rules by data source
3. Enhance reports to show "Verified from Logs" vs "Needs Inspection"
4. Fix REG-SENS-3 to handle single-sensor vs dual-sensor data

**Non-Goals:**
1. Do NOT remove any rules - just categorize them
2. Do NOT change severity levels for existing rules
3. Do NOT break existing API contracts
4. Do NOT implement new validation logic - just categorization

## Decisions

### 1. ValidationSource Enum
**Decision**: Create explicit enum for data sources

```python
from enum import Enum

class ValidationSource(Enum):
    LOGS = "logs"           # Fully testable from system logs
    IMAGES = "images"       # Requires VLM/AI image analysis
    INSPECTION = "inspection"  # Requires physical inspection
    COMBINED = "combined"   # Needs multiple sources
```

**Rationale**: Clear, type-safe categorization that can be used for filtering

### 2. Rule Base Class Enhancement
**Decision**: Add `data_source` and `confidence` fields to BaseRule

```python
class BaseRule:
    rule_id: str
    description: str
    category: str
    default_severity: Severity
    data_source: ValidationSource = ValidationSource.LOGS  # NEW
    confidence: float = 1.0  # NEW - 1.0 = fully testable
    
    # For inspection-only rules:
    inspection_hint: Optional[str] = None
```

**Rationale**: Each rule self-declares what data it needs

### 3. Engine Filtering
**Decision**: Add `include_sources` parameter to `validate_all()`

```python
def validate_all(
    self, 
    logs: List[LogEntry], 
    context: Dict = None,
    include_sources: Optional[List[ValidationSource]] = None  # NEW
) -> ValidationResult:
```

**Rationale**: Caller can decide what rules to run based on available data

### 4. Report Structure Enhancement
**Decision**: Separate findings into sections in report output

```json
{
  "summary": {...},
  "verified_from_logs": {
    "total_rules": 12,
    "passed": 9,
    "failed": 3,
    "findings": [...]
  },
  "partially_testable": {
    "notes": "REG-SENS-3: Only single sensor data available",
    "findings": [...]
  },
  "needs_physical_inspection": {
    "rules": ["REG-SENS-2", "REG-ALARM-2", "REG-ALARM-3", "REG-COOL-1", "REG-INS-1", "REG-INS-2"],
    "findings": [...]
  }
}
```

### 5. Rule Categorization Mapping

| Rule ID | Data Source | Confidence | Notes |
|---------|-------------|------------|-------|
| REG-TEMP-1 | LOGS | 1.0 | TEMP_READING values |
| REG-TEMP-2 | LOGS | 1.0 | TEMP_READING + timing |
| REG-TEMP-3 | LOGS | 1.0 | TEMP_READING + DOOR_OPEN |
| REG-TEMP-4 | LOGS | 1.0 | TEMP_READING interval |
| REG-SENS-1 | LOGS | 1.0 | SENSOR_TIMEOUT events |
| REG-SENS-2 | INSPECTION | 0.0 | Needs blueprint/measurement |
| REG-SENS-3 | COMBINED | 0.7 | Needs dual-sensor data to fully verify |
| REG-ALARM-1 | LOGS | 1.0 | TEMP_READING + ALARM_TRIGGERED |
| REG-ALARM-2 | INSPECTION | 0.0 | Needs end-to-end timing test |
| REG-ALARM-3 | INSPECTION | 0.0 | Needs 3-channel verification |
| REG-DATA-1 | LOGS | 1.0 | Log structure + DB RLS |
| REG-DATA-2 | LOGS | 1.0 | TELEMETRY_SYNC_FAILED + gaps |
| REG-DATA-3 | COMBINED | 0.5 | Needs 72h of data |
| REG-POWER-1 | COMBINED | 0.6 | Can estimate from drain rate |
| REG-POWER-2 | LOGS | 0.9 | VOLTAGE + TEMP_READING |
| REG-COOL-1 | INSPECTION | 0.0 | Needs inspection/blueprint |
| REG-COOL-2 | LOGS | 0.8 | TEMP_READING + COOLING_RECOVERY_START |
| REG-INS-1 | INSPECTION | 0.0 | Needs physical measurement |
| REG-INS-2 | INSPECTION | 0.0 | Needs inspection |
| REG-OPS-1 | LOGS | 1.0 | DOOR_OPEN + TEMP_READING |
| REG-OPS-2 | LOGS | 1.0 | DOOR_OPEN frequency |

**Image-Analyzable Rules** (via VLM):
- REG-TEMP-1 (from temperature charts)
- REG-TEMP-2 (from temperature charts)
- REG-TEMP-3 (from temperature charts with door events)
- REG-OPS-1 (from temperature charts)
- Plus future: REG-SENS-2, REG-COOL-1, REG-INS-1, REG-INS-2 from blueprints

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Report users confused by new sections | Keep old format available, add `format` parameter |
| Breaking existing API consumers | Make `include_sources` optional (defaults to ALL) |
| REG-SENS-3 false negatives | Add clear INFO finding when only single sensor data |
| Inspection rules being ignored | Highlight them prominently in reports with "Action Required" |

## Migration Plan

1. **Add ValidationSource enum** in base.py
2. **Update each rule** with `data_source` field
3. **Update engine.py** with filter support
4. **Enhance report aggregator** with new sections
5. **Test with sample log** to verify detection of:
   - SENSOR_TIMEOUT SECONDARY → REG-SENS-1 violation
   - TELEMETRY_SYNC_FAILED → REG-DATA-2 violation
   - Frequent DOOR_OPEN → REG-OPS-2 check

**Rollback Strategy**: Remove `data_source` field - it's optional/defaults to LOGS
