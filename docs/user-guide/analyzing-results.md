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

Details about each violation. Violations are sorted by default in order of severity (most critical first):

| Severity | Sort Priority | Required Action |
|----------|---------------|-----------------|
| **CRITICAL** | 1 (highest) | Immediate action (24 hours) |
| **HIGH** | 2 | High priority (72 hours) |
| **MEDIUM** | 3 | Next maintenance |
| **LOW** | 4 | Monitor |
| **INFO** | 5 (lowest) | Information only |

**Sorting:**
- Default: Severity (CRITICAL → HIGH → MEDIUM → LOW → INFO)
- Can also sort by: Rule ID, Category, Timestamp, Message

**Temperature Severity Mapping:**
- **CRITICAL**: T < 0°C or T > 10°C
- **HIGH**: 0°C ≤ T < 2°C or 8°C < T ≤ 10°C
- Within 2-8°C: No violation

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

---

## Multi-Modal Analysis Features

When you upload both log files and chart images, the system provides additional multi-modal analysis capabilities.

### Unified Timeline

The unified timeline shows all violations from all sources in a single chronological view, with badges indicating the source of each violation:

| Badge | Color | Source | Description |
|-------|-------|--------|-------------|
| **Logs** | Blue | Log files | Violations detected from device logs |
| **Chart** | Green | Chart images | Violations extracted from temperature charts |
| **Correlated** | Orange | Both | Violations confirmed by both logs and charts |

**Features:**
- Filter by source (click on legend items to show/hide)
- Hover on violation markers to see details
- Zoom and pan to focus on specific time ranges

### Correlation Insights

When both log and chart data are available, the system analyzes the correlation between findings from both sources:

**Correlation Types:**
| Type | Description | Action |
|------|-------------|--------|
| **Strong Correlation** | Same violation detected in both logs and chart at the same time | High confidence - prioritize remediation |
| **Weak Correlation** | Violation detected in one source but not the other (timing mismatch) | Verify time alignment, check for partial coverage |
| **Conflicting** | One source shows violation, other shows compliant data at same time | Investigate - may indicate sensor issue or chart misinterpretation |

**Correlation Summary:**
- Number of correlated findings
- Number of conflicting findings
- Overall confidence score

### Alignment Uncertainty Banner

If the system detects potential time alignment issues between log files and chart images, it shows a warning banner:

**When it appears:**
- Chart time range doesn't match log time range
- Alignment confidence < 0.7
- Significant gaps between log and chart data points

**What to do:**
- Check that log files and chart images cover the same time period
- Verify chart timestamps are correct
- Consider uploading additional data for better alignment
