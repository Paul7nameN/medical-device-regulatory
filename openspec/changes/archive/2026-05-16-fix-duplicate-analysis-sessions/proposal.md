## Why

**Problema fundamentală:** Există **două cai separate** pentru aceleași date de analiză, fiecare cu:
- **Timestamp diferit** → deduplicare eșuată → dubluri
- **Structură diferită** → neconcordanțe → scor 100% eronat

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FLUX ACTUAL (CU PROBLEME)                            │
└─────────────────────────────────────────────────────────────────────────┘

  User uploadă .txt:
  ─────────────────────────

  [Frontend] FileUploadZone → POST /api/reports/generate
       │
       ▼
  [Backend] reports.py → generate_compliance_report()
       │
       ├──────────────────────────────────────────────────────────────────┐
       │  PAS 1: Creează base_report                                    │
       │  ─────────────────────────────                                  │
       │  base_report = engine.validate()                               │
       │    → ComplianceReport                                           │
       │    → analyzed_at: timestamp CÂND s-a făcut validarea          │
       │    → summary: { TEMP: {passed,failed,total}, SENS: ... }     │
       │    → findings: [Finding, Finding, ...]                         │
       │    → passed_count, failed_count                                 │
       │                                                                 │
       ├──────────────────────────────────────────────────────────────────┤
       │  PAS 2: Salvează în BD                                         │
       │  ─────────────────────                                          │
       │  persistence.save_analysis_session(                            │
       │    report=base_report,  ← FOLOSEȘTE base_report!              │
       │    ...                                                          │
       │  )                                                              │
       │                                                                 │
       │  Ce se salvează în _latest_analysis_data:                      │
       │  {                                                              │
       │    "analyzedAt": base_report.analyzed_at,     ← TIMESTAMP A   │
       │    "validationResult": base_report.to_dict(),  ← STRUCTURĂ A  │
       │  }                                                              │
       │                                                                 │
       ├──────────────────────────────────────────────────────────────────┤
       │  PAS 3: Creează aggregated pentru RĂSPUNS                     │
       │  ────────────────────────────────────────────────────          │
       │  aggregated = aggregator.aggregate(                            │
       │    regulatory_report=base_report,                              │
       │    ...                                                          │
       │  ) → AggregatedComplianceReport                                │
       │                                                                 │
       │  aggregated are:                                                │
       │    → generated_at: datetime.now()  ← TIMESTAMP B (NOU!)      │
       │    → summary: { critical_count, high_count, ... }  ← DIFERIT! │
       │    → violations_by_severity: { critical: [...], ... }         │
       │    → violations_by_rule: {...}                                 │
       │    → FINDINGS NU sunt direct accesibili!                       │
       │                                                                 │
       ├──────────────────────────────────────────────────────────────────┤
       │  PAS 4: Returnează frontendului                                │
       │  ─────────────────────────                                      │
       │  return {                                                       │
       │    report: aggregated,         ← AggregatedComplianceReport   │
       │    generated_at: datetime.now() ← ALT TIMESTAMP!               │
       │  }                                                              │
       └──────────────────────────────────────────────────────────────────┘
       │
       ▼
  [Frontend] Primește { report: aggregated, generated_at }
       │
       ▼
  [Frontend] EXTRAGE findings DIN aggregated.violations_by_severity
       │
       ├─► Nu găsește findings direct → le extrage din altă structură
       ├─► Construiește UN NOU ValidationResult cu:
       │     • analyzedAt = generated_at (TIMESTAMP B)
       │     • findings (extrase din violations_by_severity)
       │
       ▼
  [Frontend] addAnalysis() → localStorage
       │
       ├─► analyzedAt = TIMESTAMP B (diferit de cel din BD)
       └─► validationResult = structură construită manual

  La RESTART/REFRESH:
  ─────────────────────

  Din BD (încărcat în refreshHistory):
    • analyzedAt = TIMESTAMP A (base_report.analyzed_at)
    • validationResult = base_report.to_dict()

  Din localStorage:
    • analyzedAt = TIMESTAMP B (datetime.now())
    • validationResult = structură construită manual

  REZULTAT:
    • Două timestamp-uri DIFERITE → DEDUPLICARE EȘUATĂ → DOUBLERI!
    • Două structuri DIFERITE → NECOARDONĂȚE → posibil SCOR 100%!
```

---

## What Changes

### Schimbarea Fundamentală: Un singur "sursă de adevăr"

**Timestamp UNIC:**
- Folosește `base_report.analyzed_at` (sau un singur timestamp consistent)
- Atât când salvezi în BD, CÂT și când returnezi frontendului

**Structură UNICĂ:**
- Opțiunea A (simplă): Returnează și `base_report.to_dict()` în răspuns
- Opțiunea B (mai complexă): Salvează și returnează întotdeauna aceeași structură

### Soluția Recomandată: Opțiunea A (Minimală)

1. **Backend:** Când returnează răspunsul, folosește același timestamp:
   - În loc de `datetime.now()` pentru `generated_at`, folosește `base_report.analyzed_at`

2. **sau, și mai bine:** Adaugă `base_report.to_dict()` direct în răspuns:
   - Frontendul NU trebuie să construiască ValidationResult din AggregatedComplianceReport
   - Primește DIRECT ceea ce este salvat în BD

3. **Frontend:** Folosește datele primite direct, fără a le reconstrui
   - Această schimbare poate fi optională dacă facem backendul să returneze structura corectă

---

## Capabilities

### Modified Capabilities
- `analysis-sessions`: Corectează unicitatea sesiunilor și consistența datelor
- `log-storage`: Asigură consistența între ce se salvează și ce se returnează

---

## Impact

- **Backend:**
  - `app/api/reports.py`: Modifică timestamp-ul și/sau structura răspunsului
  - Poate fi nevoie de o cheie unică mai bună pentru deduplicare

- **Frontend:**
  - Opțional: Dacă backendul returnează structura corectă, modificări minore
  - Sau: Folosește o cheie de deduplicare mai robustă (ID sesiune, hash findings)
