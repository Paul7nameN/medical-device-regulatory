## Why

The MED-THERM Compliance Platform has multiple instances of hardcoded sample data that appear instead of actual analysis results:

1. **Upload.tsx:** After ANY successful upload, shows:
   - "25 Rules Passed"
   - "7 Violations Detected"
   - "3 Critical Issues"
   
   These badges are hardcoded and do NOT reflect the actual API response.

2. **Reports.tsx:** Entire page populated with static sample data:
   - `categoryData`: 8 REG categories with fixed passed/failed counts
   - `severityData`: Fixed critical/high/medium/low counts
   - `trendData`: Fixed weekly compliance scores (85, 82, 78, 75, 78, 81, 78)
   - `reports`: 4 fake report entries
   - `ComplianceScore score={78}`: Hardcoded score on line 159

## What Changes

- Extract actual counts from `uploadResult` in Upload.tsx and display dynamically
- Connect Reports.tsx to use `AnalysisContext` data instead of static sample arrays
- When no data available, show proper empty states (like Dashboard and Violations pages already do)
- If history tracking needed, implement proper history storage/retrieval

## Capabilities

### Modified Capabilities

- **file-upload**: Shows actual analysis result counts instead of hardcoded badges
- **compliance-visualization**: Reports page connects to real data source

### New Capabilities

- None

## Impact

- Changes to `frontend/src/pages/Upload.tsx` - read from `uploadResult`
- Changes to `frontend/src/pages/Reports.tsx` - use `useAnalysis()` or show empty state
- No backend API changes needed
