## Context

**Current Architecture Problem:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        THE DUPLICATION MESS                                   │
└─────────────────────────────────────────────────────────────────────────────┘

  There are THREE different type systems for the SAME concepts:

  Layer 1: Database ORM Enums (app/models/enums.py)
  ┌─────────────────────────────────────────────────────────────┐
  │ LogType = { TELEMETRY, EVENT, ALERT, STATUS }              │
  │     → Only 4 values, HIGH LEVEL categories                  │
  │     → Used by SQLAlchemy ORM models only                    │
  │     → Values are lowercase: "telemetry", "event", etc.     │
  └─────────────────────────────────────────────────────────────┘

  Layer 2: Business Logic Pydantic (app/models/logs.py)
  ┌─────────────────────────────────────────────────────────────┐
  │ LogType = { TEMP_READING, FAN_SPEED, VOLTAGE, ... }        │
  │     → 14 values, SPECIFIC event types                        │
  │     → Used by ALL rules, parser, engine                      │
  │     → Values are UPPERCASE: "TEMP_READING", etc.            │
  └─────────────────────────────────────────────────────────────┘

  Layer 3: "New" Parser System (app/regulatory/log_parser/)
  ┌─────────────────────────────────────────────────────────────┐
  │ LogType = { TEMP_READING, FAN_SPEED, VOLTAGE, ... }        │
  │     → 14 values, IDENTICAL to layer 2                       │
  │     → Same uppercase values                                   │
  │     → Different class! Different import path!                │
  └─────────────────────────────────────────────────────────────┘

  The Adapter: app/regulatory/parser.py
  ┌─────────────────────────────────────────────────────────────┐
  │ def _adapt_log_entry(new_entry: NewLogEntry) -> LogEntry:   │
  │     """Convert from Layer 3 format to Layer 2 format"""    │
  │     log_type_str = new_entry.log_type.value                  │
  │     adapted_log_type = LogType(log_type_str)                │
  │     ...                                                       │
  └─────────────────────────────────────────────────────────────┘

  THIS IS CRAZY: Same values, same concepts, 3 different enum classes!
