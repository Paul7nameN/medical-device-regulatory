# Tasks: Compliance Report Aggregator

## Implementation Tasks

### Phase 1: Project Setup

- [x] **1.1** Create reports module structure
  - Create `backend/app/reports/` directory
  - Create `__init__.py` for package exports

- [x] **1.2** Create Pydantic data models
  - `models.py`: Extended data models
  - `AggregatedComplianceReport` - Main report model
  - `ViolationSummary` - Per-rule violation summary
  - `TimelineEvent`, `CriticalPeriod`, `GapAnalysis`, `RecoveryInterval` - Temporal models
  - `TemporalAnalysis` - Temporal analysis container
  - `AIEnhancements` - AI analysis merge container
  - `Recommendation` - Prioritized recommendation model

---

### Phase 2: Severity Classification

- [x] **2.1** Create severity classifier
  - `severity.py`: `SeverityClassifier` class
  - `classify()` method - Determine severity based on rule + context
  - `is_critical_violation()` method - Quick critical check
  - `get_critical_rules()` method - List of rules that can be critical

- [x] **2.2** Implement critical detection rules
  - REG-TEMP-1: >3 violations = CRITICAL, 1-3 = HIGH
  - REG-TEMP-2: Always CRITICAL
  - REG-SENS-1: Dual sensor failure = CRITICAL, single = HIGH
  - REG-ALARM-1: Always HIGH (critical implications noted)

- [x] **2.3** Implement classification context building
  - Count temperature violations
  - Detect dual vs single sensor failure
  - Map existing finding severity to standardized scale

---

### Phase 3: Temporal Analysis

- [x] **3.1** Implement timeline construction
  - `temporal.py`: `build_event_timeline()` function
  - Merge log entries, findings, and AI chart violations
  - Sort events chronologically
  - Include severity and rule_id for violations

- [x] **3.2** Implement critical period detection
  - `detect_critical_periods()` function
  - 15-minute sliding window
  - Trigger: 1+ CRITICAL or 3+ HIGH severity events
  - Merge overlapping/adjacent periods
  - Include count of violations per period

- [x] **3.3** Implement gap detection
  - `detect_gaps()` function
  - Thresholds: >30s = sampling gap, >90s = telemetry gap
  - Include preceding/following event types
  - Calculate gap duration in seconds

- [x] **3.4** Implement recovery interval analysis (optional enhancement)
  - Detect door open → temperature recovery cycles
  - Measure recovery duration
  - Flag recoveries > 3min (REG-TEMP-3)

---

### Phase 4: Recommendation Engine

- [x] **4.1** Create rule remediation hints
  - `recommendations.py`: `RULE_REMEDIATION_HINTS` dict
  - REG-TEMP-1: Cooling, door access, sensor calibration
  - REG-TEMP-2: CRITICAL - immediate cooling investigation
  - REG-TEMP-3: Recovery capacity, door seals
  - REG-SENS-1: Sensor wiring, power, replacement
  - REG-ALARM-1: Alarm config, thresholds, integration
  - REG-DATA-2: Network, logging service, sync

- [x] **4.2** Implement recommendation generation
  - `generate_recommendations()` function
  - Sort by severity (CRITICAL → HIGH → MEDIUM → LOW → INFO)
  - Include temporal context (first/last occurrence)
  - Include evidence count
  - Merge AI insights if available

- [x] **4.3** Implement temporal context helper
  - `_get_temporal_context()` function
  - Format first/last occurrence timestamps
  - Link to critical periods if applicable

---

### Phase 5: Core Aggregator

- [x] **5.1** Implement ComplianceReportAggregator class
  - `aggregator.py`: Main class
  - `__init__()`: Initialize SeverityClassifier
  - `aggregate()`: Main orchestration method

- [x] **5.2** Implement classification context builder
  - `_build_classification_context()` method
  - Count REG-TEMP-1 violations
  - Detect dual sensor failure in REG-SENS-1
  - Extract metadata for all rules

- [x] **5.3** Implement finding classification
  - `_classify_findings()` method
  - Apply SeverityClassifier to each finding
  - Count by severity level
  - Track critical/high violations

- [x] **5.4** Implement grouping functions
  - `_group_by_rule()`: Group findings by rule_id
  - `_group_by_severity()`: Group by classified severity
  - Include timestamps (first/last occurrence)
  - Sample findings for each rule

