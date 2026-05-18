## Context

**Arhitectura curentă:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            SITUAȚIA ACTUALĂ                                  │
└─────────────────────────────────────────────────────────────────────────────┘

  FRONTEND                              BACKEND
  ┌──────────────────────┐            ┌──────────────────────────────────┐
  │                      │            │                                  │
  │  AnalysisContext     │            │  Modele ORM (definite, NEFOLOSITE) │
  │  ┌────────────────┐  │            │  • devices                       │
  │  │ sessionStorage │◀─┼────────────┼─• analysis_sessions             │
  │  │ (DOAR AICI!)  │  │   NU SCRIE │  • log_entries                   │
  │  └────────────────┘  │   IN BD!   │  • detected_violations           │
  │                      │            │  • compliance_reports             │
  │  La pornire:         │            │  • audit_log                     │
  │  • NU fetch din BD   │            │                                  │
  │  • doar citește      │            │  Endpoint-uri:                  │
  │    sessionStorage    │            │  • POST /validate → returnează  │
  │                      │            │  • POST /reports/generate → returnează │
  └──────────────────────┘            │  • POST /logs/ingest → returnează │
                                       │  • NICIUN ENDPOINT GET !         │
                                       └──────────────────────────────────┘

  PROBLEMĂ: sessionStorage se ȘTERGE când:
  ✗ Închizi tab-ul browserului
  ✗ Repornești backendul
  ✗ Cureți cache-ul browserului
```

**Ce există deja (NU trebuie reinventat):**
- Toate modelele SQLAlchemy în `backend/app/models/orm.py`
- Toate tabelele create în PostgreSQL (din migrații)
- Database session management în `backend/app/database.py`
- Configurarea conexiunii în `backend/app/config.py`

## Goals / Non-Goals

**Goals:**
1. **Toate datele se salvează automat în PostgreSQL** după fiecare operație
2. **Frontendul încarcă istoricul din backend** la pornire
3. **sessionStorage devine doar cache** (fallback), nu sursă unică
4. **Adaugă endpoint-uri GET** pentru a citi istoricul

**Non-Goals:**
1. **Nu schimbăm logica de validare** - doar adăugăm persistența
2. **Nu schimbăm schema bazei de date** - toate modelele sunt deja bune
3. **Nu adăugăm autentificare/autorizare** - acesta este un change separat
4. **Nu refacem AnalysisContext** - doar îi schimbăm sursa de date

## Decisions

### Decizia 1: Strat de Persistență Unificat

**Opțiuni:**
1. **Adaugă logica direct în fiecare endpoint** - rapid, dar duplicație de cod
2. **Creează un serviciu `PersistenceService`** - centralizat, testabil, reutilizabil

**Decizie:** Serviciu dedicat `app/services/persistence.py`

```
┌────────────────────────────────────────────────────────────────────────┐
│                    PersistenceService (centralizat)                     │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  + save_analysis_session(device_id, config, logs, report)           │
│     → Creează AnalysisSession + LogEntry + DetectedViolation        │
│                                                                        │
│  + save_compliance_report(device_id, aggregated_report)              │
│     → Creează ComplianceReport                                        │
│                                                                        │
│  + get_analysis_sessions(limit, offset) → List[AnalysisSession]      │
│  + get_analysis_session(id) → AnalysisSession complet                │
│  + get_reports(limit, offset) → List[ComplianceReport]               │
│  + get_logs(device_id, start_date, end_date) → List[LogEntry]       │
│                                                                        │
│  + log_audit(action, actor, resource, old_val, new_val)             │
│     → Creează AuditLog (IMUTABIL)                                    │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

**Rationale:**
- Evită duplicarea codului între `/validate`, `/reports`, `/logs/ingest`
- Ușor de testat independent
- Centralizează logica de audit
- Ușor de înlocuit/extins în viitor

### Decizia 2: Fluxul de Date

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            FLUX CORECT (NOU)                                 │
└─────────────────────────────────────────────────────────────────────────────┘

  Utilizator încarcă loguri:

  [Frontend] Upload → POST /api/validate
                          │
                          ▼
  [Backend]  RegulatoryEngine.validate() → returnează ComplianceReport
                          │
                          ▼
  [Backend]  PersistenceService.save_analysis_session()
             ├── Creează/încarcă Device (după device_id)
             ├── Creează AnalysisSession (PENDING → COMPLETED)
             ├── Creează LogEntry pentru fiecare log
             ├── Creează DetectedViolation pentru fiecare finding eșuat
             └── log_audit(action="ANALYSIS_CREATED", ...)
                          │
                          ▼
  [Frontend]  Primește răspunsul + îl salvează în context
              (sessionStorage = cache, nu singura sursă)


  La pornirea Frontendului:

  [Frontend]  La mount-ul AnalysisContext:
              ├── 1. Fetch GET /api/analysis?limit=20
              ├── 2. Fetch GET /api/reports?limit=10
              ├── 3. Merge cu sessionStorage (dacă există)
              └── 4. Afișează utilizatorului
