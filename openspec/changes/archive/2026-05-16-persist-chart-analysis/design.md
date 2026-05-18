## Context

**Situația actuală:**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FLUX URIOS (CURRENT)                               │
└─────────────────────────────────────────────────────────────────────────┘

  Când utilizatorul încarcă o imagine (.png/.jpg):

  1. Frontend: FileUploadZone.tsx
     ┌──────────────────────────────────────────────────────────────┐
     │ if (isImage) {                                             │
     │   result = await aiApi.analyzeChart(formData)             │
     │   // NU mai este folosit addAnalysis()                     │
     │   // DOAR: await refreshHistory()                         │
     │ }                                                          │
     └──────────────────────────────────────────────────────────────┘
                              │
                              ▼
  2. Backend: POST /api/ai/analyze-chart (ai.py)
     ┌──────────────────────────────────────────────────────────────┐
     │ analyzer = ChartAnalyzer()                                  │
     │ result = await analyzer.analyze(image_bytes, image_format) │
     │                                                              │
     │ // AICI ESTE PROBLEMA:                                      │
     │ // NU este apelat:                                          │
     │ // persistence.save_analysis_session(...)                   │
     └──────────────────────────────────────────────────────────────┘
                              │
                              ▼
  3. Frontend: refreshHistory()
     ┌──────────────────────────────────────────────────────────────┐
     │ GET /api/analysis                                           │
     │ // Încarcă DOAR ce este în DB                              │
     │ // Imaginea NU ESTE acolo pentru că NU a fost salvată!    │
     └──────────────────────────────────────────────────────────────┘
                              │
                              ▼
  4. Rezultat:
     - Utilizatorul vede ultima analiză .txt (nu imaginea)
     - Sau "Nu există date"
     - Confuzie maximă
```

---

## Goals / Non-Goals

**Goals:**
1. **Consistență** - .txt și .png/.jpg se comportă identic
2. **Persistență** - Toate analizele sunt salvate în DB
3. **Refolosire** - Reutilizăm `persistence.save_analysis_session()` existent
4. **Compatibilitate** - Nu modificăm schema bazei de date
5. **Frontend minime** - Nu trebuie să modificăm nimic în frontend

**Non-Goals:**
1. **Nu modificăm schema DB** - Reutilizăm tabelele existente
2. **Nu schimbăm formatul răspunsului** - `ChartAnalysisResponse` rămâne același
3. **Nu adăugăm noi endpoint-uri** - Modificăm doar existentul `/api/ai/analyze-chart`
4. **Nu afectăm `.txt`** - Fluxul pentru .txt rămâne neschimbat

---

## Decisions

### Decizia 1: Unde salvăm?

**Opțiuni:**

| Opțiune | Unde | Avantaje | Dezavantaje |
|---------|------|----------|-------------|
| **A (Recomandată)** | În endpoint `/api/ai/analyze-chart` | Consistență cu .txt, același flux | Puțin mai mult cod în ai.py |
| B | În frontend, după `analyzeChart()` | Simplu pentru backend | Frontend trebuie să facă 2 apeluri, duplicare cod |
| C | Endpoint separat `POST /api/analysis/save-chart` | Modular | Mai multe endpoint-uri de întreținut |

**Decizie FINALĂ: Opțiunea A**

**Rationale:**
1. `.txt` folosește `POST /api/reports/generate` care include și salvarea
2. Ar fi logic ca `.png/.jpg` să folosească același pattern
3. Un singur endpoint = un singur loc de întreținut
4. Frontendul nu trebuie să știe nimic despre asta

---

### Decizia 2: Cum convertim `ChartAnalysisResult`?

Trebuie să convertim:
```
ChartAnalysisResult → date pentru save_analysis_session()
```

**Ce primește `save_analysis_session`:**
```python
async def save_analysis_session(
    self,
    device_id: str,           ← DIN numele fișierului sau Query Param
    logs: List[LogEntry],     ← GOL pentru imagini
    report: ComplianceReport, ← CREAT din ChartViolation
    config: Optional[Dict],   ← Include _latest_analysis_data
    raw_logs: Optional[List[str]],  ← GOL
)
```

**Ce avem în `ChartAnalysisResult`:**
```python
class ChartAnalysisResult:
    chart_type: str                    # "single_sensor" sau "dual_sensor"
    violations: List[ChartViolation]  # ← Convertim în Finding
    temperature_readings: List[ChartTemperatureReading]
    confidence: float
    analyzed_at: datetime
    model_used: str
```

**Plan de conversie:**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CONVERSIE DATE                                    │
└─────────────────────────────────────────────────────────────────────────┘

  ChartViolation                     Finding (pentru ComplianceReport)
  ┌─────────────────┐                 ┌─────────────────────────┐
  │ rule_code       │────────────────▶│ rule_id                 │
  │ description     │────────────────▶│ message                 │
  │ severity        │────────────────▶│ severity (convert)      │
  │ evidence        │────────────────▶│ evidence                │
  │ chart_position  │                 │                         │
  │ sensor          │                 │                         │
  └─────────────────┘                 └─────────────────────────┘

  Plus:
  ─────────────────────────────────────────────────────────────────────────
  • device_id: Query Param din frontend (?device_id=filename)
  • logs: [] (gol pentru imagini)
  • raw_logs: [] (gol pentru imagini)
  • config["_latest_analysis_data"]: IMPORTANT pentru afișare
    - deviceId
    - analyzedAt
    - rawLogs: []
    - validationResult: ← Toate findings-urile
    - temperatureData: ← extras din temperature_readings
```

