## 1. Create ChartViolation → Finding Conversion Utility

- [x] 1.1 Add `DataSource` type import from `@/lib/api/types` (already exists: `'logs' | 'inspection' | 'combined' | 'images'`)
- [x] 1.2 Create `chartViolationsToFindings()` function in `transformers.ts`
- [x] 1.3 Map `violation_type: "excursion"` → `rule_id: "REG-TEMP-1"`, category: "TEMP"
- [x] 1.4 Map `violation_type: "gap"` → `rule_id: "REG-DATA-1"`, category: "DATA"
- [x] 1.5 Map `violation_type: "slow_recovery"` → `rule_id: "REG-TEMP-5"`, category: "TEMP"
- [x] 1.6 Map `violation_type: "frequent_access"` → `rule_id: "REG-OPS-3"`, category: "OPS"
- [x] 1.7 Add unknown type fallback → `rule_id: "REG-IMAGES-001"`
- [x] 1.8 Calculate severity based on confidence: >0.8=critical, >0.6=high, >0.3=medium, else=low
- [x] 1.9 Set defaults: `passed: false`, `needs_visual_verification: true`, `data_source: "images"`, `evidence: []`
- [x] 1.10 Use `timestamp_start` if available, else `analyzed_at` from chart result, else current time

## 2. Update FileUploadZone Response Detection

- [x] 2.1 Import `chartViolationsToFindings` from `transformers`
- [x] 2.2 Detect `ChartAnalysisResponse` shape: `result && 'success' in result && 'result' in result`
- [x] 2.3 Check if nested `result.result?.violations` exists and is array
- [x] 2.4 Extract `violations[]` and `analyzed_at` from nested `result.result`
- [x] 2.5 Call `chartViolationsToFindings(violations, chartAnalysisResult)` to convert
- [x] 2.6 Build `ValidationResult` shape with the converted findings
- [x] 2.7 Call `setLatestAnalysis()` to persist to context
- [x] 2.8 Handle `success === false` - throw Error to trigger error handler

## 3. Edge Cases & Defensive Checks

- [x] 3.1 Handle case when `result.success === false` (error response) - throw Error to be caught
- [x] 3.2 Handle case when `result.result === null` - don't save
- [x] 3.3 Handle empty `violations` array - save with 0 findings

## 4. Test & Verify

- [ ] 4.1 Upload a PNG/JPG image with chart content
- [ ] 4.2 Verify that after upload success, navigate to Dashboard
- [ ] 4.3 Verify Dashboard shows findings from image analysis
- [ ] 4.4 Verify Violations page shows converted findings
- [ ] 4.5 Verify sidebar badge shows count if violations exist
- [ ] 4.6 Check that image findings have `needs_visual_verification: true` and `data_source: "images"`
