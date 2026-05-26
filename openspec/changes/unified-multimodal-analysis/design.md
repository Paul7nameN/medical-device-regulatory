## Context

Current state: Each file upload creates an isolated AnalysisSession. The frontend sorts files by intent (constraints first), but each processed file creates a separate session with no connection. An existing `AIAugmentedRegulatoryEngine` in `app/ai/integration/engine.py` has a basic `_cross_validate` method that only compares counts of violations, not temporal correlation. This engine is NOT wired into the main API endpoints (`/api/reports/generate`, `/api/ai/analyze-chart`).

Constraints:
- No database migrations (use existing `AnalysisSession.config` JSONB field)
- Logs are ground truth; charts have inherent uncertainty (VLLM extraction + alignment)
- Batch-only for now (no incremental add-files later)
- Backward compatible: existing single-file workflows continue to work

## Goals / Non-Goals

**Goals:**
1. Batch upload of multiple files → single unified AnalysisSession
2. Multiple log files: auto-merge, sort, deduplicate
3. Chart time alignment: map relative time to absolute timestamps with confidence tracking
4. Temporal correlation: window-by-window comparison between logs and aligned chart data
5. Enhanced reports: source tracking, multi-modal confidence, correlation insights, conflict flags
6. Full backward compatibility with existing single-file uploads

**Non-Goals:**
1. Incremental upload workflow (add files after analysis starts)
2. Real-time collaboration
3. Multi-device comparison (all files assumed to be same device session)
4. Schema changes/migrations (all in JSONB config)

## Decisions

### Decision 1: Log Merge Strategy

**Decision:** Always merge multiple log files. Sort by timestamp, deduplicate by (timestamp, log_type, raw_value).

**Rationale:**
- User's explicit choice: "Merge"
- Most common enterprise case: same device, different time periods or log rotations
- Deduplication handles overlaps gracefully

**Alternatives considered:**
- Smart merge with device_id detection → overcomplicated, not needed for batch
- User-controlled grouping → UX complexity, scope creep

### Decision 2: Chart Alignment Priority

**Decision:** Alignment method priority:
1. Pattern matching against logs (if logs available AND confidence > 0.8)
2. LLM extraction from chart image
3. Proceed without alignment + mark uncertain

**Rationale:**
- Pattern matching is more reliable when temperature curves match
- LLM can hallucinate dates/times
- User's choice: "do it and mark" rather than block

**Thresholds:**
- Confidence ≥ 0.85 → HIGH confidence alignment
- Confidence 0.70-0.84 → MEDIUM confidence + note
- Confidence < 0.70 → LOW + "Alignment uncertain" banner

### Decision 3: Conflict Resolution

**Decision:** Logs are ground truth. Chart disagreements are flagged as "potential discrepancy" for human review.

**Rationale:**
- User's explicit choice: "logs, yes"
- Logs have explicit timestamps and structured format
- Chart has two sources of uncertainty: VLLM extraction + time alignment
- In medical regulatory context, explicit sensor logs > visual interpretation

**Impact on findings:**
- Log-only violation: normal confidence
- Log + Chart matching: +confidence boost (multi-modal confirmation)
- Log says OK, Chart says VIOLATION: keep as "OK" but add "Discrepancy noted: visual chart suggests possible issue at time X"
- Log says VIOLATION, Chart says OK: keep as VIOLATION but add "Note: chart image at this time does not show violation"

### Decision 4: Data Storage (No Migrations)

**Decision:** All new data stored in `AnalysisSession.config` JSONB, following existing `_extracted_rules` pattern.

