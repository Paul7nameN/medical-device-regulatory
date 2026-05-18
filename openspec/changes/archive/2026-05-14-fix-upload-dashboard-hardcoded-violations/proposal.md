## Why

The MED-THERM Compliance Platform has three critical issues that break the user workflow:

1. **Hardcoded Violations Badge**: The sidebar navigation shows "3" next to Violations at all times, regardless of actual data. This is confusing and misleading for users.

2. **Uploads Not Saving to Context**: Only .txt log files properly save their analysis results to the shared AnalysisContext. Image uploads (analyzeChart) and other file types (logsApi.ingest) call the API but never persist results, so the Dashboard and Violations pages remain empty.

3. **Empty Dashboard**: Because uploaded data isn't being properly shared via context, users upload files but see "No data" on Dashboard and Violations pages.

## What Changes

- Make sidebar Violations badge dynamic based on actual analysis data
- Fix FileUploadZone to save all upload type results to AnalysisContext
- Ensure proper data flow: Upload → API Call → Context → SessionStorage → Dashboard/Violations pages

## Capabilities

### Modified Capabilities

- **dashboard-layout**: Dynamic badge showing actual violation count
- **file-upload**: All upload types properly save results to context
- **analysis-context**: Data properly flows through sessionStorage persistence

### New Capabilities

- None

## Impact

- Changes to `frontend/src/components/Layout.tsx` - dynamic badge
- Changes to `frontend/src/components/FileUploadZone.tsx` - save all upload results
- Backend APIs remain unchanged - only frontend data flow fixes
