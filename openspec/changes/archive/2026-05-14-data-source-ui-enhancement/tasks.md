## 1. Backend Model Updates

- [x] 1.1 Add `data_source`, `confidence`, `inspection_hint` to `Finding` model
  - Location: `backend/app/models/findings.py`
  - All fields are Optional[str] / Optional[float]
  - Update Pydantic model with new fields

- [x] 1.2 Update `BaseRule.create_finding()` to set source fields
  - Location: `backend/app/regulatory/rules/base.py`
  - Pass `rule.data_source`, `rule.confidence`, `rule.inspection_hint` to Finding
  - Ensure backward compatibility if rule doesn't have these fields

- [x] 1.3 Update `get_all_rules()` and `get_rule_info()` to return source info
  - Location: `backend/app/regulatory/engine.py`
  - Add `data_source`, `confidence`, `inspection_hint` to returned rule info
  - NOTE: Already done in previous change (focus-on-testable-rules)

## 2. Backend API Updates

- [x] 2.1 Add `include_sources` parameter to validation endpoint
  - Location: `backend/app/api/validate.py`
  - Query param: `include_sources` (comma-separated: "logs,combined,images")
  - Pass to `engine.validate()`

- [x] 2.2 Add `exclude_sources` parameter to validation endpoint
  - Location: `backend/app/api/validate.py`
  - Query param: `exclude_sources` (comma-separated: "inspection")
  - Pass to `engine.validate()`

- [x] 2.3 Add health/rules endpoint to list all rules with source info
  - Location: `backend/app/api/health.py`
  - Return categorized rules for frontend to display

## 3. Frontend Type Updates

- [x] 3.1 Add `DataSource` type to types.ts
  - Location: `frontend/src/lib/api/types.ts`
  - Type: `type DataSource = 'logs' | 'inspection' | 'combined' | 'images'`

- [x] 3.2 Update `Finding` interface with new optional fields
  - Location: `frontend/src/lib/api/types.ts`
  - Add: `data_source?: DataSource`
  - Add: `confidence?: number`
  - Add: `inspection_hint?: string`

- [x] 3.3 Add color constants for each source
  - Location: `frontend/src/lib/api/types.ts`
  - Constants: `DATA_SOURCE_LABELS`, `DATA_SOURCE_COLORS`, `DATA_SOURCE_DESCRIPTIONS`

## 4. Frontend UI Components

- [x] 4.1 Create `DataSourceBadge` component
  - Location: `frontend/src/components/ui/badge.tsx` (added to existing badge file)
  - Uses shadcn/ui Badge component + Tooltip
  - Props: `source: DataSource`, `showLabel?: boolean`, `showTooltip?: boolean`
  - Color-coded based on source type
  - Optional tooltip with source description

- [ ] 4.2 Create `SourceFilterDropdown` component (Optional nice-to-have)
  - Location: `frontend/src/components/SourceFilterDropdown.tsx`
  - Uses shadcn/ui Select or Dropdown Menu
  - Options: "All Rules", "Only Log-Validated", "Exclude Inspection"

- [ ] 4.3 Create `InspectionHintTooltip` component (Integrated in DataSourceBadge)
- [ ] 4.4 Create `ConfidenceIndicator` component (Optional nice-to-have)

## 5. Frontend Integration (For Future Implementation)

- [ ] 5.1 Add `DataSourceBadge` to `ViolationsTable`
  - Location: `frontend/src/components/ViolationsTable.tsx`
  - Note: Frontend currently uses `DetectedViolation`, not `Finding`
  - Need to update API response mapping or use in ValidationResult display

- [ ] 5.2 Add `inspection_hint` tooltip for INSPECTION rules
- [ ] 5.3 Update `ViolationDetail` modal to show all source fields

## 6. Frontend Integration - Dashboard (For Future Implementation)

- [ ] 6.1 Add `SourceFilterDropdown` to Dashboard page
- [ ] 6.2 Pass filter params to API calls
- [ ] 6.3 Add filter to Violations page
- [ ] 6.4 Update Summary cards to show source breakdown

## 7. API Client & State Management (For Future Implementation)

- [ ] 7.1 Update API client to accept source filter params
- [ ] 7.2 Update React Query hooks/mutations if used

## 8. Testing & Validation

- [x] 8.1 Test backend API with filter params (DONE - verified working)
  - Test `?include_sources=logs` returns only LOGS rules
  - Test `?exclude_sources=inspection` excludes INSPECTION rules
  - Test default (no params) returns all rules

- [x] 8.2 Verify Finding model returns source fields (DONE - verified working)
  - Check that findings from LOGS rules have `data_source: "logs"`
  - Check that findings from INSPECTION rules have `inspection_hint` set

- [ ] 8.3 Test frontend badge component
- [ ] 8.4 Test filter integration

## Task Summary

**Total Tasks:** 28 tasks
**Completed:** 10 core tasks (Backend + Types + DataSourceBadge)
**Pending:** 18 tasks (Integration + nice-to-haves)

**Completed This Session:**
- [x] Backend Finding model updated with new fields
- [x] Backend API `/validate` updated with filter params
- [x] Backend `/health/rules` updated to return source info
- [x] Frontend types updated with DataSource type and constants
- [x] Frontend DataSourceBadge component created (with Tooltip)

**Verification Results:**
- 21 rules with correct `data_source` categorization
- Filter working: 21 findings without filter, 15 findings with `exclude_sources=inspection`
- Findings have `data_source` field populated correctly
