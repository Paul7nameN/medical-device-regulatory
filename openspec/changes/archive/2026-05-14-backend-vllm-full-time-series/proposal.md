## Why

Când utilizatorul încarcă imagini cu grafice de temperatură în pagina "Temperature", datele nu apar în grafic. Motivul:
- **Prompt-ul VLLM** cere doar `violations` (nereguli), nu întreaga serie temporală de temperaturi
- **Frontend-ul** (deja implementat) caută câmpuri precum `data_points`, `time_series` - dar backend nu le returnează
- **Fallback** funcționează DOAR când există nereguli detectate, și chiar și atunci afișează doar punctele asociate cu nereguli, nu întregul grafic

Acest lucru înseamnă că un utilizator care încarcă un grafic COMPLIANT (fără nereguli) nu va vedea NIMIC în pagina Temperature, deși graficul a fost analizat cu succes.

## What Changes

- **Update VLLM prompt** pentru a cere extragerea întregii serii temporale de temperaturi din grafic (nu doar nereguli)
- **Extindere model `ChartAnalysisResult`** cu câmpul `data_points: List[TemperatureReading]`
- **Modificare `ChartAnalyzer`** pentru a extrage și popula `data_points` din răspunsul VLLM
- **API Response**: `ChartAnalysisResponse.result` va include acum `data_points`

## Capabilities

### Modified Capabilities
- `chart-image-data-extraction`: Extindere pentru a returna seria temporală completă, nu doar neregulele
- `analysis-sessions`: Rezultatele analizelor de imagini includ acum și citirile de temperatură

## Impact

- **Backend Python**:
  - `backend/app/ai/image/prompts.py` - modificare prompt
  - `backend/app/ai/image/models.py` - adăugare model `TemperatureReading`, extensie `ChartAnalysisResult`
  - `backend/app/ai/image/analyzer.py` - extragere `data_points` din răspunsul parsat

- **API**: Răspunsul de la `/api/ai/analyze-chart` include acum `result.data_points`

- **Frontend**: Deja pregătit pentru a consuma aceste date (implementat în schimbarea `fix-temperature-display-and-time-overlap`)
