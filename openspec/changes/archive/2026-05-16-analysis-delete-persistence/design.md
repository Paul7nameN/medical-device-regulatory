## Context

**Situația actuală:**

```
Frontend are funcții de ștergere, dar ele sunt "fantomă":

┌─────────────────────────────────────────────────────────────────────────┐
│                           CURRENT STATE                                   │
└─────────────────────────────────────────────────────────────────────────┘

  Frontend                          Backend + DB
     │                                 │
     │  removeAnalysis(index)         │
     │    (doar .filter() pe state)  │
     │                                 │
     │  NICIUN apel către API         │
     │                                 │
     └────────────────────────────────►
           Nu există DELETE endpoint


  DB Schema (actual):
  
  ┌──────────────────┐         ┌──────────────────┐
  │  AnalysisSession │         │    LogEntry      │
  ├──────────────────┤         ├──────────────────┤
  │ id (PK)          │◄────────│ analysis_session │
  │ ...              │  FK     │ _id              │
  └──────────────────┘         │ ondelete=SET NULL│
                               └──────────────────┘
                                       │
                          Când ștergi AnalysisSession:
                          LogEntry rămâne dar cu FK=NULL
                          = date orfane în DB
```

---

## Goals / Non-Goals

**Goals:**
1. **Ștergere permanentă** - când utilizatorul șterge, datele dispar din DB
2. **CASCADE delete** - ștergerea unei analize șterge și logs/violations asociate
3. **Buton "Șterge tot"** - functional, șterge toate din DB
4. **Menține confirmarea** - `confirm()` înainte de ștergere
5. **Nicio modificare UI** - folosim același buton "X", același confirm

**Non-Goals:**
1. **Nu facem soft-delete** - pentru început, hard-delete este OK
2. **Nu modificăm fronted UI-ul** - doar logica din spate
3. **Nu adăugăm audit log** - există deja `audit_log` table, poate fi extins separat
4. **Nu schimbăm structura API-urilor existente** - doar adăugăm endpoint-uri noi

---

## Decisions

### Decizia 1: CASCADE vs SET NULL

**Opțiuni:**

| Opțiune | Ce se întâmplă când ștergi AnalysisSession | Avantaje | Dezavantaje |
|---------|---------------------------------------------|----------|-------------|
| **CASCADE** | Șterge automat LogEntry + DetectedViolation | Curat, fără date orfane | Datele dispar definitiv |
| **SET NULL** (actual) | Rămân dar cu FK=NULL | Păstrează datele | Date orfane, confusionare |
| **RESTRICT** | Nu poți șterge dacă există copii | Sigur | Blochează funcționalitatea |

**Decizie FINALĂ: CASCADE**

**Rationale:**
1. Dacă utilizatorul vrea să șterge o analiză, vrea să o șteargă COMPLET
2. Nu are sens să păstrăm log-uri fără o analiză părinte
3. Curățarea automată = fără menajare manuală
4. Pentru sisteme medicale: dacă ștergi, ștergi tot (sau ai alt mecanism de audit)

---

### Decizia 2: Schema DB - cum schimbăm FK?

Schema actuală are `ondelete="SET NULL"`. Trebuie să schimbăm în `ondelete="CASCADE"`.

**Opțiuni:**

**Opțiunea A: Alembic Migration (Recomandată)**

```bash
# 1. Modifică models/orm.py
# 2. Rulează:
alembic revision --autogenerate -m "Change FK ondelete to CASCADE"
alembic upgrade head
```

**Opțiunea B: Drop + Recreate (doar pentru dev)**

```sql
-- În PostgreSQL:
ALTER TABLE log_entries 
DROP CONSTRAINT IF EXISTS fk_log_entries_analysis_session;

ALTER TABLE log_entries 
ADD CONSTRAINT fk_log_entries_analysis_session 
FOREIGN KEY (analysis_session_id) 
REFERENCES analysis_sessions(id) 
ON DELETE CASCADE;

-- Similar pentru detected_violations
```

**Decizie: Opțiunea A cu Alembic**

Avem deja structura de migrări în `backend/migrations/`.

---

### Decizia 3: Endpoint-uri API

**Ce adăugăm:**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     NOI ENDPOINT-URI                                     │
└─────────────────────────────────────────────────────────────────────────┘

1. DELETE /api/analysis/{session_id}
   ┌──────────────────────────────────────┐
   │ Șterge o singură sesiune de analiză  │
   │                                      │
   │ Request: DELETE /api/analysis/{uuid} │
   │ Response:                             │
   │ {                                     │
   │   "success": true,                    │
   │   "deleted": 1,                       │
   │   "session_id": "uuid..."             │
   │ }                                     │
   └──────────────────────────────────────┘

2. DELETE /api/analysis/all
   ┌──────────────────────────────────────┐
   │ Șterge TOATE sesiunile (bulk)        │
   │                                      │
   │ Request: DELETE /api/analysis/all    │
   │ Response:                             │
   │ {                                     │
   │   "success": true,                    │
   │   "deleted": 42                       │
   │ }                                     │
   └──────────────────────────────────────┘