```

**What Actually Works Today:**

Looking at the code usage:

| Enum/Type | Where it's ACTUALLY used |
|-----------|--------------------------|
| `app/models/enums.py:LogType` | **Almost nowhere** except ORM column type definition |
| `app/models/logs.py:LogType` | **EVERYWHERE**: rules, engine, parser adapter |
| `app/regulatory/log_parser/log_parser.py:LogType` | Only inside log_parser module itself |

**Decision: Which one to keep?**

→ **Keep `app/models/logs.py:LogType`**
  - It's the one actually used by the business logic
  - It has all 14 specific event types
  - Rules like `RegTemp1`, `RegSens1`, etc. all reference `LogType.TEMP_READING`, `LogType.SENSOR_TIMEOUT`, etc.

→ **Keep `app/models/findings.py:Severity`**
  - Used together with `Finding` model
  - Has extra Pydantic integration

→ **DELETE/MODIFY the others:**
  - `app/models/enums.py`: Keep OTHER enums (`AnalysisSessionStatus`, etc.), but **DELETE** `LogType` and `Severity` (duplicates)
  - `app/regulatory/log_parser/log_parser.py`: **DELETE** the local `LogType` and `LogEntry` class definitions, **IMPORT** from `app/models/logs.py`
  - `app/regulatory/parser.py`: **DELETE THIS FILE ENTIRELY** - it's just an adapter that won't be needed anymore

## Goals / Non-Goals

**Goals:**
1. **Single source of truth** for `LogType`, `Severity`, `LogEntry`
2. **Eliminate `_report_to_dict` duplication** - one function, one location
3. **Eliminate Frontend transformer duplication**
4. **Single source for temperature constants** (2-8°C)
5. **Remove the adapter layer** (`app/regulatory/parser.py`)

**Non-Goals:**
1. **Not changing any business logic** - only refactoring, same behavior
2. **Not changing database schema** - ORM enums mapping handled separately
3. **Not adding new features** - just cleanup
4. **Not re-architecting** - just fixing duplication within existing architecture

## Decisions

### Decision 1: Enum Unification Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ENUM UNIFICATION APPROACH                                  │
└─────────────────────────────────────────────────────────────────────────────┘

  BEFORE:
  ════════

  app/models/enums.py:
  ┌────────────────────────────────────────┐
  │ class LogType(str, enum.Enum):         │ ← DELETE THESE TWO
  │     TELEMETRY = "telemetry"            │
  │     EVENT = "event"                    │
  │     ALERT = "alert"                    │
  │     STATUS = "status"                  │
  ├────────────────────────────────────────┤
  │ class Severity(str, enum.Enum):        │ ← DELETE THIS TOO
  │     CRITICAL = "critical"              │
  │     ...                                │
  ├────────────────────────────────────────┤
  │ class AnalysisSessionStatus(...):      │ ← KEEP THESE
  │ class ViolationStatus(...):            │ ← KEEP THESE
  │ ...                                    │
  └────────────────────────────────────────┘

  app/models/logs.py:
  ┌────────────────────────────────────────┐
  │ class LogType(str, Enum):              │ ← KEEP, BECOME SOURCE
  │     TEMP_READING = "TEMP_READING"      │
  │     FAN_SPEED = "FAN_SPEED"            │
  │     ... (14 values)                     │
  ├────────────────────────────────────────┤
  │ class LogEntry(BaseModel):             │ ← KEEP, BECOME SOURCE
  │     timestamp: datetime                 │
  │     log_type: LogType                   │
  │     ...                                 │
  └────────────────────────────────────────┘

  app/models/findings.py:
  ┌────────────────────────────────────────┐
  │ class Severity(str, Enum):             │ ← KEEP, BECOME SOURCE
  │     CRITICAL = "critical"              │
  │     HIGH = "high"                      │
  │     ...                                 │
  └────────────────────────────────────────┘

  app/regulatory/log_parser/log_parser.py:
  ┌────────────────────────────────────────┐
  │ class LogType(str, Enum):              │ ← DELETE, IMPORT from logs.py
  │     TEMP_READING = "TEMP_READING"      │
  │     ... (SAME 14 values)               │
  ├────────────────────────────────────────┤
  │ class LogEntry:                         │ ← DELETE, IMPORT from logs.py
  │     def __init__(self, ...):           │   (or keep if plain class needed?)
  │         self.timestamp = ...           │
  └────────────────────────────────────────┘


  AFTER:
  ═══════

  ONLY ONE LogType, ONE LogEntry, ONE Severity:

  app/models/logs.py:
  ┌────────────────────────────────────────┐
  │ class LogType(str, Enum):              │ ← THE ONE TRUE LogType
  │     TEMP_READING = "TEMP_READING"      │
  │     FAN_SPEED = "FAN_SPEED"            │
  │     ...                                 │
  ├────────────────────────────────────────┤
  │ class LogEntry(BaseModel):             │ ← THE ONE TRUE LogEntry
  │     timestamp: datetime                 │
  │     log_type: LogType                   │
  │     ...                                 │
  └────────────────────────────────────────┘

  app/models/findings.py:
  ┌────────────────────────────────────────┐
  │ class Severity(str, Enum):             │ ← THE ONE TRUE Severity
  │     CRITICAL = "critical"              │
  │     ...                                 │
  └────────────────────────────────────────┘

  app/models/enums.py:
  ┌────────────────────────────────────────┐
  │ class AnalysisSessionStatus(...):      │ ← STILL HERE
  │ class ViolationStatus(...):            │ ← STILL HERE
  │ class ReportStatus(...):               │ ← STILL HERE
  │ ...                                    │ ← LogType & Severity REMOVED
  └────────────────────────────────────────┘

  app/regulatory/log_parser/log_parser.py:
  ┌────────────────────────────────────────┐
  │ from app.models.logs import LogType, LogEntry  │ ← NOW IMPORTS
  │                                                   │   (no local definition)
  └──────────────────────────────────────────────────┘

  DELETED FILE:
  ═══════════════
  app/regulatory/parser.py  ←  GONE. Adapter no longer needed.
```

**Special Case: ORM `enums.py:LogType` with only 4 values**

