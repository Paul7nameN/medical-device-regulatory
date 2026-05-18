## Why

When users upload chart images (PNG/JPG) for AI analysis, the analysis results are not persisted to the shared AnalysisContext. This means:
- Dashboard page shows "No data" after image upload
- Violations page shows "No violations data" 
- No badge appears in navigation
- The analysis is essentially lost after the upload component shows "success"

The root cause is that `/api/ai/analyze-chart` returns a different response structure than `/api/reports/generate` (used for .txt files):
- **TXT uploads**: Returns `{ report: AggregatedComplianceReport }` with nested findings
- **Image uploads**: Returns `{ success: boolean, result: ChartAnalysisResult }` with `violations: ChartViolation[]`

The types don't match:
- `ChartViolation` has: `violation_type`, `description`, `confidence`, `extracted_value`
- `Finding` expects: `rule_id`, `category`, `severity`, `evidence`, `data_source`, `needs_visual_verification`

## What Changes

- Create mapping from `ChartViolation` → `Finding` format
- Detect `ChartAnalysisResponse` shape (`success: boolean` + nested `result.violations`)
- Properly persist image analysis results to `AnalysisContext`
- Mark image findings with `data_source: 'images'` and `needs_visual_verification: true`

## Capabilities

### Modified Capabilities

- **file-upload**: Now properly handles image analysis responses
- **analysis-context**: Now stores findings from both logs and images

### New Capabilities

- **chart-violation-mapping**: Converts AI chart violations to regulatory Finding format

## Impact

- Changes to `frontend/src/components/FileUploadZone.tsx` - add ChartViolation → Finding conversion
- Optional: utility function added to `frontend/src/lib/utils/transformers.ts` for reusability
- No backend API changes needed