**Schema:**
```python
config: {
    # Existing fields preserved
    "_extracted_rules": [...],
    "_ruleset_meta": {...},
    
    # New fields for unified multi-modal
    "_sources": [
        {
            "id": "file_1",
            "name": "morning.log",
            "type": "log_file",
            "entry_count": 450,
            "time_range": ["2026-01-15T08:00:00", "2026-01-15T12:00:00"]
        },
        {
            "id": "file_2", 
            "name": "chart.png",
            "type": "chart_image",
            "alignment": {
                "method": "pattern_matched",  # or "llm_extracted", "manual"
                "confidence": 0.82,
                "start_time": "2026-01-15T08:00:00",
                "end_time": "2026-01-15T14:00:00",
                "uncertain": false  # true if confidence < 0.7
            }
        }
    ],
    
    "_correlation": {
        "correlated_findings": [...],
        "conflicting_findings": [...],
        "summary": {
            "total_correlated": 3,
            "total_conflicting": 1,
            "avg_correlation_confidence": 0.88
        }
    }
}
```

**Rationale:**
- Follows existing pattern (no new DB columns to migrate)
- Backward compatible: old sessions simply won't have these keys
- Flexible for future extension

### Decision 5: Architecture - Layered Approach

```
┌─────────────────────────────────────────────────────────────────┐
│                     API Layer (FastAPI)                          │
│  POST /api/multimodal/analyze                                    │
│  GET  /api/multimodal/status/{id}                                │
│  GET  /api/multimodal/results/{id}                               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  MultiModalWorkflow Orchestrator                 │
│  - Sequences: ingest → align → validate → correlate → report    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────────┐
│  Ingestion    │  │   Alignment   │  │    Correlation    │
│    Service    │  │    Service    │  │      Engine       │
└───────────────┘  └───────────────┘  └───────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              Reusable Existing Infrastructure                    │
│  RegulatoryEngine, ComplianceReportAggregator, LogParser,      │
│  ChartAnalyzer, TextAnalyzer (rule extraction), ModelArkClient  │
└─────────────────────────────────────────────────────────────────┘
```

**Decision:** New services in `app/multimodal/` that orchestrate existing infrastructure.

**Rationale:**
- Don't break or significantly modify existing working code
- Existing `RegulatoryEngine`, `ComplianceReportAggregator` are well-tested
- New services act as orchestrators, not replacements
- Existing single-file endpoints remain unchanged

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| **VLLM chart extraction hallucination** | All chart-derived values have explicit confidence; only correlate when confidence > 0.5; logs are always ground truth |
| **Chart time alignment error** → wrong correlation | Track alignment confidence; low confidence = "Alignment uncertain" banner + reduced correlation confidence; user can override manually |
| **Merging logs from different devices** | For batch scope, assume same device; future enhancement could detect device_id and warn; UI shows what was merged |
| **Performance: multiple VLLM calls (chart analysis + alignment + rule extraction)** | Batch mode is explicit UX choice; VLLM calls are parallelizable where independent; status polling endpoint for long-running operations |
| **Log entries don't have unique identifiers** → deduplication edge cases | Dedupe by (timestamp, log_type, raw_value) tuple; rare false positives acceptable vs missing overlaps |

## Migration Plan

Since there are no schema changes and no breaking API changes, deployment is straightforward:

1. Deploy new backend modules (`app/multimodal/*`)
2. Deploy new API endpoint (`app/api/multimodal.py`)
3. Deploy updated frontend with unified batch upload mode
4. Existing endpoints (`/api/reports/generate`, `/api/ai/analyze-chart`) continue working unchanged

**Rollback:**
- Simply don't use the new multimodal endpoints if issues
- Frontend can hide batch mode feature flag
- Old single-file flow is always available

## Open Questions

1. **Manual alignment UI**: When alignment confidence is low, should we show a full dialog with datetime picker, or just a warning banner? (Design: start with banner only, add dialog later if needed)

2. **Parallel VLLM calls**: Can we do rule extraction + chart analysis in parallel? (Design: Yes, orchestrator handles parallel execution when independent)

3. **Unified timeline UI**: How to visually distinguish log events vs chart-derived events? (Design: Different colors/icons; legend shown in timeline component)
