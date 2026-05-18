## 0. Pre-condiții: Verifică Tooling

- [ ] 0.1 Verifică dacă PostgreSQL este instalat:
  - Rulează în Command Prompt: `psql --version`
  - Sau în PowerShell: `Get-Service -Name "postgresql*"`
  - Dacă nu există: instalează de pe https://www.postgresql.org/download/windows/

- [ ] 0.2 Verifică Python 3.11+:
  - `python --version` (trebuie să fie >= 3.11)

- [ ] 0.3 Verifică Node.js:
  - `node --version`

---

## 1. Configurare PostgreSQL Local

### 1.1 Creează baza de date

- [ ] 1.1.1 Deschide Command Prompt sau pgAdmin
- [ ] 1.1.2 Conectează-te ca postgres: `psql -U postgres`
- [ ] 1.1.3 Creează baza de date: `CREATE DATABASE med_therm;`
- [ ] 1.1.4 Verifică: `\l` ar trebui să afișeze `med_therm`

**Notă:** Dacă ai parolă pentru utilizatorul `postgres`, actualizează și `backend/.env`:
```
DATABASE_URL=postgresql+psycopg2://postgres:PAROLA_TA_AICI@localhost:5432/med_therm
DATABASE_URL_ASYNC=postgresql+asyncpg://postgres:PAROLA_TA_AICI@localhost:5432/med_therm
```

### 1.2 Rulează migrările Alembic

- [ ] 1.2.1 Deschide terminal în `backend/`
- [ ] 1.2.2 Creează virtual environment:
  ```bash
  python -m venv venv
  .\venv\Scripts\activate
  ```
- [ ] 1.2.3 Instalează dependențe:
  ```bash
  pip install -r requirements.txt
  ```
- [ ] 1.2.4 Rulează migrările:
  ```bash
  alembic upgrade head
  ```
- [ ] 1.2.5 Verifică tabelele în psql: `\c med_therm` apoi `\dt`
  - Ar trebui să vezi: `alembic_version`, `analysis_session`, `audit_log`, `compliance_report`, `detected_violation`, `device`, `log_entry`

---

## 2. Configurare AI (ModelArk)

- [ ] 2.1 Deschide `backend/.env`
- [ ] 2.2 Înlocuiește `MODELARK_API_KEY=your-api-key-here` cu cheia ta reală
- [ ] 2.3 Setează `AI_ENABLED=true`
- [ ] 2.4 Salvă fișierul
- [ ] 2.5 (Mai târziu) Testează: după ce rulezi backendul, accesează `http://localhost:8000/api/ai/models`

---

## 3. Testează Backendul

- [ ] 3.1 Rulează backendul:
  ```bash
  cd backend
  .\venv\Scripts\activate
  uvicorn app.main:app --reload --port 8000
  ```
- [ ] 3.2 Deschide în browser: `http://localhost:8000/docs`
- [ ] 3.3 Testează endpoint `GET /api/health`:
  - Ar trebui să afișeze: `status: "healthy"`, `rules_loaded: 21`
- [ ] 3.4 Testează `GET /api/validate/quick-test`:
  - Ar trebui să returneze un raport cu violations din datele sample

---

## 4. Frontend: Data Layer (Context + Hooks)

### 4.1 Creează AnalysisContext

Locație: `frontend/src/lib/context/AnalysisContext.tsx`

- [ ] 4.1.1 Creează folderul `context` dacă nu există
- [ ] 4.1.2 Creează interfața `LatestAnalysis`:
  ```typescript
  import type { ValidationResult } from '@/lib/api';

  export interface TemperaturePoint {
    time: string;
    sensorA: number;
    sensorB?: number;
  }

  export interface LatestAnalysis {
    result: ValidationResult;
    rawLogs: string[];
    temperatureData: TemperaturePoint[];
    analyzedAt: string;
    deviceId: string;
  }
  ```
- [ ] 4.1.3 Creează `AnalysisContextType` cu:
  - `latestAnalysis: LatestAnalysis | null`
  - `setLatestAnalysis: (a: LatestAnalysis) => void`
  - `clearAnalysis: () => void`
  - `isAnalyzing: boolean`
  - `setIsAnalyzing: (v: boolean) => void`
