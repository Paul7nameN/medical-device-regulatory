## 1. Fix Dynamic Violations Badge in Layout

- [x] 1.1 Import `useAnalysis` hook in `Layout.tsx`: `import { useAnalysis } from '@/lib/context/AnalysisContext'`
- [x] 1.2 Move static `navItems` array logic inside Sidebar component or create `getNavItems()` helper
- [x] 1.3 Inside Sidebar, call `useAnalysis()` to get `latestAnalysis`
- [x] 1.4 Calculate actual violation count: count findings where `!finding.passed`
- [x] 1.5 Replace hardcoded `badge: 3` with dynamic count (`undefined` when no data or 0)
- [x] 1.6 Keep mobile navigation consistent - uses same data source
- [x] 1.7 Add defensive check: ensure `findings` is an Array before iterating
- [x] 1.8 Also add same logic to MobileNav (separate function, same calculation)

## 2. Fix Image Upload Data Flow

- [x] 2.1 In `FileUploadZone.tsx`, after `aiApi.analyzeChart(formData)` call
- [x] 2.2 Check if response has direct `findings: Finding[]` before saving
- [x] 2.3 Skip saving to context if response shape is unknown (like `ChartAnalysisResponse` wrapper)

## 3. Fix TXT Upload (AggregatedComplianceReport Conversion)

- [x] 3.1 Convert `AggregatedComplianceReport` to proper `ValidationResult` shape
- [x] 3.2 Flatten `violations_by_severity: Dict` into `findings: Finding[]` array
- [x] 3.3 Map `generated_at` to `analyzed_at` field name
- [x] 3.4 Keep all other fields with proper type checking

## 4. Fix AnalysisContext Data Validation

- [x] 4.1 Add `isValidAnalysis()` type guard function
- [x] 4.2 Validate `findings` is an Array in `loadFromStorage()`
- [x] 4.3 Clear sessionStorage if data is malformed (prevents crash on page load)
- [x] 4.4 Add defensive check in `buildSeverityCounts()` too

## 5. Test & Verify

- [ ] 5.1 Refresh browser - malformed sessionStorage data should be auto-cleared
- [ ] 5.2 Test that sidebar Violations badge is NOT visible when no data
- [ ] 5.3 Upload a TXT file with sample log data
- [ ] 5.4 Verify badge shows correct count after upload
- [ ] 5.5 Verify Dashboard shows violations table and temperature data
