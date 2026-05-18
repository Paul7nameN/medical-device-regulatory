## 1. Analysis Context Refactor

- [x] 1.1 Add `analysisHistory: LatestAnalysis[]` state
- [x] 1.2 Add `activeAnalysisIndex: number` state
- [x] 1.3 Add `addAnalysis(analysis)` function - adds NEW entry to history, sets as active
- [x] 1.4 Add `switchAnalysis(index)` function
- [x] 1.5 Add `removeAnalysis(index)` function
- [x] 1.6 Add `clearHistory()` function
- [x] 1.7 Update `severityCountsByCategory` to use active analysis via `latestAnalysis`
- [x] 1.8 Update `hasData` to check if history has entries
- [x] 1.9 Keep `setLatestAnalysis` for backward compatibility (updates active analysis)
- [x] 1.10 Add `loadHistoryFromStorage` using new key `med-therm-analysis-history`
- [x] 1.11 Add `loadActiveIndexFromStorage` using new key `med-therm-active-index`
- [x] 1.12 Add `useEffect` to save history and index to storage on changes

## 2. File Upload Zone Update

- [x] 2.1 Replace `setLatestAnalysis` with `addAnalysis` in `FileUploadZone.tsx`
- [x] 2.2 Update `Upload.tsx` badge calculation to work with actual API response shapes (TXT vs Image uploads)
- [x] 2.3 Add history counter in Upload page linking to Reports

## 3. Reports Page History UI

- [x] 3.1 Add Select dropdown for quick switching between analyses (when history.length > 1)
- [x] 3.2 Update History tab to show table with all analyses
- [x] 3.3 Table columns: #, Device, Analyzed At, Score, Violations, Status, Actions
- [x] 3.4 Add "View" button to switch to analysis
- [x] 3.5 Add "X" button to remove individual analysis
- [x] 3.6 Add "Clear All" button to clear entire history
- [x] 3.7 Update Overview tab to show analysis counter in header
- [x] 3.8 Highlight active analysis in table

## 4. Test & Verify

- [ ] 4.1 Test that Dashboard uses active analysis from history
- [ ] 4.2 Test that Violations page uses active analysis
- [ ] 4.3 Test upload of multiple files - verify each creates entry in history
- [ ] 4.4 Test switching between analyses in Reports page
- [ ] 4.5 Test removing analyses
- [ ] 4.6 Test clearing history
- [ ] 4.7 Test persistence across browser refresh (sessionStorage)
