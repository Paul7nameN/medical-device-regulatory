## Context

**Hardcoded data identified:**

### 1. Upload.tsx (lines 90-92)
```tsx
<Badge variant="low">25 Rules Passed</Badge>
<Badge variant="critical">7 Violations Detected</Badge>
<Badge variant="outline">3 Critical Issues</Badge>
```

The `handleUploadComplete` function receives the actual `result` from the API:
```tsx
const handleUploadComplete = (result: unknown) => {
  setUploadResult(result)
  setShowResult(true)
}
```

So `uploadResult` contains the actual API response. We need to extract:
- `passed_count` 
- `failed_count` (violations)
- `critical_count`

### 2. Reports.tsx (lines 34-95, 159)

**Static sample arrays:**
```tsx
const categoryData = [...]    // 8 REG categories, fixed counts
const severityData = [...]    // Fixed severity distribution
const trendData = [...]       // Fixed weekly scores
const reports = [...]         // 4 fake report entries
```

**Hardcoded ComplianceScore:**
```tsx
<ComplianceScore score={78} totalRules={32} passedRules={25} failedRules={7} />
```

**Expected behavior:**
- If `latestAnalysis` exists: Display data from current analysis
- If no data: Show proper empty state like Dashboard/Violations pages
- Historical reports: Not currently stored - could show "Upload logs to generate reports" empty state

## Decisions

### 1. Upload.tsx - Extract from API response

**Decision:** Extract counts from the actual API response structure.

**Response structures:**

**TXT upload → `GenerateReportResponse`:**
```typescript
{
  report: {
    passed_count: number,
    failed_count: number,
    critical_count: number,
    total_rules_evaluated: number,
    summary: {...}
  },
  generated_at: datetime
}
```

**Image upload → `ChartAnalysisResponse`:**
```typescript
{
  success: boolean,
  result: {
    violations: ChartViolation[],  // Count these
    confidence: number
  }
}
```

**Approach:**
- Check if `uploadResult` has the expected structure
- TXT: Extract `uploadResult.report.passed_count`, etc.
- Image: Calculate from `uploadResult.result.violations.length`
- Fallback: Hide badges if structure is unknown

### 2. Reports.tsx - Connect to AnalysisContext

**Decision:** Simplify Reports page to show current analysis data (like Dashboard), with empty state when no data.

**Implementation:**
1. Import `useAnalysis` from `@/lib/context/AnalysisContext`
2. Get `latestAnalysis`, `severityCountsByCategory` from context
3. If no data: Show empty state card like Dashboard:
   - "No reports available"
   - "Upload device log files to generate compliance reports"
   - Action button to navigate to Upload

4. For existing charts:
   - `categoryData` → Build from `severityCountsByCategory`
   - `severityData` → Aggregate from `severityCountsByCategory` values
   - `trendData` → Not stored, hide this chart or show "No historical data"
   - `reports` history → Not available, remove or show empty
   - `ComplianceScore` → Calculate from `severityCountsByCategory` or `latestAnalysis.validationResult`

### 3. Compliance Score Calculation

**Decision:** Calculate actual score from data:
```typescript
const total = passed + failed
const score = total > 0 ? Math.round((passed / total) * 100) : 0
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Different API response shapes | Use type guards and property checks |
| Missing fields in response | Fallback to 0 or hide badge |
| Reports has no history yet | Show empty state instead of fake data |
| User expects historical reports | Clarify that Reports page shows current analysis data |

## Migration Plan

1. Fix Upload.tsx first - extract from actual response
2. Fix Reports.tsx - connect to AnalysisContext
3. Test: Upload .txt file and verify badges match actual violations

**Rollback:** Changes isolated to two files.
