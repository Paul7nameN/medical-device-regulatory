## 1. Investighează formatul datelor (Prioritate înaltă)

- [x] 1.1 Verifică `ChartViolation` și `ChartTemperatureReading` în `backend/app/ai/image/models.py`
  - Ce câmpuri au?
  - Cum se compară cu `Finding` și `TemperatureDataPoint`?

- [x] 1.2 Verifică `chartViolationsToFindings()` din frontend (`lib/utils/transformers.ts`)
  - Ce logică folosește?
  - Putem copia-o în backend?

- [x] 1.3 Verifică cum este format `_latest_analysis_data` la .txt
  - Caută în `persistence.py`: `config["_latest_analysis_data"]`
  - Verifică toate câmpurile necesare

---

## 2. Creează funcții de conversie în backend

- [x] 2.1 Adaugă un helper pentru `ChartViolation` → `Finding`
  - Localizare: `backend/app/ai/image/` sau un modul comun
  - Convertește:
    - `rule_code` → `rule_id`
    - `description` → `message`
    - `severity`: "critical" → Severity.CRITICAL, etc.
    - `evidence` → păstrează

- [x] 2.2 Adaugă un helper pentru `ChartTemperatureReading` → formatul pentru `temperatureData`
  - Verifică ce format așteaptă frontendul
  - La .txt, `extractTemperatureFromRawLogs()` returnează `TemperatureDataPoint[]`

---

## 3. Modifică endpoint-ul `POST /api/ai/analyze-chart`

- [x] 3.1 Adaugă importurile necesare în `backend/app/api/ai.py`:
  ```python
  from app.database import get_async_db
  from app.services.persistence import PersistenceService
  from sqlalchemy.ext.asyncio import AsyncSession
  from fastapi import Depends
  ```

- [x] 3.2 Modifică semnătura funcției pentru a include DB:
  ```python
  async def analyze_chart(
      file: UploadFile = File(...),
      device_id: Optional[str] = Query(None),
      db: AsyncSession = Depends(get_async_db),  # NOU
  ):
  ```

- [x] 3.3 După analiza cu succes, adaugă logica de salvare:
  ```python
  # După: result = await analyzer.analyze(image_bytes, image_format)
  
  # Convertim violations în findings
  findings = convert_chart_violations_to_findings(result.violations)
  
  # Construim un raport minimal (similar cu .txt)
  # Sau folosim un RegulatoryReport gol doar cu findings
  
  # Inițializează PersistenceService
  persistence = PersistenceService(db)
  
  # Construim config cu _latest_analysis_data
  # IMPORTANT: Include TOT ce este nevoie pentru afișare
  
  latest_analysis_data = {
      "deviceId": device_id or file.filename or "unknown-device",
      "analyzedAt": result.analyzed_at.isoformat(),
      "rawLogs": [],  # Gol pentru imagini
      "validationResult": {
          "device_id": device_id or file.filename or "unknown-device",
          "analyzed_at": result.analyzed_at.isoformat(),
          "total_entries": len(result.temperature_readings),
          "summary": {},
          "findings": [f.to_dict() for f in findings],
          "passed_count": 0,
          "failed_count": len(result.violations),
          "critical_count": len([v for v in result.violations if v.severity == "critical"]),
      },
      "temperatureData": convert_temperature_readings(result.temperature_readings),
  }
  
  # Salvează în DB
  await persistence.save_analysis_session(
      device_id=device_id or file.filename or "unknown-device",
      logs=[],  # Gol pentru imagini
      report=...,  # Crează un raport compatibil
      config={"_latest_analysis_data": latest_analysis_data},
      raw_logs=[],  # Gol
  )
  ```

---

## 4. Asigură-te că `_latest_analysis_data` este COMPLET

- [x] 4.1 Verifică `TemperatureDataPoint` din frontend
  - Locație: `frontend/src/components/TemperatureChart.tsx`
  - Ce câmpuri are nevoie?

- [x] 4.2 Asigură-te că `temperatureData` este inclus corect
  - Acest câmp este CRITIC pentru afișarea graficului!
  - La .txt, el este extras din rawLogs în frontend
  - La imagini, el trebuie inclus în `_latest_analysis_data`

- [x] 4.3 Verifică că `validationResult` are toate câmpurile:
  - `device_id`
  - `analyzed_at`
  - `total_entries`
  - `summary`
  - `findings`
  - `passed_count`
  - `failed_count`
  - `critical_count`

---

## 5. Verifică compatibilitatea cu `save_analysis_session`

- [x] 5.1 Citește `persistence.save_analysis_session()` cu atenție
  - Ce parametri așteaptă?
  - `logs: List[LogEntry]` - Putem trimite o listă goală?
  - `report: ComplianceReport` - Trebuie să fie un obiect valid?

- [x] 5.2 Dacă `report` trebuie să fie un `ComplianceReport` valid:
  - Creează un raport minimal cu findings-urile
  - Sau verifică dacă putem trimite `None` sau un gol

- [x] 5.3 Alternativă: Poți modifica `save_analysis_session()` pentru a accepta un parametru diferit?
  - Mai bine NU - păstrează consistența
  - Mai bine creezi un raport compatibil

---

## 6. Testare

- [ ] 6.1 Test cu .png:
  - Încarcă un fișier .png
  - Verifică că apare în istoric
  - F5 refresh → NU trebuie să dispară
  - Verifică că graficul de temperatură apare

- [ ] 6.2 Test cu .jpg:
  - Similar cu .png

- [ ] 6.3 Test comparativ cu .txt:
  - Încarcă un .txt
  - Încarcă un .png
  - Verifică că AMBELE apar în istoric
  - Refresh → AMBELE rămân

- [ ] 6.4 Test DB direct:
  - Verifică în `analysis_sessions` table
  - Verifică `config` column
  - Verifică că `_latest_analysis_data` există și are toate câmpurile

---

## Ordinea de Implementare (Recomandată)

```
ÎNTÂI:
  → Task 1.1, 1.2, 1.3: Investighează formatele

APOI:
  → Task 2.1, 2.2: Creează convertoarele

APOI (CRITIC):
  → Task 5.1, 5.2, 5.3: Înțelege ce așteaptă persistence.save_analysis_session()

APOI:
  → Task 3.1, 3.2, 3.3: Modifică endpoint-ul

APOI (FOARTE IMPORTANT):
  → Task 4.1, 4.2, 4.3: Asigură-te că temperatureData este inclus corect!

LA FINAL:
  → Teste (Task 6)
```

---

## Ce NU trebuie modificat

- ❌ Frontendul - NU are nevoie de modificări
- ❌ Endpoint-urile pentru .txt - rămân neschimbate
- ❌ Schema DB - nu este nevoie
- ❌ Altă parte a codului - doar `POST /api/ai/analyze-chart`
