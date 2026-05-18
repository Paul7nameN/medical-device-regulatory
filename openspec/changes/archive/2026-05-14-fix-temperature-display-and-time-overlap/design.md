## Context

**Probleme curente identificate:**

1. **Suprapunere etichete axă X** (`TemperatureChart.tsx:247-254`):
   - Configurația `interval={isMobile ? 'preserveStartEnd' : 0}` afișează TOATE tick-urile pe desktop
   - Când sunt multe puncte de date (ex: 24+ ore cu citiri la fiecare 5 minute), etichetele se suprapun

2. **Date temperatură din imagini (VLLM) nu apar în grafice**:
   - Când utilizatorul încarcă screenshots de grafice (.png/.jpg), `aiApi.analyzeChart()` extrage doar `violations`
   - `rawLogs = []` pentru imagini, deci `extractTemperatureFromRawLogs()` nu găsește nimic
   - `LatestAnalysis.temperatureData` rămâne gol, graficul nu afișează nimic

**Flux actual:**
```
Fișier .txt → rawLogs[] → extractTemperatureFromRawLogs() → temperatureData[] → GRAFIC
Fișier .png → violations[] → chartViolationsToFindings() → findings[] → DOAR violări (fără grafic)
```

## Goals / Non-Goals

**Goals:**
- Corectați afișarea etichetelor pe axa X (fără suprapunere)
- Asigurați-vă că datele din VLLM (imagini) populează și `temperatureData[]` pentru afișare în grafice
- Păstrați compatibilitatea cu datele existente

**Non-Goals:**
- Rescrierea completă a motorului VLLM (doar extensie parsare răspuns)
- Adăugarea de noi funcționalități de analiză (doar fixuri)

## Decisions

### Decizie 1: Fix interval axă X

**Problema:** `interval=0` afișează toate etichetele.

**Opțiuni considerate:**
1. `interval="preserveStartEnd"` pentru toate dispozitivele - simplu, dar arată puține etichete
2. `interval={Math.ceil(data.length / 8)}` - calcul dinamic în funcție de numărul de puncte
3. **`angle={-45}` + `textAnchor="end"` + padding** - rotirea etichetelor pentru a se încadra

**Decizie:** Combinație:
- `interval={Math.min(Math.ceil(data.length / 10), 10)}` - maxim 10 etichete
- `tick={{ fontSize: isMobile ? 9 : 11 }}` - font micșorat
- Dacă sunt încă multe puncte, se poate adăuga rotirea

**Rationale:** Echilibru între lizibilitate și cantitate de informație.

### Decizie 2: Extragere time-series din răspuns VLLM

**Problema:** VLLM returnează `violations[]` dar nu și seria completă de temperaturi.

**Opțiuni considerate:**
1. Modificare backend pentru a returna și `time_series` în răspuns
2. **Extragere date din răspunsul existent dacă există** (câmpuri suplimentare)
3. Încercare de inferență a valorilor din timestamp-urile violations

**Decizie:**
- Extindeți `transformers.ts` pentru a căuta câmpul `time_series` sau `data_points` în răspunsul VLLM
- Dacă există, conversie în `TemperatureDataPoint[]`
- Dacă nu există, se creează puncte minime din `violations` (doar timestamp-urile cu excursion)

**Rationale:** Soluție incrementală, compatibilă cu răspunsurile VLLM existente, cu potențial de îmbunătățire pe backend.

### Decizie 3: Modificare flux în FileUploadZone

**Problema:** `createAnalysisData(validationResult, rawLogs)` folosește doar `rawLogs`.

**Decizie:**
- Adăugați un al treilea parametru opțional `temperatureDataPoints?: TemperatureDataPoint[]`
- Sau: extindeți `createAnalysisData()` pentru a căuta date în `validationResult` dacă `rawLogs` este gol
- Sau: în `FileUploadZone.tsx`, după extragerea datelor din VLLM, construiți `analysisData` manual

**Rationale:** A treia opțiune este cea mai puțin invazivă - modificăm doar `FileUploadZone.tsx`.

## Risks / Trade-offs

| Risk | Mitigare |
|------|----------|
| Datele VLLM nu includ întotdeauna serie completă | Folosim violations ca fallback; marcăm sursa datelor în UI |
| Etichetele rotite sunt dificil de citit | Folosim întai calcul dinamic al intervalului; rotirea ca ultimă opțiune |
| Modificarea intervalului afectează zoom/brush | Testăm cu Brush activ; păstrăm funcționalitatea |

## Open Questions

1. Ce câmpuri returnează de fapt backend-ul VLLM în `result`? (data_points, time_series, readings?)
2. Este nevoie de modificări și pe backend pentru a returna seria completă?

*Pentru implementarea inițială, vom presupune că putem extrage date din violations ca fallback, și că viitoare modificări backend vor adăuga câmpul `time_series`.*
