## Context

### Starea actuala

In momentul de fata, sistemul functioneaza cu reguli **100% hardcodate**:

```
FRONTEND                          BACKEND
┌─────────────────────┐         ┌─────────────────────────────┐
│ regulatoryRules.ts  │         │ regulatory/rules/*.py       │
│ (307 linii, doar    │         │ (24 clase Python, fiecare   │
│  pentru afisare)    │         │  cu logica si constante)    │
└─────────────────────┘         └─────────────────────────────┘
```

Flow-ul de upload actual (din `FileUploadZone.tsx`):
- `.txt` → detecteaza automat daca are timestamps → trimite la `/api/reports/generate`
- `.png/.jpg` → trimite la `/api/ai/analyze-chart`
- `.pdf` → trimite la `/api/logs/ingest`

**Problema**: Nicăieri nu există conceptul de "fișier de reguli/constraints".

### Constrangeri
- AI text analysis există deja (`TextAnalyzer`) cu același pattern: `system_prompt` + `user_prompt` → JSON response
- Nu avem nevoie de migratii DB mari - `analysis_session.config` este deja `JSONB`
- Frontendul are deja `RulesList` component - trebuie doar să fie dinamic
- Trebuie sa pastram compatibilitatea cu vechile analize

## Goals / Non-Goals

**Goals:**
1. Userul poate uploada un fisier `.md`/`.txt` de constraints alaturi de logs
2. AI extrage automat regulile structurate din document
3. Validarea ruleaza pe baza regulilor extrase (sau fallback la default)
4. Fiecare analiza salveaza ce reguli au fost folosite (audit trail)
5. Tab-ul "Rules" afiseaza regulile din analiza curenta

**Non-Goals:**
1. ~~Editare manuala de reguli in UI~~ (poate intr-o iteratie viitoare)
2. ~~Reusable rule sets cu nume si salvare separata~~ (prima iteratie: per-analysis embedded)
3. ~~Validare pentru TOATE tipurile de reguli~~ (ne focusam pe cele care functioneaza cu loguri: threshold, duration, frequency)

## Decisions

### 1. Locul clasificarii fisierelor: Frontend

**Problema**: Cum detectam daca un fisier este `LOG_FILE` sau `CONSTRAINTS_DOCUMENT`?

**Variante considerate:**

| Varianta | Avantaje | Dezavantaje |
|----------|----------|-------------|
| **Frontend (Regex)** | Rapid, fara request extra, userul vede imediat clasificarea | Putin mai putin precis |
| **Backend (API separat)** | Mai precis, poate folosi AI | Un request extra, delay |
| **Hibrid** | Frontend detecteaza rapid, Backend valideaza/afineaza | Complexitate mare |

**Decizie**: **Hibrid light**
- Frontend face o clasificare initiala pe baza de pattern-uri:
  - Daca are `REG-` sau cuvinte cheie: `constraints`, `regulatory`, `rules`, `standard` → `CONSTRAINTS`
  - Daca are timestamps `YYYY-MM-DD HH:MM:SS` + log types: `TEMP_READING`, `DOOR_OPEN` → `LOGS`
- Categorizarea este afisata userului cu optiunea de a schimba manual
- La trimitere, trimitem si `file_intent` (user override)

**Rationale**: Cel mai bun echilibru. Pentru 99% din cazuri (inclusiv fisierul din exemple: `Medical Device Regulatory Constraints.md` cu `REG-TEMP-1`, etc), pattern-urile sunt suficiente.

---

### 2. Formatul JSON pentru reguli extrase

**Problema**: Ce structura trebuie sa aiba o regula extrasa pentru a fi:
1. Afisabila in UI
2. Executabila (parcial) in `RegulatoryEngine`
3. Compatibila cu structura actuala

**Decizie**: Structura cu `type` discriminant:

```typescript
interface ExtractedRule {
  id: string                    // Ex: "REG-TEMP-1"
  name: string                  // Ex: "Operating Temperature Range"
  category: string              // Ex: "TEMP", "SENS", etc
  description: string           // Text complet din document
  
  type: 'threshold_range'      // Ce tip de logica
      | 'duration_limit'
      | 'frequency_limit'
      | 'presence_check'
      | 'inspection_only'
  
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  confidence: number            // 0.0 - 1.0 (LLM confidence)
  
  // Campuri specifice pe baza de `type`
  thresholds?: {
    field?: string              // "temperature", "door_events", etc
    min?: number
    max?: number
    unit?: string               // "°C", "seconds", "events_per_hour"
    maxDurationSeconds?: number // pentru duration
    timeWindowSeconds?: number  // pentru frequency
    maxCount?: number           // pentru frequency
  }
  
  data_source: 'logs' | 'inspection' | 'combined'
  inspection_hint?: string      // Daca nu se poate valida din logs
  
  extraction_notes?: string     // Note despre ambiguitati
}
```

