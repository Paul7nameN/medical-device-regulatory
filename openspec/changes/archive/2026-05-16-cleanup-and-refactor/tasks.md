## Phase 1: Unify LogType and LogEntry in log_parser

**Goal:** Eliminate the duplicate LogType and LogEntry defined locally in log_parser.py. Use the versions from app/models/logs.py instead.

- [x] 1.1 Compare the two LogEntry implementations:
  - `app/models/logs.py`: Pydantic BaseModel with fields: timestamp, log_type, raw_value, parsed_value, sensor_id, metadata
  - `app/regulatory/log_parser/log_parser.py`: Plain class with __init__, same fields, plus `to_dict()` method
  - Check if log_parser code modifies LogEntry instances (Pydantic might be immutable by default)

- [x] 1.2 Check ParseResult class in log_parser.py:
  - Does it need modification if LogEntry changes?

- [x] 1.3 Modify `app/regulatory/log_parser/log_parser.py`:
  - DELETE local `LogType` enum definition (lines 23-36)
  - DELETE local `LogEntry` class definition (lines 39-64)
  - ADD import at top: `from app.models.logs import LogType, LogEntry`
  - Check if `to_dict()` method is needed - Pydantic has `.model_dump()` instead
  - If `.to_dict()` is called on LogEntry elsewhere, either:
    a) Add `.to_dict()` method to Pydantic LogEntry, OR
    b) Replace `.to_dict()` calls with `.model_dump()`

