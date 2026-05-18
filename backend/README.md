# MED-THERM Compliance Engine

Regulatory compliance validation engine for medical device temperature-controlled transport units.

## Overview

This Python backend validates device logs against the **MED-THERM-2026** regulatory standard.

### Regulatory Categories (25 Rules)

| Category | Rules | Description |
|----------|-------|-------------|
| **Thermal** | REG-TEMP 1-4 | Temperature range, excursions, recovery, sampling |
| **Sensor** | REG-SENS 1-3 | Redundancy, placement, agreement |
| **Alarm** | REG-ALARM 1-3 | Activation, latency, channels |
| **Data** | REG-DATA 1-3 | Immutable logs, gaps, retention |
| **Power** | REG-POWER 1-2 | Battery runtime, degraded mode |
| **Cooling** | REG-COOL 1-2 | Airflow paths, failure tolerance |
| **Insulation** | REG-INS 1-2 | Thickness, battery isolation |
| **Operational** | REG-OPS 1-2 | Door recovery, access frequency |

## Quick Start

### Installation

```bash
cd backend
pip install -r requirements.txt
```

### Run API Server

```bash
uvicorn app.main:app --reload --port 8000
```

### API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Health & Rules

```bash
# Health check
GET /api/health

# List all rules
GET /api/health/rules

# List categories
GET /api/health/categories
```

### Log Ingestion

```bash
# Ingest logs from raw lines
POST /api/logs/ingest
Content-Type: application/json

{
  "raw_logs": [
    "2026-05-14 14:00:10 TEMP_READING 4.3C",
    "2026-05-14 14:00:20 FAN_SPEED 2029RPM"
  ]
}

# Ingest from file upload
POST /api/logs/ingest/file
Content-Type: multipart/form-data
```

### Validation

```bash
# Validate logs
POST /api/validate
Content-Type: application/json

{
  "raw_logs": [...],
  "device_id": "CRYOSAFE-001",
  "filter_rules": ["REG-TEMP-1", "REG-SENS-1"]  # optional
}

# Quick test with sample data
GET /api/validate/quick-test
```

## Log Format

The parser supports logs in this format:

```
2026-05-14 14:00:10 TEMP_READING 4.3C
2026-05-14 14:00:20 FAN_SPEED 2029RPM
2026-05-14 14:01:00 VOLTAGE 12.26V
2026-05-14 14:02:10 HUMIDITY 77%
2026-05-14 14:07:40 BATTERY_LEVEL 99.9%
2026-05-14 14:04:50 DOOR_OPEN
2026-05-14 14:01:20 DOOR_CLOSE
2026-05-14 14:00:00 ALARM_TRIGGERED
2026-05-14 14:09:20 TEMP_WARNING
2026-05-14 14:02:30 SENSOR_TIMEOUT SECONDARY_SENSOR
2026-05-14 14:00:30 TELEMETRY_SYNC_FAILED
2026-05-14 14:01:30 COOLING_RECOVERY_START
2026-05-14 14:00:50 DEVICE_START
```

## Severity Levels

| Level | Description |
|-------|-------------|
| **critical** | Immediate patient safety risk, regulatory non-compliance |
| **high** | Significant compliance gap requiring immediate attention |
| **medium** | Non-critical deviation requiring remediation |
| **low** | Minor issue, warning, or observation |
| **info** | Operational insight without compliance impact |

## Testing

```bash
cd backend
pytest -v
```

Test files:
- `tests/test_parser.py` - Log parsing tests
- `tests/test_engine.py` - Engine integration tests
- `tests/rules/` - Rule-specific unit tests

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Settings
│   │
│   ├── api/
│   │   ├── health.py        # GET /api/health, /api/health/rules
│   │   ├── logs.py          # POST /api/logs/ingest
│   │   └── validate.py      # POST /api/validate
│   │
│   ├── models/
│   │   ├── logs.py          # LogEntry, LogType
│   │   └── findings.py      # Finding, Severity, ComplianceReport
│   │
│   └── regulatory/
│       ├── parser.py        # LogParser
│       ├── normalizer.py    # LogNormalizer
│       ├── engine.py        # RegulatoryEngine
│       ├── registry.py      # RuleRegistry
│       └── rules/
│           ├── base.py      # BaseRule abstract class
│           ├── temp.py      # REG-TEMP 1-4
│           ├── sens.py      # REG-SENS 1-3
│           ├── alarm.py     # REG-ALARM 1-3
│           ├── data.py      # REG-DATA 1-3
│           ├── power.py     # REG-POWER 1-2
│           ├── cool.py      # REG-COOL 1-2
│           ├── ins.py       # REG-INS 1-2
│           └── ops.py       # REG-OPS 1-2
│
├── tests/
│   ├── test_parser.py
│   ├── test_engine.py
│   └── rules/
│
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Example: Validate Sample Logs

```python
from app.regulatory.parser import parse_raw_logs
from app.regulatory.engine import RegulatoryEngine

sample_logs = [
    "2026-05-14 14:00:10 TEMP_READING 4.3C",
    "2026-05-14 14:00:40 TEMP_READING 9.1C",  # Violation!
    "2026-05-14 14:02:30 SENSOR_TIMEOUT SECONDARY_SENSOR",
]

entries, warnings = parse_raw_logs(sample_logs)
engine = RegulatoryEngine()
report = engine.validate(entries, device_id="test-device")

print(f"Passed: {report.passed_count}")
print(f"Failed: {report.failed_count}")
print(f"Critical: {report.critical_count}")

for finding in report.findings:
    if not finding.passed:
        print(f"[{finding.severity.value}] {finding.rule_id}: {finding.message}")
```

## Related Documentation

- `../docs/client/Medical Device Regulatory Constraints.md` - Full MED-THERM-2026 specification
- `../docs/client/medical_device_logs_1000.txt` - Sample log data
- `../openspec/` - OpenSpec project definition and change artifacts