---

### 3. Unde stocam regulile

**Problema**: Tabel nou `rule_sets` sau embedded in `analysis_session.config`?

**Variante:**

| Varianta | Avantaje | Dezavantaje |
|----------|----------|-------------|
| **Embedded in config** | Fara migratie, simplu, fiecare analiza self-contained | Nu poti refolosi acelasi set de reguli intre analize |
| **Tabel nou `rule_sets`** | Reutilizabil, poti avea "Standard MED-THERM-2026", "Custom Client X" | Migratie, complexitate, relatii |

**Decizie**: **Embedded in config** pentru prima iteratie.

**Ulei de spate**: Vom salva cu o cheie consistentă:

```python
analysis_session.config = {
    # ... ce era deja
    "_extracted_rules": [...],           # Regulile propriu-zise
    "_ruleset_meta": {
        "source": "default" | "extracted",
        "filename": "Medical Device Regulatory Constraints.md",  # daca extracted
        "extracted_at": "2026-05-19T...",
        "model_used": "GLM-4.7",
        "rule_count": 24
    }
}
```

**Rationale**: Pentru cazul de utilizare descris (userul da upload la un fisier de constraints impreuna cu logs pentru ACEA analiza), embedded este perfect. Daca va iesi la iveala ca userii vor sa defineasca un set de reguli si sa il foloseasca la 10 analize diferite, atunci facem tabelul separat.

---

### 4. Strategia de validare: Regulile extrase in paralel cu cele default?

**Problema**: Cand ambele disponibile:
- Rulez doar custom rules?
- Rulez doar default?
- Rulez ambele si fac merge?

**Decizie**: **Custom rules scot complet default rules**, dar cu optiune de a alege.

In `FileUploadZone`, dupa ce detecteaza ca ambele fisiere:
- Un mic toggle/selector:
  - [x] Foloseste DOAR regulile extrase din constraints
  - [ ] Merge: regulile default + extrase

Default: doar custom rules (daca exista).

**Rationale**: Daca userul a dat upload la un fisier de constraints specific, intentioneaza ca acela sa fie singura sursa de adevar. "Merge" este un edge case.

---

### 5. AI Prompt pentru extragere

**Problema**: Cum structuram promptul?

**Pattern existent in cod**:
- `SYSTEM_PROMPT_*` constante in `prompts.py`
- `USER_PROMPT_TEMPLATE` cu placeholders
- LLM returneaza JSON, parsat cu `parse_json_response`

**Decizie**: Acelasi pattern.

Vom crea noi constante:
- `SYSTEM_PROMPT_RULE_EXTRACTION`: Context despre MED-THERM, structura JSON, etc.
- `USER_PROMPT_RULE_EXTRACTION`: Template cu continutul fisierului

