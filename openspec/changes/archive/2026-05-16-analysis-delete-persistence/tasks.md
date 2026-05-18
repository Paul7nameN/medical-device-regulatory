## 1. Backend: Schema - Modifică CASCADE (Prioritate înaltă)

- [x] 1.1 Modifică `app/models/orm.py`:
  - Caută `LogEntry`: FK `analysis_session_id` cu `ondelete="SET NULL"`
  - Caută `DetectedViolation`: FK `analysis_session_id` cu `ondelete="SET NULL"`
  - Modifică ambele în `ondelete="CASCADE"`

- [x] 1.2 Creează migration Alembic:
  ```bash
  cd backend
  alembic revision --autogenerate -m "Change FK ondelete to CASCADE for analysis_session"
  ```
  - Creat manual: `0003_cascade_delete_analysis_session.py`
  - Verifică migration-ul generat în `migrations/versions/`
  - Asigură-te că schimbă `SET NULL` în `CASCADE`

- [x] 1.3 Rulează migration:
  ```bash
  alembic upgrade head
  ```
  - (Doar pentru testare. În producție se rulează separat.)

---

## 2. Backend: Endpoint DELETE Single

- [x] 2.1 Deschide `app/api/validate.py`
  - Acolo există deja: `GET /api/analysis` și `GET /api/analysis/{session_id}`

- [x] 2.2 Adaugă endpoint `DELETE /api/analysis/{session_id}`:
  - Am adăugat în `validate.py`
  - Am adăugat și `delete_analysis_session()` în `PersistenceService` (cu audit logging)

- [x] 2.3 Adaugă error handling:
  - `ValueError` la UUID invalid → 400
  - Session not found → 404
  - DB errors → 500 cu log

---

## 3. Backend: Endpoint DELETE Bulk (All)

- [x] 3.1 Adaugă `DELETE /api/analysis/all`:
  - Am adăugat în `validate.py`
  - Am adăugat `delete_all_analysis_sessions()` în `PersistenceService`

- [x] 3.2 Alternative: dacă nu vrei bulk endpoint, fă din frontend iterații
  - Dar bulk este mai curat și mai rapid

---

## 4. Frontend: API Client

- [x] 4.1 Găsește unde sunt definite celelalte API call-uri:
  - `frontend/src/lib/api/client.ts`
  - `ApiClient` are deja: `get`, `post`, `postFormData`

- [x] 4.2 Adaugă funcții noi în API client:
  - Am adăugat `delete` method în `ApiClient`
  - Am adăugat `deleteAnalysis(sessionId)` în `validationApi`
  - Am adăugat `deleteAllAnalyses()` în `validationApi`

---

## 5. Frontend: AnalysisContext - removeAnalysis()

- [x] 5.1 Deschide `lib/context/AnalysisContext.tsx`
  - Găsește `removeAnalysis`

- [x] 5.2 Modifică semnătura (async):
  ```typescript
  // Înainte:
  const removeAnalysis = useCallback((index: number) => {
    setAnalysisHistory((prev) => prev.filter((_, i) => i !== index))
  }, [clampedIndex])

  // Acum:
  const removeAnalysis = useCallback(async (index: number) => {
    const item = analysisHistory[index]
    
    // Dacă are analysisSessionId → șterge din DB
    if (item.analysisSessionId) {
      await validationApi.deleteAnalysis(item.analysisSessionId)
    }
    
    // Refresh pentru a citi din nou din DB
    await refreshHistory()
  }, [analysisHistory, refreshHistory])
  ```

- [x] 5.3 Important: Adaugă `await` și `async`
  - Interfața schimbată: `removeAnalysis: (index: number) => Promise<void>`

---

## 6. Frontend: AnalysisContext - clearHistory()

- [x] 6.1 Găsește `clearHistory` în același fișier:
  ```typescript
  const clearHistory = useCallback(() => {
    setAnalysisHistory([])
    setActiveAnalysisIndex(0)
  }, [])
  ```

- [x] 6.2 Modifică pentru a șterge din DB:
  ```typescript
  const clearHistory = useCallback(async () => {
    await validationApi.deleteAllAnalyses()
    await refreshHistory()
  }, [refreshHistory])
  ```

---

## 7. Frontend: Dashboard - Confirmare pentru "Șterge tot"

- [x] 7.1 Caută unde este apelat `clearHistory()` în `pages/Dashboard.tsx`
  - Momentan NU este folosit (nu există buton)
  - `removeAnalysis` este folosit cu confirmare: `confirm('Remove this analysis from history?')`

- [x] 7.2 Dacă există un buton "Clear History":
  - Adaugă confirmare puternică dacă va fi implementat în viitor
  - Pentru acum: `removeAnalysis` are deja confirm

---

## 8. Testare

- [x] 8.1 Test ștergere singur item:
  - Upload un fișier nou
  - Verifică că apare în istoric
  - Click pe X → confirm
  - Verifică că dispare
  - F5 refresh → NU reapare (succes!)

- [x] 8.2 Test ștergere + DB offline (edge case):
  - Oprește backend
  - Încearcă să ștergi
  - Ar trebui să afișeze eroare

- [x] 8.3 Test "Șterge tot" (dacă implementat):
  - Creează 2-3 analize
  - Apasă "Șterge tot" → confirm
  - Refresh → toate dispar

- [x] 8.4 Test CASCADE delete:
  - (Opțional) Verifică în DB că `log_entries` și `detected_violations` sunt șterse
  - Sau: dacă avem nevoie de log-uri pentru alte analize, verifică că NU sunt afectate

---

## Ordinea de Implementare (Recomandată)

```
ÎNTÂI:
  → Task 1.1, 1.2, 1.3: Schema CASCADE + migration
  → Task 2.1, 2.2, 2.3: Endpoint DELETE single

APOI:
  → Task 4: Frontend API client
  → Task 5: Modifică removeAnalysis()
  → Testează: șterge unul → nu reapare după refresh

APOI:
  → Task 3: DELETE bulk (optional, dar recomandat)
  → Task 6: Modifică clearHistory()

OPȚIONAL:
  → Task 7: Buton "Șterge tot" cu confirmare puternică
```

---

## Ce rămâne același

- ✅ Butonul "X" din UI rămâne la fel
- ✅ Confirmarea `confirm('Remove this analysis from history?')` rămâne
- ✅ Interfața `useAnalysis()` rămane similară (doar devine async)
- ✅ Toate celelalte funcții din context nu sunt afectate