- [ ] 4.1.4 Creează `AnalysisProvider` component care:
  - Stochează state în `useState`
  - (Opțional) Persistă în `sessionStorage` pentru a nu pierde datele la refresh
  - Expune valoarea prin `Context.Provider`
- [ ] 4.1.5 Creează hook-ul `useAnalysis()` custom

### 4.2 Adaugă Provider în aplicație

Locație: `frontend/src/main.tsx`

- [ ] 4.2.1 Importă `AnalysisProvider`
- [ ] 4.2.2 Împachetează `<App />` în `<AnalysisProvider>`
- [ ] 4.2.3 (Dacă există și `QueryClientProvider`) păstrează ordinea: `QueryClientProvider > AnalysisProvider > App`

### 4.3 Creează React Query Custom Hooks

Locație: `frontend/src/lib/api/hooks.ts`

- [ ] 4.3.1 Creează fișierul nou `hooks.ts`
- [ ] 4.3.2 Importă din `@tanstack/react-query`: `useQuery`, `useMutation`, `useQueryClient`
- [ ] 4.3.3 Creează:

  ```typescript
  import { apiClient, reportsApi, validationApi, aiApi, logsApi } from './client';
  import type { ValidationResult } from './types';

  // Hook pentru lista regulilor
  export function useRules() {
    return useQuery({
      queryKey: ['rules'],
      queryFn: () => apiClient.get<{ rules: RuleInfo[] }>('/api/health/rules'),
      staleTime: Infinity, // regulile nu se schimbă
    });
  }

  // Hook pentru health check
  export function useHealth() {
    return useQuery({
      queryKey: ['health'],
      queryFn: () => apiClient.get('/api/health'),
      refetchInterval: 30000, // la fiecare 30s
    });
  }

  // Mutation pentru validare
  export function useValidateLogs() {
    const queryClient = useQueryClient();
    return useMutation({
      mutationFn: (rawLogs: string[]) => 
        validationApi.validate({ raw_logs: rawLogs }),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['latest-analysis'] });
      },
    });
  }

  // Mutation pentru generare raport
  export function useGenerateReport() {
    const queryClient = useQueryClient();
    return useMutation({
      mutationFn: (rawLogs: string[]) => 
        apiClient.post<{ report: ValidationResult; generated_at: string }>(
          '/api/reports/generate',
          { raw_logs: rawLogs }
        ),
    });
  }
  ```

- [ ] 4.3.4 Adaugă și `useAnalyzeChart()` mutation care folosește `aiApi.analyzeChart()`

### 4.4 Actualizează API Client (dacă este nevoie)

Locație: `frontend/src/lib/api/client.ts`

- [ ] 4.4.1 Verifică dacă `reportsApi.generate` trimite datele corect
- [ ] 4.4.2 Dacă este nevoie, adaugă funcții noi:
  - `getHealth()`
  - `getRules()`
  - `generateReportFromLogs(rawLogs: string[])`

---

## 5. Frontend: Adaugă Demo Mode Indicator

### 5.1 Creează componentă `DemoModeBanner`

Locație: `frontend/src/components/DemoModeBanner.tsx`

- [ ] 5.1.1 Creează componentă care verifică `useAnalysis().latestAnalysis`
- [ ] 5.1.2 Dacă `latestAnalysis === null`, afișează un banner galben:
  > "Demo Mode - Datele afișate sunt de probă. Încărcați fișiere pe pagina Upload pentru a analiza date reale."
- [ ] 5.1.3 Bannerul are un link către `/upload`

### 5.2 Adaugă banner în Layout

Locație: `frontend/src/components/Layout.tsx` (sau unde este header-ul)

- [ ] 5.2.1 Importă `DemoModeBanner`
- [ ] 5.2.2 Adaugă-l sub header, deasupra conținutului paginii

---

## 6. Frontend: Integrare Păgini

### 6.1 Pagina Upload

Locație: `frontend/src/pages/Upload.tsx`

