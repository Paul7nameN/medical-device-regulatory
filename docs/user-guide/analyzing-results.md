# How to Analyze Results

---

## After Upload, You'll See

### Compliance Score

Compliance score (0-100%):
- **90-100%** - Very good
- **70-89%** - Acceptable
- **Below 70%** - Needs attention

Calculated as:
```
Score = (Rules Passed / Total Rules) × 100
```

### Categories

Which categories have issues:
- **TEMP** - Temperature control
- **SENS** - Sensors
- **ALARM** - Alarms
- **DATA** - Data
- **POWER** - Power
- **COOL** - Cooling
- **INS** - Insulation
- **OPS** - Operations

### Violations

Details about each violation:

| Severity | Required Action |
|----------|-----------------|
| **CRITICAL** | Immediate action (24 hours) |
| **HIGH** | High priority (72 hours) |
| **MEDIUM** | Next maintenance |
| **LOW** | Monitor |

### Temperature Chart

Temperature evolution over time:
- **Blue line** - Sensor A (primary)
- **Purple line** - Sensor B (secondary)
- **Green band** - Safe range (2-8°C)
- **Red/Orange** - Excursions outside range

**Features:**
- Drag to zoom on specific ranges
- Click on legend to show/hide sensors
- Hover on points to see exact value
