## Why

Sistemul MED-THERM Compliance Engine este parțial implementat, dar nu poate fi utilizat în mod util în starea actuală:

1. **Baza de date nu este configurată**:
   - PostgreSQL este specificat în `.env` dar baza de date `med_therm` nu există
   - Migrațiile Alembic există dar nu au fost aplicate
   - Frontendul nu are de unde să citească date reale

2. **Frontendul afișează doar date mock**:
   - `Dashboard.tsx` folosește `sampleViolations`, `sampleCategoryData`, `sampleTemperatureData` hardcodate
   - `Violations.tsx` folosește același array de sample
   - `Temperature.tsx` și `Reports.tsx` la fel
   - React Query este instalat dar nu este utilizat pentru încărcarea datelor reale

3. **AI nu este activat**:
   - `AI_ENABLED=false` în `.env`
   - `MODELARK_API_KEY` este un placeholder
   - Utilizatorul are deja cheia API dar nu a fost configurată

**User Experience Problem:**
- Utilizatorul deschide aplicația și vede "78% compliance", "3 Critical" - dar acestea sunt date fake
- Nu există nicio indicație că acestea sunt demo
- Utilizatorul încarcă fișiere pe pagina Upload, dar rezultatele nu apar pe Dashboard/Violations
- Sistemul pare "funcțional" dar nu produce rezultate reale

## What Changes

### Part 1: Configurare Bază de Date PostgreSQL

| Task | Locație |
|------|---------|
| Creează baza de date `med_therm` | PostgreSQL local (cli: `createdb med_therm`) |
| Rulează migrațiile Alembic | `backend/alembic/` → `alembic upgrade head` |
| Verifică tabelele create | `device`, `analysis_session`, `log_entry`, `detected_violation`, `compliance_report`, `audit_log` |

### Part 2: Configurare AI (ModelArk)

| Task | Locație |
|------|---------|
| Actualizează `MODELARK_API_KEY` | `backend/.env` - înlocuiește placeholder cu cheia reală |
| Setează `AI_ENABLED=true` | `backend/.env` |
| Verifică `/api/ai/models` | Ar trebui să returneze modelele disponibile |

### Part 3: Frontend - React Query Hooks pentru Date Reale

Creează hooks noi care încarcă date din API în loc de date mock:

| Hook | Purpose | Endpoint |
|------|---------|----------|
| `useComplianceSummary` | Scor conformitate, reguli trecut/eșuate | `GET /api/health`, `POST /api/reports/summary` |
| `useViolations` | Listă încălcări din baza de date | (Necesită nou endpoint sau din session) |
| `useTemperatureData` | Date temperatură din loguri | (Din loguri analizate) |
| `useRulesInfo` | Lista tuturor regulilor cu descrieri | `GET /api/health/rules` |

### Part 4: Frontend - Actualizare Păgini

| Pagină | Schimbări |
|--------|-----------|
| **Dashboard.tsx** | Înlocuiește `sampleCategoryData`, `sampleViolations`, `sampleTemperatureData` cu date din React Query hooks |
| **Violations.tsx** | Înlocuiește `sampleViolations` cu hook `useViolations()` |
| **Temperature.tsx** | Înlocuiește datele mock cu `useTemperatureData()` |
| **Reports.tsx** | Conectează la `/api/reports/generate` |
| **Upload.tsx** | După upload reușit, invalidează cache React Query pentru a afișa date noi |

### Part 5: Backend - API Endpoints Lipsă (Dacă este nevoie)

| Endpoint | Purpose | Status |
|----------|---------|--------|
| `GET /api/violations` | Returnează încălcările din DB | De verificat dacă există |
| `GET /api/logs/session/{id}` | Returnează logurile unei sesiuni | De verificat |
| `GET /api/devices` | Listă dispozitive | De verificat |

## Capabilities

### Capabilități Noi

- `postgres-connected`: Backendul se conectează la PostgreSQL funcțional
- `migrations-applied`: Toate tabelele sunt create corect
- `ai-enabled`: Analiza imaginilor (chart-uri) prin VLLM este activă
- `react-query-live`: Frontendul încarcă date reale din API, nu mock

### Capabilități Modificate

- `dashboard-data`: Datele afișate pe vină din analize reale, nu sunt hardcodate
- `violations-display`: Încălcările sunt din baza de date, nu sample
- `upload-flow`: După upload, rezultatele apar automat pe celelalte pagini

## Impact

**Bază de date:**
- Se creează tabelele: `device`, `analysis_session`, `log_entry`, `detected_violation`, `compliance_report`, `audit_log`
- Row Level Security este activat pe `audit_log` pentru REG-DATA-1 (immutable logs)

**Backend:**
- `backend/.env` - se actualizează cheia API și `AI_ENABLED=true`
- `backend/app/api/` - posibile adăugări de endpoints dacă lipsesc

**Frontend:**
- `frontend/src/lib/api/client.ts` - extindere cu hooks React Query noi
- `frontend/src/pages/Dashboard.tsx` - eliminare date mock, utilizare hooks
- `frontend/src/pages/Violations.tsx` - eliminare date mock
- `frontend/src/pages/Temperature.tsx` - conectare la date reale
- `frontend/src/pages/Reports.tsx` - conectare la API reports

**Fără Breaking Changes:**
- Frontendul va avea loading states (skeletons) în timp ce datele se încarcă
- Dacă API-ul nu răspunde, se poate afișa un mesaj de eroare prietenos
- Upload endpoint rămâne același
