## Why

**Problema actuală:** Analiza imaginilor (.png/.jpg) nu se salvează în baza de date.

```
┌─────────────────────────────────────────────────────────────────────────┐
│         FLUX INCONSISTENT (CURRENT)                                  │
└─────────────────────────────────────────────────────────────────────────┘

  .txt Log File:                           .png/.jpg Image:
  ┌─────────────────────────┐              ┌─────────────────────────┐
  │ Frontend:               │              │ Frontend:               │
  │ reportsApi.             │              │ aiApi.analyzeChart()   │
  │ generateFromLogs()      │              │                         │
  └───────────┬─────────────┘              └───────────┬─────────────┘
              │                                        │
              ▼                                        ▼
  ┌─────────────────────────┐              ┌─────────────────────────┐
  │ Backend:                │              │ Backend:                │
  │ POST /api/reports/      │              │ POST /api/ai/analyze-  │
  │ generate                │              │ chart                   │
  │                         │              │                         │
  │ ✅ persistence.save_    │              │ ❌ DOAR analizează,    │
  │    analysis_session()   │              │    NU salvează în DB!  │
  │    → salvează în DB     │              │                         │
  └───────────┬─────────────┘              └───────────┬─────────────┘
              │                                        │
              ▼                                        ▼
  ┌─────────────────────────┐              ┌─────────────────────────┐
  │ Frontend după upload:  │              │ Frontend după upload:  │
  │ refreshHistory()        │              │ refreshHistory()        │
  │ GET /api/analysis       │              │ GET /api/analysis       │
  └───────────┬─────────────┘              └───────────┬─────────────┘
              │                                        │
              ▼                                        ▼
  ┌─────────────────────────┐              ┌─────────────────────────┐
  │ ✅ Apare în istoric    │              │ ❌ NU apare în istoric  │
  │ ✅ Persistă după F5    │              │ ❌ "Dispare" după F5   │
  │ ✅ Are analysisSessionId│              │ ❌ Vezi ultimul .txt   │
  └─────────────────────────┘              └─────────────────────────┘
```

**De ce este o problemă:**
1. **Inconsistență** - Două tipuri de upload au comportamente diferite
2. **Experiență proastă** - Utilizatorul crede că imaginea a fost încărcată, dar nu reapare după refresh
3. **Confuzie** - În locul analizei imaginii, apare ultima analiză .txt încărcată
4. **Sursă unică de adevăr** - Imaginea nu ajunge niciodată în DB, care este sursa unică de adevăr

---

## What Changes

**Soluția:** Adaugă `persistence.save_analysis_session()` în endpoint-ul `POST /api/ai/analyze-chart`.

```
┌─────────────────────────────────────────────────────────────────────────┐
│         FLUX CONSISTENT (NOU)                                        │
└─────────────────────────────────────────────────────────────────────────┘

  .txt Log File:                           .png/.jpg Image:
  ┌─────────────────────────┐              ┌─────────────────────────┐
  │ Frontend:               │              │ Frontend:               │
  │ reportsApi.             │              │ aiApi.analyzeChart()   │
  │ generateFromLogs()      │              │                         │
  └───────────┬─────────────┘              └───────────┬─────────────┘
              │                                        │
              ▼                                        ▼
  ┌─────────────────────────┐              ┌─────────────────────────┐
  │ Backend:                │              │ Backend:                │
  │ POST /api/reports/      │              │ POST /api/ai/analyze-  │
  │ generate                │              │ chart                   │
  │                         │              │                         │
  │ ✅ persistence.save_    │              │ ✅ persistence.save_    │
  │    analysis_session()   │              │    analysis_session()   │
  │                         │              │    ← NOU!              │
  └───────────┬─────────────┘              └───────────┬─────────────┘
              │                                        │
              ▼                                        ▼
  ┌─────────────────────────┐              ┌─────────────────────────┐
  │ ✅ AMBELE apar în      │              │ ✅ AMBELE apar în      │
  │    istoric              │              │    istoric              │
  │ ✅ AMBELE persistă     │              │ ✅ AMBELE persistă     │
  │    după refresh         │              │    după refresh         │
  └─────────────────────────┘              └─────────────────────────┘
```

