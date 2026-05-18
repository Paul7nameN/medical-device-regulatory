## Why

**Problema actuală:** Butonul de "Șterge" din istoric nu funcționează corect.

```
┌─────────────────────────────────────────────────────────────────────────┐
│         FLUX CU BUG (CURRENT)                                          │
└─────────────────────────────────────────────────────────────────────────┘

  1. Utilizatorul: click pe "X" (Șterge)
                      │
                      ▼
  2. Dashboard.tsx:893 → removeAnalysis(index)
                      │
                      ▼
  3. AnalysisContext.tsx:338:
     ┌──────────────────────────────────────┐
     │ setAnalysisHistory((prev) => {       │
     │   return prev.filter((_, i) => i !== index)
     │ })                                   │
     └──────────────────────────────────────┘
     → DOAR modifică React state!
     → NU șterge din baza de date!
                      │
                      ▼
  4. (Am eliminat și localStorage useEffect!)
     → Nici măcar nu se salvează în localStorage
                      │
                      ▼
  5. Utilizatorul: F5 (refresh pagină)
                      │
                      ▼
  6. refreshHistory() → GET /api/analysis
                      │
                      ▼
  7. ÎNCARCĂ TOATE analizele DIN baza de date
     → Toate reapar în istoric!
     → Utilizatorul: "Am șters deja asta de 3 ori..."
```

**De ce este o problemă:**
1. **Experiență proastă** - utilizatorul crede că a șters, dar nu a șters nimic
2. **Confuzie** - datele reapar fără explicație
3. **Nu există control** - utilizatorul nu poate curăța istoricul
4. **Pentru sisteme medicale** - ar trebui să poți șterge datele dacă este nevoie

---

## What Changes

**Soluția: Ștergere permanentă în baza de date**

```
┌─────────────────────────────────────────────────────────────────────────┐
│         FLUX NOU (CORECTAT)                                             │
└─────────────────────────────────────────────────────────────────────────┘

  1. Utilizatorul: click pe "X" + confirmă
                      │
                      ▼
  2. removeAnalysis(sessionId)
                      │
                      ▼
  3. DELETE /api/analysis/{session_id}  ← NOU!
                      │
                      ▼
  4. Backend: Șterge AnalysisSession din DB
     → CASCADE: LogEntry și DetectedViolation se șterg automat
                      │
                      ▼
  5. refreshHistory() → GET /api/analysis
                      │
                      ▼
  6. Afișează istoricul FĂRĂ item-ul șters
     → Acum este GONE pentru totdeauna
```

---

## Changes Detaliate

### 1. Backend: Schema - CASCADE Delete

**Problema cu schema curentă:**

```python
# orm.py (actual)
class LogEntry(...):
    analysis_session_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("analysis_sessions.id", ondelete="SET NULL")  ← PROBLEMĂ!
    )

class DetectedViolation(...):
    analysis_session_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("analysis_sessions.id", ondelete="SET NULL")  ← PROBLEMĂ!
    )
```

**Ce înseamnă `ondelete="SET NULL"`:**
- Când ștergi un `AnalysisSession`
- `LogEntry.analysis_session_id` devine `NULL`
- `DetectedViolation.analysis_session_id` devine `NULL`
- Dar **înregistrările rămân în DB** = date orfane

**Ce vrem:**

```python
# DORIT
ondelete="CASCADE"

# Când ștergi AnalysisSession:
# → ȘTERGE automat toate LogEntry-urile asociate
# → ȘTERGE automat toate DetectedViolation-urile asociate
```

---

### 2. Backend: Endpoint DELETE

**Endpoint-uri noi:**

| Endpoint | Metodă | Descriere |
|----------|--------|-----------|
| `/api/analysis/{session_id}` | DELETE | Șterge o singură analiză |
| `/api/analysis/all` | DELETE | Șterge TOATE analizele (bulk) |

**Structură răspuns:**
```json
{
  "success": true,
  "deleted": 1,
  "session_id": "uuid-..."
}
```

---

### 3. Frontend: AnalysisContext modificat

**Ce se schimbă în AnalysisContext.tsx:**

| Funcție | Înainte | Acum |
|---------|---------|------|
| `removeAnalysis(index)` | DOAR `.filter(...)` pe state | `DELETE /api/analysis/{id}` + refresh |
| `clearHistory()` | DOAR `setHistory([])` | `DELETE /api/analysis/all` + refresh |

**Important:** Index → Session ID

Înainte: `removeAnalysis(index: number)` 
- Folosea index-ul din array

Acum: `removeAnalysis(sessionId: string)` SAU `removeAnalysis(index: number)` dar extragem `analysisSessionId` din item
- Trebuie ID-ul sesiunii pentru API

---

### 4. Consecințe pozitive

| Avantaj | Descriere |
|---------|-----------|
| **Ștergere permanentă** | Datele nu reapar după refresh |
| **Curățare ușoară** | Buton "Șterge tot" funcționează |
| **Consistență** | Toate operațiunile folosesc DB ca sursă unică |
| **Liniște în DB** | Nu mai avem date orfane cu FK=NULL |

---

## Capabilities

### Modified Capabilities
- `analysis-sessions`: Adăugată operațiunea de DELETE
- `violation-tracking`: CASCADE delete cu AnalysisSession
- `log-storage`: CASCADE delete cu AnalysisSession

---

## Impact

### Frontend
- **`AnalysisContext.tsx`**: 
  - `removeAnalysis()` → va apela API-ul DELETE
  - `clearHistory()` → va apela API-ul DELETE bulk
- **`Dashboard.tsx`**: 
  - Păstrează `confirm()` existent
  - Poate fi nevoie de mică ajustare dacă semnătura funcției se schimbă

### Backend
- **`app/api/validate.py`**:
  - Adaugă `@router.delete("/analysis/{session_id}")`
  - Adaugă `@router.delete("/analysis/all")` (opțional)
- **`app/models/orm.py`**:
  - Modifică `ondelete="SET NULL"` → `ondelete="CASCADE"` pentru `LogEntry` și `DetectedViolation`
- **`migrations/`**:
  - Trebuie migration nouă pentru a schimba FK constraint
  - SAU, dacă baza de date poate fi recreată: simplu

### Database
- **Schema change**: Foreign Key constraint `ON DELETE` behavior change
- **Data loss**: Orice ștergere viitoare va șterge și datele copil
- **Datele existente**: Rămân neschimbate până când se rulează migration

---

## Open Questions

1. **Ce facem cu datele existente care au FK=NULL?**
   - Le ștergem?
   - Le păstrăm?
   - Le asociem cu ceva?
   - *Răspuns: Probabil le ștergem sau ignorăm - sunt orfane oricum*

2. **Avem nevoie de un soft-delete?**
   - Adăugăm un câmp `deleted_at`?
   - Sau hard-delete pur și simplu?
   - *Răspuns: Pentru început, hard-delete este suficient. Pentru sisteme medicale, poate fi nevoie de audit log - dar avem deja `audit_log` table.*

3. **Audit la ștergere?**
   - Înregistrăm în `audit_log` când cineva șterge o analiză?
   - *Răspuns: Ar fi bine, dar poate fi adăugat separat. Nu în scope-ul acestei schimbări.*
