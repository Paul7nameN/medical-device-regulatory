## Why

Currently, the MED-THERM Compliance Platform has critical limitations in the file upload workflow:

1. **Single analysis only**: `AnalysisContext` holds only one `latestAnalysis`. When a user uploads a second file, the first analysis is **overwritten and lost**.

2. **No history tracking**: Users cannot:
   - See previous analysis results
   - Switch between different analyses
   - Compare multiple device sessions

3. **Upload workflow confusing**:
   - After uploading files with success status, the files remain in the queue
   - No indication whether a "fresh start" is possible
   - No way to clear the queue and upload new files without reloading the page

## What Changes

- Extend `AnalysisContext` to support **analysis history** (array of analyses, not just one)
- Track **current/active analysis** with ability to switch
- Add functions to: add to history, switch analysis, clear history, merge analyses
- Update `FileUploadZone` to:
  - Clear queue after successful upload
  - Allow new files to be added after previous uploads complete
  - Option to merge findings with current analysis
- Update `Reports` page to show analysis history and allow switching
- Update `Dashboard` and `Violations` pages to use active analysis from context

## Capabilities

### Modified Capabilities

- **analysis-context**: Now supports history array, active analysis tracking
- **file-upload**: Better workflow with clear/reset options
- **reports**: Show history, allow switching analyses

### New Capabilities

- **analysis-history**: Track multiple analysis sessions with timestamps

## Impact

- Changes to `frontend/src/lib/context/AnalysisContext.tsx` - major refactor
- Changes to `frontend/src/components/FileUploadZone.tsx` - workflow improvements
- Changes to `frontend/src/pages/Reports.tsx` - add history UI
- Minimal changes to Dashboard/Violations pages - use active analysis
- No backend API changes needed
