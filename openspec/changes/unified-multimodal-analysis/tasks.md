## 1. Backend - Shared Models & Types

- [x] 1.1 Create Pydantic models for multi-modal: `SourceFile`, `ChartAlignment`, `CorrelatedFinding`, `ConflictingFinding`, `CorrelationSummary`
- [x] 1.2 Extend `AggregatedComplianceReport` model with `data_sources`, `confidence`, `correlation_insights`, `conflicting_findings` fields
- [x] 1.3 Create TypeScript types in frontend for all new multi-modal models (match backend)

## 2. Backend - MultiModal Ingestion Service

- [x] 2.1 Create `app/multimodal/__init__.py` module structure
- [x] 2.2 Implement `MultiModalIngestionService.ingest_log_files()`: parse multiple files, sort by timestamp
- [x] 2.3 Implement deduplication: `dedupe_log_entries()` using (timestamp, log_type, raw_value) tuple
- [x] 2.4 Implement source tracking: build `_sources` array with file metadata
- [x] 2.5 Integrate existing rule extraction for constraints documents
- [x] 2.6 Create `app/multimodal/prompts.py` for chart alignment VLLM prompts

## 3. Backend - Chart Time Alignment Service

- [x] 3.1 Create `app/multimodal/chart_alignment.py` module
- [x] 3.2 Implement `extract_time_range_from_chart()`: VLLM call to ask about chart time coverage
- [x] 3.3 Implement `pattern_match_alignment()`: temperature curve correlation between logs and chart
- [x] 3.4 Implement `calculate_pattern_confidence()` using curve correlation coefficient
- [x] 3.5 Implement `align_chart_data_points()`: map relative time to absolute timestamps
- [x] 3.6 Implement uncertainty flag: mark when confidence < 0.70

## 4. Backend - Temporal Correlation Engine

- [x] 4.1 Create `app/multimodal/correlation.py` module
- [x] 4.2 Implement time window comparison: `create_sliding_windows()` (±60s default)
- [x] 4.3 Implement `detect_matching_violations()`: log+chart pattern matching
- [x] 4.4 Implement confidence calculation: `calculate_multimodal_confidence()`
- [x] 4.5 Implement `generate_correlation_insights()`: narrative for door→temp, recovery patterns
- [x] 4.6 Implement conflict detection: `detect_discrepancies()` (logs OK vs chart VIOLATION)
- [x] 4.7 Replace basic `AIAugmentedRegulatoryEngine._cross_validate()` with new temporal engine

## 5. Backend - Unified Report Generator

- [x] 5.1 Create `app/multimodal/unified_report.py` module
- [x] 5.2 Implement `enhance_findings_with_sources()`: add `data_sources` array to each finding
- [x] 5.3 Implement `build_unified_timeline()`: combine log events + chart-derived events
- [x] 5.4 Integrate `ComplianceReportAggregator` with correlation results
- [x] 5.5 Add correlation insights and discrepancies to report structure

## 6. Backend - API Endpoints

- [x] 6.1 Create `app/api/multimodal.py` new API router
- [x] 6.2 Implement `POST /api/multimodal/analyze`: accept multipart form with files + options
- [x] 6.3 Implement orchestration flow: ingest → (parallel: rule extraction + chart analysis) → align → validate → correlate → report
- [x] 6.4 Implement `GET /api/multimodal/status/{id}`: status polling endpoint
- [x] 6.5 Implement `GET /api/multimodal/results/{id}`: return unified report
- [x] 6.6 Register router in main app
- [x] 6.7 Add frontend API client functions in `frontend/src/lib/api/`

## 7. Frontend - File Upload Zone (Batch Mode)

- [x] 7.1 Add "Batch Unified Analysis" mode toggle/UI to `FileUploadZone.tsx`
- [x] 7.2 Add file grouping display: show count by intent type (logs, constraints, charts)
- [x] 7.3 Add merged log preview: time range span, entry count before/after dedupe (backend provides, frontend shows via status polling)
- [x] 7.4 Implement call to new `/api/multimodal/analyze` endpoint
- [x] 7.5 Implement status polling for long-running operations
- [x] 7.6 Keep existing single-file flow working unchanged (backward compatibility)

## 8. Frontend - Enhanced Rules & Findings Display

- [ ] 8.1 Extend `RuleCard.tsx` to show source indicators (log icon, chart icon, both)
- [ ] 8.2 Extend `RuleCard.tsx` to show confidence score (0-100%) visual indicator
- [ ] 8.3 Modify "From [filename]" badge to show multiple sources when applicable
- [ ] 8.4 Add alignment uncertainty warning banner component
- [ ] 8.5 Implement banner logic: show when `alignment.uncertain` or `confidence < 0.7`

## 9. Frontend - Correlation Insights & Conflicts Sections

- [ ] 9.1 Create `CorrelationInsights.tsx` component: displays narrative multi-modal insights
- [ ] 9.2 Create `ConflictsSection.tsx` component: displays discrepancies for human review
- [ ] 9.3 Add both components to analysis results page (after violations, before timeline)
- [ ] 9.4 Implement side-by-side display for conflict details: log value vs chart value

## 10. Frontend - Unified Timeline

- [ ] 10.1 Create `UnifiedTimeline.tsx` component
- [ ] 10.2 Implement event type rendering: log events, violations, chart-derived events, correlation markers
- [ ] 10.3 Implement visual source distinction: different colors/icons per source type
- [ ] 10.4 Add timeline legend explaining source coding
- [ ] 10.5 Replace existing timeline or add as enhanced view option

## 11. Integration & Context Management

- [ ] 11.1 Extend `AnalysisContext` with unified analysis state: `hasMultipleSources`, `alignmentUncertain`, `correlationInsights`, `conflictingFindings`
- [ ] 11.2 Ensure `config._sources`, `config._correlation` are properly stored and retrieved
- [ ] 11.3 Test backward compatibility: old sessions without new keys load gracefully

## 12. Tests & Documentation

- [ ] 12.1 Write unit tests for `MultiModalIngestionService` (merge, dedupe)
- [ ] 12.2 Write unit tests for `TemporalCorrelationEngine` (window comparison, confidence calculation)
- [ ] 12.3 Write unit tests for chart alignment confidence thresholds
- [ ] 12.4 Update `docs/user-guide/uploading-files.md` with multi-modal batch upload instructions
- [ ] 12.5 Update `docs/CHANGELOG.md`