```

**Unde le adăugăm:**

În `backend/app/api/validate.py` - acolo este deja `GET /api/analysis`.

---

### Decizia 4: Frontend - Semnatura funcțiilor

**Problema:**

Acum `removeAnalysis(index: number)` primește **index**.

Dar pentru API avem nevoie de **session_id** (`analysisSessionId`).

**Opțiuni:**

**Opțiunea A: Schimbă semnătura**
```typescript
// Nou:
removeAnalysis(sessionId: string): Promise<void>

// Și în Dashboard:
const item = analysisHistory[index]
await removeAnalysis(item.analysisSessionId!)
```

**Opțiunea B: Păstrează index, dar extrage ID în interior**
```typescript
// Există dar modificat:
const removeAnalysis = useCallback(async (index: number) => {
  const session = analysisHistory[index]
  if (session.analysisSessionId) {
    await deleteApiCall(session.analysisSessionId)
  }
  // apoi refresh
}, [analysisHistory])
```

**Opțiunea C: Ambele**
- Un `removeAnalysisByIndex(index)` 
- Un `removeAnalysisById(sessionId)`

**Decizie: Opțiunea B (simplu)**

Motiv:
1. Menține compatibilitatea cu codul existent
2. `Dashboard.tsx` nu trebuie modificat (doar confirmarea rămâne)
3. `analysisHistory` are deja `analysisSessionId` pe fiecare item

---

### Decizia 5: Frontend - După ștergere: refresh vs optimist?

**Opțiuni:**

| Opțiune | Cum funcționează | Avantaje | Dezavantaje |
|---------|------------------|----------|-------------|
| **Optimist** | Șterge din state, apoi apelează API | Rapid | Dacă API eșuează, inconsistenta |
| **Refresh după** | Apelează API, apoi `refreshHistory()` | Sigur, consistent | Un pic mai lent |
| **Ambele** | Optimist + refresh | Rapid și sigur | Puțin mai mult cod |

**Decizie: Refresh după (simplu și sigur)**

Flux:
1. Utilizator click pe X → confirm
2. Apel `DELETE /api/analysis/{id}`
3. Așteaptă răspuns
4. Apel `refreshHistory()` → afișează starea actualizată din DB

---

## Risks / Trade-offs

| Risk | Mitigare |
|------|----------|
| Ștergere accidentală | Păstrăm `confirm()` existent. Pentru "Șterge tot", adăugăm un mesaj puternic. |
| Data loss ireversibil | Este dorit. Dacă avem nevoie de soft-delete ulterior, putem adăuga câmp `deleted_at`. |
| Schema change trebuie migration | Avem Alembic configurat. Pentru dev, poate fi `alembic upgrade head`. |
| Frontend trebuie să manece erori API | Adăugăm try/catch și setError() în caz de eșec. |

---

## Implementation Plan

**Etapa 1: Backend - Schema CASCADE**
1. Modifică `app/models/orm.py`: `ondelete="SET NULL"` → `"CASCADE"` pentru LogEntry și DetectedViolation
2. Creează migration Alembic: `alembic revision --autogenerate`
3. Testează migration

**Etapa 2: Backend - Endpoint-uri DELETE**
1. Adaugă `DELETE /api/analysis/{session_id}` în `validate.py`
2. (Opțional) Adaugă `DELETE /api/analysis/all` pentru bulk
3. Adaugă error handling: 404 dacă nu găsește, 500 pentru erori DB

**Etapa 3: Frontend - API client**
1. Adaugă `deleteAnalysis(sessionId)` în fișierul de API
2. Adaugă `deleteAllAnalyses()` dacă facem bulk

**Etapa 4: Frontend - AnalysisContext**
1. Modifică `removeAnalysis(index)`: 
   - Extrage `analysisSessionId` din item
   - Apelează API DELETE
   - Apelează `refreshHistory()`
2. Modifică `clearHistory()`:
   - Apelează DELETE bulk (sau iterează și șterge fiecare)
   - `refreshHistory()`

**Etapa 5: Testare**
1. Test ștergere singur item → dispare după refresh
2. Test ștergere tot → gol
3. Test eșec API → afișează eroare

---

## Open Questions

1. **Avem nevoie de "Șterge tot" ca endpoint separat?**
   - Putem face și din frontend: iterează prin toate și apelează DELETE individual
   - Dar endpoint bulk este mai curat și mai rapid
   - **Decizie: DA, vom adăuga DELETE /api/analysis/all**

2. **Ce facem cu elementele care nu au `analysisSessionId`?**
   - Elementele vechi din localStorage (înainte de DB) nu au ID
   - Pentru acestea: pur și simplu le eliminăm din state (sunt fallback offline)
   - **Decizie: Dacă nu are ID, doar elimină din state; altfel DELETE API**

3. **Confirmare pentru "Șterge tot"?**
   - DA, foarte important
   - Ex: `"Sigur vrei să ștergi TOATE cele {N} analize? Această acțiune este ireversibilă!"`