**Exemplu de system prompt pe scurt**:
```
Esti un expert în extractia de reguli din documente de conformitate medicala.

EXTRAGE regulile din documentul urmator ca ARRAY JSON.

Fiecare regula MUST include: id, name, category, description, type, severity, confidence, data_source.

Categorie mapare:
- Daca despre temperaturi → "TEMP"
- Daca despre senzori → "SENS"
- Daca despre alarme → "ALARM"
- ...

Type mapare (cea mai importanta pentru executie):
- "Valoarea trebuie sa fie intre X si Y" → type: "threshold_range"
- "Nu mai mult de X secunde/minute" → type: "duration_limit"
- "Nu mai mult de X evenimente pe perioada" → type: "frequency_limit"
- "Trebuie sa existe Y" → type: "presence_check"
- "Nu se poate verifica din loguri, necesita inspectie" → type: "inspection_only"

Confidence:
- 1.0 = clar, fara ambiguitate
- 0.7-0.9 = ceva ambiguitate, dar rezonabil
- <0.7 = foarte ambigu, noteaza in extraction_notes

RETURNEAZA DOAR JSON VALID, fara markdown fence.
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| **AI hallucina reguli** | `confidence` field, regulile cu <0.7 nu se executa automat, se afiseaza cu "Needs review" |
| **Format JSON gresit** | Foloseste acelasi `parse_json_response` robust ca existent, cu retry daca esueaza |
| **Performance: request AI extra** | Doar cand se detecteaza un constraints document. Upload cu doar logs = ca pana acum, 0 overhead |
| **Compatibilitate cu istoric** | Vechile analize nu au `_extracted_rules` → le tratam ca `source: "default"` cu `ruleset_name: "MED-THERM-2026"` |
| **Reguli care nu se pot executa** | Toate sunt afisate in tab-ul Rules. Cele de tip `inspection_only` si cele cu `confidence < 1.0` nu genereaza findings, doar info |

## Migration Plan

**Fara migratii DB necesare** pentru prima iteratie!
- `analysis_session.config` este deja JSONB
- Doar adaugam noi chei care incep cu `_` (conventie existenta in cod: vezi `_latest_analysis_data`, `_ai_analysis`)

**Dupa implementare, cand rulam o veche analiza:**
```
IF config._extracted_rules EXISTS → foloseste-le
ELSE → fallback la default MED-THERM-2026 + seteaza _ruleset_meta.source = "default"
```

## Open Questions

1. **Vrem un UI de review/editare a regulilor extrase?**
   - Acum: doar afisare cu confidence indicator
   - Optional: userul poate sa editeze manual un camp inainte de rulare?

2. **Executarea regulilor dinamice**
   - Am specificat in specs ca `threshold_range`, `duration_limit`, `frequency_limit` trebuie sa fie executabile
   - Dar: logica actuala este in clase Python. Cum mapam un JSON la executie?
   - **Raspuns provizoriu**: Cream un `DynamicRuleEvaluator` care are "handleri" pe baza de `type`. Nu inlocuim sistemul actual, doar adaugam un layer nou.

3. **Ce facem cu regulile hardcodate pe termen lung?**
   - Acum: raman ca default / fallback
   - Viitor: poate le exportam ca un JSON "MED-THERM-2026.json" si le incarcam dinamic si pe ele → devine un sistem 100% dinamic, fara cod hardcodat

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           NOUL FLOW                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  USER UPLOAD:                                                            │
│  ┌──────────────────┐  ┌──────────────────┐                             │
│  │ constraints.md   │  │ device_logs.txt  │                             │
│  └────────┬─────────┘  └────────┬─────────┘                             │
│           │                     │                                       │
│           └──────────┬──────────┘                                       │
│                      │                                                  │
│                      ▼                                                  │
│           ┌──────────────────────┐                                      │
│           │ FileUploadZone       │                                      │
│           │ (Frontend)           │                                      │
│           │ - Detecteaza tipuri  │                                      │
│           │ - Afiseaza userului │                                      │
│           │ - Optiune:           │                                      │
│           │   Custom sau Merge?  │                                      │
│           └──────────┬───────────┘                                      │
│                      │                                                  │
│                      ▼                                                  │
│           ┌──────────────────────┐                                      │
│           │ POST /api/ai/       │                                      │
│           │   extract-rules     │◄──── NOUL ENDPOINT                  │
│           └──────────┬───────────┘                                      │
│                      │                                                  │
│                      ▼                                                  │
│           ┌──────────────────────┐                                      │
│           │ TextAnalyzer         │                                      │
│           │ cu NOUL prompt       │                                      │
│           │ pentru extragere    │                                      │
│           └──────────┬───────────┘                                      │
│                      │                                                  │
│                      │ ExtractedRule[]                                  │
│                      ▼                                                  │
│           ┌──────────────────────────────────────────────┐              │
│           │ POST /api/reports/generate                   │              │
│           │ CU parametru nou: `rule_set` optional        │              │
│           └──────────────────────┬───────────────────────┘              │
│                                  │                                       │
│                                  ▼                                       │
│           ┌──────────────────────────────────────────────┐              │
│           │ RegulatoryEngine.validate()                   │              │
│           │ - Daca are rule_set → DynamicRuleEvaluator   │              │
│           │ - Altfel → Fallback la regulile hardcodate  │              │
│           └──────────────────────┬───────────────────────┘              │
│                                  │                                       │
│                                  ▼                                       │
│           ┌──────────────────────────────────────────────┐              │
│           │ Salveaza in analysis_session.config:          │              │
│           │   _extracted_rules                            │              │
│           │   _ruleset_meta                               │              │
│           └──────────────────────────────────────────────┘              │
│                                                                          │
│  Frontend cand incarca analiza:                                         │
│  - Daca are _extracted_rules → RulesList le incarca din acestea        │
│  - Altfel → RulesList le incarca din cele hardcodate                   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```
