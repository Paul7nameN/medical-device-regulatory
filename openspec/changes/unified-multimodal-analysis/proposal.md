## Why

Currently, each file upload creates an isolated analysis session. Logs, charts, and constraints documents are analyzed separately with no temporal correlation between modalities. This prevents the system from delivering on the enterprise client request: "correlating findings across multiple modalities (logs, charts, specifications) to produce root cause analysis and explainable compliance conclusions."

An existing `AIAugmentedRegulatoryEngine` with `CrossValidationResult` model was discovered but is unused in main API flows. The basic cross-validation is just count-based, not temporal. This change unifies multi-modal analysis with true temporal correlation.

## What Changes

- **New batch upload flow**: User selects all files (multiple logs + chart + constraints) → single "Analyze All" action
- **Multiple log files**: Auto-merged into single continuous timeline, deduplicated by timestamp+content
- **Chart time alignment**: Maps chart relative time ("08:00", "30min") to absolute timestamps via:
  1. LLM extraction from chart image
  2. Pattern matching against logs (if available)
  3. Falls back to proceeding with uncertainty warning + lower confidence
- **Temporal Correlation Engine**: Window-by-window comparison between log-derived readings and chart-extracted values
- **Enhanced findings**: Each violation shows source(s), confidence score, cross-modal evidence
- **Conflict resolution**: Logs are ground truth; chart disagreements flagged as "for human review"
- **No database migrations**: All new data stored in existing `AnalysisSession.config` JSONB field

## Capabilities

### New Capabilities

- `multimodal-ingestion`: Batch upload of multiple files with type detection, log merging/deduplication, and unified workspace tracking
- `chart-time-alignment`: Map chart relative time to absolute timestamps using LLM extraction, pattern matching against logs, or manual anchor points; track alignment confidence and method
- `temporal-correlation`: Window-by-window temporal comparison between log-derived values and chart-extracted values; produce correlated_findings, conflicting_findings, and multi-modal confidence scores
- `unified-report-generation`: Single unified compliance report with cross-modal evidence per finding, correlation insights section, and "for human review" section for conflicts

### Modified Capabilities

- `analysis-sessions`: Extended to track multiple source files in `config._sources`, chart alignment metadata, and correlation results; supports unified workspace concept
- `compliance-reporting`: Extended to include source tracking per finding, multi-modal confidence scores, correlation insights, and conflict flags
- `chart-image-data-extraction`: Enhanced scenario for aggregated analysis from multiple sources now includes explicit alignment requirements and confidence tracking

## Impact

| Area | Impact |
|------|--------|
| **Frontend** | `FileUploadZone.tsx` extended for batch mode; new components: `ChartAlignmentDialog`, `CorrelationInsights`, `ConflictsSection`, `UnifiedTimeline` |
| **Backend** | New modules: `multimodal/ingestion.py`, `multimodal/chart_alignment.py`, `multimodal/correlation.py`, `multimodal/unified_report.py`, `multimodal/prompts.py` |
| **API** | New endpoints: `POST /api/multimodal/analyze`, `GET /api/multimodal/status/{id}`, `GET /api/multimodal/results/{id}` |
| **Models** | Extended `AggregatedComplianceReport` with source tracking, confidence, correlation fields; no DB migrations (all in JSONB config) |
| **Existing Code** | Reuses existing `RegulatoryEngine`, `ComplianceReportAggregator`, VLLM clients, and log parser; existing AIAugmentedRegulatoryEngine's basic `_cross_validate` replaced by new temporal engine |