- [ ] 6.1.1 Importă `useAnalysis()` și `useGenerateReport()`
- [ ] 6.1.2 Modifică logica din `FileUploadZone`:
  - După ce un fișier `.txt` este uploadat cu succes la `/api/logs/ingest/file`, avem `sample_entries`
  - **De făcut:** Salvăm raw logurile și trimitem și către `/api/reports/generate` pentru validare completă
- [ ] 6.1.3 Când avem rezultatul de la `/api/reports/generate`:
  - Extragem datele temperaturii din `rawLogs`
  - Apelăm `setLatestAnalysis()` cu toate datele
  - Afișează un mesaj: "Analiză completă! Vezi rezultatele pe Dashboard"
- [ ] 6.1.4 (Opțional) Pentru fișiere imagine (`.png`, `.jpg`):
  - Trimite către `/api/ai/analyze-chart`
  - Afișează rezultatul

### 6.2 Pagina Dashboard

Locație: `frontend/src/pages/Dashboard.tsx`

- [ ] 6.2.1 Șterge (sau comentează) variabilele `sampleCategoryData`, `sampleViolations`, `sampleTemperatureData`
- [ ] 6.2.2 Importă `useAnalysis()`
- [ ] 6.2.3 Creează logica de fallback:
  ```typescript
  const { latestAnalysis } = useAnalysis();
  
  // Folosește date reale dacă există, altfel demo
  const categoryData = latestAnalysis 
    ? transformSummaryToCategoryData(latestAnalysis.result.summary)
    : sampleCategoryData;
  
  const violations = latestAnalysis
    ? transformFindingsToViolations(latestAnalysis.result.findings)
    : sampleViolations;
  
  const temperatureData = latestAnalysis
    ? latestAnalysis.temperatureData
    : generateSampleTemperatureData();
  ```
- [ ] 6.2.4 Creează funcția `transformSummaryToCategoryData()`:
  - Transformă `ValidationResult.summary` (care are `by_category`) în formatul așteptat de `SummaryCard`
- [ ] 6.2.5 Creează funcția `transformFindingsToViolations()`:
  - Transformă `Finding[]` în `DetectedViolation[]` conform design.md
- [ ] 6.2.6 Adaugă loading state:
  - Când `isAnalyzing` este true, afișează skeleton-urile (`ComplianceScoreSkeleton`, etc.)

### 6.3 Pagina Violations

Locație: `frontend/src/pages/Violations.tsx`

- [ ] 6.3.1 Șterge variabila `sampleViolations` sau mut-o ca fallback
- [ ] 6.3.2 Importă `useAnalysis()`
- [ ] 6.3.3 Folosește aceeași logică ca la Dashboard:
  ```typescript
  const { latestAnalysis } = useAnalysis();
  const violations = latestAnalysis
    ? transformFindingsToViolations(latestAnalysis.result.findings)
    : sampleViolations; // fallback
  ```
- [ ] 6.3.4 Reutilizează aceeași funcție `transformFindingsToViolations` (să fie într-un fișier separat `utils/transformers.ts`)
- [ ] 6.3.5 Butonul "Refresh" ar trebui să:
  - Re-valideze aceleași loguri (dacă există `latestAnalysis.rawLogs`)
  - Sau afișeze un mesaj: "Încărcați un fișier pentru a analiza"

### 6.4 Pagina Temperature

Locație: `frontend/src/pages/Temperature.tsx`

- [ ] 6.4.1 Importă `useAnalysis()`
- [ ] 6.4.2 Dacă `latestAnalysis?.temperatureData` există, folosește-l
- [ ] 6.4.3 Altfel, folosește `generateSampleTemperatureData()` ca fallback
- [ ] 6.4.4 Butonul "Refresh" are aceeași logică ca la Violations
- [ ] 6.4.5 (Opțional) Dacă avem doar un senzor date, afișează doar Sensor A

### 6.5 Pagina Reports

Locație: `frontend/src/pages/Reports.tsx`

- [ ] 6.5.1 Conectează datele din `latestAnalysis?.result`
- [ ] 6.5.2 Calculează compliance score:
  ```
  score = Math.round((passed_count / total_rules) * 100)
  ```