The ORM layer has:
```python
# app/models/enums.py (4 values, lowercase)
class LogType(str, enum.Enum):
    TELEMETRY = "telemetry"
    EVENT = "event"
    ALERT = "alert"
    STATUS = "status"
```

But the business logic has:
```python
# app/models/logs.py (14 values, UPPERCASE)
class LogType(str, Enum):
    TEMP_READING = "TEMP_READING"
    FAN_SPEED = "FAN_SPEED"
    ...
```

**QUESTION: What's in the actual database column?**

Let me check `orm.py` to see how this maps...

Actually, looking at the code more carefully:

1. `enums.py:LogType` (4 vals) is used as SQLAlchemy column type
2. `logs.py:LogType` (14 vals) is used in Pydantic/business logic
3. They have **DIFFERENT VALUES**: `"telemetry"` vs `"TEMP_READING"`

**This is potentially a bigger issue.** But wait - let me check if `enums.py:LogType` is actually used for any real column storage, or if it's just unused leftover...

Actually, for this cleanup phase, let's be **conservative**:

**Phase 1 Decision:**
- Keep `enums.py` AS IS for ORM-related enums
- Just make sure `logs.py:LogType` is the one used everywhere in business logic
- The 4-value LogType in enums? If it's only used as a DB type and not actively in logic, we can address it later or just leave it
- **Main goal: Eliminate the 14-value LogType DUPLICATE (logs.py vs log_parser.py)**

### Decision 2: _report_to_dict Extraction

**Current state - 3 locations:**

| Location | Lines | Key Differences |
|----------|-------|-----------------|
| `validate.py:95-143` | 49 | Includes `evidence_logs` → `evidence` mapping, `violation_logs` handling |
| `persistence.py:397-445` | 49 | Almost identical to validate.py version |
| `aggregator.py:304-324` | 21 | SHORTER - only does summary, no findings/violations conversion |

**Strategy:**
1. Create a canonical version in `app/reports/serializers.py`
2. It should handle ALL cases (the superset)
3. Delete all 3 copies
4. Update imports

**Canonical Function Signature:**
```python
def compliance_report_to_dict(
    report: ComplianceReport,
    include_findings: bool = True,
    include_evidence: bool = True
) -> Dict[str, Any]:
    """
    Convert ComplianceReport to dict for API response.
    
    Handles:
    - Summary with category breakdowns
    - Findings → DetectedViolation conversion
    - Evidence mapping (ORM objects to dict)
    """
```

### Decision 3: Frontend Transformer Unification

**Current duplicates:**

```
Dashboard.tsx:42-59
  function findingsToViolations(findings: Finding[]): DetectedViolation[]

transformers.ts:36-53
  function findingsToDetectedViolations(findings: Finding[]): DetectedViolation[]
  → Slightly different fields, but same purpose
```

```
Dashboard.tsx:61-68
  function calculateComplianceScore(passedCount: number, failedCount: number): number
  → total = passed + failed

transformers.ts:84-90
  function calculateComplianceScore(passedCount: number, totalRules: number): number
  → takes total directly
```

**Strategy:**
1. `transformers.ts` should be the **single source**
2. Add any missing functionality from Dashboard.tsx to transformers.ts
3. Delete the Dashboard.tsx local copies
4. Update Dashboard.tsx to import from transformers.ts

**For the signature difference in calculateComplianceScore:**
- Keep both as overloads OR create a unified one
- Or keep the `(passed, total)` version and update Dashboard to compute total locally

### Decision 4: Constants Unification

**Current:**
- `RegTemp1.MIN_TEMP = 2.0`, `RegTemp1.MAX_TEMP = 8.0` - defined ONCE in rules
- But hardcoded as `2.0 <= x <= 8.0` in:
  - `alarm.py:47`
  - `cool.py:98`
  - `power.py:135`
  - `ops.py:82`
  - `Dashboard.tsx:40`

**Strategy:**
1. **Backend:** Just reference `RegTemp1.MIN_TEMP` and `RegTemp1.MAX_TEMP` directly
   - These are already defined as class constants
   - No need for a separate constants module (yet)

