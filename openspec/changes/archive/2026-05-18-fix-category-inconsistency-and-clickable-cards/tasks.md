# Tasks: Fix Category Inconsistency + Clickable Cards

## Ordine de executie

**Recomandare:** Progreseaza pe rand. Testeaza dupa fiecare task.

---

## PHAZA 1: MODIFICARI IN BACKEND (Unificarea categoriilor)

### Task 1: Modifica engine.py - RULE_ORDER

- [ ] 1.1 Deschide: `backend/app/regulatory/engine.py`

- [ ] 1.2 Gasesceste RULE_ORDER ~linia 12:
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

- [ ] 1.3 **INLOCUIESTE-Le** cu:
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

---

### Task 2: Modifica toate fisierele din rules/

Pentru fiecare fisier, modifica `category`:

#### temp.py
- [ ] 2.1 Deschide: `backend/app/regulatory/rules/temp.py`
- [ ] 2.2 Linia ~13: `category = "thermal"` → `category = "TEMP"`

#### sens.py
- [ ] 2.3 Deschide: `backend/app/regulatory/rules/sens.py`
- [ ] 2.4 Linia ~13: `category = "sensor"` → `category = "SENS"`

#### cool.py
- [ ] 2.5 Deschide: `backend/app/regulatory/rules/cool.py`
- [ ] 2.6 Linia ~14: `category = "cooling"` → `category = "COOL"`

#### ins.py
- [ ] 2.7 Deschide: `backend/app/regulatory/rules/ins.py`
- [ ] 2.8 Linia ~13: `category = "insulation"` → `category = "INS"`

#### ops.py
- [ ] 2.9 Deschide: `backend/app/regulatory/rules/ops.py`
- [ ] 2.10 Linia ~15: `category = "operational"` → `category = "OPS"`

#### Verifica si celelalte (deja ar trebui sa fie ok):
- [ ] 2.11 Verifica `alarm.py`: `category` ar trebui sa fie `"alarm"` → `"ALARM"`
- [ ] 2.12 Verifica `data.py`: `category` ar trebui sa fie `"data"` → `"DATA"`
- [ ] 2.13 Verifica `power.py`: `category` ar trebui sa fie `"power"` → `"POWER"`

---

### TESTARE RAPIDA dupa Phaza 1

- [ ] Porneste backend (`python -m uvicorn app.main:app --reload`)
- [ ] Porneste frontend (`npm run dev`)
- [ ] Incarca un fisier .txt NOU (sau cel cu 1000 logs)
- [ ] Verifica daca **Compliance by Category** acum afiseaza numarul corect de issues
- [ ] Daca DA, mergi mai departe. Daca NU, verifica din nou.

---

## PHAZA 2: COMPATIBILITATE CU VECHILE DATE (Frontend)

Acest task este OPTIONAL daca nu mai ai date vechi in baza de date. Dar daca ai, fa-l.

### Task 3: Adauga layer de conversie categorii

- [ ] 3.1 Deschide: `frontend/src/lib/utils/transformers.ts`

- [ ] 3.2 Adauga la inceput (dupa importuri):
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
  // Daca exista in mapare, returneaza noua valoare
  // Altfel, returneaza asa cum este (pentru cand sunt deja in noul format)
  if (OLD_TO_NEW_CATEGORY[category]) {
    return OLD_TO_NEW_CATEGORY[category]
  }
  return category
}
```

- [ ] 3.3 Modifica `groupViolationsByCategory` pentru a folosi conversia:

**Gaseste functia** ~linia 55:
```typescript
for (const finding of findings) {
  if (finding.passed) continue
  const category = finding.category as RegCategory
  // ...
}
```

**INLOCUIESTE cu:**
```typescript
for (const finding of findings) {
  if (finding.passed) continue
  const rawCategory = finding.category
  const category = convertCategory(rawCategory) as RegCategory
  // ... restul ramane la fel
}
```

**sau**, poti modifica si `findingsToDetectedViolations` daca vrei sa fie consistenta peste tot.

**sau** daca vrei un layer mai centralizat, poti face conversia in `AnalysisContext.tsx` cand incarc din baza de date.

---

### TESTARE dupa Phaza 2

- [ ] Daca ai vechi analize in History, incarca-le
- [ ] Verifica daca **Compliance by Category** acum afiseaza numarul corect de issues
- [ ] Daca DA, mergi mai departe.

---

## PHAZA 3: DEZACTIVAREA CLICK-URILOR (Frontend)

### Task 4: Dezactiveaza click pe carduri in Overview

- [ ] 4.1 Deschide: `frontend/src/pages/Dashboard.tsx`

- [ ] 4.2 Gasesceste sectiunea **"Compliance by Category"** ~linia 534

- [ ] 4.3 Gasesceste cardurile care au `onClick`:

Arata cam asa:
```tsx
<div
  key={category}
  onClick={() => handleCategoryClick(category)}
  className="cursor-pointer ..."
  // ...
