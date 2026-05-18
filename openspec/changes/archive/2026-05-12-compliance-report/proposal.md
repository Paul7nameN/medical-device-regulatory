# Proposal: Compliance Report Aggregator

## What

Build a **Compliance Report Aggregator** Python module that:

1. **Aggregates** results from multiple sources:
   - Log Parser (structured log entries)
   - Regulatory Engine (rule-based validation findings)
   - AI Analysis (visual chart analysis, log insights, generated reports)

2. **Produces** structured compliance reports containing:
   - **Violations List** - Mapped to REG-* codes with severity classification
   - **Severity Classification** - Critical/Major/Minor/Info levels based on MED-THERM-2026
   - **Temporal Analysis** - Timeline of events, gap detection, sequence analysis
   - **Actionable Recommendations** - Prioritized remediation steps

3. **Identifies Critical Violations**:
   - **REG-TEMP-1** - Temperature exceedances outside 2-8°C range
   - **REG-SENS-1** - Sensor redundancy failures (primary + secondary timeouts)
   - **REG-ALARM-1** - Delayed alarm activation (excursions ≥2min without alarm)

## Why

### Problem Being Solved

The current system has multiple analysis modules working independently:

1. **Fragmented Results** - Log parser, regulatory engine, and AI analysis produce separate outputs that need manual correlation
2. **No Unified Severity** - Each module uses different severity scales; no consistent prioritization
3. **Missing Temporal Context** - Rule violations aren't analyzed in time sequence to detect patterns
4. **Audit Trail Gaps** - No comprehensive report that auditors can directly use for MED-THERM-2026 compliance
5. **Duplicate Work** - Engineers manually aggregate findings from multiple sources

### Business Need

MED-THERM-2026 compliance requires:
- **Unified audit trails** with clear violation tracking
- **Prioritized remediation** based on severity and timing
- **Cross-source validation** confidence scores
- **Comprehensive reporting** for regulatory submissions

### User Benefits

| Stakeholder | Benefit |
|-------------|---------|
| **QA Team** | Single source of truth for all compliance findings |
| **Engineers** | Prioritized action items with temporal context |
| **Regulatory Team** | Audit-ready reports mapped directly to MED-THERM-2026 rules |
| **Management** | Executive summary with critical vs non-critical breakdown |

## Goals

1. Aggregate findings from log-parser, regulatory-engine, and ai-analysis
2. Map all violations to REG-* rule codes with consistent severity
3. Implement temporal analysis for event sequences and gap detection
4. Generate actionable recommendations prioritized by risk
5. Create API endpoint for unified compliance report generation
6. Maintain backward compatibility with existing `ComplianceReport` model

## Non-Goals

- **New validation rules** - Use existing rules from regulatory-engine
- **Model training** - No AI model changes required
- **Real-time streaming** - Batch report generation only
- **Multi-language support** - English-only for initial implementation
- **PDF generation** - Structured JSON output only (UI can render to PDF)

## Success Metrics

| Metric | Target |
|--------|--------|
| Source Integration | 3 sources aggregated (log-parser, regulatory-engine, ai-analysis) |
| Rule Coverage | All REG-* rules mapped with severity |
| Temporal Features | Timeline, gap analysis, sequence detection |
| API Performance | Report generation < 2 seconds (aggregation only) |
| Test Coverage | 85%+ on aggregation and severity logic |

## Critical Violations Definition

### REG-TEMP-1: Temperature Exceedances

**Classification:** CRITICAL (when >3 violations) or HIGH (1-3 violations)

**Trigger:** Any `TEMP_READING` value outside [2.0°C, 8.0°C] range

**Context from Code (`temp.py:45`):**
```python
severity = Severity.CRITICAL if len(violations) > 3 else Severity.HIGH
```

### REG-SENS-1: Redundancy Failures

**Classification:** CRITICAL (both sensors) or HIGH (single sensor)

**Trigger:** 
- `SENSOR_TIMEOUT` for PRIMARY → HIGH
- `SENSOR_TIMEOUT` for SECONDARY → HIGH
- Both PRIMARY + SECONDARY → CRITICAL

**Context from Code (`sens.py:36-43`):**
```python
if primary_timeout and secondary_timeout:
    severity = Severity.CRITICAL  # Complete redundancy failure
elif secondary_timeout or primary_timeout:
    severity = Severity.HIGH      # Redundancy compromised
```

### REG-ALARM-1: Delayed Alarms

**Classification:** HIGH (default) but with critical implications

**Trigger:** Excursion ≥2 minutes without corresponding `ALARM_TRIGGERED`