2. **Frontend:** Hardcoded `{ min: 2, max: 8 }`
   - Options:
     a) Create a config endpoint `GET /api/config/regulatory-constants`
     b) Include in existing responses like `GET /api/health`
     c) Just document it and keep hardcoded (least good)
   
   - Choose (b) for simplicity: add to health endpoint response

## Migration Plan

**Order is important!**

```
Phase 1: Unify LogType/LogEntry (log_parser.py)
─────────────────────────────────────────────────
1. Delete local LogType and LogEntry from app/regulatory/log_parser/log_parser.py
2. Add imports: from app.models.logs import LogType, LogEntry
3. Verify LogEntry is compatible (Pydantic class vs plain class with __init__)
   - If needed, create adapter function INSIDE log_parser.py (temporary)
   - Or convert log_parser to use Pydantic LogEntry

Phase 2: Delete the adapter layer (parser.py)
─────────────────────────────────────────────────
1. Find all imports of app/regulatory.parser
2. Replace them with direct imports from app/regulatory.log_parser
3. DELETE app/regulatory/parser.py

Phase 3: Handle Severity duplicate
─────────────────────────────────────────────────
1. Find all imports from app.models.enums import Severity
2. Replace with from app.models.findings import Severity
3. Delete Severity class from app/models/enums.py
4. Keep other enums in enums.py (AnalysisSessionStatus, etc.)

Phase 4: Extract _report_to_dict
─────────────────────────────────────────────────
1. Create app/reports/serializers.py
2. Copy the most complete version (validate.py or persistence.py)
3. Make it handle all edge cases
4. Update validate.py to import from serializers
5. Update persistence.py to import from serializers
6. Update aggregator.py to import from serializers
7. DELETE the local copies from all 3 files

Phase 5: Frontend transformers unification
─────────────────────────────────────────────────
1. Compare findingsToViolations (Dashboard) vs findingsToDetectedViolations (transformers)
2. Unify them in transformers.ts
3. Delete local version from Dashboard.tsx
4. Update Dashboard imports

Phase 6: Fix constant hardcoding
─────────────────────────────────────────────────
1. Update alarm.py:47 → use RegTemp1.MIN_TEMP, RegTemp1.MAX_TEMP
2. Update cool.py:98 → same
3. Update power.py:135 → same
4. Update ops.py:82 → same
5. Backend: Consider adding safe_range to API responses
6. Frontend: Either fetch from API or keep documented

Phase 7: Test & Verify
─────────────────────────────────────────────────
1. Run existing tests
2. Manual test: upload logs, verify analysis works
3. Check for any import errors
4. Docker rebuild test
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| LogEntry Pydantic vs plain class compatibility | Compare signatures carefully. If `log_parser` needs plain class for mutability, create a conversion function or keep a minimal wrapper. |
| Breaking imports | Do each phase in sequence, verify after each. Use search for import patterns. |
| _report_to_dict versions have subtle differences | Create a test that compares output from all 3 versions with the same input, then make the canonical one match expected behavior. |
| Frontend has different function signatures | Keep both as separate functions or create adapters. Don't break existing usage. |

## Open Questions

1. **LogEntry: Pydantic model vs plain class?**
   - `app/models/logs.py:LogEntry` is a Pydantic `BaseModel`
   - `app/regulatory/log_parser/log_parser.py:LogEntry` is a plain class with `__init__` and `to_dict()`
   - Are these interchangeable? Does log_parser need mutability that Pydantic doesn't allow?

2. **What about the 4-value LogType in enums.py?**
   - It seems to be for ORM level only, with different values (lowercase, high-level categories)
   - Is this actually used in the database? Should it be unified with the 14-value one?
   - For now: leave it, focus on the 14-value duplicate first

3. **Frontend safe range: Fetch from API or keep hardcoded?**
   - The 2-8°C comes from the regulatory spec (`docs/client/Medical Device Regulatory Constraints.md`)
   - It's unlikely to change often
   - Options:
     a) Hardcode but centralize in a `constants.ts` file
     b) Add to API response
   - Leaning toward (a) for simplicity + (b) for "single source of truth" ideal
