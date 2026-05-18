## Context

**Starea curentă:**
1. **Prompt VLLM** (`prompts.py`): Cere doar `violations` și metadate de bază, nu întreaga serie temporală
2. **Model** (`models.py`): `ChartAnalysisResult` nu are câmpul `data_points`
3. **Analyzer** (`analyzer.py`): Extrage doar `violations`, `time_range`, `temperature_range` din răspunsul VLLM parsat
4. **Frontend**: Deja caută `data_points`, `time_series`, etc. (implementat în `fix-temperature-display-and-time-overlap`)
5. **Problema**: Dacă un grafic este COMPLIANT (fără `violations`), nimic nu apare în pagina Temperature

**Răspuns backend actual:**
```json
{
  "success": true,
  "result": {
    "violations": [...],
    "time_range_start": "...",
    "temp_range_min": 2,
    ...
  }
}
```

**Răspuns necesar:**
```json
{
  "success": true,
  "result": {
    "violations": [...],
    "data_points": [
      {"time": "10:00", "temperature": 5.2, "sensor": "A"},
      {"time": "10:30", "temperature": 5.0, "sensor": "A"},
      ...
    ],
    ...
  }
}
```

## Goals / Non-Goals

**Goals:**
- Prompt-ul VLLM să ceară extragerea tuturor citirilor de temperatură din grafic
- Modelul `ChartAnalysisResult` să includă `data_points`
- Analyzerul să extragă `data_points` din răspunsul parsat
- API-ul să returneze `data_points` în răspuns

**Non-Goals:**
- Rescriere completă a fluxului VLLM
- Modificări frontend (deja implementate)
- Modificări structurale bazei de date

## Decisions

### Decizia 1: Structura pentru `TemperatureReading`

**Opțiuni:**
1. Câmpuri simple: `time`, `temperature`, `sensor`
2. Similar cu frontend `TemperatureDataPoint`: `timestamp`, `time`, `sensorA`, `sensorB`
3. Structură flexibilă: `timestamp`, `values: Dict[sensor, float]`

**Decizie:** Opțiunea 2, aliniată cu frontend-ul.

```python
class TemperatureReading(BaseModel):
    time: str                    # "10:30"
    timestamp: Optional[datetime] = None
    sensor_a: float
    sensor_b: Optional[float] = None
    source: str = "chart_image"
```

**Rationale:** Frontend-ul deja înțelege `TemperatureDataPoint` cu aceleași câmpuri.

### Decizia 2: Ce cerem în prompt

**Opțiuni:**
1. Cere "toate punctele de date" - general, ambiguu
2. Cere "citiri pe oră/minut" - depinde de rezoluția graficului
3. Cere "extrage toate valorile de temperatură vizibile pe axa X" - specific pentru grafice

**Decizie:** Combinare:
- "Extract ALL temperature readings visible in the chart"
- "For each labeled time on the X-axis, provide the temperature value(s)"
- "Include Y values even when within safe range"

**Rationale:** VLLM performează mai bine când instrucțiunile sunt specifice contextului (grafice cu axe X/Y).

## Risks / Trade-offs

| Risk | Mitigare |
|------|----------|
| VLLM nu returnează întotdeauna `data_points` consistent | Frontend are deja fallback la `violations`; putem adăuga și fallback la generare puncte din `time_range` |
| Prompt mai lung = costuri mai mari | Adăugăm doar 1-2 paragrafe; costul este justificat |
| Răspunsuri mai grele | Puctele de date sunt relativ puține (maxim ~50 pentru un grafic de 24h) |
| Breaking changes? | Adăugăm câmpuri NOI; răspunsul rămâne compatibil cu clienții existenți |

## Open Questions

1. Ce nume de câmp folosește frontend-ul? `data_points`, `time_series`, `readings`, `temperature_data`?
   - Frontend-ul caută TOATE acestea. Vom folosi `data_points` (cel mai descriptiv).

2. Ar trebui să extindem și fallback-ul pentru când NICI `data_points` NICI `violations` nu există?
   - Da: putem genera puncte minime din `time_range` și `temp_range` pentru a afișa cel puțin "interval monitorizat".
