## Why

**Technical Debt Identified During Codebase Audit:**

The project has a **good architectural foundation** but suffers from **unfinished refactoring** and **code duplication** that creates confusion and potential bugs.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CURRENT STATE: CODE DUPLICATION                        │
└─────────────────────────────────────────────────────────────────────────────┘

  ENUMs & Models:
  ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
  │ app/models/      │     │ app/models/      │     │ app/regulatory/  │
  │ enums.py         │────▶│ logs.py          │────▶│ log_parser/      │
  │                  │     │                  │     │ log_parser.py    │
  │ LogType (4 vals) │     │ LogType (14 vals)│     │ LogType (14 vals)│
  │ Severity         │     │ LogEntry (Pydantic)│   │ LogEntry (plain) │
  └──────────────────┘     │ Severity (copy!) │     └──────────────────┘
                           └──────────────────┘              │
                                    │                         │
                                    ▼                         ▼
                           ┌──────────────────────────────────────┐
                           │  app/regulatory/parser.py            │
                           │  (ADAPTER ONLY! Converts between    │
                           │   the duplicate models)              │
                           └──────────────────────────────────────┘

  Functions:
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  _report_to_dict() - 3 IDENTICAL copies in:                             │
  │    • validate.py:95-143    (49 lines)                                   │
  │    • persistence.py:397-445 (49 lines)                                  │
  │    • aggregator.py:304-324  (21 lines - shorter version)               │
  └─────────────────────────────────────────────────────────────────────────┘

  Frontend:
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  findingsToViolations() in Dashboard.tsx  ──▶ findingsToDetectedViolations()│
  │  calculateComplianceScore() in Dashboard   ──▶ (similar) in transformers.ts  │
  │  categoryData logic inline                 ──▶ groupViolationsByCategory()    │
  └─────────────────────────────────────────────────────────────────────────┘

  Constants:
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  RegTemp1.MIN_TEMP = 2.0, MAX_TEMP = 8.0 (defined ONCE)               │
  │                                                                          │
  │  ...but HARDCODED as `2.0 <= x <= 8.0` in:                            │
  │    • alarm.py:47      • cool.py:98      • power.py:135   • ops.py:82  │
  │    • Dashboard.tsx:40 (Frontend)                                        │
  └─────────────────────────────────────────────────────────────────────────┘
