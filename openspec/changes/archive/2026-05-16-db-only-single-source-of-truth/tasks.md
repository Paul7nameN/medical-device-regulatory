## 1. Simplificare `AnalysisContext.tsx` (Prioritate înaltă)

- [x] 1.1 Modifică `refreshHistory()`:
  - Elimină logica de comparare cu localStorage
  - Elimină logica de merge
  - Elimină logica de deduplicare
  - DOAR: fetch din DB → actualizează `analysisHistory`
  - (Opțional) Dacă reușește, salvează și în localStorage ca cache

- [x] 1.2 Adaugă logica de FALLBACK offline:
  - Dacă `GET /api/analysis` eșuează:
    - Încearcă `loadHistoryFromStorage()`
    - Dacă există date: afișează-le
    - Afișează un mesaj vizual: "Mod offline. Datele din cache."
  - Dacă nici localStorage nu are date: afișează stare goală

- [x] 1.3 Elimină `useEffect` care salvează automat în localStorage:
  ```typescript
  // Aceasta trebuie eliminată sau modificată:
  useEffect(() => {
    saveHistoryToStorage(analysisHistory)
  }, [analysisHistory])
  ```
  - **NOTĂ:** O varianta este să o păstrăm, dar DOAR ca cache când DB răspunde
  - Sau o eliminăm complet (decizie în timpul implementării)

- [x] 1.4 Verifică și actualizează celelalte funcții:
  - `addAnalysis()` - rămâne pentru compatibilitate, dar nu mai este folosit în upload
  - `removeAnalysis()`, `clearHistory()` - rămân (dar operează doar pe state, nu pe DB)
  - `setLatestAnalysis()` - rămâne

---

## 2. Modificare `FileUploadZone.tsx`

- [x] 2.1 Identifică locul unde se apelează `addAnalysis()`:
  - După upload cu succes, se construiește `analysisData`
  - Apoi se apelează `addAnalysis({ ... })`

- [x] 2.2 Elimină apelul la `addAnalysis()`:
  - NU mai este nevoie, deoarece backendul salvează deja în DB
  - DOAR: apelează `refreshHistory()` după upload

- [x] 2.3 (Opțional) Adaugă un mic delay sau retry:
  - Pentru a fi siguri că DB a salvat înainte de a face refresh
  - Sau folosește `await` pentru operațiile asincrone (folosit: `await refreshHistory()`)

---

## 3. (Opțional) Curățare

- [x] 3.1 Verifică dacă `loadHistoryFromStorage()` și `saveHistoryToStorage()` sunt folosite:
  - Dacă DA: păstrează-le pentru fallback/cache
  - Dacă NU: pot fi eliminate (să lăsam pentru viitor)

- [x] 3.2 Verifică dacă mai sunt alte referințe la localStorage în `AnalysisContext.tsx`:
  - Șterge sau comentează codul nefolosit
  - Eliminat: `mergeValidationResults`, `mergeAnalyses`, `createDeduplicationKey`, `preferBetterItem`

---

## 4. Testare

- [ ] 4.1 Test cu UPLOAD nou:
  - Upload un fișier .txt
  - Verifică că apare DOAR O DATĂ în istoric
  - Verifică că scorul este corect

- [ ] 4.2 Test cu REFRESH:
  - Refresh pagina (F5)
  - Verifică că aceleași date reapar
  - Verifică că NU sunt duble

- [ ] 4.3 Test cu OPRIREA backendului (fallback offline):
  - Oprește backendul (sau doar simulează)
  - Refresh pagina
  - Verifică că apare mesajul "Mod offline"
  - Verifică că datele din localStorage apar (dacă există)

- [ ] 4.4 Test cu REPORNIREA backendului:
  - Repornește backendul
  - Apasă buton de "Reîncearcă" sau refresh
  - Verifică că se încarcă din baza de date
  - Verifică că nu sunt probleme

---

## Ordinea de Implementare (Recomandată)

```
FAZĂ ÎNTÂI:
  → Task 1.1, 1.2: Simplifică refreshHistory() și adaugă fallback
  → Testează: merge refresh cu și fără backend

APOI:
  → Task 2.1, 2.2: Modifică FileUploadZone.tsx (elimină addAnalysis, adaugă refreshHistory)
  → Testează: upload nou → refresh → apare o dată

APOI (OPȚIONAL):
  → Task 1.3, 3.1, 3.2: Curățare cod nefolosit
```

---

## Notă Importanță

**Acest change va SIMPLIFICA semnificativ codul și va ELIMINA problemele cu:**
- ❌ Dubluri în istoric
- ❌ Sincronizarea între localStorage și DB
- ❌ Deduplicarea (nu mai este nevoie)
- ❌ Conflictele între date

**Ce rămâne același:**
- ✅ Interfața `useAnalysis()` rămâne neschimbată
- ✅ Toate componentele care folosesc `useAnalysis()` nu trebuie modificate
- ✅ Backendul rămâne neschimbat
- ✅ `isLoadingHistory`, `error`, etc. rămân același

**Ceea ce se schimbă:**
- 🔄 `refreshHistory()` devine simplu: DOAR fetch din DB
- 🔄 După upload: DOAR refresh, NU mai `addAnalysis()`
- 🔄 localStorage devine DOAR un fallback offline (cache)
