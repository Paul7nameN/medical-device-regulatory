# Design: Regulatory Engine

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FASTAPI APPLICATION                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐      │
│  │   /api/logs     │     │  /api/validate  │     │  /api/findings  │      │
│  │   (ingestion)   │     │    (engine)     │     │   (reporting)   │      │
│  └────────┬────────┘     └────────┬────────┘     └────────┬────────┘      │
│           │                         │                         │               │
│           └─────────────────────────┼─────────────────────────┘               │
│                                     ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │                        REGULATORY ENGINE CORE                         │     │
│  │                                                                       │     │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐       │     │
│  │  │  PARSER   │  │ NORMALIZER│  │  ENGINE   │  │  FINDINGS │       │     │
│  │  │           │  │           │  │           │  │  GENERATOR │       │     │
│  │  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘       │     │
│  │        │              │              │              │              │     │
│  │        ▼              ▼              ▼              ▼              │     │
│  │  ┌─────────────────────────────────────────────────────────────┐   │     │
│  │  │                      RULE REGISTRY                            │   │     │
│  │  │                                                                 │   │     │
│  │  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │   │     │
│  │  │  │REG-TEMP │ │REG-SENS │ │REG-ALARM│ │REG-DATA │ ...       │   │     │
│  │  │  │ (4 rules)│ │ (3 rules)│ │ (3 rules)│ │ (3 rules)│           │   │     │
│  │  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │   │     │
│  │  └─────────────────────────────────────────────────────────────┘   │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Module Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Settings, environment config
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── logs.py             # POST /api/logs (ingest)
│   │   ├── validate.py         # POST /api/validate (run validation)
│   │   └── findings.py         # GET /api/findings (retrieve results)
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── logs.py             # LogEntry, LogType, SensorReading, etc.
│   │   ├── rules.py            # RuleDefinition, RegulatoryCategory
│   │   └── findings.py         # Finding, Severity, Evidence, ComplianceReport
│   │
│   ├── regulatory/
│   │   ├── __init__.py
│   │   ├── parser.py           # LogParser, parse_raw_logs()
│   │   ├── normalizer.py       # LogNormalizer, normalize_timestamps()
│   │   ├── engine.py           # RegulatoryEngine, validate()
│   │   ├── registry.py         # RuleRegistry, register_rule(), get_rules()
│   │   └── rules/
│   │       ├── __init__.py
│   │       ├── base.py         # BaseRule (abstract base class)
│   │       ├── temp.py         # REG-TEMP-1 to REG-TEMP-4
│   │       ├── sens.py         # REG-SENS-1 to REG-SENS-3
│   │       ├── alarm.py        # REG-ALARM-1 to REG-ALARM-3
│   │       ├── data.py         # REG-DATA-1 to REG-DATA-3
│   │       ├── power.py        # REG-POWER-1 to REG-POWER-2
│   │       ├── cool.py         # REG-COOL-1 to REG-COOL-2
│   │       ├── ins.py          # REG-INS-1 to REG-INS-2
│   │       └── ops.py          # REG-OPS-1 to REG-OPS-2
│   │
│   └── services/
│       ├── __init__.py
│       └── report.py           # ComplianceReportService
│
├── tests/
│   ├── __init__.py
│   ├── test_parser.py          # Log parsing tests
│   ├── test_engine.py          # Engine integration tests
│   └── rules/
│       ├── test_temp.py        # REG-TEMP rules
│       ├── test_sens.py        # REG-SENS rules
│       ├── test_alarm.py       # REG-ALARM rules
│       ├── test_data.py        # REG-DATA rules
│       ├── test_power.py       # REG-POWER rules
│       ├── test_cool.py        # REG-COOL rules
│       ├── test_ins.py         # REG-INS rules
│       └── test_ops.py         # REG-OPS rules
│
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Core Data Models

### Log Entry (Pydantic)