- [ ] 6.5.3 Butonul "New Report" ar trebui să:
  - Deschidă un modal (sau redirecteze la Upload) pentru a selecta fișiere noi
  - Sau dacă avem deja loguri, le re-validează

---

## 7. (Utilitar) Creează Transformers

Locație: `frontend/src/lib/utils/transformers.ts`

- [ ] 7.1 `transformFindingsToViolations(findings: Finding[]): DetectedViolation[]`
- [ ] 7.2 `transformSummaryToCategoryData(summary: ...): Record<RegCategory, SeverityCounts>`
- [ ] 7.3 `extractTemperatureDataFromRawLogs(rawLogs: string[]): TemperaturePoint[]`
  - Parsează liniile care conțin `TEMP_READING`
  - Extrage valoarea numerică
- [ ] 7.4 `calculateComplianceScore(passed: number, total: number): number`

---

## 8. Testare Finală

### 8.1 Rulează ambele servicii

- [ ] 8.1.1 **Terminal 1 (Backend):**
  ```bash
  cd backend
  .\venv\Scripts\activate
  uvicorn app.main:app --reload --port 8000
  ```

- [ ] 8.1.2 **Terminal 2 (Frontend):**
  ```bash
  cd frontend
  npm run dev
  ```

### 8.2 Testează fluxul complet

- [ ] 8.2.1 Deschide frontendul: `http://localhost:5173`
- [ ] 8.2.2 Verifică că vezi bannerul galben "Demo Mode"
- [ ] 8.2.3 Mergi la pagina **Upload**
- [ ] 8.2.4 Încarcă fișierul: `docs/client/medical_device_logs_1000.txt`
- [ ] 8.2.5 Așteaptă până când apare "Analysis Complete"
- [ ] 8.2.6 Mergi la **Dashboard**:
  - Ar trebui să vezi date REALE din analiza logurilor
  - Bannerul galben ar trebui să dispară (să spună "Live Mode" sau nimic)
- [ ] 8.2.7 Mergi la **Violations**:
  - Ar trebui să vezi încălcările detectate
- [ ] 8.2.8 Mergi la **Temperature**:
  - Ar trebui să vezi graficele temperaturii din logurile încărcate

### 8.3 (Opțional) Testează AI

- [ ] 8.3.1 Mergi la **Upload**
- [ ] 8.3.2 Încarcă: `docs/client/noncompliant_temperature_profile.png`
- [ ] 8.3.3 Verifică dacă AI analizează imaginea și returnează violations
- [ ] 8.3.4 Verifică `/api/ai/models` returnează modelele cu status "available"

---

## Task Summary

**Total Tasks:** ~40 task-uri organizate în 8 secțiuni

**Ordine recomandată de implementare:**
1. [x] Secțiunea 0 - Verificări inițiale
2. [ ] Secțiunea 1 - PostgreSQL + migrări
3. [ ] Secțiunea 2 - Configurare AI
4. [ ] Secțiunea 3 - Testare backend
5. [ ] Secțiunea 4 - Frontend Data Layer (Context + Hooks)
6. [ ] Secțiunea 5 - Demo Mode Banner
7. [ ] Secțiunea 6 - Integrarea tuturor paginilor
8. [ ] Secțiunea 7 - Utilitare/Transformers
9. [ ] Secțiunea 8 - Testare finală

**Fișiere care vor fi modificate:**
- `backend/.env` (doar configurare, nu cod)
- `frontend/src/main.tsx` - adăugare Provider
- `frontend/src/pages/Dashboard.tsx` - date reale în loc de mock
- `frontend/src/pages/Violations.tsx` - date reale în loc de mock
- `frontend/src/pages/Temperature.tsx` - date reale în loc de mock
- `frontend/src/pages/Upload.tsx` - salvare rezultate în Context
- `frontend/src/pages/Reports.tsx` - conectare la date reale

**Fișiere noi care vor fi create:**
- `frontend/src/lib/context/AnalysisContext.tsx`
- `frontend/src/lib/api/hooks.ts`
- `frontend/src/lib/utils/transformers.ts`
- `frontend/src/components/DemoModeBanner.tsx`
