## Context

Acest change se bazează pe 3 probleme identificate în timpul explorării:

### Problema 1: Redundanță UI
În `Dashboard.tsx` există:
- Un **tab "History"** întotdeauna vizibil în bara de taburi
- Un **buton "View History"** care apare când `analysisHistory.length > 1`

Ambele fac același lucru: `setActiveTab('history')`. Această redundanță creează confuzie.

### Problema 2: Lipsă Rules Reference
Nu există un loc central unde utilizatorul poate vedea TOATE cele 21 de reguli MED-THERM-2026:
- 4 REG-TEMP
- 3 REG-SENS
- 3 REG-ALARM
- 3 REG-DATA
- 2 REG-POWER
- 2 REG-COOL
- 2 REG-INS
- 2 REG-OPS

Regulile sunt "imprasticate" în:
- `backend/app/regulatory/rules/*.py` (implementare)
- `docs/client/Medical Device Regulatory Constraints.md` (document oficial)
- `backend/app/ai/analyst/prompts.py` (context pentru AI)

### Problema 3: Bug ID-uri reguli
În `backend/app/ai/image/converters.py`, dicționarul `CHART_VIOLATION_MAPPINGS` folosește ID-uri incorecte:

| Tip violare | ID curent (greșit) | ID corect |
|-------------|---------------------|-----------|
| excursion | REG-TEMP-1 ✅ | REG-TEMP-1 |
| gap | REG-DATA-1 ✅ | REG-DATA-1 |
| slow_recovery | REG-TEMP-5 ❌ | REG-TEMP-3 |
| frequent_access | REG-OPS-3 ❌ | REG-OPS-2 |
| fallback | REG-IMAGES-001 ❌ | (nu există) |

Acest bug cauzează că:
- Violările din analiza imaginilor au ID-uri care nu există în sistem
- Nu se pot corela cu regulile din `@register_rule`
- Inconsistență între analiza .txt și analiza .png

---

## Goals / Non-Goals

**Goals:**
1. ✅ Elimină redundanța UI - șterge butonul "View History", păstrează doar tab-ul
2. ✅ Creează un tab "Rules" în Dashboard care afișează TOATE cele 21 de reguli
3. ✅ Corectează maparea ID-urilor de reguli în `converters.py`
4. ✅ Regulile trebuie filtrable pe categorii și tip validare

**Non-Goals:**
1. ❌ Nu se modifică implementarea regulilor existente (clasele `@register_rule`)
2. ❌ Nu se creează un nou endpoint API pentru reguli (se folosesc constante în frontend)
3. ❌ Nu se rescrie prompții AI doar pentru reguli
4. ❌ Nu se schimbă flow-ul de analiză existent

---

## Decisions

### Decizia 1: Unde să stocăm datele despre reguli?

**Opțiuni considerate:**
- **A**: Endpoint backend `/api/rules` care citește din `@register_rule`
- **B**: Constante în frontend replicate din document
- **C**: Hibrid: Endpoint care returnează datele dinamice

**Decizie: Opțiunea B (Constante în frontend)**

**Rationale:**
- Regulile sunt STABILE (MED-THERM-2026 standard, nu se schimbă)
- Pentru display în UI, nu avem nevoie de date dinamice
- Mai simplu, fără requests suplimentare
- Putem include și descrieri detaliate și informații de context

**Structură:**
```typescript
// frontend/src/lib/constants/regulatoryRules.ts

export interface RegulatoryRule {
  id: string;                    // "REG-TEMP-1"
  category: string;              // "TEMP", "SENS", etc.
  categoryName: string;          // "Thermal Safety", "Sensor Redundancy", etc.
  title: string;                 // "Operating Temperature Range"
  description: string;           // Descriere detaliată
  threshold: string;             // "2°C ≤ T ≤ 8°C"
  severity: Severity;            // "CRITICAL", "HIGH", etc.
  validationType: "operational" | "inspection";
  source: string;                // "logs" | "inspection" | "combined"
  confidence: number;            // 1.0, 0.5, 0.0
}
```

### Decizia 2: Structura UI pentru Rules Reference

**Arhitectură:**
```
Dashboard
├── Tab: Overview
├── Tab: Temperature
├── Tab: Violations
├── Tab: History
└── Tab: Rules ◀── NOU
    ├── Filters: [Toate Categorii ▼]  [Toate Tipurile ▼]
    └── Cards grid:
        ┌─────────────────────────────┐
        │ REG-TEMP-1    [Operational] │
        │ Thermal Safety              │
        │                             │
        │ Prag: 2°C ≤ T ≤ 8°C        │
        │ Severitate: HIGH            │
        │                             │
        │ Descriere: Sistemul trebuie│
        │ să mențină temperatura în   │
        │ intervalul permis în orice  │
        │ moment.                     │
        └─────────────────────────────┘
```

### Decizia 3: Fix pentru converters.py

**Minimal change - doar actualizează dicționarul:**

