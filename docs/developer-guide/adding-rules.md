# Cum Adaugi Reguli Noi

O regula este o clasa Python care mosteneste din `BaseRule`.

---

## Structura unei reguli

```python
from app.regulatory.rules.base import BaseRule, register_rule
from app.models.findings import Severity

@register_rule
class RegTempNou(BaseRule):
    rule_id = "REG-TEMP-NEW"
    description = "Noua regula"
    category = "TEMP"
    default_severity = Severity.HIGH

    def validate(self, logs, context):
        # Logica de validare aici
        pass
```

---

## Unde sa o pui

Adauga o regula in fisierul corespunzator categoriei:

| Categorie | Fisier |
|-----------|--------|
| TEMP | `backend/app/regulatory/rules/temp.py` |
| SENS | `backend/app/regulatory/rules/sens.py` |
| ALARM | `backend/app/regulatory/rules/alarm.py` |
| DATA | `backend/app/regulatory/rules/data.py` |
| POWER | `backend/app/regulatory/rules/power.py` |
| COOL | `backend/app/regulatory/rules/cool.py` |
| INS | `backend/app/regulatory/rules/ins.py` |
| OPS | `backend/app/regulatory/rules/ops.py` |

---

## Cum o inregistrezi

### Metoda 1: Cu decorator (Recomandat)

Foloseste decoratorul `@register_rule`:

```python
from app.regulatory.rules.base import BaseRule, register_rule
from app.models.findings import Severity

@register_rule
class RegNou(BaseRule):
    rule_id = "REG-NEW-1"
    # ... restul codului
```

Regula va fi inregistrata automat in `RuleRegistry` cand modulul este importat.

---

## Exemplu Complet

```python
from typing import List, Dict, Any
from app.regulatory.rules.base import BaseRule, register_rule
from app.models.findings import Severity, Finding, Evidence
from app.models.logs import LogEntry

@register_rule
class RegTempNou(BaseRule):
    rule_id = "REG-TEMP-NEW"
    description = "Verifica ca temperatura nu scade sub 0°C"
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
                            message=f"Temperatura {temp}°C scade sub 0°C",
                            evidence_logs=[log],
                            severity=Severity.CRITICAL,
                            remediation_hint="Verifica sistemul de incalzire"
                        )
                    )
        
        if not findings:
            findings.append(self.create_pass_finding())
        
        return findings
```

---

## Metode ajutatoare in `BaseRule`

### `create_finding()`

Creeaza un finding cu toate campuri:

- `passed: bool` - True daca regula a trecut
- `message: str` - Mesaj explicativ
- `evidence_logs: List[LogEntry]` (optional) - Log-urile care au dus la aceasta concluzie
- `severity: Severity` (optional) - Daca nu e nevoie de un severity diferit de cel implicit
- `remediation_hint: str` (optional) - Indiciune despre ce trebuie sa faci
- `needs_visual_verification: bool` (optional) - Daca necesita verificare vizuala

### `create_pass_finding()`

Creeaza un finding de "trecere.

### `create_info_finding()`

Creeaza un finding de tip info.

---

## Dupa ce ai creat regula noua

1. Verifica daca este importata in `main.py`

In `backend/app/main.py`:

```python
from app.regulatory.rules import (
    # ... regulile
)
```

Daca ai adaugi o noua categorie noua in fisier existent, nu trebuie sa modificat nimic in `main.py` - decoratorul face treaba.

2. Ruleaza testele:

```bash
cd backend
pytest tests/test_engine.py -v
```
