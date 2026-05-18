## Why

**Probleme CRITICE identificate în timpul explorării:**

Există două bug-uri care fac ca istoricul de analize să DISPARĂ după ce închizi și redeschizi aplicația, deși datele sunt în PostgreSQL:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SITUAȚIA ACTUALĂ                                 │
└─────────────────────────────────────────────────────────────────────────┘

  Ceea ce crezi că se întâmplă:          Ceea ce se întâmplă DE ADEVĂRAT:
  ┌─────────────────────────────────┐       ┌─────────────────────────────────┐
  │  Frontend                        │       │  Frontend                        │
  │  • La pornire: fetch din BD     │       │  • La pornire: fetch din BD     │
  │  • Afișează istoricul           │  ❌   │  • Răspunsul BD NU are          │
  │                                 │       │    latest_analysis_data           │
  │                                 │       │  • Frontendul returnează NULL    │
  │                                 │       │  • Apoi se încarcă din           │
  │                                 │       │    sessionStorage care este GOL!  │
  └─────────────────────────────────┘       └─────────────────────────────────┘
                │                                           │
                ▼                                           ▼
  ┌─────────────────────────────────┐       ┌─────────────────────────────────┐
  │  Backend + PostgreSQL           │       │  sessionStorage (Browser)        │
  │  • Datele EXISTĂ (3 analize)   │       │  • Se ȘTERGE când:              │
  │  • Cu _latest_analysis_data     │       │    - închizi tab-ul             │
  │  • Salvate corect în config     │       │    - repornești browserul        │
  │                                 │       │    - cureți cache-ul              │
  └─────────────────────────────────┘       └─────────────────────────────────┘
```

**Detalii tehnice (descoperite în timpul explorării):**

### Problema #1: sessionStorage → localStorage (Frontend)

Locație: `frontend/src/lib/context/AnalysisContext.tsx`

```typescript
// Line 19, 71, 106, 114...
const HISTORY_STORAGE_KEY = 'med-therm-analysis-history'

// Se folosește sessionStorage:
sessionStorage.getItem(HISTORY_STORAGE_KEY)
sessionStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(history))
```

**Problema:** `sessionStorage` este **per tab** și se **șterge automat** când:
- Închizi tab-ul browserului
- Repornești browserul
- Închizi complet browserul

**Ar trebui:** `localStorage` care persistă între sesiuni.

### Problema #2: latest_analysis_data nu ajunge în răspunsul API (Backend)

Acesta este **cel mai grav bug**. Chiar dacă datele sunt în BD, frontendul nu le poate folosi.

**Fluxul:**

```
1. Userul face upload → POST /api/reports/generate
2. Backendul salvează corect AnalysisSession:
   • config = { _latest_analysis_data: { validationResult, rawLogs, ... }, ... }
3. Userul închide app și intră iar
4. Frontendul apelează GET /api/analysis
5. Răspunsul NU include latest_analysis_data!
6. Frontendul (backendItemToLatestAnalysis) returnează NULL
7. Istoricul pare gol
```

**Unde ar putea fi problema:**

Locații suspecte:
- `backend/app/api/validate.py` → `_orm_session_to_list_item()`
- `backend/app/services/persistence.py` → `get_analysis_sessions()`

Codul din `_orm_session_to_list_item`:
```python
def _orm_session_to_list_item(session) -> dict:
    config = session.config or {}                    # ← Problema aici?
    latest_analysis_data = config.get("_latest_analysis_data")
    
    if latest_analysis_data:                         # ← Nu intră aici!
        result["latest_analysis_data"] = latest_analysis_data
```

**Posibile cauze:**
1. `session.config` este `None` atunci când se face SELECT fără a include coloana `config` (deși ar trebui să fie inclusă automat)
2. `_latest_analysis_data` se salvează cu un alt nume în unele endpoint-uri
3. Există o problemă cu conversia JSON între PostgreSQL și Python

### Problema #3: Imaginele (.png, .jpg) NU sunt salvate în BD deloc

Când se încarcă o imagine, se folosește `/api/ai/analyze-chart`:
```typescript
// FileUploadZone.tsx line 145-148
if (isImage) {
  result = await aiApi.analyzeChart(formData)
  // ← Nu se salvează în AnalysisSession!
}
```

Compară cu .txt:
```typescript
// FileUploadZone.tsx line 153-156
} else if (fileItem.name.endsWith('.txt')) {
  result = await reportsApi.generateFromLogs({
    // ← Acesta salvează în AnalysisSession
  })
}
```

---

## What Changes

### 1. Frontend: sessionStorage → localStorage
- Înlocuiește TOATE aparițiile `sessionStorage` cu `localStorage` în `AnalysisContext.tsx`
- Acest lucru va face ca datele locale să persisté între reporniri

### 2. Backend: Investighează și repară lipsa `latest_analysis_data` din răspuns
- Debughează de ce `session.config` nu include `_latest_analysis_data` când se citește din BD
- Posibil:
  - Adaugare logging suplimentar în `_orm_session_to_list_item`
  - Verificare dacă `config` este lazy loaded
  - Verificare dacă valorile sunt salvate corect

### 3. Frontend: Fallback logic robustă
- Dacă `latest_analysis_data` lipsește, dar `session` există, folosește ce informații ai (summary, etc.)
- Nu returna `null` - creează un obiect minim

### 4. Backend: Salvează și analizele din imagini în BD
- Modifică `/api/ai/analyze-chart` să salveze în `AnalysisSession`
- Sau modifică frontendul să folosească același pattern ca pentru .txt

---

## Capabilities

### Modified Capabilities
- `analysis-sessions`: Corectează încărcarea istoricului din BD
- `log-storage`: localStorage persistent (nu sessionStorage)

---

## Impact

- **Frontend:**
  - `frontend/src/lib/context/AnalysisContext.tsx`: Înlocuire sessionStorage → localStorage
  - Poate fi nevoie de ajustări la logica de conversie din format backend

- **Backend:**
  - Investigare în `app/api/validate.py` (funcția `_orm_session_to_list_item`)
  - Investigare în `app/services/persistence.py`
  - Debugging: trebuie să înțelegem de ce `config` nu se încarcă corect

- **Database:**
  - Nicio modificare la schemă
  - Doar investigare a datelor existente
