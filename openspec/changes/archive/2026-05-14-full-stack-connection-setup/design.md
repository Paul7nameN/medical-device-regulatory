## Context

Sistemul MED-THERM Compliance Engine are următoarea stare actuală:

### Backend API existent:

| Endpoint | Method | Purpose | Salvează în DB? |
|----------|--------|---------|-----------------|
| `/api/health` | GET | Health check + rules count | Nu |
| `/api/health/rules` | GET | Listă toate regulile | Nu |
| `/api/logs/ingest` | POST | Parsează loguri raw | Nu |
| `/api/logs/ingest/file` | POST | Parsează fișier uploadat | Nu |
| `/api/validate` | POST | Validează loguri împotriva regulilor | Nu |
| `/api/reports/summary` | POST | Generează rezumat concis | Nu |
| `/api/reports/generate` | POST | Generează raport complet | Nu |
| `/api/ai/*` | GET/POST | Analiză AI (dacă activat) | Nu |

**Observație importantă:** Toate endpoint-urile sunt "stateless" - procesează datele și le returnează, dar nu le salvează în PostgreSQL. Modelele ORM există (`AnalysisSession`, `LogEntry`, `DetectedViolation`, `ComplianceReport`) dar nu sunt folosite de API.

### Frontend stare actuală:

| Pagină | Sursa datelor |
|--------|---------------|
| Dashboard | `sampleViolations`, `sampleCategoryData`, `sampleTemperatureData` (hardcodate) |
| Violations | `sampleViolations` array (hardcodat) |
| Temperature | `generateSampleTemperatureData()` (hardcodat) |
| Reports | Date mock nefinalizate |
| Upload | Se conectează la API, dar rezultatele nu sunt salvate/sincronizate cu alte pagini |

**React Query** este instalat și configurat (`@tanstack/react-query`), dar nu este utilizat încă.

**Vite Proxy:** Frontendul are configurat proxy în `vite.config.ts`:
```typescript
proxy: {
  "/api": {
    target: "http://localhost:8000",
    changeOrigin: true,
  },
}
```
Aceasta înseamnă că request-urile către `/api/*` din frontend sunt redirecționate automat către backendul pe port 8000.

## Goals / Non-Goals

**Goals:**
1. Face PostgreSQL conectabil și migrațiile aplicate
2. Activează AI cu cheia API a utilizatorului
3. Frontendul afișează date REALE din analize, nu mock
4. Când utilizatorul încarcă un fișier pe pagina Upload, rezultatele apar automat pe Dashboard/Violations
5. Folosește React Query pentru caching și state management

**Non-Goals:**
1. Nu este nevoie de salvarea persistentă în DB pentru prima fază (React Query cache + Context sunt suficiente)
2. Nu schimbăm logica de validare din backend
3. Nu adăugăm reguli noi
4. Nu refacem design-ul UI - doar conectăm sursele de date

## Decisions

### 1. Arhitectură "Analysis Context" + React Query

**Decizie:** Folosim un pattern hibrid:
- `AnalysisContext` (React Context) pentru a stoca ultimul rezultat de validare
- React Query pentru apelurile API și caching
- Când un upload reușește, invalidăm cache-ul React Query și actualizăm Context-ul

**De ce:**
- FastAPI backendul este deja stateless și funcțional
- React Query gestionează loading/error states automat
- Context-ul permite împărtășirea rezultatelor între pagini fără props drilling
- Nu necesită modificări backend în prima fază

**Flux de date:**
```
Upload Page
    ↓
POST /api/logs/ingest/file → parsează
    ↓
POST /api/reports/generate → validează și returnează ValidationResult
    ↓
setLatestAnalysis(result) → AnalysisContext
    ↓
queryClient.invalidateQueries() → React Query reîncarcă
    ↓
Dashboard / Violations / Temperature citesc din Context + Query
```

### 2. Structura AnalysisContext

```typescript
interface LatestAnalysis {
  result: ValidationResult | null;
  rawLogs: string[] | null;
  temperatureData: TemperatureChartData[] | null;
  analyzedAt: Date | null;
  deviceId: string;
}

interface AnalysisContextType {
  latestAnalysis: LatestAnalysis | null;
  setLatestAnalysis: (analysis: LatestAnalysis) => void;
  clearAnalysis: () => void;
  isAnalyzing: boolean;
  setIsAnalyzing: (val: boolean) => void;
}
```

### 3. Custom React Query Hooks

Vom crea hooks noi în `frontend/src/lib/api/hooks.ts`:

