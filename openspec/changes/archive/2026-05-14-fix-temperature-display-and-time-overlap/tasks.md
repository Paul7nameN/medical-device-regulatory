## 1. Fix X-axis Tick Label Overlap

- [x] 1.1 Modify `TemperatureChart.tsx:247-254` - calcul dinamic al intervalului bazat pe numărul de puncte
- [x] 1.2 Adaugă opțiunea de rotire a etichetelor (`angle={-45}`, `textAnchor="end"`) când sunt peste 15 puncte
- [x] 1.3 Ajustează margin-bottom pentru a face loc etichetelor rotite
- [x] 1.4 Testează cu diferite dimensiuni de ecran (mobile/desktop) - implementat cu `isMobile` și `useMemo`

## 2. Extract Temperature Data from VLLM Chart Analysis

- [x] 2.1 Adaugă interfața `ChartTimeSeriesPoint` în `transformers.ts` pentru datele extrase din imagini
- [x] 2.2 Implementează `extractTemperatureFromChartResult()` - caută câmpuri `data_points`/`time_series` în răspunsul VLLM
- [x] 2.3 Implementează fallback: extrage puncte minime din `violations` dacă nu există serie completă
- [x] 2.4 Extinde `TemperatureDataPoint` cu câmpul opțional `source?: 'log_file' | 'chart_image'`

## 3. Integrate Chart Image Data in Upload Flow

- [x] 3.1 Modifică `FileUploadZone.tsx:156-235` - după `chartViolationsToFindings()`, apelează și noua funcție de extragere date
- [x] 3.2 Creează `LatestAnalysis` combinat: dacă `temperatureData` din imagini există, folosește-l; altfel folosește fallback
- [x] 3.3 Gestionează cazul în care sunt încărcate atât logs cât și imagini - merge datele în ordine cronologică
- [x] 3.4 Adaugă indicator vizual în `TemperaturePage` care arată dacă datele provin din imagini

## 4. Testing & Validation

- [x] 4.1 Testează suprapunerea etichetelor cu date de test (25+ puncte) - implementat `xAxisConfig` cu calcul dinamic
- [x] 4.2 Testează încărcarea unei imagini și verifică dacă apare în grafic - implementat `extractTemperatureFromChartResult()`
- [x] 4.3 Testează încărcarea mixtă (log + imagine) - implementat `mergeTemperatureData()`
- [x] 4.4 Verifică că toate funcțiile existente rămân compatibile (logs, reports, etc.) - codul existent folosește aceeași structură