```

### Decizia 3: Strategy de Sincronizare

**Problema:** Ce se întâmplă dacă există date atât în sessionStorage CÂT și în BD?

**Opțiuni:**
1. **BD este sursa unică** - ignoră complet sessionStorage (simplu, dar poate pierde date nesincronizate)
2. **Merge cu prioritate BD** - IA toate din BD, și doar cele din sessionStorage care NU sunt în BD (complex, dar sigur)
3. **Afișează un prompt** - "Ai date nesincronizate. Vrei să le salvezi?" (cel mai sigur pentru utilizator)

**Decizie:** Variantă 2 + 3 (hibrid)

```
La pornire:
1. Fetch GET /api/analysis → toate din BD
2. Citește sessionStorage → date locale
3. Compară:
   - Dacă nu există conflicte → afișează toate (BD + locale neînregistrate)
   - Dacă există conflicte (aceeași analiză dar diferită) →
     → Afișează badge "Ai X analize nesincronizate"
     → Utilizatorul alege: "Salvează-le" sau "Ignoră"
4. sessionStorage devine doar "draft" pentru analizele care nu au fost încă salvate
```

### Decizia 4: Imutabilitatea AuditLog

**Problema:** AuditLog trebuie să fie IMUTABIL (niciodată nu poate fi modificat).

**Soluții:**
1. **La nivel ORM**: Nu definește niciodată `session.add(audit_log)` cu obiect modificat
2. **La nivel BD**: Creează un `RULE` sau `TRIGGER` care blochează UPDATE/DELETE pe `audit_log`
3. **La nivel BD**: `REVOKE UPDATE, DELETE ON audit_log FROM app_user`

**Decizie:** Toate trei, în ordine:

1. **La nivel BD (principal)**: Adaugă migrație care creează o regulă:
```sql
CREATE RULE audit_log_no_delete AS ON DELETE TO audit_log DO INSTEAD NOTHING;
CREATE RULE audit_log_no_update AS ON UPDATE TO audit_log DO INSTEAD NOTHING;
```

2. **La nivel ORM (secundar)**: `AuditLog` nu are câmp `updated_at` și serviciul nu are metodă de update

**Rationale:** Pentru sisteme medicale/regulatorii, garanția imutabilității trebuie să fie la nivelul bazei de date, nu doar al aplicației.

## Risks / Trade-offs

| Risk | Mitigare |
|------|----------|
| Datele din sessionStorage se pierd înainte de sincronizare | La fiecare analiză, salvează IMEDIAT în BD + în sessionStorage (double write). SessionStorage devine doar cache offline. |
| Performanță: încărcarea tuturor analizelor la pornire | Paginare (`limit=20`, `offset=0`) + "Load More" + lazy loading detaliilor fiecărei analize |
| Conflict între datele locale și cele din BD | Strategia hibridă: BD are prioritate, dar datele locale nesincronizate sunt păstrate și afișate cu un indicator vizual |
| Migrarea datelor existente (dacă sunt deja în sessionStorage) | La prima rulare după deploy, oferă utilizatorului opțiunea de a "Salva toate analizele locale în BD" |
| Backup și restaurare | Poate un topic separat, dar din moment ce suntem în PostgreSQL, avem deja PITR, dump-uri automate, etc. |

## Migration Plan

**Etapa 1: Backend - Serviciul de Persistență**
1. Creează `app/services/persistence.py` cu `PersistenceService`
2. Creează metodele `save_analysis_session()`, `get_analysis_sessions()`, `log_audit()`
3. Creează migrație pentru regulile de imutabilitate `audit_log`

**Etapa 2: Backend - Conectează Endpoint-urile**
1. Modifică `/api/validate` → folosește `PersistenceService.save_analysis_session()`
2. Modifică `/api/reports/generate` → salvează raportul
3. Modifică `/api/logs/ingest` → salvează logurile

**Etapa 3: Backend - Endpoint-uri GET**
1. `GET /api/analysis` → listă analize (paginată)
2. `GET /api/analysis/{id}` → detalii complete + findings + logs
3. `GET /api/reports` → listă rapoarte
4. `GET /api/reports/{id}` → raport complet
5. `GET /api/logs` → căutare loguri (device_id, date range)

**Etapa 4: Frontend - Api Client**
1. Adaugă funcții noi în `lib/api/`: `getAnalysisList()`, `getAnalysis()`, `getReports()`
2. Verifică că toate răspunsurile sunt tipizate corect

**Etapa 5: Frontend - AnalysisContext**
1. La `useEffect([])` (mount), fă fetch din backend
2. Actualizează `loadHistoryFromStorage()` să fie doar fallback
3. După fiecare analiză nouă, actualizează și contextul și (în background) asigură-te că e salvată

**Etapa 6: Testare și Migrare Date**
1. Testează că după restart backend, datele reapar în frontend
2. Testează că după închidere tab, datele reapar
3. (Opțional) Feature de "Migrează datele locale în BD" pentru utilizatorii existenți

## Open Questions

1. **Paginare: câte elemente per pagină?**
   - 20 pentru liste, 50 pentru loguri
   - Sau configurabil per request

2. **Avem nevoie de "soft delete"?**
   - Modelele nu au câmp `deleted_at`
   - Pentru sisteme regulatorii, poate ar fi mai bine NU a avea deloc delete
   - Decizie: NU soft delete. Pur și simplu nu există endpoint de DELETE.

3. **Ce facem cu `sessionStorage` pe viitor?**
   - Opțiunea 1: Îl păstrăm ca offline cache
   - Opțiunea 2: Îl eliminăm complet după migrație
   - Decizie: Păstrăm ca cache, dar BD este sursa unică de adevăr

4. **Avem nevoie de versionare?**
   - O analiză poate fi "re-rulată" cu același loguri?
   - Sau fiecare rulare creează o înregistrare nouă?
   - Decizie: Fiecare `POST /validate` creează o înregistrare nouă. Analizele sunt append-only.