- [x] **5.5** Implement temporal analysis integration
  - `_perform_temporal_analysis()` method
  - Build timeline from logs + findings
  - Detect critical periods
  - Detect gaps
  - Identify time range

- [x] **5.6** Implement AI analysis merge
  - `_merge_ai_analysis()` method
  - Chart violations from AI image analysis
  - Log insights from AI text analysis
  - Cross-validation confidence scores

- [x] **5.7** Implement executive summary generation
  - `_generate_executive_summary()` method
  - No violations case: Positive message
  - With violations: List critical/high rules
  - Include critical period info if applicable

- [x] **5.8** Implement report conversion helper
  - `_report_to_dict()` method
  - Serialize ComplianceReport to dict
  - For optional `include_raw_report` parameter

---

### Phase 6: API Endpoints

- [x] **6.1** Create reports API router
  - `api/reports.py`: FastAPI router
  - Import existing dependencies

- [x] **6.2** Implement report generation endpoint
  - `POST /reports/generate`
  - Accept `raw_logs` or `entries` (same as /validate)
  - Accept `device_id`, `filter_rules`, `include_ai_analysis`, `include_raw_report`
  - Parse logs → run validation → aggregate → return report

- [x] **6.3** Implement summary endpoint (optional)
  - `GET /reports/summary/{device_id}`
  - Return concise summary with critical/high rules
  - Return recommendation count

- [x] **6.4** Register router in main app
  - Update `main.py` to include `/api/reports` router
  - Ensure CORS and middleware apply

---

### Phase 7: Exceptions & Error Handling

- [x] **7.1** Create custom exceptions
  - `exceptions.py`: Exception classes
  - `ReportError`: Base exception
  - `AggregationError`: Aggregation failures
  - `TemporalAnalysisError`: Temporal analysis failures
  - `InvalidInputError`: Invalid input data (includes field name)

- [x] **7.2** Implement error handling in API
  - Catch HTTPException and re-raise
  - Catch other exceptions → return 500 with detail
  - Log all errors with context

---

### Phase 8: Module Exports

- [x] **8.1** Update `__init__.py`
  - Export `ComplianceReportAggregator`
  - Export all data models
  - Export `SeverityClassifier`
  - Export custom exceptions

---

### Phase 9: Testing

- [x] **9.1** Create unit tests for severity classification
  - `tests/test_severity_classifier.py`
  - Test REG-TEMP-1: 1 violation = HIGH, 4+ = CRITICAL
  - Test REG-TEMP-2: Always CRITICAL
  - Test REG-SENS-1: Single = HIGH, Dual = CRITICAL
  - Test REG-ALARM-1: Always HIGH
  - Test severity override matrix

- [x] **9.2** Create unit tests for temporal analysis
  - `tests/test_temporal_analysis.py`
  - Test timeline construction: Logs + Findings merged
  - Test critical period detection: 15min window, merge logic
  - Test gap detection: 30s threshold, 90s threshold
  - Test sorting: Chronological order

- [ ] **9.3** Create unit tests for recommendation engine
  - `tests/test_recommendations.py`
  - Test priority ordering: CRITICAL first
  - Test rule-specific remediation hints
  - Test temporal context inclusion
  - Test AI insight merging

- [x] **9.4** Create unit tests for aggregator
  - `tests/test_aggregator.py`
  - Test aggregation happy path
  - Test no violations case
  - Test critical violations detection
  - Test executive summary generation
  - Test raw report inclusion

- [ ] **9.5** Create integration tests
  - `tests/test_reports_api.py`
  - Test `POST /reports/generate` with raw_logs
  - Test `POST /reports/generate` with entries
  - Test error handling for empty input
  - Test with `docs/client/medical_device_logs_1000.txt`

---

### Phase 10: Integration with Existing Workflow

- [x] **10.1** Verify backward compatibility
  - Existing `/validate` endpoint unchanged
  - New `/reports` endpoints use same input format
  - Both use same `RegulatoryEngine`

- [ ] **10.2** Update documentation
  - Add API docs for new endpoints
  - Document critical violation detection rules
  - Document severity classification matrix

---

## Dependencies

