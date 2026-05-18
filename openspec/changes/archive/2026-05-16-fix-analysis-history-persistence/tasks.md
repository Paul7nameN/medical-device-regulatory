## 0. Investigare (Înțelege exact cauza)

- [ ] 0.1 Rulează query SQL în PostgreSQL pentru a verifica conținutul `config`:
  ```sql
  SELECT 
    id, 
    config IS NOT NULL AS has_config,
    config ? '_latest_analysis_data' AS has_latest_data,
    left(config::text, 500) AS config_preview
  FROM analysis_sessions 
  ORDER BY created_at DESC 
  LIMIT 3;
  ```
  Scop: Verificăm dacă `_latest_analysis_data` există în baza de date.

- [ ] 0.2 Adaugă logging temporar în `backend/app/api/validate.py`:
  - Editează funcția `_orm_session_to_list_item`
  - Printează `type(session.config)` și `session.config`
  - Repornește backendul
  - Accesează `/api/analysis`
  - Verifică logurile

- [x] 0.3 Verifică modelul `AnalysisSession` în `backend/app/models/orm.py`:
   - Câmpul `config` este **JSONB** (linie 63)
   - **NU** are niciun marcaj `deferred`
   - Ar trebui să fie încărcat automat în SELECT

---

## 1. Frontend: sessionStorage → localStorage (IMPLEMENTARE IMEDIATĂ)

Acest lucru poate fi făcut fără a aștepta rezultatele investigației.

- [ ] 1.1 Deschide `frontend/src/lib/context/AnalysisContext.tsx`
- [x] 1.2 Înlocuiește TOATE aparițiile `sessionStorage` cu `localStorage`:
  - Line 71: `sessionStorage.getItem(...)` → `localStorage.getItem(...)`
  - Line 106: `sessionStorage.setItem(...)` → `localStorage.setItem(...)`
  - Line 77, 81: `sessionStorage.removeItem(...)` → `localStorage.removeItem(...)`
  - Line 91: `sessionStorage.getItem(...)` → `localStorage.getItem(...)`
  - Line 114: `sessionStorage.setItem(...)` → `localStorage.setItem(...)`
- [ ] 1.3 Testează:
  - Upload un fișier
  - Închide tab-ul
  - Redeschide tab-ul
  - Verifică dacă istoricul există

---

## 2. (DUPĂ INVESTIGAȚIE) Backend: Repară lipsa `latest_analysis_data`

Aceste task-uri depind de ce descoperim în etapa 0.

### Opțiunea A: Dacă `config` este deferred (nu se încarcă)

- [x] 2.A.1 Modifică `backend/app/services/persistence.py` → `get_analysis_sessions`:
  - Adaugă `undefer(AnalysisSession.config)` în `options()`
  - **PLUS:** Am identificat și reparat o problemă și MAI IMPORTANTĂ:
    - `AnalysisSessionListItem` (modelul Pydantic) NU includea `latest_analysis_data`
    - Prin urmare, chiar dacă `_orm_session_to_list_item` adăuga câmpul, **Pydantic îl ștergea** din răspuns!
  - Fix: Am adăugat `latest_analysis_data: Optional[Dict[str, Any]] = None` în `AnalysisSessionListItem`

### Opțiunea B: Dacă `config` există dar `_latest_analysis_data` are alt nume

- [ ] 2.B.1 Verifică în toate locurile unde se salvează:
  - `persistence.py` (salvează corect)
  - Orice altă cale?

### Opțiunea C: Dacă este problemă de conversie JSON

- [ ] 2.C.1 Investighează mai mult...

---

## 3. Frontend: Logică de Deduplicare Robustă (Implementată)

Aceasta rezolvă problema duplicatelor care apar din cauza:
- Timestamp-uri ușor diferite între `base_report` (salvat în BD) și `aggregated` (returnează la frontend)
- Obiecte parțiale din BD care nu au toate datele

- [x] 3.1 Adăugate funcții helper pentru deduplicare (în afara componentei):
  - `createDeduplicationKey(a)` → creează cheie unică: `deviceId|timestamp_rotunjit|failed_count`
  - `preferBetterItem(a, b)` → alege item-ul "mai bun":
    - Preferă cel NON-parțial în locul celui parțial
    - Preferă cel cu mai multe findings

- [x] 3.2 Modificată logica din `refreshHistory()`:
  - Înainte: `Set(analyzedAt)` + filtrare binară
  - Acum: `Map<dedupeKey, item>` cu rezolvare de conflicte
  - Când doi itemi au aceeași cheie, se păstrează cel "mai bun"
  - Se evită astfel duplicatele cauzate de mici diferențe de timestamp

- [ ] 3.3 (Opțional pentru viitor) Adaugă urmărire pe `analysis_session_id`:
  - Acest lucru ar face deduplicarea perfectă (ID unic bazat pe ID-ul din BD)
  - Necesită modificări în mai multe locuri: API response, context, etc.

---

## 4. Testare Finală

- [ ] 4.1 Test cu .txt:
  - Upload fișier .txt
  - Verifică că apare în istoric
  - Închide browserul COMPLET
  - Redeschide
  - Verifică că analiza ESTE acolo

- [ ] 4.2 Test cu .png/.jpg:
  - Upload imagine
  - Aceleași pași
  - Notă: Acestea poate nu sunt salvate în BD (știu asta), dar cel puțin ar trebui să fie în localStorage

- [ ] 4.3 Verifică API-ul:
  - Mergi pe `/api/analysis`
  - Verifică că `latest_analysis_data` există acum în răspuns

---

## Rezumat Raport de Investigare (Ce am găsit azi)

Înainte de a implementa, ar trebui să scriem aici ce am găsit în etapa 0.

**Observații inițiale:**
1. Datele EXISTĂ în PostgreSQL (ai verificat cu `/api/analysis` și ai văzut 3 items)
2. Dar răspunsul NU include `latest_analysis_data`
3. Proba: Frontendul are `console.log('⚠️ backendItemToLatestAnalysis: missing latest_analysis_data')`
4. Consecință: Funcția returnează `null`

**Cea mai probabilă cauză:**
- `session.config` este `None` sau `{}` când `_orm_session_to_list_item` este apelată
- De ce? Poate este lazy loaded / deferred
- Sau poate există o problemă la citire din ORM

---

## Notă Rapidă: localStorage vs sessionStorage

```
Spațiul înainte (cu sessionStorage):
┌─────────────────────────────────────────────────────────────┐
│  Userul încarcă 10 analize                                   │
│  sessionStorage are toate cele 10                            │
│  Userul închide tab-ul                                       │
│  sessionStorage este GOL (șters automat)                    │
│  Userul redeschide → "Nicio analiză în istoric"             │
└─────────────────────────────────────────────────────────────┘

Spațiul DUPĂ (cu localStorage):
┌─────────────────────────────────────────────────────────────┐
│  Userul încarcă 10 analize                                   │
│  localStorage are toate cele 10                              │
│  Userul închide tab-ul                                       │
│  localStorage CONSERVĂ toate cele 10                        │
│  Userul redeschide → "10 analize în istoric"                │
│                                                              │
│  ȘI CA BONUS: Dacă backendul merge, se încarcă din backend  │
│  (care este sursa unică de adevăr)                           │
└─────────────────────────────────────────────────────────────┘
```

**Concluzie:** Schimbarea `sessionStorage` → `localStorage` este **100% benefică** și **nu are niciun dezavantaj real** în contextul acestei aplicații.