- [x] 1.4 Update all imports from log_parser:
  - `app/regulatory/parser.py` (we'll delete this next phase)
  - Anywhere else that imports LogType/LogEntry from log_parser

- [x] 1.5 Run tests to verify log_parser still works:
  - `tests/test_log_parser.py`
  - `tests/test_parser.py`

---

## Phase 2: Delete the Adapter Layer (parser.py)

**Goal:** `app/regulatory/parser.py` exists solely to convert between the "old" and "new" log_parser systems. After Phase 1 unification, this adapter is no longer needed.

- [x] 2.1 Find all imports of `app.regulatory.parser`:
  - Search the codebase for `from app.regulatory.parser import` or `from app.regulatory import parser`

- [x] 2.2 For each importer, redirect to `app.regulatory.log_parser`:
  - `from app.regulatory.parser import LogParser, parse_raw_logs`
    → `from app.regulatory.log_parser import LogParser, parse_raw_logs`
  - Note: parser.py also re-exported `detect_telemetry_gaps`, etc. from log_parser

- [x] 2.3 Check for any usage differences:
  - `parser.py:LogParser.parse_lines()` returns `List[LogEntry]`
  - `log_parser.py:LogParser.parse_lines()` returns `ParseResult` object
  - If code expects `List[LogEntry]` but gets `ParseResult`, need `.entries`

- [x] 2.4 DELETE file: `app/regulatory/parser.py`

- [x] 2.5 Run tests:
  - Check that nothing breaks

---

## Phase 3: Unify Severity Enum

**Goal:** `Severity` is defined in TWO places:
1. `app/models/enums.py:17-22`
2. `app/models/findings.py:7-12` (IDENTICAL values!)

Keep the one in `findings.py` (used with Finding model), delete the duplicate.

- [x] 3.1 Find all imports of Severity:
  - Search: `from app.models.enums import Severity`
  - Search: `from app.models.findings import Severity`
  - Search: `from app.models import enums` then `enums.Severity`

- [x] 3.2 Update imports to use `app.models.findings`:
  - `from app.models.enums import Severity` → `from app.models.findings import Severity`

- [x] 3.3 DELETE `Severity` class from `app/models/enums.py`:
  - Remove lines 17-22 (the Severity enum)
  - KEEP all other enums: `AnalysisSessionStatus`, `ViolationStatus`, `ReportStatus`, `AuditAction`, `DeviceStatus`
  - KEEP `LogType` in enums.py for now (only 4 values, ORM-related, separate issue)

- [x] 3.4 Verify:
  - No more `from app.models.enums import Severity`
  - All Severity usage comes from `app.models.findings`

---

## Phase 4: Extract _report_to_dict to Central Location

**Goal:** `_report_to_dict` exists in 3 files with almost identical code. Create one canonical version.

- [x] 4.1 Read and compare all 3 versions:
  - `app/api/validate.py:95-143`
  - `app/services/persistence.py:397-445`
  - `app/reports/aggregator.py:304-324` (shorter version)

- [x] 4.2 Identify the differences:
  - What fields does each include?
  - How is evidence/violation_logs handled?
  - Create a "superset" version that handles all cases

- [x] 4.3 Create `app/reports/serializers.py`:
  - Add function `compliance_report_to_dict(report, include_findings=True, include_evidence=True)`
  - Make it the most complete version
  - Handle edge cases from all 3 callers

- [x] 4.4 Add `__init__.py` to `app/reports/` if not exists:
  - Export the new function

- [x] 4.5 Update `app/api/validate.py`:
  - Remove local `_report_to_dict` function
  - Import from `app.reports.serializers` instead
  - Verify behavior is identical

- [x] 4.6 Update `app/services/persistence.py`:
  - Remove local `_report_to_dict` function
  - Import from `app.reports.serializers` instead
  - Verify behavior is identical

- [x] 4.7 Update `app/reports/aggregator.py`:
  - This one has a SHORTER version - check if it needs full version
  - Remove local conversion code
  - Import and use the centralized function

---

## Phase 5: Frontend - Unify Transformer Functions

**Goal:** Dashboard.tsx has local copies of functions that also exist in transformers.ts.

- [x] 5.1 Compare the two findings converters:
  - `Dashboard.tsx:42-59`: `findingsToViolations(findings)`
  - `transformers.ts:36-53`: `findingsToDetectedViolations(findings)`
  - Compare returned field by field:
    - id generation
    - reg_code vs rule_id
    - status logic
    - evidence field
    - timestamps

- [x] 5.2 Compare compliance score calculators:
  - `Dashboard.tsx:61-68`: `calculateComplianceScore(passedCount, failedCount)`
    - total = passed + failed
  - `transformers.ts:84-90`: `calculateComplianceScore(passedCount, totalRules)`
    - takes total directly

- [x] 5.3 Compare category grouping:
  - `Dashboard.tsx:166-195`: `categoryData` useMemo (inline logic)
  - `transformers.ts:55-82`: `groupViolationsByCategory(findings)`

- [x] 5.4 Decide: Keep which versions?
  - Keep the `transformers.ts` versions (central location)
  - Add any missing fields/features from Dashboard versions

- [x] 5.5 Update `transformers.ts` if needed:
  - Add overload or variant for `calculateComplianceScore(passed, failed)` vs `(passed, total)`
  - Or just update Dashboard to compute total = passed + failed

- [x] 5.6 Modify `Dashboard.tsx`:
  - REMOVE local `findingsToViolations()` function
  - REMOVE local `calculateComplianceScore()` function
  - REPLACE inline `categoryData` logic with `groupViolationsByCategory()` call
  - ADD imports from `@/lib/utils/transformers`
  - Test: verify Dashboard still works

---

## Phase 6: Fix Hardcoded Temperature Constants

**Goal:** `2.0` and `8.0` are hardcoded in many places. Use `RegTemp1.MIN_TEMP` and `RegTemp1.MAX_TEMP` instead.

**Current locations with hardcoded values:**

| File | Line | Code |
|------|------|------|
| `app/regulatory/alarm.py` | 47 | `in_range = 2.0 <= temp <= 8.0` |
| `app/regulatory/cool.py` | 98 | `in_range = 2.0 <= val <= 8.0` |
| `app/regulatory/power.py` | 135 | `if t_val < 2.0 or t_val > 8.0:` |
| `app/regulatory/ops.py` | 82 | `in_range = 2.0 <= val <= 8.0` |
| `frontend/src/pages/Dashboard.tsx` | 40 | `const safeRange = { min: 2, max: 8 }` |

**Already defined in:** `app/regulatory/rules/temp.py`:
```python
class RegTemp1(BaseRule):
    ...
    MIN_TEMP = 2.0
    MAX_TEMP = 8.0
```

- [x] 6.1 Update `app/regulatory/alarm.py`:
  - Add import: `from app.regulatory.rules.temp import RegTemp1`
  - Change line 47: `in_range = RegTemp1.MIN_TEMP <= temp <= RegTemp1.MAX_TEMP`

- [x] 6.2 Update `app/regulatory/cool.py`:
  - Add import: `from app.regulatory.rules.temp import RegTemp1`
  - Change line 98: `in_range = RegTemp1.MIN_TEMP <= val <= RegTemp1.MAX_TEMP`

- [x] 6.3 Update `app/regulatory/power.py`:
  - Add import: `from app.regulatory.rules.temp import RegTemp1`
  - Change line 135: `if t_val < RegTemp1.MIN_TEMP or t_val > RegTemp1.MAX_TEMP:`

- [x] 6.4 Update `app/regulatory/ops.py`:
  - Add import: `from app.regulatory.rules.temp import RegTemp1`
  - Change line 82: `in_range = RegTemp1.MIN_TEMP <= val <= RegTemp1.MAX_TEMP`

- [x] 6.5 Frontend: Decide approach for `safeRange`:
  - Option A: Keep hardcoded but add comment: `// Matches REG-TEMP-1: 2-8°C`
  - Option B: Create `src/lib/constants.ts` with `REGULATORY_TEMP_RANGE = { min: 2, max: 8 }`
  - Option C: Fetch from backend API (requires backend change)
  
  → **Recommendation:** Option B for now. Simple, documented, single location.

- [x] 6.6 If Option B: Create `frontend/src/lib/constants.ts`:
  ```typescript
  export const REGULATORY_CONSTANTS = {
    safeTemperatureRange: {
      min: 2,
      max: 8,
    },
  } as const
  ```

- [x] 6.7 Update `Dashboard.tsx` to use constants:
  - Import from `@/lib/constants`
  - Replace inline object

---

## Phase 7: Test, Verify, Docker

- [x] 7.1 Run all backend tests:
  ```bash
  cd backend
  python -m pytest tests/ -v
  ```

- [x] 7.2 Fix any failing tests

- [x] 7.3 Run frontend type check:
  ```bash
  cd frontend
  npm run build  # or npm run typecheck if exists
  ```

- [x] 7.4 Rebuild and test with Docker:
  ```bash
  docker-compose down
  docker-compose up -d --build
  docker-compose logs -f
  ```

- [x] 7.5 Manual verification:
  - Open frontend: http://localhost:5173
  - Upload sample log file
  - Verify analysis works
  - Check Dashboard displays correctly

---

## Summary of Files Changed

| Action | Files |
|--------|-------|
| **Modified** | `app/regulatory/log_parser/log_parser.py` |
| **Modified** | `app/models/enums.py` (remove Severity) |
| **Modified** | `app/api/validate.py` (remove _report_to_dict) |
| **Modified** | `app/services/persistence.py` (remove _report_to_dict) |
| **Modified** | `app/reports/aggregator.py` (remove local conversion) |
| **Modified** | `app/regulatory/alarm.py`, `cool.py`, `power.py`, `ops.py` (constants) |
| **Modified** | `frontend/src/pages/Dashboard.tsx` (use transformers, constants) |
| **Modified** | Multiple other files: import statement updates |
| **Created** | `app/reports/serializers.py` |
| **Created** | `frontend/src/lib/constants.ts` (optional) |
| **Deleted** | `app/regulatory/parser.py` |

---

## Order of Implementation

**Do these in order:**
1. Phase 1 (log_parser unification)
2. Phase 2 (delete parser.py adapter)
3. Phase 3 (Severity enum unification)
4. Phase 4 (_report_to_dict extraction)
5. Phase 5 (Frontend transformers)
6. Phase 6 (Constants)
7. Phase 7 (Test & Verify)