| Task | Depends On |
|------|------------|
| 1.2 | 1.1 (module structure) |
| 2.1 | 1.2 (models) |
| 2.2 | 2.1 (SeverityClassifier) |
| 2.3 | 2.1 (SeverityClassifier) |
| 3.1 | 1.2 (models) |
| 3.2 | 3.1 (timeline) |
| 3.3 | 3.1 (timeline) |
| 3.4 | 3.1, 3.2 (timeline + periods) |
| 4.1 | 1.2 (models) |
| 4.2 | 4.1 (remediation hints), 1.2 (models) |
| 4.3 | 4.2 (recommendations) |
| 5.1 | 1.2 (models), 2.1 (severity), 3.x (temporal), 4.x (recommendations) |
| 5.2 | 5.1 (aggregator class) |
| 5.3 | 5.1, 2.1 |
| 5.4 | 5.1 |
| 5.5 | 5.1, 3.x |
| 5.6 | 5.1 |
| 5.7 | 5.1 |
| 5.8 | 5.1 |
| 6.1 | 5.1 (aggregator ready) |
| 6.2 | 6.1 (router), 5.1 (aggregator) |
| 6.3 | 6.2 (main endpoint) |
| 6.4 | 6.2 (endpoints) |
| 7.1 | 1.1 (module) |
| 7.2 | 6.2 (endpoint), 7.1 (exceptions) |
| 8.1 | 5.1, 6.x, 7.x |
| 9.1 | 2.1, 2.2, 2.3 |
| 9.2 | 3.1, 3.2, 3.3 |
| 9.3 | 4.1, 4.2, 4.3 |
| 9.4 | 5.1 - 5.8 |
| 9.5 | 6.2, 6.3 |
| 10.1 | 6.x (API) |
| 10.2 | All implementation tasks |

## Estimated Complexity

| Phase | Complexity | Notes |
|-------|------------|-------|
| Phase 1 | Low | Module structure and Pydantic models |
| Phase 2 | Medium | Severity logic requires understanding existing rules |
| Phase 3 | Medium | Temporal logic, windowing, gap detection |
| Phase 4 | Low | Rule mapping and priority sorting |
| Phase 5 | Medium-High | Main orchestration class, integrates all modules |
| Phase 6 | Low | API endpoints using existing patterns |
| Phase 7 | Low | Custom exceptions and error handling |
| Phase 8 | Low | Module exports |
| Phase 9 | Medium | Comprehensive test coverage |
| Phase 10 | Low | Integration verification |

## Critical Rules to Test

### REG-TEMP-1: Temperature Exceedances

**Test Cases:**
- 1 violation → HIGH severity
- 3 violations → HIGH severity
- 4 violations → CRITICAL severity
- In executive summary → "CRITICAL: n violation(s) detected"

### REG-SENS-1: Sensor Redundancy

**Test Cases:**
- Single sensor timeout → HIGH severity
- Dual sensor timeout → CRITICAL severity
- Message contains "both PRIMARY and SECONDARY" → triggers CRITICAL

### REG-TEMP-2: Excursion Limits

**Test Cases:**
- Any violation → Always CRITICAL
- Base severity already CRITICAL in `rules/temp.py`

### REG-ALARM-1: Delayed Alarms

**Test Cases:**
- Any violation → Always HIGH
- Note: Remediation hint says "CRITICAL: Verify alarm system" but severity is HIGH

## Notes

- **Backward Compatibility:** Must maintain existing `/validate` endpoint behavior
- **Sample Data:** Use `docs/client/medical_device_logs_1000.txt` for integration tests
- **Existing Models:** Extend, don't replace, `ComplianceReport` and `Finding`
- **Critical Thresholds:** Follow existing code logic from `rules/temp.py`, `rules/sens.py`, `rules/alarm.py`
- **AI Integration:** AI analysis is optional; aggregator works without it
- **Raw Report Inclusion:** `include_raw_report` flag for debugging/auditing

## Checkpoints

- [x] All Pydantic models defined
- [x] Severity classifier correctly implements critical detection
- [x] Temporal analysis: timeline, gaps, critical periods, recovery intervals working
- [x] Recommendations ordered by severity with remediation hints
- [x] Aggregator orchestrates all modules correctly
- [x] API endpoints match `/validate` input format
- [x] Summary endpoint implemented
- [x] Unit tests created (severity, temporal, aggregator)
- [ ] All unit tests passing
- [ ] Integration tests with sample data passing
- [x] Backward compatibility verified