```python
# ÎNAINTE (greșit):
CHART_VIOLATION_MAPPINGS: Dict[str, Dict[str, Any]] = {
    "excursion": {"rule_id": "REG-TEMP-1", ...},
    "gap": {"rule_id": "REG-DATA-1", ...},
    "slow_recovery": {"rule_id": "REG-TEMP-5", ...},  # ❌
    "frequent_access": {"rule_id": "REG-OPS-3", ...},  # ❌
}

# DUPĂ (corect):
CHART_VIOLATION_MAPPINGS: Dict[str, Dict[str, Any]] = {
    "excursion": {"rule_id": "REG-TEMP-1", ...},      # ✅
    "gap": {"rule_id": "REG-DATA-1", ...},             # ✅
    "slow_recovery": {"rule_id": "REG-TEMP-3", ...},   # ✅ (recovery ≤3min)
    "frequent_access": {"rule_id": "REG-OPS-2", ...},  # ✅ (<10 events/hour)
}
```

**Pentru fallback:**
- Înlocuim `REG-IMAGES-001` cu un ID existent
- Sau folosim `REG-TEMP-1` ca fallback generic
- Sau eliminăm fallback-ul și aruncăm o eroare

**Decizie:** Folosim `REG-TEMP-1` ca fallback (cea mai comună regulă)

---

## Risks / Trade-offs

### Riscul 1: Datele din frontend nu sunt sincronizate cu backend

**Descriere:** Dacă se adaugă o regulă nouă în backend, constantele din frontend rămân vechi.

**Mitigare:**
- Regulile sunt parte din STANDARD (MED-THERM-2026), nu se schimbă des
- Adăugăm un comentariu în cod: `// Sync with backend/app/regulatory/rules/*.py`
- Viitor: Eventual endpoint `/api/rules` pentru sincronizare automată

### Riscul 2: Istoricul analizelor vechi are ID-uri greșite

**Descriere:** Analizele făcute cu `REG-TEMP-5`, `REG-OPS-3`, `REG-IMAGES-001` există deja în DB.

**Evaluare:**
- Acestea sunt în coloana `config` ca JSON (nu sunt FK-uri)
- Nu este nevoie de migrare - sunt doar date istorice
- Viitoare analize vor folosi ID-urile corecte

**Mitigare:**
- Fără acțiune necesară. Este un bug care se "self-heals" pe viitoare analize.

### Trade-off: Tab nou în Dashboard vs pagină separată

**Tab nou:**
- ✅ Integrat în contextul existent
- ✅ Ușor de găsit
- ⚠️ Adaugă încă un element în bara de taburi (deja 4 elemente → 5)

**Pagină separată:**
- ✅ Mai mult spațiu pentru UI complex
- ⚠️ Mai greu de găsit
- ⚠️ Trebuie navigare din Dashboard

**Decizie:** Tab nou în Dashboard
- Utilizatorii sunt deja în Dashboard când se gândesc la reguli
- 5 taburi sunt acceptabile (pe mobil se afișează în grid)

---

## Migration Plan

### Pas 1: Frontend - Ștergere buton
1. Identifică butonul în `Dashboard.tsx` (liniile 315-325)
2. Șterge secțiunea `{hasData && analysisHistory.length > 1 && (...)}`
3. Nu este nevoie de altă schimbare - tab-ul există deja

### Pas 2: Frontend - Reguli
1. Creează fișierul `frontend/src/lib/constants/regulatoryRules.ts`
2. Populează cu toate cele 21 de reguli din document
3. Creează componenta `RulesReference.tsx` cu filtre
4. Adaugă tab-ul nou în `Dashboard.tsx`

### Pas 3: Backend - Bug fix
1. Actualizează `CHART_VIOLATION_MAPPINGS` din `converters.py`
2. Verifică că:
   - `slow_recovery` → `REG-TEMP-3`
   - `frequent_access` → `REG-OPS-2`
   - fallback → `REG-TEMP-1` (sau elimină)

### Pas 4: Testare
1. Verifică că butonul a dispărut, tab-ul History funcționează
2. Verifică că noul tab Rules afișează toate regulile
3. Încarcă un grafic (.png) și verifică că violările au ID-uri corecte

### Rollback
- Orice schimbare poate fi inversată individual
- Pentru UI: readaugă butonul / șterge tab-ul
- Pentru backend: restaurează dicționarul

---

## Open Questions

1. **Ar trebui să adăugăm și un endpoint `/api/rules`?**
   - Pentru moment: Nu, constantele în frontend sunt suficiente
   - Viitor: Dacă regulile devin dinamice, reconsiderăm

2. **Ce facem cu analizele istorice care au ID-uri greșite?**
   - Decizie: Niciodată acțiune. Sunt date istorice, nu afectează funcționalitatea.
   - Dacă apar în UI, se vor afișa ca "Unknown Rule" sau similar.

3. **Ar trebui ca regulile să includă și exemple?**
   - Poate într-o versiune viitoare
   - Pentru această schimb: Focus pe informațiile de bază (ID, prag, descriere)