```python
from datetime import datetime
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel

class LogType(str, Enum):
    TEMP_READING = "TEMP_READING"
    FAN_SPEED = "FAN_SPEED"
    VOLTAGE = "VOLTAGE"
    HUMIDITY = "HUMIDITY"
    BATTERY_LEVEL = "BATTERY_LEVEL"
    DOOR_OPEN = "DOOR_OPEN"
    DOOR_CLOSE = "DOOR_CLOSE"
    DEVICE_START = "DEVICE_START"
    ALARM_TRIGGERED = "ALARM_TRIGGERED"
    TEMP_WARNING = "TEMP_WARNING"
    SENSOR_TIMEOUT = "SENSOR_TIMEOUT"
    TELEMETRY_SYNC_FAILED = "TELEMETRY_SYNC_FAILED"
    COOLING_RECOVERY_START = "COOLING_RECOVERY_START"

class LogEntry(BaseModel):
    timestamp: datetime
    log_type: LogType
    raw_value: str
    parsed_value: Optional[Any] = None
    sensor_id: Optional[str] = None
    metadata: dict = {}
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

### Finding & Severity

```python
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel

class Severity(str, Enum):
    CRITICAL = "critical"      # Immediate patient safety risk
    HIGH = "high"              # Significant compliance gap
    MEDIUM = "medium"          # Non-critical deviation
    LOW = "low"                # Minor issue
    INFO = "info"              # Operational insight

class Evidence(BaseModel):
    entry_index: int
    timestamp: datetime
    log_type: str
    raw_value: str
    explanation: str

class Finding(BaseModel):
    rule_id: str                    # e.g., "REG-TEMP-1"
    rule_description: str
    category: str                   # "thermal", "sensor", "alarm", etc.
    severity: Severity
    passed: bool
    message: str
    evidence: List[Evidence] = []
    timestamp: datetime
    remediation_hint: Optional[str] = None

class ComplianceReport(BaseModel):
    device_id: str = "unknown"
    analyzed_at: datetime
    total_entries: int
    time_range_start: Optional[datetime] = None
    time_range_end: Optional[datetime] = None
    
    summary: dict                   # category -> {passed, failed, total}
    findings: List[Finding]
    passed_count: int
    failed_count: int
    critical_count: int
    
    def get_findings_by_severity(self, severity: Severity) -> List[Finding]:
        return [f for f in self.findings if f.severity == severity]
    
    def get_findings_by_rule(self, rule_id: str) -> List[Finding]:
        return [f for f in self.findings if f.rule_id == rule_id]
```

## Rule Base Class Design

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from app.models.logs import LogEntry
from app.models.findings import Finding, Severity, Evidence

class BaseRule(ABC):
    rule_id: str
    description: str
    category: str
    default_severity: Severity
    
    @abstractmethod
    def validate(self, logs: List[LogEntry], context: Dict[str, Any]) -> List[Finding]:
        """
        Validate log entries against this rule.
        
        Args:
            logs: Chronologically sorted list of log entries
            context: Shared context from previous rules / pre-processing
            
        Returns:
            List of findings (may be empty if rule passed)
        """
        pass
    
    def create_finding(
        self,
        passed: bool,
        message: str,
        evidence_logs: Optional[List[LogEntry]] = None,
        severity: Optional[Severity] = None,
        remediation_hint: Optional[str] = None
    ) -> Finding:
        evidence = []
        if evidence_logs:
            for i, log in enumerate(evidence_logs):
                evidence.append(Evidence(
                    entry_index=i,
                    timestamp=log.timestamp,
                    log_type=log.log_type,
                    raw_value=log.raw_value,
                    explanation=f"Log entry {i}: {log.raw_value}"
                ))
        
        return Finding(
            rule_id=self.rule_id,
            rule_description=self.description,
            category=self.category,
            severity=severity or self.default_severity,
            passed=passed,
            message=message,
            evidence=evidence,
            timestamp=datetime.now(),
            remediation_hint=remediation_hint
        )
    
    def create_pass_finding(self) -> Finding:
        return self.create_finding(
            passed=True,
            message=f"Rule {self.rule_id} passed: {self.description}"
        )
```