**Context from Code (`alarm.py:16-116`):**
```python
ACTIVATION_THRESHOLD = timedelta(minutes=2)
# If excursion ≥ ACTIVATION_THRESHOLD but no ALARM_TRIGGERED during → violation
severity = Severity.HIGH
# Remediation note: "CRITICAL: Verify alarm system is properly configured"
```

## Severity Classification Matrix

| Severity | Level | REG-* Examples | Action Required |
|----------|-------|----------------|-----------------|
| **CRITICAL** | P0 | REG-TEMP-1 (>3 violations), REG-SENS-1 (dual failure) | Immediate investigation, 24-hour response |
| **HIGH** | P1 | REG-TEMP-1 (1-3), REG-SENS-1 (single), REG-ALARM-1, REG-TEMP-2, REG-TEMP-3, REG-SENS-3 | Within 72 hours, prioritize for next maintenance |
| **MEDIUM** | P2 | REG-TEMP-4, REG-DATA-2, REG-ALARM-2 | Next scheduled maintenance window |
| **LOW** | P3 | Minor sampling gaps, insufficient readings | Monitor, no immediate action |
| **INFO** | P4 | REG-SENS-2, REG-ALARM-3 (needs physical verification) | Document, no action required |

## Dependencies

### Existing Modules to Integrate

| Module | Location | Purpose |
|--------|----------|---------|
| **Log Parser** | `backend/app/regulatory/log_parser/` | Structured log entries, event detection |
| **Regulatory Engine** | `backend/app/regulatory/engine.py` | Rule-based validation, `ComplianceReport`, `Finding` |
| **AI Analysis** | `backend/app/ai/` | Chart analysis, log insights, cross-validation |

### Data Models to Extend

| Model | Location | Purpose |
|-------|----------|---------|
| `ComplianceReport` | `backend/app/models/findings.py` | Existing report structure (extend if needed) |
| `Finding` | `backend/app/models/findings.py` | Individual rule findings with severity |
| `Severity` | `backend/app/models/findings.py` | Enum: CRITICAL, HIGH, MEDIUM, LOW, INFO |
| `CrossValidationResult` | `backend/app/ai/image/models.py` | AI cross-validation scores |
| `LogAnalysisResult` | `backend/app/ai/text/models.py` | AI log insights |

### Python Dependencies

- Python 3.11+ (existing)
- `collections` (standard library) for aggregation
- `datetime` (standard library) for temporal analysis
- `typing` (standard library) for type hints
- `pydantic` (existing) for data modeling
- `logging` (standard library) for observability

## Integration Points

### Input Sources

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Log Parser    │     │ Regulatory Engine│     │   AI Analysis   │
├─────────────────┤     ├──────────────────┤     ├─────────────────┤
│ LogEntry list   │────▶│ ComplianceReport │────▶│ ChartAnalysis   │
│ ParseResult     │     │ Finding[]        │     │ LogAnalysis     │
│ Detected events │     │ Severity levels  │     │ CrossValidation │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                      │                         │
         └──────────────────────┼─────────────────────────┘
                                ▼
                    ┌──────────────────────┐
                    │  Compliance Report   │
                    │    Aggregator        │
                    └──────────────────────┘
```

### Output Structure

```python
AggregatedComplianceReport = {
    # Metadata
    "device_id": "CRYOSAFE-001",
    "generated_at": datetime,
    "time_range_start": datetime,
    "time_range_end": datetime,
    
    # Summary
    "summary": {
        "total_findings": 15,
        "critical_count": 2,
        "high_count": 3,
        "medium_count": 4,
        "low_count": 4,
        "info_count": 2,
        "passed_rules": 8,
        "failed_rules": 3
    },
    
    # Violations by Rule
    "violations_by_rule": {
        "REG-TEMP-1": {
            "severity": "CRITICAL",
            "count": 5,
            "findings": [...]
        },
        "REG-SENS-1": {
            "severity": "HIGH",
            "count": 1,
            "findings": [...]
        }
    },
    
    # Temporal Analysis
    "temporal_analysis": {
        "event_timeline": [...],
        "critical_periods": [...],
        "recovery_intervals": [...],
        "gaps_detected": [...]
    },
    
    # AI Enhancements (if available)
    "ai_enhancements": {
        "chart_violations": [...],
        "log_insights": [...],
        "cross_validation_confidence": 0.92
    },
    
    # Recommendations
    "recommendations": [
        {
            "priority": "CRITICAL",
            "rule_id": "REG-TEMP-1",
            "description": "Immediate cooling system investigation...",
            "remediation_hint": "..."
        }
    ]
}
```