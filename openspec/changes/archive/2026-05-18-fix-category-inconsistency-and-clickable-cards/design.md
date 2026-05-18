# Design: Fix Category Inconsistency + Clickable Cards

## 1. Unificarea Categoriilor (Backend)

### Problema
Backend (current)

In `rules/*:

| Fisier | Categorie Veche |
|---------|---------------------|
| `temp.py:13 | `"thermal"` |
| `sens.py:13` | `"sensor"` |
| `alarm.py` | `"alarm"` |
| `cool.py:14` | `"cooling"` |
| `ins.py:13` | `"insulation"` |
| `ops.py:15` | `"operational"` |
| `data.py` | `"data"` |
| `power.py` | `"power"` |

### Solutie

Inlocuim toate cu formatul frontend:

| Categorie Veche | Categorie Noua |
|---------------------|-----------------|
| `"thermal"` | `"TEMP"` |
| `"sensor"` | `"SENS"` |
| `"alarm"` | `"ALARM"` |
| `"cooling"` | `"COOL"` |
| `"insulation"` | `"INS"` |
| `"operational"` | `"OPS"` |
| `"data"` | `"DATA"` (deja acelasi) |
| `"power"` | `"POWER"` (deja acelasi) |

### Fisiere de modificat in Backend

#### 1. `engine.py`: RULE_ORDER

**INAINTE:
```python
RULE_ORDER = [
    "thermal",
    "sensor",
    "alarm",
    "data",
    "power",
    "cooling",
    "insulation",
    "operational"
]
```

**DUPA:
```python
RULE_ORDER = [
    "TEMP",
    "SENS",
    "ALARM",
    "DATA",
    "POWER",
    "COOL",
    "INS",
    "OPS"
]
```

#### 2. Fisiere din `rules/`

Pentru fiecare fisier:

| Fisier | Modificare |
|---------|-------------|
| `temp.py:13 | `category = "thermal"` → `category = "TEMP"` |
| `sens.py:13` | `category = "sensor"` → `category = "SENS"` |
| `alarm.py` | `category = "alarm"` → `category = "ALARM"` (deja acelasi, verifica) |
| `cool.py:14` | `category = "cooling"` → `category = "COOL"` |
| `ins.py:13` | `category = "insulation"` → `category = "INS"` |
| `ops.py:15` | `category = "operational"` → `category = "OPS"` |
| `data.py` | `category = "data"` → `category = "DATA"` (deja acelasi) |
| `power.py` | `category = "power"` → `category = "POWER"` (deja acelasi) |

---

## 2. Compatibilitate cu Vechile Date (Frontend)

### Problema

Daca avem date deja stocate in baza de date cu vechea categorie ("thermal"), acestea nu vor fi afectate.

Cand le incarcam din history:
- `findings` au `category = "thermal"` (veche)
- Frontend cauta `"TEMP"`
- Nu le ignora

### Solutie

Adaugam un **layer de conversie** in `AnalysisContext.tsx` (sau intr-un fisier de transformers).

#### Locul potrivit: In `backendItemToLatestAnalysis()` sau intr-un fisier separat.

Conversia:

```typescript
const OLD_TO_NEW_CATEGORY: Record<string, string> = {
    "thermal": "TEMP",
    "sensor": "SENS",
    "alarm": "ALARM",
    "cooling": "COOL",
    "insulation": "INS",
    "operational": "OPS",
    "data": "DATA",
    "power": "POWER",
}

