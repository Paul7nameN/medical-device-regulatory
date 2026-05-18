## 1. Backend: Creează PersistenceService

- [x] 1.1 Creează director `app/services/` (dacă nu există)
- [x] 1.2 Creează `app/services/persistence.py` cu clasa `PersistenceService`
- [x] 1.3 Implementează metoda `save_analysis_session()`:
  - Creează/încarcă Device (după device_id)
  - Creează AnalysisSession cu status PENDING
  - Creează LogEntry pentru fiecare intrare din logs
  - Creează DetectedViolation pentru fiecare finding eșuat
  - Actualizează AnalysisSession la COMPLETED + completed_at
  - Commit toate într-o singură tranzacție
- [x] 1.4 Implementează metoda `get_analysis_sessions(limit, offset)`:
  - Returnează lista AnalysisSession cu Device și Violations (eager load)
  - Ordine descrescătoare după created_at
- [x] 1.5 Implementează metoda `get_analysis_session(id)`:
  - Returnează Analiza completă cu toate LogEntry și DetectedViolation asociate
- [x] 1.6 Implementează metoda `save_compliance_report()`:
  - Salvează ComplianceReport din aggregated_report
- [x] 1.7 Implementează metoda `get_reports(limit, offset)`:
  - Lista rapoartelor cu device
- [x] 1.8 Implementează metoda `log_audit(action, actor, resource_type, resource_id, description, old_value, new_value, request_context)`:
  - Creează AuditLog (fără nicio posibilitate de update ulterior)
- [x] 1.9 Adaugă `__init__.py` în `app/services/`

## 2. Backend: Migrație pentru AuditLog Imutabilitate

- [x] 2.1 Creează migrație nouă cu `alembic revision -m "add_audit_log_immutability_rules"`
  - Notă: Folosește RLS (Row Level Security) în loc de RULEs - abordare modernă și echivalentă
  - Migrarea există deja: `migrations/versions/0002_audit_log_immutability.py`
- [x] 2.2 Adaugă în `upgrade()`:
  - `ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;`
  - `ALTER TABLE audit_log FORCE ROW LEVEL SECURITY;`
  - Polici pentru SELECT și INSERT, FĂRĂ politici UPDATE/DELETE = implicit interzis
- [x] 2.3 Adaugă în `downgrade()`:
  - Dezactivează RLS și elimină politicile
- [x] 2.4 Rulează migrarea: `alembic upgrade head`
  - Notă: Migrarea face parte din schema inițială 0002

## 3. Backend: Conectează Endpoint-urile la Persistență

- [x] 3.1 Modifică `app/api/validate.py`:
  - Injectează `get_async_db` ca dependință
  - După ce `engine.validate()` returnează, apelează `PersistenceService.save_analysis_session()`
  - Adaugă `audit_log` cu `action="ANALYSIS_CREATED"`
  - Asigură-te că toate sunt în aceeași tranzacție sau rollback corect
- [x] 3.2 Modifică `app/api/reports.py`:
  - Injectează DB session
  - Salvează folosind `save_analysis_session()` (înainte de agregare, cu base_report și raw_logs)
  - Acesta este endpoint-ul folosit de `FileUploadZone`
- [x] 3.3 Modifică `app/api/logs.py`:
  - Injectează DB session
  - După parsare, salvează LogEntry în baza de date
  - Adaugă audit_log cu `action="LOGS_INGESTED"` (folosește CREATE)
  - Adaugă și endpoint GET `/api/logs` (vezi §4.5)

## 4. Backend: Creează Endpoint-uri GET

- [x] 4.1 Adaugă în `app/api/validate.py` sau endpoint nou:
  - `GET /api/analysis` → listă analizelor paginate
  - Query params: `limit` (default 20), `offset` (default 0), `device_id` (opțional)
  - Response include: id, device_id, status, created_at, completed_at, summary (număr findings)
- [x] 4.2 `GET /api/analysis/{id}` → analiză completă
  - Include: toate logurile, toate findings, config-ul
  - Format similar cu ceea ce returnează `POST /validate`
- [x] 4.3 Adaugă în `app/api/reports.py`:
  - `GET /api/reports` → listă rapoartelor
  - Query params: `limit`, `offset`, `device_id`
- [x] 4.4 `GET /api/reports/{id}` → raport complet
- [x] 4.5 Adaugă în `app/api/logs.py`:
  - `GET /api/logs` → listă logurilor
  - Query params: `device_id` (opțional), `start_date`, `end_date`, `limit`, `offset`
  - Poate fi folosit pentru debug și pentru a re-exporta logurile

## 5. Backend: Teste Persistență

