## Context

**Situația actuală:**

```
Frontendul are un flux COMPLEX pentru istoric:

1. La pornire:
   - Citește din localStorage
   - Fetch din DB (GET /api/analysis)
   - Face merge între cele două
   - Face deduplicare pe baza de timestamp + deviceId + failed_count
   - Salvează înapoi în localStorage

2. După fiecare upload:
   - `addAnalysis()` adaugă direct în context
   - Contextul are un `useEffect` care salvează automat în localStorage
   - După aceea, la următorul refresh, se întâmplă tot fluxul de mai sus

3. Probleme:
   - Timestamp-urile pot fi ușor diferite
   - Dubluri în istoric
   - Complexitate inutilă
   - Două surse de adevăr = sincronizare = bug-uri
```

**Arhitectura dorită:**

```
SURSĂ UNICĂ DE ADEVĂR = DOAR BAZA DE DATE

1. La pornire:
   - DOAR: GET /api/analysis
   - Afișează ce vine din DB

2. După fiecare upload:
   - DOAR: refreshHistory() → GET /api/analysis
   - Afișează ce vine din DB

3. localStorage (opțional):
   - DOAR ca fallback offline
   - Dacă DB nu răspunde, afișează ce este în cache
   - Dar NU face merge, NU face sincronizare
```

---

## Goals / Non-Goals

**Goals:**
1. **Elimina sincronizarea** între localStorage și DB
2. **Elimina deduplicarea** - nu va mai fi nevoie
3. **Simplifica fluxul** - DOAR DB = sursă unică
4. **Menține interfața** `useAnalysis()` - componente nu trebuie modificate
5. **Adăugă fallback offline** (opțional, dar recomandat)

**Non-Goals:**
1. **Nu modificăm backendul** - toate endpoint-urile există deja
2. **Nu schimbăm schema bazei de date** - nimic de modificat în PostgreSQL
3. **Nu refacem logica de validare/agregare** - doar fluxul de date în frontend
4. **Nu afectăm utilizatorii existenți** (decât în sens pozitiv: fără dubluri)

---

## Decisions

### Decizia 1: Ce facem cu localStorage?

**Opțiuni:**

**Opțiunea A: localStorage ca FALLBACK OFFLINE (Recomandată)**

```
Flux:
1. La pornire:
   - Încearcă GET /api/analysis
   - Dacă SUCCES:
     → Folosește DOAR datele din DB
     → (Opțional) Actualizează și localStorage ca cache
   - Dacă EȘEC:
     → Citește din localStorage (dacă există)
     → Afișează un mesaj: "Mod offline. Datele din cache."

2. După upload:
   - DOAR: refreshHistory() (încearcă din DB)
   - Dacă DB răspunde: folosește-le
   - Dacă NU: rămâi cu ce ai (sau afișează eroare)
```

**Avantaje:**
- Sigur pentru utilizatori
- Funcționează și fără conexiune
- Tranziție lină

**Dezavantaje:**
- Puțin mai mult cod decât Opțiunea B
- Rămâne puțină complexitate

---

**Opțiunea B: FĂRĂ localStorage (Maxim Simplu)**

```
Flux:
1. La pornire:
   - DOAR: GET /api/analysis
   - Dacă EȘEC:
     → Afișează "Nu se poate conecta la server."
     → (Opțional) Buton "Reîncearcă"

2. După upload:
   - DOAR: refreshHistory()
   - Dacă DB nu răspunde: eroare
```

**Avantaje:**
- Maxim de simplu
- Niciun fel de sincronizare
- Niciun fel de conflicte

**Dezavantaje:**
- Aplicația devine dependentă de backend
- Nu funcționează offline

---

**Decizie FINALĂ: Opțiunea A (localStorage ca FALLBACK)**

**Rationale:**
1. Pentru un sistem medical/regulatoriu, vrem robustețe
2. Vrem să funcționeze și în cazuri de conectivitate slabă
3. Dar NU mai facem merge sau sincronizare
4. localStorage devine DOAR un cache "read-only" pentru offline
5. Când conexiunea revine, se încarcă din DB

---

### Decizia 2: Ce păstrăm și ce eliminăm din `AnalysisContext.tsx`?

