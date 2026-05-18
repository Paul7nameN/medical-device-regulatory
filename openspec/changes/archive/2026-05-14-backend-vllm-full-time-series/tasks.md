## 1. Update VLLM Prompt for Full Time-Series Extraction

- [x] 1.1 Adaugă în `SYSTEM_PROMPT_CHART_ANALYSIS` secțiune pentru extragerea tuturor citirilor de temperatură
- [x] 1.2 Adaugă în `RESPONSE FORMAT` câmpul `data_points` cu structura specificată
- [x] 1.3 Actualizează `IMAGE_ANALYSIS_USER_PROMPT_TEMPLATE` pentru a clarifica că toate citirile sunt necesare, nu doar cele care reprezintă nereguli

## 2. Extindere Model de Date

- [x] 2.1 Creează clasa `TemperatureReading` în `backend/app/ai/image/models.py` cu câmpurile: `time`, `timestamp` (optional), `sensor_a`, `sensor_b` (optional), `source`
- [x] 2.2 Adaugă câmpul `data_points: List[TemperatureReading] = []` în clasa `ChartAnalysisResult`
- [x] 2.3 Adaugă `field_serializer` pentru datetime dacă este necesar

## 3. Extragere Data Points din Răspunsul VLLM

- [x] 3.1 Modifică `ChartAnalyzer._build_result()` pentru a căuta `data_points`, `time_series`, `readings` sau `temperature_data` în răspunsul parsat
- [x] 3.2 Implementează conversia din dicționar VLLM în `TemperatureReading`
- [x] 3.3 Tratează cazurile în care `sensor_b` lipsește sau valorile sunt în format diferit

## 4. Testare și Verificare

- [x] 4.1 Rulează testele existente pentru a verifica compatibilitatea
- [x] 4.2 Verifică că răspunsul API `/api/ai/analyze-chart` include acum `result.data_points`
- [x] 4.3 Verifică că frontend-ul poate consuma noile date (deja implementat)

## 5. (Opțional) Fallback Avansat

- [x] 5.1 Dacă nici `data_points` nici `violations` nu există, generează puncte minime din `time_range` și `temp_range` pentru a afișa "interval monitorizat"
- [x] 5.2 Adaugă log-uri care să indice când VLLM nu returnează `data_points`
