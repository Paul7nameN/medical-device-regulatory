# Proposal: Regulatory Engine

## What

Build a Python backend module (**Regulatory Engine**) that:

1. **Parses** MED-THERM-2026 regulatory constraints from structured definitions into executable validation rules
2. **Ingests** and normalizes device log data (time-series temperature readings, sensor events, alarms, system status)
3. **Validates** log data against all 25 regulatory rules across 8 categories:
   - **REG-TEMP** (1-4): Thermal safety (2-8°C range, excursions, recovery time, sampling frequency)
   - **REG-SENS** (1-3): Sensor redundancy (dual sensors, placement constraints, ±0.5°C agreement)
   - **REG-ALARM** (1-3): Alarm system (2min activation, 10s latency, 3 notification channels)
   - **REG-DATA** (1-3): Data integrity (immutable logs, ≤90s gaps, 72h retention)
   - **REG-POWER** (1-2): Power system (≥4h battery, degraded mode compliance)
   - **REG-COOL** (1-2): Cooling system (≥2 airflow paths, 3min failure tolerance)
   - **REG-INS** (1-2): Structural insulation (≥4cm thickness, battery isolation)
   - **REG-OPS** (1-2): Operational behavior (door recovery, access frequency)
4. **Generates** structured compliance findings with:
   - Severity classification (Critical → High → Medium → Low → Info)
   - Evidence linking (timestamps, log entries)
   - Explainable violation descriptions
   - Regulatory reference IDs

## Why

**Business Need:** The client requires a Proof of Concept for an AI-driven compliance platform for regulated medical devices (portable temperature-controlled plasma transport units). Manual compliance auditing is slow, error-prone, and cannot scale to analyze heterogeneous data sources at scale.

**Problem Being Solved:**

- **Manual analysis bottleneck:** Engineers and QA teams spend hours reviewing logs, charts, and documents
- **Human error in complex rule application:** MED-THERM-2026 has 25 interrelated rules with temporal dependencies
- **Lack of explainable evidence:** Audit trails need clear, timestamped evidence linking violations to specific log entries
- **No systematic cross-correlation:** Violations detected in one modality (e.g., logs) aren't correlated with visual evidence (e.g., charts)

**User Benefits:**

| Stakeholder | Benefit |
|-------------|---------|
| QA Team | Automated log validation in seconds vs. hours |
| Engineers | Root cause analysis with temporal correlations |
| Regulatory Team | Structured compliance reports with audit-ready evidence |
| Management | Clear severity-based prioritization of remediation |

## Goals

1. Parse and represent all 25 MED-THERM-2026 rules as executable code
2. Ingest and normalize logs from `docs/client/medical_device_logs_1000.txt` format
3. Achieve 100% rule coverage for the 8 regulatory categories
4. Generate findings with severity classification and evidence linking
5. Create FastAPI endpoints for log ingestion and validation
6. Expose OpenAPI/Swagger documentation

## Non-Goals

- **VLLM Integration** - Out of scope for this change (handled separately)
- **User Authentication** - Single-user PoC, no auth required
- **Database Persistence** - For initial PoC, can be in-memory first
- **Frontend UI** - Backend API only in this change
- **Image/Document Analysis** - Log-only validation in this iteration
- **Report Generation** - JSON output only, PDF/HTML report later

## Success Metrics

| Metric | Target |
|--------|--------|
| Rule Coverage | 25/25 MED-THERM-2026 rules implemented |
| Log Throughput | Process 1000 log entries in < 1 second |
| API Latency | Validation endpoint < 200ms p95 |
| Test Coverage | 80%+ on validation rule logic |
| Severity Accuracy | All Critical violations correctly identified |

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Temporal rule complexity (e.g., REG-TEMP-2 cumulative excursions) | High | High | Build stateful rule evaluators with comprehensive tests |
| Log format variations across devices | Medium | Medium | Design flexible parser with adapter pattern |
| Rule inter-dependencies (e.g., alarm rules depend on temp readings) | High | Medium | Implement explicit rule ordering and dependency graph |
| Performance on large log datasets | Medium | Low | Initial PoC optimizes for correctness first, profile later |

## Dependencies

- Python 3.11+
- FastAPI for API endpoints
- Pydantic for data modeling
- pytest for testing

## Open Questions

1. **Rule Configuration:** Should rules be defined in YAML (editable) or hardcoded in Python?
   - *Recommendation:* Start with Python classes for PoC speed, add YAML serialization later

2. **Time Zone Handling:** Are device logs in UTC or local time?
   - *Recommendation:* Assume UTC, add time zone configuration if needed

3. **State Persistence:** Do we need to track state across multiple validation runs?
   - *Recommendation:* Stateless for PoC, each validation run is independent

4. **Custom Rules:** Will users need to define custom rules per device model?
   - *Recommendation:* Out of scope for PoC, but design with extensibility in mind
