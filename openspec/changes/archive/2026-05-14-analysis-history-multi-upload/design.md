## Context

**Current Limitations:**

1. **Single Analysis Only**: `AnalysisContext` stores only one `latestAnalysis`. When a new file is uploaded, the previous analysis is completely overwritten and lost.

2. **No History Tracking**: Users cannot:
   - View previous analysis results
   - Switch between analyses from different files/sessions
   - Compare multiple device analyses

3. **Upload Workflow Issues**:
   - After uploading files with success status, they remain in the queue
   - No clear "new upload" workflow without manual clearing
   - Files uploaded together (multi-select) get analyzed individually, but only the last one is kept

## Goals / Non-Goals

**Goals:**
- Track all uploaded analyses in a history array
- Allow switching between analyses
- Allow removing individual analyses or clearing all history
- Keep backward compatibility with existing `latestAnalysis` pattern
- Update Reports page to show history UI
- Each upload creates a NEW entry in history

**Non-Goals:**
- Persist history beyond browser session (sessionStorage is sufficient)
- Cross-device sync (beyond current session)
- History merge/combine features (for now)

## Decisions

### 1. Analysis Context Refactor

**Decision:** Extend `AnalysisContext` to track history with active index

**Data Model:**
```typescript
interface AnalysisContextType {
  // Existing (backward compatible)
  latestAnalysis: LatestAnalysis | null
  setLatestAnalysis: (analysis: LatestAnalysis) => void  // Updates active analysis
  clearAnalysis: () => void
  
  // New
  analysisHistory: LatestAnalysis[]
  activeAnalysisIndex: number
  addAnalysis: (analysis: LatestAnalysis) => void  // Adds NEW entry to history, sets as active
  switchAnalysis: (index: number) => void
  removeAnalysis: (index: number) => void
  clearHistory: () => void
  
  // ... existing properties
}
```

**Rationale:**
- `setLatestAnalysis` keeps backward compatibility for existing code
- `addAnalysis` is the NEW function that FileUploadZone should use for uploads
- History persists in `sessionStorage` with new keys:
  - `med-therm-analysis-history`: stores the array
  - `med-therm-active-index`: stores active index

### 2. File Upload Behavior

**Decision:** Each file upload creates a NEW entry in history using `addAnalysis`

**Changes in FileUploadZone.tsx:**
- Replace `setLatestAnalysis` calls with `addAnalysis`
- After upload, files can stay in list, but user can "Clear all"

**Rationale:**
- User uploads 3 .txt files → 3 separate analyses in history
- User can switch between them in Reports page
- Previous analysis is not lost

### 3. Reports Page UI

**Decision:** Add History tab with list/table of analyses

**Features:**
- Table showing: #, Device, Time, Score, Violations, Status
- Switch between analyses (click "View")
- Remove individual analyses (X button)
- Clear All button
- Dropdown selector in header for quick switching

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Large history in sessionStorage | Each analysis is not huge, max 10-20 entries reasonable |
| Browser refresh resets data | Uses sessionStorage, survives refresh within session |
| Confusion between "add" vs "set" | Clear naming: `addAnalysis` = new entry, `setLatestAnalysis` = update active |

## Migration Plan

1. **AnalysisContext.tsx**: Add history state, functions, storage
2. **FileUploadZone.tsx**: Use `addAnalysis` instead of `setLatestAnalysis`
3. **Reports.tsx**: Add history UI
4. **Existing pages**: Dashboard, Violations, Temperature - automatically work because they use `latestAnalysis` which now comes from activeIndex in history