## Example Rule Implementation (REG-TEMP-1)

```python
from typing import List, Dict, Any
from datetime import datetime, timedelta

from app.regulatory.rules.base import BaseRule
from app.models.logs import LogEntry, LogType
from app.models.findings import Severity

class RegTemp1(BaseRule):
    rule_id = "REG-TEMP-1"
    description = "Maintain internal temperature: 2°C ≤ T ≤ 8°C at all times"
    category = "thermal"
    default_severity = Severity.HIGH
    
    MIN_TEMP = 2.0
    MAX_TEMP = 8.0
    
    def validate(self, logs: List[LogEntry], context: Dict[str, Any]) -> List[Finding]:
        temp_readings = [
            log for log in logs 
            if log.log_type == LogType.TEMP_READING
        ]
        
        if not temp_readings:
            return [self.create_finding(
                passed=False,
                message="No temperature readings found - cannot verify REG-TEMP-1",
                severity=Severity.MEDIUM,
                remediation_hint="Ensure device is configured to log temperature readings"
            )]
        
        violations = []
        for reading in temp_readings:
            temp = reading.parsed_value
            if temp is None:
                continue
            
            if temp < self.MIN_TEMP or temp > self.MAX_TEMP:
                violations.append(reading)
        
        if not violations:
            return [self.create_pass_finding()]
        
        # Check severity - any violation is significant, but pattern matters
        return [self.create_finding(
            passed=False,
            message=f"Found {len(violations)} temperature readings outside range [{self.MIN_TEMP}°C, {self.MAX_TEMP}°C]",
            evidence_logs=violations[:10],  # Limit to first 10 for readability
            severity=Severity.CRITICAL if len(violations) > 3 else Severity.HIGH,
            remediation_hint="Check cooling system performance and door event patterns"
        )]
```

## API Endpoints

### POST /api/logs/ingest
```
Request:
{
  "raw_logs": ["2026-05-14 14:00:10 TEMP_READING 4.3C", ...]
}

Response (200 OK):
{
  "ingested": 1000,
  "normalized": 985,
  "warnings": ["Could not parse line 42: 'invalid format'", ...]
}
```

### POST /api/validate
```
Request:
{
  "logs": [{"timestamp": "2026-05-14T14:00:10", ...}, ...],
  "filter_rules": ["REG-TEMP-1", "REG-SENS-1"],  # optional
  "device_id": "CRYOSAFE-001"  # optional
}

Response (200 OK):
{
  "report": {
    "device_id": "CRYOSAFE-001",
    "analyzed_at": "2026-05-12T14:05:00",
    "total_entries": 1000,
    "summary": {
      "thermal": {"passed": 2, "failed": 2, "total": 4},
      "sensor": {"passed": 1, "failed": 2, "total": 3},
      ...
    },
    "findings": [
      {
        "rule_id": "REG-TEMP-1",
        "category": "thermal",
        "severity": "critical",
        "passed": false,
        "message": "Found 5 temperature readings outside range...",
        "evidence": [...],
        "remediation_hint": "..."
      },
      ...
    ],
    "passed_count": 12,
    "failed_count": 8,
    "critical_count": 3
  }
}
```

### GET /api/health
```
Response (200 OK):
{
  "status": "healthy",
  "rules_loaded": 25,
  "categories": ["thermal", "sensor", "alarm", "data", "power", "cool", "insulation", "operational"]
}
```

## Rule Registry Pattern