function convertCategory(category: string): string {
    // Daca este deja in noul format, returneaza asa cum este.
    // Altfel, incearca conversia.
    if (OLD_TO_NEW_CATEGORY[category]) {
        return OLD_TO_NEW_CATEGORY[category];
    }
    return category;
}
```

**Unde aplicam conversia?
1. Cand incarcam din baza de date (history)
2. Cand salvam in localStorage
3. Sau intr-un layer centralizat

**sau** putem face conversia **in `groupViolationsByCategory()` in `transformers.ts`

---

## 3. Dezactivarea Click-urilor (Frontend)

### Problema

In `Dashboard.tsx`:

**Sectiunea "Compliance by Category" din tab-ul "Overview":

**Actualmente:
- Cardurile au `onClick={handleCategoryClick}`
- La click:
  - `selectedCategory` se seteaza
  - Textul devine `(Filtered: REG-{category})`
  - Cardul primeste `ring-2 ring-primary`

**Problema:**
- Efectul (`filteredViolations`) se vede DOAR in tab-ul "Violations"
- In tab-ul "Overview" nimic nu se schimba
- UX prost

### Solutie

**Varianta aleasa: Dezactivam complet click-ul in tab-ul "Overview".

**Ce modificam:

1. **Eliminam `onClick` de pe carduri in sectiunea "Compliance by Category" (Overview)

2. **Eliminam textul `(Filtered: REG-{selectedCategory})` din titlu cand suntem in tab-ul "Overview"

3. **Eliminam stilul de "selected" (`ring-2 ring-primary`) cand suntem in tab-ul "Overview"

4. **Dar pastram toata logica pentru tab-ul "Violations":
   - `selectedCategory` state
   - `filteredViolations`
   - Daca vrem, putem muta UI-ul de filtrare DIRECT in tab-ul "Violations" (optional, intr-un viitor)

### Unde sunt aceste lucruri in `Dashboard.tsx`:

| Element | Linie aproximativa |
|---------|-----------------|
| `handleCategoryClick` | ~130-132 |
| Textul `(Filtered:` | ~517-523 |
| Stilul de selected | ~542-547 |
| `filteredViolations` | ~150-156 |

### Optional: Mutat UI in Violations

Daca vrem sa pastram functionalitatea, putem:

**Optiune:**

In tab-ul "Violations", putem adauga acelasi set de carduri (sau un dropdown) pentru filtrare.

**Sau** putem lasa pur si simplu cum este acum, dar doar dezactivam in Overview.

---

## 4. Harta Modificarilor

### Backend

| Fisier | Actiune |
|---------|---------|
| `app/regulatory/engine.py | RULE_ORDER |
| `app/regulatory/rules/temp.py` | category = "thermal" → "TEMP" |
| `app/regulatory/rules/sens.py` | category = "sensor" → "SENS" |
| `app/regulatory/rules/alarm.py` | category = "alarm" → "ALARM" (daca nu este) |
| `app/regulatory/rules/data.py` | category = "data" → "DATA" (daca nu este) |
| `app/regulatory/rules/power.py` | category = "power" → "POWER" (daca nu este) |
| `app/regulatory/rules/cool.py` | category = "cooling" → "COOL" |
| `app/regulatory/rules/ins.py` | category = "insulation" → "INS" |
| `app/regulatory/rules/ops.py` | category = "operational" → "OPS" |

### Frontend

| Fisier | Actiune |
|---------|---------|
| `src/lib/utils/transformers.ts` | (optional) Adaugam conversie categorii vechi → noi |
| `src/pages/Dashboard.tsx` | Dezactivam click in Overview |

---

## 5. Testare dupa Fix

### Teste de facut:

1. **Test 1: Upload fisier .txt nou
   - Compliance Score: ar trebui sa fie acelasi
   - Compliance by Category: **acum ar trebui sa afiseze numarul corect de issues

2. **Test 2: Chart image
   - Ar trebui sa functioneze la fel ca inainte (deja folosea formatul corect)

3. **Test 3: Vechile analize din History
   - Daca avem date cu vechea categorie, acestea ar trebui sa fie convertite corect
   - Sau daca nu mai avem date vechi, acestea vor ramane "No issues" pana cand le convertim)

4. **Test 4: Light mode inainte/Dark mode
   - Nu ar trebui sa functioneze la fel ca inainte