- [ ] 5.1 Creează `tests/test_persistence.py`
- [ ] 5.2 Testează `save_analysis_session()`:
  - Creează analiză, verifică că există în BD
  - Verifică că logurile sunt salvate
  - Verifică că violations sunt salvate
- [ ] 5.3 Testează `get_analysis_sessions()`:
  - Paginația funcționează
  - Filtrarea după device_id funcționează
- [ ] 5.4 Testează imutabilitatea AuditLog:
  - Încearcă să faci UPDATE pe un AuditLog → trebuie să eșueze sau să nu schimbe nimic
  - Încearcă DELETE → trebuie să nu ștergă

## 6. Frontend: Extinde Api Client

- [x] 6.1 Identifică unde sunt definite apelurile API (probabil `frontend/src/lib/api/`)
- [x] 6.2 Adaugă funcții noi:
  - `getAnalysisList(limit?, offset?, deviceId?)` → GET /api/analysis
  - `getAnalysis(id)` → GET /api/analysis/{id}
  - `getReports(limit?, offset?, deviceId?)` → GET /api/reports
  - `getReport(id)` → GET /api/reports/{id}
  - `getLogs(deviceId?, startDate?, endDate?)` → GET /api/logs
- [x] 6.3 Adaugă tipuri TypeScript pentru răspunsuri (dacă nu există deja)

## 7. Frontend: Modifică AnalysisContext

- [x] 7.1 Adaugă stare pentru `isLoadingHistory` (pentru loader)
- [x] 7.2 Adaugă `useEffect([])` care se execută o dată la mount:
  1. Fetch `getAnalysisList(limit=100)`
  2. Convertește din format backend → `LatestAnalysis`
  3. Compară cu sessionStorage (după analyzed_at)
  4. Merge: backend are prioritate, dar se păstrează și item-urile locale care nu sunt în BD
  5. Actualizează `analysisHistory`
- [x] 7.3 Modifică `addAnalysis()`:
  - Backendul salvează ACUM în `/api/reports/generate`
  - SessionStorage rămâne ca cache/fallback
  - La reload, se încarcă din backend
- [ ] 7.4 Adaugă funcționalitate de "Sincronizează" (opțional pentru viitor):
  - Buton sau acțiune care salvează analizele locale nesincronizate în BD
  - Fiecare în parte, cu `POST /api/validate` pentru fiecare

## 8. Frontend: UI pentru Istoric

- [ ] 8.1 (Dacă nu există deja) Adaugă indicator vizual pentru "sincronizat" vs "nesincronizat"
- [ ] 8.2 La începutul paginii, afișează "Se încarcă istoricul..." dacă `isLoadingHistory`
- [ ] 8.3 (Opțional) Adaugă buton "Load More" dacă sunt mai multe analize

## 9. Testare End-to-End

- [ ] 9.1 Rulează flow complet:
  1. Upload fișier log
  2. Verifică că apare în lista de analize
  3. **Repornește backendul**
  4. **Închide tab-ul și redeschide**
  5. Verifică că analiza ESTE ÎNCĂ acolo (se încarcă din BD)
- [ ] 9.2 Verifică că există date în BD cu SQL:
  - `SELECT COUNT(*) FROM analysis_sessions;`
  - `SELECT COUNT(*) FROM log_entries;`
  - `SELECT COUNT(*) FROM detected_violations;`
- [ ] 9.3 Testează paginația:
  - Creează 25 de analize
  - Verifică că primele 20 apar
  - Click "Load More", apar următoarele 5

## 10. Curățare și Documentație

- [ ] 10.1 Șterge orice cod comentat sau neutilizat
- [ ] 10.2 Adaugă comentarii supline în `PersistenceService` dacă este nevoie (deja bine comentat)
- [x] 10.3 Adaugă un endpoint `GET /api/health/db` care returnează statusul conexiunii la BD
  - Include și statistici: număr devices, analysis_sessions, compliance_reports

---

### Notă Importanță

**Acest change rezolvă o problemă CRITICĂ:**
- Înainte: TOATE datele dispareau după restart
- După: TOATE datele sunt permanente în PostgreSQL
- Audit logul este IMUTABIL (cerință standard pentru dispozitive medicale și sisteme de audit)

**Ordinea de implementare este importantă:**
1. Fă mai întâi backendul (PersistenceService + endpoint-uri)
2. Testează că backendul salvează corect cu POSTMAN / curl
3. Abia apoi modifică frontendul

Dacă vrei, putem împărți change-ul în 2 change-uri separate:
- `backend-data-persistence` (doar backend)
- `frontend-connect-to-backend` (doar frontend)