```python
from typing import Dict, List, Type, Optional
from app.regulatory.rules.base import BaseRule

class RuleRegistry:
    _rules: Dict[str, Type[BaseRule]] = {}
    _by_category: Dict[str, List[str]] = {}
    
    @classmethod
    def register(cls, rule_class: Type[BaseRule]) -> None:
        cls._rules[rule_class.rule_id] = rule_class
        
        if rule_class.category not in cls._by_category:
            cls._by_category[rule_class.category] = []
        cls._by_category[rule_class.category].append(rule_class.rule_id)
    
    @classmethod
    def get(cls, rule_id: str) -> Optional[Type[BaseRule]]:
        return cls._rules.get(rule_id)
    
    @classmethod
    def get_all(cls) -> List[Type[BaseRule]]:
        return list(cls._rules.values())
    
    @classmethod
    def get_by_category(cls, category: str) -> List[Type[BaseRule]]:
        rule_ids = cls._by_category.get(category, [])
        return [cls._rules[rid] for rid in rule_ids if rid in cls._rules]
    
    @classmethod
    def get_categories(cls) -> List[str]:
        return list(cls._by_category.keys())

# Decorator for auto-registration
def register_rule(cls: Type[BaseRule]) -> Type[BaseRule]:
    RuleRegistry.register(cls)
    return cls

# Usage:
# @register_rule
# class RegTemp1(BaseRule):
#     ...
```

## Engine Execution Flow

```
1. Client POST /api/validate with logs
         │
         ▼
2. RegulatoryEngine.validate(logs)
         │
         ├───► 3. Pre-process: sort by timestamp, build context
         │         │
         │         ├──► Extract time range
         │         ├──► Count door events per hour
         │         ├──► Identify sensor availability
         │         └──► Build temperature time-series
         │
         ├───► 4. Execute rules in dependency order
         │         │
         │         ├──► REG-TEMP (depends on: none)
         │         ├──► REG-SENS (depends on: REG-TEMP for readings)
         │         ├──► REG-ALARM (depends on: REG-TEMP for threshold context)
         │         ├──► REG-DATA (depends on: none - analyzes gaps)
         │         ├──► REG-POWER (depends on: none)
         │         ├──► REG-COOL (depends on: REG-TEMP for excursion analysis)
         │         ├──► REG-INS (depends on: none - needs VLLM for blueprint analysis)
         │         └──► REG-OPS (depends on: REG-TEMP, door events)
         │
         └───► 5. Aggregate findings
                   │
                   ├──► Group by rule/category
                   ├──► Count pass/fail
                   ├──► Rank by severity
                   └──► Generate compliance report
```

## Technology Decisions

| Decision | Rationale | Alternatives Considered |
|----------|-----------|-------------------------|
| **FastAPI** | Modern, async, excellent OpenAPI support, Pydantic integration | Flask, Django REST Framework |
| **Pydantic v2** | Type-safe data validation, excellent JSON serialization, fast | Dataclasses, Marshmallow |
| **Class-based Rules** | Extensible, testable, clear separation of concerns | Function-based, config-driven |
| **In-memory (PoC)** | Simplicity for validation, no DB setup overhead | SQLite, PostgreSQL |
| **Chronological processing** | Rules have temporal dependencies, easier to reason about | Event sourcing |

## Cross-Cutting Concerns

### Logging
- Use Python `logging` module with structured output
- Log each validation run: request ID, rule count, timing
- Log findings summary for audit trail

### Error Handling
- Parse errors: Return warnings array, continue processing valid entries
- Rule execution errors: Log error, mark rule as "error" status in findings
- API errors: Return `{"error": "...", "detail": "..."}` with appropriate HTTP status

### Performance
- PoC: Optimize for correctness first
- Log ingestion: O(n) parsing, single pass
- Validation: O(r * n) where r = rules, n = log entries
- Target: < 1s for 1000 entries (as per success metrics)

## Testing Strategy

### Unit Tests
- Each rule has dedicated test file
- Test happy paths, edge cases, violation scenarios
- Test `BaseRule` helpers (finding creation, evidence handling)

### Integration Tests
- `test_engine.py`: Full validation pipeline
- Test log sample from `docs/client/medical_device_logs_1000.txt`
- Verify expected findings count and severity distribution

### Test Data
- Create synthetic log fixtures for each rule type
- Use actual sample logs as integration test data
- Edge case fixtures: empty logs, single entry, all-violating, all-passing