**Ce rămâne:**
```typescript
// Stări:
- analysisHistory
- activeAnalysisIndex
- isAnalyzing
- isLoadingHistory
- error, setError, etc.

// Funcții care rămân neschimbate:
- setLatestAnalysis (înlocuiește o analiză)
- clearAnalysis
- switchAnalysis
- removeAnalysis
- clearHistory (în DB, dar API-ul trebuie să existe?)
- refreshHistory (DOAR fetch din DB)
```

**Ce eliminăm/simplificăm:**
```typescript
// Se elimină:
- useEffect care salvează automat în localStorage după fiecare modificare
- Logica de merge între DB și localStorage
- Logica de deduplicare

// Se simplifică:
- loadHistoryFromStorage() → devine doar pentru fallback
- saveHistoryToStorage() → poate fi eliminat sau doar pentru cache
```

---

### Decizia 3: Ce modificăm în `FileUploadZone.tsx`?

**Înainte:**
```typescript
// După upload cu succes:
addAnalysis({
  validationResult: analysisData.validationResult,
  rawLogs: analysisData.rawLogs,
  ...
})
// Contextul salvează automat în localStorage
```

**Acum:**
```typescript
// După upload cu succes:
// NU mai apelăm addAnalysis()

// DOAR:
refreshHistory()  // ← Fetch din baza de date

// Contextul va afișa DOAR ce vine din baza de date
```

**De ce:**
- Backendul SALVEAZĂ deja analiza în DB în timpul upload-ului
- Nu este nevoie să adăugăm și în context/localStorage
- DOAR un refresh este suficient

---

## Risks / Trade-offs

| Risk | Mitigare |
|------|----------|
| Ce se întâmplă dacă utilizatorul are analize vechi în localStorage? | Opțiunea A include un fallback. Pentru viitor, putem adăuga un buton "Migrează în DB". Dar pentru început, simplu: când DB răspunde, folosește-le pe alea. |
| Ce se întâmplă dacă un upload are succes în DB, dar conexiunea cade înainte de refresh? | Rară, dar posibil. Următorul refresh va încărca din DB. Sau putem apela refreshHistory() de 2 ori cu retry. |
| Performanță: la pornire, mereu un request | Request-ul `GET /api/analysis` este ușor (doar listare). Dacă dorim, putem adăuga un cache cu TTL, dar nu pentru început. |
| Utilizatorii existenți vor avea istoric gol? | Nu! Pentru că: 1) Opțiunea A are fallback, 2) Dacă au date în DB, acelea vor fi afișate, 3) Dacă aveau doar în localStorage, vor fi afișate ca fallback. |

---

## Migration Plan

**Etapa 1: Simplifică `AnalysisContext.tsx`**
1. Modifică `refreshHistory()`: DOAR fetch din DB
2. Elimină logica de merge/deduplicare
3. Elimină `useEffect` care salvează automat în localStorage
4. Adaugă logica de fallback: dacă DB nu răspunde, folosește localStorage (doar pentru citire)

**Etapa 2: Modifică `FileUploadZone.tsx`**
1. După upload cu succes: elimină apelul la `addAnalysis()`
2. În schimb, DOAR apelează `refreshHistory()`

**Etapa 3: Testare**
1. Test cu upload nou → apare o dată
2. Test cu refresh → același rezultat
3. Test cu oprirea backendului → afișează fallback (dacă există localStorage)
4. Test cu repornirea backendului → refresh încarcă din DB

---

## Open Questions

1. **Vrem să adăugăm un buton de "Migrează în DB"?**
   - Pentru utilizatorii care au analize vechi doar în localStorage
   - Pentru început: NU. Lăsăm ca fallback offline. Pentru viitor, poate.

2. **Vrem să păstrăm `saveHistoryToStorage()` ca cache?**
   - Când DB răspunde, putem salva și în localStorage
   - Pentru a avea un cache recent pentru cazurile offline
   - Decizie: DA, dar DOAR ca cache, NU ca sursă de adevăr

3. **Ce facem cu `removeAnalysis()` și `clearHistory()`?**
   - Acestea operează pe state-ul din context
   - Ar trebui să cheme API-uri de DELETE în backend?
   - Sau rămân doar pe durata sesiunii?
   - **Decizie:** Acum, ele rămân doar pe state (ca până acum). Pentru viitor, putem adăuga endpoint-uri de DELETE, dar NU este în scope-ul acestui change.
