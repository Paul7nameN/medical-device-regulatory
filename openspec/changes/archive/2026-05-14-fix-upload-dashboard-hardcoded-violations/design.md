## Context

Current issues identified in the codebase:

**1. Layout.tsx - Hardcoded badge**:
- `navItems` is a static array defined outside the Sidebar component
- Violations item has `badge: 3` hardcoded
- Layout component doesn't import or use `useAnalysis()` to get actual data
- Even mobile nav uses the same static `navItems`

**2. FileUploadZone.tsx - Incomplete data flow**:
- For **.txt files** (lines 141-162): Calls `reportsApi.generateFromLogs` → extracts `reportResult.report` → calls `createAnalysisData()` → calls `setLatestAnalysis()` → data saved properly
- For **images** (lines 137-140): Calls `aiApi.analyzeChart(formData)` → `result` never saved to context
- For **PDFs/other** (lines 163-166): Calls `logsApi.ingest(formData)` → `result` never saved to context
- Images and PDFs return `ValidationResult` shape but don't go through `createAnalysisData()` and `setLatestAnalysis()`

**3. Analysis Context Flow**:
- `setLatestAnalysis()` calls `saveToStorage()` which uses `sessionStorage.setItem(STORAGE_KEY, ...)`
- `loadFromStorage()` is called on initial mount
- Pages like Dashboard.tsx and Violations.tsx use `useAnalysis()` to get `latestAnalysis`
- Without calling `setLatestAnalysis()`, pages see `null`

**Constraints**:
- `aiApi.analyzeChart` and `logsApi.ingest` return `ValidationResult` shape
- `reportsApi.generateFromLogs` returns `{ report, generated_at }` shape
- All validation results need to be processed through `createAnalysisData()` to extract temperature data and properly format for storage
- For image files without raw logs, `rawLogs = []` is acceptable

## Goals / Non-Goals

**Goals:**
1. Make navItems dynamic by moving it inside component or creating a helper that uses context
2. Fix FileUploadZone to save ALL upload type results to AnalysisContext
3. Create consistent data flow pattern regardless of upload type
4. Ensure empty raw logs (images) still work with `createAnalysisData()`

**Non-Goals:**
1. Don't change backend API contracts
2. Don't change data structure in AnalysisContext
3. Don't add new features - just fix existing broken functionality

## Decisions

### 1. Dynamic Navigation Badge
**Decision**: Convert static `navItems` to a `useMemo` hook inside Sidebar that uses `useAnalysis()`

**Rationale**:
- `navItems` is currently defined at module level, can't access React context
- Moving logic inside Sidebar component allows access to `useAnalysis()`
- Calculate violation count from `latestAnalysis?.validationResult?.findings`
- Count only non-passed findings: `findings.filter(f => !f.passed).length`

**Alternative**: Pass badge count as prop from parent Layout → worse, Layout would need context too

### 2. Unified Upload Result Handling
**Decision**: After every successful API call, check if result has the right shape and save to context

**Rationale**:
- Create reusable pattern: `if (result) { ... process and save ... }`
- Check if result is direct `ValidationResult` or wrapped `{ report, generated_at }`
- Always use `createAnalysisData(validationResult, rawLogs)`
- For images/PDFs without raw logs: pass empty array `[]`

**Implementation pattern**:
```tsx
// After ANY successful API call:
const validationResult = result.report 
  ? (result.report as unknown as ValidationResult)  // from generateFromLogs
  : result as ValidationResult;                         // from analyzeChart or ingest

const rawLogs = /* extracted logs or [] */;
const analysisData = createAnalysisData(validationResult, rawLogs);
setLatestAnalysis({
  validationResult: analysisData.validationResult,
  rawLogs: analysisData.rawLogs,
  temperatureData: analysisData.temperatureData,
  analyzedAt: analysisData.analyzedAt,
  deviceId: analysisData.deviceId,
});
```

### 3. Image/PDF upload handling
**Decision**: For file types without raw log content, pass `rawLogs = []` and let `createAnalysisData()` handle it

**Rationale**:
- `extractTemperatureFromRawLogs([])` returns `[]` - safe
- `createAnalysisData` already handles `rawLogs` parameter with default `[]`
- Image analysis won't have temperature data, which is fine - empty array is valid state
- User can still see violations in Violations page

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| API response shapes vary | Check for `.report` property to distinguish wrapped vs direct |
| TypeScript errors from casting | Use `as unknown as ValidationResult` pattern, already exists in codebase |
| Session storage limits | Data is already being stringified and stored - no size increase |

## Migration Plan

1. **Fix Layout.tsx first**: Make badge dynamic
2. **Fix FileUploadZone.tsx**: Save ALL upload results
3. **Test end-to-end**: Upload .txt, then .png, then .pdf - verify data appears on Dashboard

**Rollback Strategy**: Revert individual files if issues found. Changes are isolated to two files.

## Open Questions

- None - all issues clearly identified in codebase