---

## Changes Detaliate

### 1. Backend: Adaugă salvare în DB în `analyze_chart`

**Ce trebuie convertit:**

| Format | `ChartAnalysisResult` (Image) | Format salvat în DB |
|--------|-------------------------------|---------------------|
| Violations | `ChartViolation[]` | `Finding[]` |
| Temperature | extras din `extractTemperatureFromChartResult()` | `TemperatureDataPoint[]` |
| Device ID | din numele fișierului | `device_id` |
| Analyzed at | `result.analyzed_at` sau `now()` | `analyzed_at` |

**Structură `ChartAnalysisResult`:**
```python
class ChartAnalysisResult:
    chart_type: str          # "single_sensor", "dual_sensor"
    violations: List[ChartViolation]
    temperature_readings: List[ChartTemperatureReading]
    confidence: float
    analyzed_at: datetime
    model_used: str
```

**Structură salvată în DB prin `save_analysis_session`:**
- `logs: List[LogEntry]` (poate fi gol pentru imagini)
- `report: ComplianceReport` (trebuie creat din `ChartAnalysisResult`)
- `raw_logs: List[str]` (poate fi gol)

---

### 2. Frontend: Verificare că fluxul rămâne același

Frontendul nu ar trebui să necesite modificări:
- După upload, deja se apelează `refreshHistory()`
- Dacă analiza este salvată în DB, `refreshHistory()` o va încărca

---

### 3. Consecințe pozitive

| Avantaj | Descriere |
|---------|-----------|
| **Consistență** | .txt și .png/.jpg au același comportament |
| **Persistență** | Toate analizele reapar după refresh |
| **Sursă unică** | Toate datele sunt în DB, conform schimbării recente |
| **Istoric complet** | Utilizatorul vede toate analizele, nu doar pe cele .txt |

---

## Capabilities

### Modified Capabilities
- `chart-image-data-extraction`: Acum include și persistența în DB
- `analysis-sessions`: Acum include și analizele din imagini
- `log-storage`: Toate sursele sunt salvate în DB

---

## Impact

### Frontend
- **Nicio modificare** - Flow-ul rămâne același
- `refreshHistory()` va încărca și analizele din imagini

### Backend
- **`app/api/ai.py`**: Adaugă `save_analysis_session()` în endpoint-ul `analyze_chart`
- **Conversie date**: `ChartAnalysisResult` → `ComplianceReport` + date necesare pentru salvare
- **Config salvat**: `_latest_analysis_data` trebuie completat (ca la .txt) pentru afișare în istoric

### Database
- **Nicio schimbare schema** - Reutilizează tabelele existente
- **Doar date noi** - Analizele din imagini vor fi salvate ca `AnalysisSession`

---

## Open Questions

1. **Ce facem cu `raw_logs` și `LogEntry` pentru imagini?**
   - Opțiunea A: Lăsăm goale
   - Opțiunea B: Creăm un `LogEntry` "fictional" cu metadate
   - **Decizie: A** - Imaginii nu au log-uri text

2. **Cum afișăm temperatura din imagine în Dashboard?**
   - Frontendul extrage temperatura din `raw_logs` folosind `extractTemperatureFromRawLogs()`
   - Pentru imagini, temperatura este extras din `ChartAnalysisResult.temperature_readings`
   - **Atenție:** Trebuie să ne asigurăm că `_latest_analysis_data` include toate datele necesare

3. **Ce facem cu `device_id`?**
   - La .txt, `device_id` provine din numele fișierului
   - La imagini, `device_id` trebuie extras și el din numele fișierului
   - **Frontendul trimite deja `device_id` ca Query Param:** `analyze-chart?device_id=...`

4. **Conflict cu `analysisSessionId` din frontend?**
   - Înainte, frontendul încerca să folosească `addAnalysis()` cu datele din `ChartAnalysisResult`
   - Acum, `addAnalysis()` nu mai este folosit (doar `refreshHistory()`)
   - **Bine:** DB devine sursa unică, așa că nu mai este nevoie de asta