>
```

- [ ] 4.4 **ELIMINA** sau **DEZACTIVEAZA** `onClick`:

**Optiune A (simpla): Elimina complet `onClick` si `cursor-pointer`**

**sau** daca vrei sa pastrezi functionalitatea doar in Violations:

**Optiune B:**
- Pastreaza `handleCategoryClick`, `selectedCategory`, `filteredViolations`
- Dar in tab-ul "Overview", cardurile NU mai au `onClick`
- Daca vrei in viitor sa adaugi filtrare si in Violations, poti face acolo un UI separat

**Unde sunt aceste lucruri:**

| Element | Unde este |
|---------|-----------|
| `handleCategoryClick` | ~linia 130-132 |
| Textul `(Filtered:` | ~linia 517-523 |
| Stilul de selected | ~linia 542-547 |

- [ ] 4.5 **Elimina textul** `(Filtered: REG-{selectedCategory})` din titlu cand suntem in Overview

**Gaseste:**
```tsx
<h2 className="...">
  Compliance by Category
  {selectedCategory && (
    <span className="...">
      (Filtered: REG-{selectedCategory})
    </span>
  )}
</h2>
```

Daca vrei sa pastrezi functionalitatea doar pentru Violations, poti:
- Fie elimina complet acea sectiune
- Fie o conditionezi doar pe cand esti in tab-ul Violations

- [ ] 4.6 **Elimina stilul** de "selected" (`ring-2 ring-primary`) cand suntem in Overview

**Gaseste:**
```tsx
className={cn(
  "...",
  selectedCategory === category && "ring-2 ring-primary"
)}
```

La fel: fie elimina complet, fie conditioneaza.

---

### TESTARE FINALA dupa Phaza 3

- [ ] Testeaza in tab-ul **"Overview"**:
  - Daca dai click pe un card din "Compliance by Category", **NU** se mai intampla nimic
  - Nu mai apare textul "(Filtered:..."
  - Nu mai apare borderul pe carduri

- [ ] Testeaza in tab-ul **"Violations"** (daca ai pastrat functionalitatea):
  - Daca vrei sa verifici daca `filteredViolations` functioneaza inca, poti sa setezi temporar `selectedCategory` manual in cod pentru a testa

- [ ] Testeaza **LIGHT MODE** - sa te asiguri ca nu ai stricat nimic

- [ ] Testeaza **DARK MODE** - acelasi lucru

---

## REZUMAT

Cand termini toate task-urile:

1. ✅ Noile analize (din logs) vor folosi categoria corecta
2. ✅ Vechile analize (din history) vor fi convertite automat (daca ai facut Task 3)
3. ✅ In tab-ul "Overview", cardurile nu mai sunt clickable
4. ✅ Functionalitatea de filtrare ramane in cod (pentru cand vrei sa o folosesti in Violations)

**Daca vrei in viitor sa adaugi filtrare si in tab-ul Violations:**
- Poti sa muti acelasi UI (cardurile) acolo
- Sau sa adaugi un dropdown
- Sau orice altceva consideri necesar
