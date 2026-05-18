## Why

After implementing `ValidationSource` categorization for all regulatory rules in `focus-on-testable-rules`, the frontend UI does not yet expose this information to users. Currently:

1. **Backend knows** which rules are `LOGS` (testable from system logs), `INSPECTION` (needs physical inspection), or `COMBINED` (partially testable)
2. **Frontend doesn't know** - users see all findings the same way, without context about how confident we are in the result
3. **No filtering** - users cannot choose to run only log-validatable rules, or hide inspection-only rules

**User Experience Problem:**
- A finding marked "PASS" from an `INSPECTION` rule is misleading - we didn't actually validate anything, we just returned an INFO finding
- A "FAIL" from a `LOGS` rule is highly confident and actionable
- Users cannot distinguish between these different confidence levels

## What Changes

### Part 1: Backend API Enhancements

Expose the new `data_source` categorization through the API:

| Change | Location |
|--------|----------|
| Add `data_source`, `confidence`, `inspection_hint` to `Finding` model | `backend/app/models/findings.py` |
| Set these fields when creating findings from rules | `backend/app/regulatory/rules/base.py` |
| Add `include_sources`/`exclude_sources` parameters to validate endpoint | `backend/app/api/validate.py` |
| Return `data_source` in `get_all_rules()` and `get_rule_info()` | `backend/app/regulatory/engine.py` |

### Part 2: Frontend Type Updates

| Change | Location |
|--------|----------|
| Add `DataSource` type | `frontend/src/lib/api/types.ts` |
| Add `data_source`, `confidence`, `inspection_hint` to `Finding` interface | `frontend/src/lib/api/types.ts` |
| Add source constants for labels, colors, icons | `frontend/src/lib/api/types.ts` |

### Part 3: Frontend UI Components

| Component | Purpose |
|-----------|---------|
| `DataSourceBadge` | Visual indicator showing rule source with color coding |
| `SourceFilterDropdown` | Filter findings/rules by data source |
| `InspectionHintTooltip` | Show detailed inspection hint on hover |
| `ConfidenceIndicator` | Visual representation of confidence level (1.0 = full, 0.5 = partial) |

### Part 4: Frontend Page Integration

| Page | Changes |
|------|---------|
| Dashboard | Add `SourceFilterDropdown`, update summary display |
| Violations | Add badge to each row in `ViolationsTable` |
| ViolationDetail Modal | Show all new fields with proper formatting |
| Upload | Pass source filter parameter when calling validate API |

## Capabilities

### New Capabilities
- `data-source-badge`: Visual indicator of rule source (LOGS/INSPECTION/COMBINED/IMAGES)
- `source-filtering`: Filter validation results by data source
- `confidence-indicator`: Visual confidence level display
- `inspection-hint-tooltip`: Display detailed inspection requirements

### Modified Capabilities
- `finding-model`: Extended with source and confidence information
- `validation-api`: Extended with source filtering parameters
- `violations-table`: Enhanced with source badges
- `dashboard-filters`: Enhanced with source filtering

## Impact

**Backend:**
- `backend/app/models/findings.py` - 3 new optional fields
- `backend/app/regulatory/rules/base.py` - set fields when creating findings
- `backend/app/api/validate.py` - optional query parameters
- `backend/app/regulatory/engine.py` - return source info in rule methods

**Frontend:**
- `frontend/src/lib/api/types.ts` - new types and constants
- `frontend/src/components/ui/` - new badge and filter components
- `frontend/src/pages/Dashboard.tsx` - add filter
- `frontend/src/pages/Violations.tsx` - add badges to table
- `frontend/src/components/ViolationsTable.tsx` - integrate badge
- `frontend/src/components/FileUploadZone.tsx` - pass filter params

**No Breaking Changes:**
- All new fields are optional
- All new API parameters are optional
- Existing API contracts preserved
