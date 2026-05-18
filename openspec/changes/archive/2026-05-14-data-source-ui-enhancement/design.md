## Context

The backend has been enhanced with `ValidationSource` categorization for all 21 regulatory rules. Each rule now has:
- `data_source`: `LOGS`, `INSPECTION`, `COMBINED`, or `IMAGES`
- `confidence`: float (1.0 = fully testable, 0.0 = inspection-only)
- `inspection_hint`: optional text for inspection-only rules

**Current Rule Categorization:**

| Source | Count | Rule IDs |
|--------|-------|----------|
| LOGS | 12 | REG-TEMP-1/2/3/4, REG-SENS-1, REG-ALARM-1, REG-DATA-1/2, REG-POWER-2, REG-COOL-2, REG-OPS-1/2 |
| INSPECTION | 6 | REG-SENS-2, REG-ALARM-2/3, REG-COOL-1, REG-INS-1/2 |
| COMBINED | 3 | REG-SENS-3, REG-DATA-3, REG-POWER-1 |
| IMAGES | 0 | (Reserved for future image/VLM analysis) |

**Color Coding Scheme (Proposal):**

| Source | Color | Rationale |
|--------|-------|-----------|
| LOGS | Green (#16a34a) | Fully validated from actual data - high confidence |
| INSPECTION | Gray (#6b7280) | Not validated - needs physical inspection |
| COMBINED | Orange (#ea580c) | Partially validated from logs + needs inspection |
| IMAGES | Blue (#2563eb) | Validated from images/VLM analysis |

**Constraints:**
- Tech stack: React + TypeScript, Tailwind CSS, shadcn/ui
- Backend: Python + FastAPI, Pydantic models
- No breaking changes to existing API contracts
- All new fields must be optional

## Goals / Non-Goals

**Goals:**
1. Expose `data_source`, `confidence`, `inspection_hint` through API
2. Create visual badge component for source indication
3. Add source filtering capability to UI
4. Show inspection hints in accessible tooltips
5. Keep backward compatibility

**Non-Goals:**
1. Do NOT remove existing functionality
2. Do NOT change severity classification logic
3. Do NOT require any user action to see existing data
4. Do NOT implement new validation logic

## Decisions

### 1. Finding Model Extension
**Decision**: Add optional fields to `Finding` Pydantic model

```python
class Finding(BaseModel):
    # Existing fields...
    data_source: Optional[str] = None  # "logs", "inspection", "combined", "images"
    confidence: Optional[float] = None  # 0.0 to 1.0
    inspection_hint: Optional[str] = None
```

**Rationale**: Optional fields ensure backward compatibility. Rules that don't set these will have `None`.

### 2. API Filter Parameters
**Decision**: Add optional `include_sources` and `exclude_sources` query parameters

```
GET /api/validate?include_sources=logs,combined
GET /api/validate?exclude_sources=inspection
```

**Rationale**: Users can choose to:
- See only fully validated rules (`include_sources=logs`)
- Hide inspection-only rules (`exclude_sources=inspection`)
- See everything (default, no params)

### 3. DataSourceBadge Component
**Decision**: Create a standalone badge component using shadcn/ui Badge

```tsx
interface DataSourceBadgeProps {
  source: 'logs' | 'inspection' | 'combined' | 'images';
  showLabel?: boolean;  // default: true
  size?: 'sm' | 'md';    // default: 'sm'
}

// Usage:
<DataSourceBadge source="logs" />        // Green badge with "Logs"
<DataSourceBadge source="inspection" />  // Gray badge with "Inspection"
```

**Rationale**: Reusable component that can be placed in:
- Violations table
- Violation detail modal
- Summary cards
- Rule info displays

### 4. SourceFilterDropdown Component
**Decision**: Create filter dropdown using shadcn/ui Select

```tsx
interface SourceFilterProps {
  selected: 'all' | 'logs-only' | 'exclude-inspection';
  onChange: (value: 'all' | 'logs-only' | 'exclude-inspection') => void;
}

// Options:
// - "All Rules" (default)
// - "Only Log-Validated" (LOGS + COMBINED)
// - "Exclude Inspection" (everything except INSPECTION)
```

**Rationale**: Simple, user-friendly options instead of forcing users to understand all 4 categories.

### 5. Integration Approach
**Decision**: Gradual integration with opt-in filtering

1. **Always show badges** - no setting needed
2. **Filter defaults to "All Rules"** - users see everything by default
3. **Filter state persists** in session storage or React Query cache

**Rationale**: Existing users see the same data plus new context badges. Power users can use filters.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Too much visual noise | Make badges small, use subtle colors, show on hover in dense views |
| Users confused by new categories | Add tooltips explaining each source type |
| Backend performance with filtering | Filter in engine layer, not DB - minimal overhead |
| Breaking existing consumers | All new fields are optional, new API params are optional |

## Migration Plan

1. **Backend First**: Update models and engine before UI changes
2. **Types Second**: Update frontend TypeScript types to match
3. **Components Third**: Build badge and filter components
4. **Integration Last**: Add components to existing pages

**Rollback Strategy**: 
- Backend: Remove optional fields (they're optional anyway - old code works)
- Frontend: Remove filter component, badge component usage is non-breaking
