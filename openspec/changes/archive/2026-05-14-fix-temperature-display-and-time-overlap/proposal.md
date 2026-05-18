## Why

Utilizatorii întâlnesc două probleme în pagina Temperature:
1. Etichetele de timp de pe axa X se suprapun când sunt multe puncte de date
2. Datele de temperatură extrase din imagini (screenshots grafice) prin VLLM nu sunt afișate în grafice

Aceste probleme afectează experiența utilizatorului și corectitudinea analizei-compliance.

## What Changes

- **Fix suprapunere etichete axă X**: Configurare interval tick-uri rațională + opțiune de rotire a etichetelor
- **Integrare date temperatură din VLLM**: Extragere time-series din analiza imaginilor și populare `temperatureData`
- **Reflectare date noi în Temperature page**: Asigurare că datele din ambele surse (logs + images) apar în grafice

## Capabilities

### New Capabilities
- `chart-image-data-extraction`: Extragere time-series de temperatură din imaginile încărcate, pentru afișare în grafice

### Modified Capabilities
- `analysis-sessions`: Extindere pentru a agrega date temperatură din multiple surse (text logs + image analysis)

## Impact

- **Frontend**: `TemperatureChart.tsx`, `AnalysisContext.tsx`, `transformers.ts`
- **Data flow**: Modificare modului în care `LatestAnalysis.temperatureData` este populat
- **VLLM**: Potențiale extensii pentru extragere time-series din răspunsurile modelului
