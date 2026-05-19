# How to Add New Rules

A rule is a Python class that inherits from `BaseRule`.

---

## Structure of a Rule

```python
from app.regulatory.rules.base import BaseRule, register_rule
from app.models.findings import Severity

@register_rule
class RegTempNew(BaseRule):
    rule_id = "REG-TEMP-NEW"
    description = "New rule description"
    category = "TEMP"
    default_severity = Severity.HIGH

    def validate(self, logs, context):
        # Validation logic here
        pass
```

---

## Where to place it

Add a rule to the file corresponding to its category:

| Category | File |
|----------|------|
| TEMP | `backend/app/regulatory/rules/temp.py` |
| SENS | `backend/app/regulatory/rules/sens.py` |
| ALARM | `backend/app/regulatory/rules/alarm.py` |
| DATA | `backend/app/regulatory/rules/data.py` |
| POWER | `backend/app/regulatory/rules/power.py` |
| COOL | `backend/app/regulatory/rules/cool.py` |
| INS | `backend/app/regulatory/rules/ins.py` |
| OPS | `backend/app/regulatory/rules/ops.py` |

---

## How to register

### Method 1: With decorator (Recommended)

Use the `@register_rule` decorator:

```python
from app.regulatory.rules.base import BaseRule, register_rule
from app.models.findings import Severity

@register_rule
class RegNew(BaseRule):
    rule_id = "REG-NEW-1"
    # ... rest of code
```

The rule is automatically registered in `RuleRegistry` when the module is imported.

---

## Complete Example

```python
from typing import List, Dict, Any
from app.regulatory.rules.base import BaseRule, register_rule
from app.models.findings import Severity, Finding, Evidence
from app.models.logs import LogEntry

@register_rule
class RegTempNew(BaseRule):
    rule_id = "REG-TEMP-NEW"
    description = "Check that temperature does not drop below 0°C"
    category = "TEMP"
    default_severity = Severity.CRITICAL

    def validate(self, logs: List[LogEntry], context: Dict[str, Any]) -> List[Finding]:
        findings = []
        
        for log in logs:
            if log.log_type.value == "TEMP_READING":
                temp = log.parsed_value
                if temp is not None and temp < 0:
                    findings.append(
                        self.create_finding(
                            passed=False,
                            message=f"Temperature {temp}°C drops below 0°C",
                            evidence_logs=[log],
                            severity=Severity.CRITICAL,
                            remediation_hint="Check heating system"
                        )
                    )
        
        if not findings:
            findings.append(self.create_pass_finding())
        
        return findings
```

---

## Helper Methods in `BaseRule`

### `create_finding()`

Create a finding with all fields:

- `passed: bool` - True if rule passed

- `message: str` - Explanatory message

- `evidence_logs: List[LogEntry]` (optional) - Log entries that led to this conclusion

- `severity: Severity` (optional) - If you need a different severity than default

- `remediation_hint: str` (optional) - Hint about what to do

- `needs_visual_verification: bool` (optional) - If visual verification is needed

### `create_pass_finding()`

Create a "pass" finding.

### `create_info_finding()`

Create an info finding.

---

## After creating the new rule

1. Check if it's imported in `main.py`

In `backend/app/main.py`:

```python
from app.regulatory.rules import (
    # ... existing rules
)
```

If you add a new category to an existing file, you don't need to modify anything in `main.py` - the decorator handles it.

2. Run tests:

```bash
cd backend
pytest tests/test_engine.py -v
```
