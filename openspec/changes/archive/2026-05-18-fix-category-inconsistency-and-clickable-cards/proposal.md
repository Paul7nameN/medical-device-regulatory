# Proposal: Fix Category Inconsistency + Clickable Cards

## Summary

Fixeaza doua probleme descoperite in timpul testarii dark mode:

1. **Bug Major:** Categorii inconsistente intre backend (regulatory engine) si frontend → "Compliance by Category" arata "No issues" chiar daca sunt regula au fost violated.

2. **Bug UX Minor:** Cardurile "Compliance by Category" din tab-ul "Overview" sunt clickable, dar efectul filtrarii se vede DOAR in tab-ul "Violations" → utilizatorul nu intelege ce se intampla.

## The Problems

### Problema 1: Inconsistenta nume categorii

**Context:**

Cand utilizatorul incarca un fisier .txt cu 1000 loguri:
- **Compliance Score:** Arata corect: 52%, 11 passed, 10 failed
- **Compliance by Category:** Toate cardurile afiseaza "No issues"

**De ce se intampla asta?**

Dupa investigatie am descoperit ca:

| Sursa | Nume categorie |
|-------|-----------------|
| **Backend (rules/*.py** | `"thermal"`, `"sensor"`, `"cooling"`, `"insulation"`, `"operational"` |
| **Frontend (types.ts)** | `"TEMP"`, `"SENS"`, `"COOL"`, `"INS"`, `"OPS"` |
| **Chart Images (transformers.ts)** | `"TEMP"`, `"DATA"` |

In `groupViolationsByCategory()`:
```typescript
const result: Record<RegCategory, SeverityCounts> = {
    TEMP: createEmptySeverityCounts(),
    SENS: createEmptySeverityCounts(),
    // ...
}

for (const finding of findings) {
    if (finding.passed) continue
    const category = finding.category as RegCategory  // "thermal" (din backend)
    if (!result[category]) continue  // result["thermal"] = undefined!
    // Toate finding-urile sunt SARITE!
}
```

**Consecinta:** Cand ruleaza regulatory engine pe logs:
- `findings` au category = "thermal"`, `"sensor"`, etc.
- Frontend cauta cheile "TEMP"`, `"SENS"`, etc.
- Toate sunt ignora → toate categoriile raman 0.

**De ce functioneaza cu imagini?**
- Cand ruleaza chart analysis:
```typescript
const CHART_VIOLATION_MAPPINGS: Record<string, ChartViolationMapping> = {
    'excursion': {
        rule_id: 'REG-TEMP-1',
        category: 'TEMP',  // ←─ Acesta este FORMATUL CORECT!
        // ...
    },
    // ...
}
```

### Problema 2: Carduri clickable fara sens

**Context:**

In tab-ul "Overview":
- Utilizatorul da click pe un card "Thermal Safety"
- Se intampla:
  ✅ Textul devine: "Compliance by Category (Filtered: REG-TEMP"
  ✅ Cardul primeste un border: `ring-2 ring-primary`
  ❌ **In acelasi tab, nimic altceva nu se schimba!

**Unde are efect filtrul?
- Doar in tab-ul **"Violations"**
- Acolo exista `ViolationsTable` care foloseste `filteredViolations`

**Problema UX:**
- Utilizatorul da click, vede "Filtered:" ca s-a intamplat ceva, dar nu vede efectul.
- Trebuie sa navigheze MANUAL pe alt tab pentru a vedea rezultatul.

## Goals

1. **Unifica numele categoriilor** intre toate componentele folosesc aceeasi conventie.
2. **Dezactiveaza click** pe cardurile din tab-ul "Overview" (pastrand functionalitatea in "Violations" daca se vrea).

## Non-Goals

- Nu schimbam functionalitatea de filtrare in sine — doar o mutam/Dezactivam unde nu are sens.
- Nu adaugam functionalitati noi — doar fixam bug-uri existente.

## Current Behavior

### Inainte de fix:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Inconsistenta Categorii                      │
├─────────────────────────────────────────────────────────────────┤
│                                                          │
│  BACKEND (rules/*.py)    FRONTEND (types.ts)           │
│  ┌──────────────┐        ┌──────────────────┐            │
│  │ "thermal"  │        │  "TEMP"           │            │
│  │ "sensor"   │        │  "SENS"           │            │
│  │ "cooling"  │        │  "COOL"           │            │
│  │ "insulation"│        │  "INS"            │            │
│  │ "operational"│       │  "OPS"            │            │
│  └──────────────┘        └──────────────────┘            │
│           ↓                        ↓                     │
│           ↓  category="thermal"    ↓  result["TEMP"] = 0    │
│           ↓                        ↓                     │
│  groupViolationsByCategory():                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  if (!result[category]) continue  // SARIT!        │   │
│  │  // result["thermal"] = undefined                │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                          │
│  Rezultat: Toate categoriile = 0 → "No issues"       │
└─────────────────────────────────────────────────────────────────┘
```

## Proposed Solution

### Solutie pentru Problema 1:

**Modificam BACKEND sa foloseasca aceeasi conventie ca frontend.

**Maparea:**

| Vechiul nume (backend) | Noul nume (unificat) |
|---------------------------|-----------------------------|
| `"thermal"` | `"TEMP"` |
| `"sensor"` | `"SENS"` |
| `"alarm"` | `"ALARM"` |
| `"alarm"` | deja acelasi (coincidenta) |
| `"data"` | `"DATA"` |
| `"power"` | `"POWER"` |
| `"cooling"` | `"COOL"` |
| `"insulation"` | `"INS"` |
| `"operational"` | `"OPS"` |

**Fisiere de modificat in backend:**

1. **`engine.py`:**
   - `RULE_ORDER` array

2. **Toate fisierele din `rules/`:**
   - `temp.py` → category = "TEMP"`
   - `sens.py` → category = "SENS"`
   - `alarm.py` → category = "ALARM"`
   - `data.py` → category = "DATA"`
   - `power.py` → category = "POWER"`
   - `cool.py` → category = "COOL"`
   - `ins.py` → category = "INS"`
   - `ops.py` → category = "OPS"`

**De ce backend si nu frontend?**
1. **Sursa unica de adevar ar trebui sa fie in backend.
2. **Chart images** folosesc deja formatul frontend (`"TEMP"`, `"DATA"`).
3. **Evitam orice confuzie** in viitor — toate componentele vor folosi aceeasi conventie.

### Solutie pentru Problema 2:

**Varianta C (aleasa de utilizator):
- **Dezactivam complet click** pe cardurile din tab-ul "Overview".
- **Pastreaza functionalitatea** de filtrare in tab-ul "Violations" (daca se vrea, putem muta UI-ul acolo).

**Ce inseamna asta in practica:

1. **In Dashboard.tsx:**
   - Elimina `onClick={handleCategoryClick}` de pe cardurile din sectiunea "Compliance by Category" (tab-ul "Overview")
   - Elimina textul `(Filtered: REG-{selectedCategory})` din titlu
   - Elimina stilul de "selected" (`ring-2 ring-primary`)

2. **Dar pastram:**
   - `selectedCategory` state
   - `filteredViolations`
   - Toata logica pentru cand sunt in tab-ul "Violations"

**Optional (daca se vrea in viitor:**
- Putem muta UI-ul de filtrare DIRECT in tab-ul "Violations" (de ex. un dropdown sau acelasi set de carduri).

## Impact

### Technical Impact

**Baza de date:
- **Important:** Daca avem date deja stocate in baza de date cu vechea categorie ("thermal"), acestea vor ramane așa.
- **Trebuie sa analizat:** Functionalitatea de "load from history" functioneaza cu vechile date?
  - Daca `findings` sunt stocate in baza de date sub forma de JSON cu vechea categorie ("thermal"), acestea vor fi afectate.
  - Solutie: Adaugam un layer de conversie in frontend care converteste vechea categorie in noua atunci cand incarcam din history.

**sau:**
  - Facem un script de migrare in baza de date.

**Compatibilitate:**
- Dupa fix, orice NOILE analize vor folosi noua categorie ("TEMP").
- Trebuie sa asiguram ca si vechile date raman compatibile.

## Risks

1. **Risc Mare:** Vechile date din baza de date.
   - **Mitigare:** Adaugam un layer de conversie in `AnalysisContext.tsx` care converteste vechea categorie in noua cand incarcam din history.

2. **Risc Mic:** Uneltile testate.
   - **Mitigare:** Testam dupa fix cu:
     - Loguri noi (upload fisier .txt)
     - Vechile analize din history
     - Chart images

## Open Questions

1. **Ce facem cu vechile date din baza de date?
   - Optiune A: Conversie in frontend (la incarcare)
   - Optiune B: Script de migrare in baza de date
   - Optiune C: Le lasam asa (nu functioneaza corect)

2. **Vrem sa pastram functionalitatea de filtrare in tab-ul "Violations"?
   - Da (decizia)
   - Nu (eliminam complet)
   - Sau mutam UI-ul de filtrare DIRECT in tab-ul "Violations"?

## Next Steps

1. Creaza design document cu detaliile tehnice.
2. Creeaza task-uri pentru implementare.
3. Implementam.