---

### Decizia 3: Ce facem cu `_latest_analysis_data`?

**Context:**
- Istoricul din frontend citește `latest_analysis_data` din configul sesiunii
- Acest câmp include: `validationResult`, `temperatureData`, etc.
- Fără el, istoricul ar afișa date incomplete

**Ce trebuie în `_latest_analysis_data`:**

```python
config["_latest_analysis_data"] = {
    "deviceId": device_id,
    "analyzedAt": result.analyzed_at.isoformat(),
    "rawLogs": [],  # Gol pentru imagini
    "validationResult": {
        # Formatul din ComplianceReport
        "device_id": device_id,
        "analyzed_at": result.analyzed_at.isoformat(),
        "total_entries": len(result.temperature_readings),
        "summary": {},
        "findings": [...],  # Din ChartViolation
        "passed_count": 0,
        "failed_count": len(result.violations),
        "critical_count": critical_count,
    },
    # PLUS: temperatureData pentru afișarea graficului!
    "temperatureData": [...],  # Convertit din temperature_readings
}
```

**Important:** La .txt, `temperatureData` este extras din `rawLogs` în frontend folosind `extractTemperatureFromRawLogs()`. Pentru imagini, noi trebuie să punem temperatura deja formată în `_latest_analysis_data`.

---

### Decizia 4: Returnăm `analysis_session_id` în răspuns?

**La .txt (reports/generate):**
```python
return GenerateReportResponse(
    report=aggregated,
    generated_at=...,
    analysis_session_id=str(session.id),  ← Returnat
)
```

**La imagine (ai/analyze-chart):**
```python
return ChartAnalysisResponse(
    result=result,
    error=None,
    success=True
    // NU este returnat analysis_session_id!
)
```

**Decizie:** NU trebuie să returnăm `analysis_session_id`.

De ce?
1. Frontendul nu mai folosește `addAnalysis()` care necesita ID
2. Frontendul doar apelează `refreshHistory()` care încarcă din DB
3. Consistență nu este necesară aici pentru că ID-ul nu este folosit

---

## Risks / Trade-offs

| Risk | Mitigare |
|------|----------|
| Conversia datelor poate introduce bug-uri | Copiem pattern-ul folosit în frontend: `chartViolationsToFindings()` |
| `temperatureData` format diferit | Verificăm cum o citește frontendul și folosim același format |
| `device_id` lipsă | Frontendul trimite deja `?device_id=` ca Query Param |
| Analizele vechi din imagini nu sunt salvate | Acest change afectează doar încărcările viitoare |

---

## Implementation Plan

**Etapa 1: Creează funcție de conversie în backend**
1. Creează un helper care convertește `ChartViolation[]` → `Finding[]`
2. Creează un helper care convertește `ChartTemperatureReading[]` → formatul așteptat în `temperatureData`
3. (Sau reutilizează funcțiile existente din frontend dacă sunt disponibile în backend)

**Etapa 2: Modifică `POST /api/ai/analyze-chart`**
1. Importă `PersistenceService` și `get_async_db`
2. După analiză, construiește datele pentru salvare
3. Apelul `persistence.save_analysis_session(...)`
4. Include `_latest_analysis_data` complet în config
5. Include `temperatureData` în `_latest_analysis_data`

**Etapa 3: Verifică că `_latest_analysis_data` are toate câmpurile**
- `deviceId`
- `analyzedAt`
- `rawLogs`
- `validationResult` (cu toate câmpurile)
- `temperatureData` (CRITIC pentru afișarea graficului!)

**Etapa 4: Testare**
1. Încarcă un .png
2. Verifică că apare în istoric
3. Refresh pagină (F5)
4. Verifică că NU a dispărut
5. Verifică că graficul de temperatură apare corect

---

## Open Questions

1. **Există deja o funcție de conversie `ChartViolation` → `Finding`?**
   - În frontend există `chartViolationsToFindings()` în `transformers.ts`
   - Putem copia logica sau o mutăm într-un loc comun?

2. **Ce format are `temperatureData` în `_latest_analysis_data`?**
   - La .txt, `extractTemperatureFromRawLogs()` returnează `TemperatureDataPoint[]`
   - La imagini, avem `ChartTemperatureReading[]` care poate fi diferit
   - Trebuie să verificăm și să convertim corect

3. **Afectăm și `POST /api/ai/analyze-logs`?**
   - Acest endpoint este pentru text analysis, nu pentru imagini
   - Nu este în scope-ul acestui change

4. **Avem nevoie de audit log?**
   - `save_analysis_session()` include deja `AuditAction.CREATE`
   - Deci va fi înregistrat automat