```

**Problems by Priority:**

| Priority | Issue | Risk |
|----------|-------|------|
| 🔴 CRITICAL | 3 different `LogType` enums + adapter layer | Subtle conversion bugs, confusion about "which one to use" |
| 🔴 CRITICAL | 2 identical `Severity` enums | Same as above |
| 🟡 MEDIUM | `_report_to_dict()` duplicated 3x | Bug fixes must be applied to all copies |
| 🟡 MEDIUM | Frontend functions duplicated | Same logic, harder to maintain |
| 🟡 MEDIUM | Temperature constants hardcoded everywhere | If range changes (2-8°C), need to fix in 6+ files |
| 🟢 MINOR | Imports inside functions (circular imports smell) | Code smell, hides architectural issues |

## What Changes

### Phase 1: Unify Core Models (CRITICAL)

1. **Choose one source of truth for enums:**
   - Keep `app/models/logs.py:LogType` (14 values - the complete one)
   - Keep `app/models/findings.py:Severity` (used everywhere with Findings)
   - **DELETE** the duplicate `LogType` from `app/regulatory/log_parser/log_parser.py`
   - **DELETE** the duplicate `Severity` from `app/models/enums.py`
   - **DELETE** the adapter layer `app/regulatory/parser.py`

2. **Update all imports:**
   - Everywhere that uses `app/regulatory/log_parser/log_parser.py:LogType` → use `app/models/logs.py:LogType`
   - Everywhere that uses `app/models/enums.py:Severity` → use `app/models/findings.py:Severity`
   - Keep other enums from `enums.py` (`AnalysisSessionStatus`, `ViolationStatus`, etc.) - only `LogType` and `Severity` are duplicated

### Phase 2: Eliminate Code Duplication (MEDIUM)

1. **Extract `_report_to_dict()` to a single location:**
   - Create `app/reports/serializers.py` or use existing `app/models/findings.py`
   - One function, tested once, used everywhere
   - Delete the 3 copies

2. **Unify Frontend transformer functions:**
   - Keep the versions in `transformers.ts` (already centralized)
   - Delete/Deduplicate the inline versions in `Dashboard.tsx`
   - Ensure `Dashboard.tsx` imports from `transformers.ts`

### Phase 3: Fix Inconsistencies (MEDIUM)

1. **Create a constants module:**
   - Create `app/regulatory/constants.py` with:
     ```python
     MIN_TEMP = 2.0  # REG-TEMP-1
     MAX_TEMP = 8.0  # REG-TEMP-1
     # ...other constants from the regulatory spec
     ```
   - Or better: **expose these from `RegTemp1` class** that already defines them
   - Update `alarm.py`, `cool.py`, `power.py`, `ops.py` to use the constant

2. **Send safe range from Backend to Frontend:**
   - Include `safe_range: { min: number, max: number }` in API responses
   - Or create a simple config endpoint `GET /api/config/ranges`
   - Frontend stops hardcoding `{ min: 2, max: 8 }`

### Phase 4: Investigate & Fix Code Smells (MINOR)

1. **Investigate circular imports:**
   - Why are there imports inside functions in `health.py`, `reports.py`, `validate.py`?
   - Draw the dependency graph and fix the cycle
   - Or document why they're necessary

## Capabilities

### Modified Capabilities
- `log-storage`: Cleaner model layer, single source of truth
- `analysis-sessions`: Unified serialization via extracted functions
- `compliance-reporting`: Same as above

### New Capabilities
- `core-constants`: Single source of truth for regulatory constants (2-8°C range, etc.)
- `model-unification`: Eliminated duplicate enum types and adapter layers

## Impact

### Files to MODIFY:

**Backend:**
- `app/models/enums.py` - Remove duplicated LogType and Severity
- `app/models/logs.py` - This becomes the source for LogType
- `app/models/findings.py` - This becomes the source for Severity
- `app/regulatory/log_parser/log_parser.py` - Remove LogType/LogEntry, import from models
- `app/regulatory/parser.py` - **DELETE THIS FILE** (adapter layer no longer needed)
- `app/regulatory/alarm.py:47` - Use RegTemp1.MIN_TEMP/MAX_TEMP
- `app/regulatory/cool.py:98` - Use RegTemp1.MIN_TEMP/MAX_TEMP
- `app/regulatory/power.py:135` - Use RegTemp1.MIN_TEMP/MAX_TEMP
- `app/regulatory/ops.py:82` - Use RegTemp1.MIN_TEMP/MAX_TEMP
- `app/api/validate.py` - Remove _report_to_dict, use centralized version
- `app/services/persistence.py` - Remove _report_to_dict, use centralized version
- `app/reports/aggregator.py` - Remove _report_to_dict, use centralized version
- Plus all files that import from the old locations

**Frontend:**
- `src/pages/Dashboard.tsx` - Remove duplicated functions, import from transformers.ts
- `src/lib/utils/transformers.ts` - Keep/extend this as central location

### Files to DELETE:
- `app/regulatory/parser.py` - Adapter layer between duplicate models

### Files to CREATE:
- `app/reports/serializers.py` (optional) - Central location for _report_to_dict
- Or just add it to an existing appropriate location

### Risk / Mitigation

| Risk | Mitigation |
|------|------------|
| Breaking imports during enum unification | Update all imports systematically. Use Find/Replace with verification. |
| _report_to_dict has subtle differences between copies | Compare all 3 versions carefully, create one "superset" version, test |
| Frontend Dashboard has different signatures | `calculateComplianceScore` takes (passed, failed) vs (passed, total) - unify or create adapter |
