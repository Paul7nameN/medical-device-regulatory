## Context

**Current API response structures:**

1. **TXT upload** → `/api/reports/generate`:
   ```typescript
   {
     report: AggregatedComplianceReport,
     generated_at: datetime
   }
   ```
   Where `AggregatedComplianceReport` has:
   - `violations_by_severity: Dict<Severity, Finding[]>` (nested structure)
   - `generated_at`, `device_id`, `summary`, etc.

2. **Image upload** → `/api/ai/analyze-chart`:
   ```typescript
   {
     success: boolean,
     result: ChartAnalysisResult | null,
     error: AIErrorResponse | null
   }
   ```
   Where `ChartAnalysisResult` has:
   - `violations: ChartViolation[]`
   - `analyzed_at`, `chart_type`, `confidence`, `temp_range_min/max`, etc.
   - `ChartViolation` has: `violation_type`, `description`, `confidence`, `timestamp_start/end`, `extracted_value`

**Finding interface expected by frontend:**
```typescript
{
  rule_id: string           // e.g., "REG-TEMP-1"
  rule_description: string  // Human-readable rule description
  category: string          // "TEMP", "SENS", etc.
  severity: Severity        // critical | high | medium | low | info
  passed: boolean           // false for violations
  message: string           // Details about the violation
  evidence: Evidence[]      // Supporting evidence
  timestamp: string         // ISO timestamp
  needs_visual_verification: boolean  // false for logs, true for images
  data_source: DataSource   // "logs", "images", "inspection", etc.
  confidence?: number       // AI confidence if applicable
}
```

**Goals:**
- Convert `ChartViolation[]` → `Finding[]` with sensible defaults
- Detect response shape correctly (handle both `.report` and `.result.violations`)
- Mark image findings appropriately for visual verification

## Decisions

### 1. ChartViolation → Finding Mapping

**Decision:** Create type-safe mapping based on `violation_type`

**Mappings:**

| ChartViolation.violation_type | Finding.rule_id | Finding.category | Finding.severity |
|-------------------------------|-----------------|------------------|-------------------|
| `"excursion"` | "REG-TEMP-1" | "TEMP" | Use confidence: >0.8="critical", >0.6="high", >0.3="medium", else="low" |
| `"gap"` | "REG-DATA-1" | "DATA" | "medium" |
| `"slow_recovery"` | "REG-TEMP-5" | "TEMP" | "high" |
| `"frequent_access"` | "REG-OPS-3" | "OPS" | "info" |
| (unknown) | "REG-IMAGES-001" | "TEMP" | "low" |

**Common defaults for ALL image findings:**
- `passed: false` (violations only)
- `needs_visual_verification: true`
- `data_source: "images"`
- `evidence: []` (empty array - acceptable)
- `rule_description` = Generated from violation type and description
- `message` = `ChartViolation.description`
- `timestamp` = Prefer `ChartViolation.timestamp_start`, fallback to `ChartAnalysisResult.analyzed_at`
- `confidence` = `ChartViolation.confidence` if available, or parent `ChartAnalysisResult.confidence`

### 2. Response Shape Detection

**Decision:** Check in this priority order:

1. `result && 'success' in result && 'result' in result` → **ChartAnalysisResponse** (image analysis)
   - Check nested `result.result?.violations`
   - Apply conversion mapping

2. `result && 'report' in result && result.report` → **GenerateReportResponse** (TXT analysis)
   - Check if `'violations_by_severity' in report` for nested structure
   - Check if `'findings' in report` for direct findings

3. `result && 'findings' in result && Array.isArray(result.findings)` → **Direct ValidationResult**
   - Use directly

### 3. Implementation Location

**Decision:** Create helper function in `transformers.ts` for reusability

- `chartViolationsToFindings(violations: unknown[], chartResult?: unknown): Finding[]`
- Called from `FileUploadZone.tsx` when image analysis response detected

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Confidence values may be missing | Fall back to reasonable defaults based on violation_type |
| Timestamps may be missing | Fall back to `new Date().toISOString()` |
| Mapped rule_ids don't exactly match real rules | Add `needs_visual_verification: true` to flag for human review |
| ChartViolation type could be unknown | Catch-all mapping with generic rule_id |

## Migration Plan

1. Create conversion utility in `transformers.ts`
2. Update `FileUploadZone.tsx` to detect `ChartAnalysisResponse` shape
3. Apply conversion and persist to `AnalysisContext`

**Rollback:** Changes isolated to two files - easy to revert.
