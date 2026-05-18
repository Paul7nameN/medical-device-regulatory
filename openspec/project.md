# MED-THERM Compliance Platform

## Project Overview

**Name:** MED-THERM Compliance Platform  
**Vision:** AI-driven compliance and operational intelligence platform for regulated medical devices  
**Status:** Proof of Concept

## Domain Context

Portable temperature-controlled plasma transport units require continuous validation against the **MED-THERM-2026** regulatory standard. This platform ingests heterogeneous data sources (logs, images, documents) and validates them against regulatory constraints to produce structured compliance reports.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React |
| Backend | Python (FastAPI) |
| Database | PostgreSQL |
| VLLM Integration | API layer for vision/language models |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      React Frontend                           │
│  • Upload Interface  • Validation Dashboard  • Report Viewer │
└───────────────────────┬─────────────────────────────────────┘
                        │
         ┌──────────────┼──────────────┐
         ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  /api/logs   │ │ /api/images  │ │ /api/docs    │
│  ingestion   │ │  analysis    │ │  parsing      │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                 │                 │
       └─────────────────┼─────────────────┘
                         ▼
              ┌──────────────────────┐
              │   Validation Engine   │
              │  (MED-THERM-2026)    │
              └──────────┬───────────┘
                         ▼
              ┌──────────────────────┐
              │     PostgreSQL        │
              │ (Logs, Findings,      │
              │  Reports, VLLM cache) │
              └──────────┬───────────┘
                         ▼
              ┌──────────────────────┐
              │    VLLM Gateway       │
              │ (Image understanding, │
              │  Document extraction) │
              └──────────────────────┘
```

## In Scope (PoC)

- **Data Ingestion:** System logs (time-series), images (charts, schematics), regulatory documents
- **Validation Engine:** MED-THERM-2026 rules codified as executable constraints
- **VLLM Integration:** API endpoints for image analysis (chart data extraction, schematic validation) and document parsing (requirement extraction)
- **Compliance Report:** Structured output with severity classification, evidence linking, explainable conclusions
- **No Auth:** Single-user PoC, no authentication/role-based access

## MED-THERM-2026 Regulatory Standard

### 1. Thermal Safety (REG-TEMP)

| ID | Requirement |
|----|-------------|
| REG-TEMP-1 | Maintain internal temperature: 2°C ≤ T ≤ 8°C at all times |
| REG-TEMP-2 | Excursion limits: max 5min per event, 10min cumulative per 24h |
| REG-TEMP-3 | Recovery time: ≤ 3 minutes after disturbance |
| REG-TEMP-4 | Sampling frequency: ≤ 30 seconds interval |

### 2. Sensor Redundancy & Accuracy (REG-SENS)

| ID | Requirement |
|----|-------------|
| REG-SENS-1 | At least one primary + one redundant secondary sensor |
| REG-SENS-2 | Sensors must not be placed within 15cm of airflow outlet |
| REG-SENS-3 | Sensor agreement: \|T1 - T2\| ≤ 0.5°C |

### 3. Alarm System Regulations (REG-ALARM)

| ID | Requirement |
|----|-------------|
| REG-ALARM-1 | Activate if temperature out of range for ≥ 2 minutes |
| REG-ALARM-2 | Notification latency: ≤ 10 seconds |
| REG-ALARM-3 | Support: audible + visual dashboard + remote mobile |

### 4. Data Integrity & Logging (REG-DATA)

| ID | Requirement |
|----|-------------|
| REG-DATA-1 | Immutable audit log: temp readings, alarms, config changes, sensor status |
| REG-DATA-2 | Data gaps: ≤ 90 seconds |
| REG-DATA-3 | Local retention: ≥ 72 hours |

### 5. Power System Regulations (REG-POWER)

| ID | Requirement |
|----|-------------|
| REG-POWER-1 | Battery backup: ≥ 4 hours continuous operation |
| REG-POWER-2 | Temperature compliance maintained in battery mode |

### 6. Cooling System Requirements (REG-COOL)

| ID | Requirement |
|----|-------------|
| REG-COOL-1 | At least 2 airflow paths |
| REG-COOL-2 | Single-point failure tolerance: ≤ 3 minutes excursion |

### 7. Structural & Insulation Requirements (REG-INS)

| ID | Requirement |
|----|-------------|
| REG-INS-1 | Insulation thickness: ≥ 4 cm on all chamber walls |
| REG-INS-2 | Battery compartment physically/thermally isolated from storage |

### 8. Operational Behavior Constraints (REG-OPS)

| ID | Requirement |
|----|-------------|
| REG-OPS-1 | After door opening: stabilize within 3min, not exceed 8°C during recovery |
| REG-OPS-2 | Access frequency warning: > 10 door events/hour triggers warning |

## Severity Classification

| Level | Description |
|-------|-------------|
| **Critical** | Immediate patient safety risk, regulatory non-compliance (e.g., REG-TEMP-2, REG-SENS-1 violations) |
| **High** | Significant compliance gap requiring immediate attention |
| **Medium** | Non-critical deviation requiring remediation |
| **Low** | Minor issue, warning, or observation |
| **Info** | Operational insight without compliance impact |

## Data Ingestion Formats

### Logs (Sample from docs/client/medical_device_logs_1000.txt)
```
2026-05-14 14:00:10 TEMP_READING 4.3C
2026-05-14 14:00:20 FAN_SPEED 2029RPM
2026-05-14 14:00:30 TELEMETRY_SYNC_FAILED
2026-05-14 14:02:30 SENSOR_TIMEOUT SECONDARY_SENSOR
```

### Images
- Temperature charts (line/scatter plots) - extract time-series data
- System dashboards - interpret visual indicators
- Engineering blueprints/schematics - validate physical layout constraints

### Documents
- Regulatory compliance documentation - extract structured requirements
- Engineering specifications - map against constraints, identify gaps

## Expected Outputs

The system produces a structured compliance report containing:

1. **Executive Summary** - Overall compliance status
2. **Regulatory Category Breakdown** - Pass/fail by REG-* category
3. **Detailed Findings** - Each violation with:
   - Regulatory reference
   - Severity level
   - Evidence timestamp(s) and source
   - Explanation of the violation
4. **Temporal Analysis** - Event sequences, excursion patterns
5. **Root Cause Correlation** - Cross-modal findings linking logs, charts, and diagrams
6. **Recommendations** - Prioritized remediation actions

## Conventions & Guidelines

- **Frontend:** React with TypeScript preferred, use existing component patterns in codebase
- **Backend:** FastAPI with Pydantic models for validation
- **Database:** PostgreSQL with SQLAlchemy ORM, migrations via Alembic
- **API Design:** RESTful, JSON request/response, OpenAPI/Swagger documentation
- **Validation Rules:** Implement as modular, testable rule classes per REG-* ID
- **VLLM Integration:** Abstract behind interface to support multiple providers (OpenAI GPT-4V, Anthropic Claude, etc.)
- **Error Handling:** Structured error responses, logging correlation IDs, audit trails
- **Testing:** pytest for Python, Jest for React - aim for high coverage on validation rules
