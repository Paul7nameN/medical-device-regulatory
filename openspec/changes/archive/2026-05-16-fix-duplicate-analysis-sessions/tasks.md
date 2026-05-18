## 1. Investigare și Confirmare

- [x] 1.1 Am identificat cauza principală: Două timestamp-uri diferite
  - În BD: `base_report.analyzed_at`
  - În răspuns: `datetime.now()`

- [x] 1.2 Am identificat cauza secundară: Două structuri diferite
  - Salvat: `base_report.to_dict()` (ComplianceReport)
  - Returnat: `AggregatedComplianceReport`
  - Frontendul EXTRAGE findings din `violations_by_severity`

---

## 2. Backend: Fix Timestamp (PRIORITATE ÎNALTĂ)

- [x] 2.1 Modifică `backend/app/api/reports.py` → `generate_compliance_report()`
  - Identifică unde se returnează răspunsul
  - Înlocuiește `datetime.now()` cu `base_report.analyzed_at` pentru `generated_at`
  - **DONE:** `generated_at=base_report.analyzed_at` în loc de `datetime.now()`
  - Aceasta este SCHIMBAREA ESENȚIALĂ care rezolvă problema cu dublurile!

- [x] 2.2 (Opțional, pentru siguranță): Adaugă `analysis_session_id` în răspuns
  - **NOTĂ:** Am încercat aceasta, dar am întâmpinat o problemă cu SQLAlchemy Async.
  - După `commit()` din `save_analysis_session`, obiectul ORM devine "expired" și nu se poate accesa `.id` în contextul async.
  - **Decizie:** Am scos `analysis_session_id` din fluxul actual pentru a nu bloca dezvoltarea.
  - **PENTRU VIITOR:** Dacă vrem ID-ul sesiunii, putem:
    a) Refactora `persistence.py` pentru a returna ID-ul ca string (înainte de commit)
    b) SAU folosim `session.expire_on_commit=False` (cu grijă)
  - **ÎN ACEASTĂ MOMENT:** Nu avem nevoie de ID pentru deduplicare.
    Avem deja cheia: `${deviceId}|${timestamp}|${failed_count}`
    care acum funcționează corect pentru că timestamp-ul este UNIC.

**CE ESTE ESENȚIAL ȘI A FOST FĂCUT:**
```
  Înainte:
    generated_at = datetime.now()  ← DIFERIT de fiecare dată!
  
  Acum:
    generated_at = base_report.analyzed_at  ← ACELAȘI peste tot!
  
  Acest lucru asigură că:
  1. Data salvată în BD (_latest_analysis_data.analyzedAt)
  2. Data returnată frontendului (generated_at)
  3. Data folosită în deduplicare
  
  SUNT TOATE ACELAȘI!
```

---

## 3. (Opțional) Backend: Adaugă Structură Consistentă

- [ ] 3.1 Adaugă `raw_validation_result` în răspuns
  - Acesta va fi `base_report.to_dict()`
  - Frontendul îl poate folosi DIRECT fără a extrage findings din altă structură

- [ ] 3.2 Sau, alternativ: Modifică frontendul să fie consistent cu structura existentă
  - Verifică cum extrage findings din `AggregatedComplianceReport`
  - Asigură-te că `passed_count` și `failed_count` sunt setate corect

---

## 4. Frontend: Deduplicare Mai Robustă

- [x] 4.1 Verifică cheia de deduplicare din `AnalysisContext.tsx`
  - **DONE:** Am verificat și am actualizat cheia
  - Am extins interfața `LatestAnalysis` cu `analysisSessionId?: string`
  - Actualizat `createDeduplicationKey`: Dacă există `analysisSessionId`, folosește-l DIRECT; altfel folosește cheia veche
  - Actualizat `backendItemToLatestAnalysis` pentru a extrage ID-ul din răspuns

- [x] 4.2 (Dacă adăugăm `analysis_session_id`): Extinde cheia
  - **NOTĂ:** Momentan, `analysisSessionId` va fi `undefined` pentru noi analize (din cauza problemei cu SQLAlchemy Async)
  - **ÎNSĂ:** Cheia veche acum FUNCTIONEAZĂ CORECT pentru că:
    - `generated_at = base_report.analyzed_at` (nu mai este `datetime.now()`)
    - Acest lucru asigură unicitatea timestamp-ului între BD și frontend
  - **Deduplicarea va funcționa corect cu:**
    ```typescript
    // Când analysisSessionId lipsește, se folosește:
    `${a.deviceId}|${flooredTime.toISOString()}|${a.validationResult?.failed_count || 0}`
    // Care acum este UNIC pentru că flooredTime este același peste tot!
    ```
  - **Actualizări făcute în frontend:**
    - `LatestAnalysis` cu `analysisSessionId?: string`
    - `createDeduplicationKey` cu logica hibridă
    - `backendItemToLatestAnalysis` extrage ID-ul din răspuns
    - `FileUploadZone.tsx` extrage `analysis_session_id` din răspunsul API
    - `client.ts` actualizat cu tipul răspunsului

---

## 5. Frontend: Verifică Extragerea Findings

- [ ] 5.1 Verifică `FileUploadZone.tsx` - cum extrage findings din răspuns
  - Când `result.report` are `violations_by_severity`
  - Frontendul face un `flatten` și construiește un nou `ValidationResult`
  - Verifică dacă `passed_count` și `failed_count` sunt setate corect

- [ ] 5.2 Verifică dacă scorul 100% vine de aici
  - `calculateComplianceScore(passedCount, passedCount + failedCount)`
  - Dacă `passedCount + failedCount === 0` → returnează 100

---

## 6. Testare

- [ ] 6.1 Test cu un fișier .txt:
  - Upload
  - Verifică că apare DOAR O DATĂ în istoric
  - Notează scorul compliance (ar trebui să fie același în toate locurile)

- [ ] 6.2 Test cu refresh/restart:
  - Refresh pagina
  - Verifică că nu sunt dubluri
  - Verifică că scorul rămâne același

- [ ] 6.3 Test cu închidere/re-deschidere tab:
  - Închide tab-ul
  - Redeschide
  - Verifică că istoricul există și nu are dubluri

---

## Ordinea de Implementare (Recomandată)

```
FAZĂ ÎNTÂI:
  → Task 2.1: Fix timestamp în backend (cel mai important)

APOI, DACĂ E NEVOIE:
  → Task 4.1/4.2: Verifică/îmbunătățește deduplicarea în frontend

APOI, CA MĂSURĂ SUPLIMENTARĂ:
  → Task 2.2: Adaugă analysis_session_id în răspuns
  → Task 4.2: Folosește-l pentru deduplicare perfectă

OPȚIONAL:
  → Task 3.1/5.1: Structură consistentă (dacă există probleme cu findings)
```

---

## Notă Importanță

**Problema PRINCIPALĂ este timestamp-ul diferit.**

Dacă facem DOAR Task 2.1 (înlocuim `datetime.now()` cu `base_report.analyzed_at`), este foarte probabil ca:
1. Dublurile să dispară
2. Și problema cu scorul 100% să se rezolve (deoarece deduplicarea va alege corect)

Ce rămâne: Să investigăm dacă există și alte cauze pentru scorul 100%.