| Hook | Purpose | Endpoint |
|------|---------|----------|
| `useRules()` | Lista tuturor regulilor | `GET /api/health/rules` |
| `useHealth()` | Starea sistemului | `GET /api/health` |
| `useValidate(rawLogs)` | Validează loguri | `POST /api/validate` |
| `useGenerateReport(rawLogs)` | Generează raport | `POST /api/reports/generate` |
| `useAiModels()` | Modele AI disponibile | `GET /api/ai/models` |
| `useAnalyzeChart(formData)` | Analiză imagine chart | `POST /api/ai/analyze-chart` |

### 4. Transformare Finding → DetectedViolation

Backendul returnează `Finding[]` în `ValidationResult.findings`. Frontendul așteaptă `DetectedViolation[]`.

**Transformare:**
```typescript
function findingToViolation(finding: Finding, index: number): DetectedViolation {
  return {
    id: `finding-${index}-${finding.rule_id}`,
    reg_code: finding.rule_id,
    severity: finding.severity,
    status: finding.passed ? 'resolved' : 'open',
    description: finding.message,
    evidence: finding.evidence,
    detected_at: finding.timestamp || new Date().toISOString(),
    created_at: new Date().toISOString(),
  };
}
```

### 5. Extragere date temperatură din ValidationResult

Pentru pagina Temperature, trebuie să extragem TEMP_READING din loguri:

```typescript
function extractTemperatureData(logEntries: LogEntry[]): TemperaturePoint[] {
  return logEntries
    .filter(e => e.log_type === 'TEMP_READING')
    .map(e => ({
      time: e.timestamp,
      sensorA: e.parsed_value as number,
      // Dacă avem senzori multipli, vom extrage și sensorB
    }));
}
```

### 6. Fallback la Mock

**Decizie:** Păstrăm datele mock ca fallback, dar cu un indicator vizual clar.

**Implementare:**
- Dacă `latestAnalysis` este `null`, afișăm un banner: "Demo Mode - încărcați fișiere pentru date reale"
- Dacă `latestAnalysis` există, folosim datele reale

**Motivație:**
- Utilizatorul vede imediat că sistemul este în demo
- Nu "mințe" utilizatorul cu date false prezentate ca reale

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Datele se pierd la refresh pagină | Salvăm `latestAnalysis` în `sessionStorage` sau `localStorage`; pe viitor salvăm în DB |
| PostgreSQL nu este instalat | Furnizăm și opțiunea Docker: `docker run --name med-therm-db -e POSTGRES_PASSWORD=... -p 5432:5432 postgres` |
| Cheia AI este invalidă | Adăugăm mesaj de eroare clar în `/api/ai/models` cu indicații de configurare |
| React Query cache nu se sincronizează între pagini | Folosim `queryClient.invalidateQueries()` după fiecare upload, cu chei de query consistente |
| Transformarea Finding → DetectedViolation pierde informații | Păstrăm câmpurile suplimentare (`data_source`, `confidence`, `inspection_hint`) în `evidence` sau ca câmpuri adiționale |

## Migration Plan

### Faza 1: Configurare (fără modificări cod)

1. **PostgreSQL:** Creează baza de date și rulează migrările
2. **AI:** Actualizează `.env` cu cheia reală și `AI_ENABLED=true`
3. **Test:** Verifică că backendul răspunde pe `/docs` și `/api/health`

### Faza 2: Frontend Data Layer

1. Creează `AnalysisContext` și `AnalysisProvider`
2. Creează React Query custom hooks în `hooks.ts`
3. Actualizează `client.ts` cu funcții lipsă pentru reports
4. Adaugă persistență în `sessionStorage`

### Faza 3: Integrare Păgini

1. **Upload.tsx:** După upload reușit, salvează în Context și invalidează cache
2. **Dashboard.tsx:** Înlocuiește sample cu date din Context; adaugă loading/error states
3. **Violations.tsx:** Înlocuiește `sampleViolations` cu transformarea `latestAnalysis.result.findings`
4. **Temperature.tsx:** Extrage date temperatură din loguri; adaugă fallback
5. **Reports.tsx:** Conectează la `/api/reports/generate`

### Faza 4: (Opțională) Persistență DB

1. Modifică endpoint-urile backend pentru a salva în PostgreSQL
2. Adaugă endpoints GET pentru a citi din DB:
   - `GET /api/analysis` - lista sesiuni
   - `GET /api/analysis/:id` - detaliile unei analize
3. Actualizează frontendul pentru a citi din aceste endpoints

## Rollback Strategy

- **Frontend:** Dacă ceva nu merge, restaurăm paginile la varianta cu sample data (le păstrăm ca comentarii sau în `fallbackData` constant)
- **Backend:** `.env` poate fi revenit la `AI_ENABLED=false`
- **Database:** Migrațiile Alembic sunt reversibile cu `alembic downgrade -1`
