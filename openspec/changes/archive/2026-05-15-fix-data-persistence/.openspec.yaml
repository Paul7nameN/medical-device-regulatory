## Why

**Problema CRITICĂ descoperită:**
Există un **gap total între arhitectura proiectată și implementarea reală**:

```
Ceea ce crezi că se întâmplă:          Ceea ce se întâmplă DE ADEVĂRAT:
┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│  PostgreSQL                     │       │  Doar sessionStorage Browser    │
│  • devices                      │       │                                 │
│  • analysis_sessions            │  ❌   │  • Rapoartele sunt ȘTERSE când │
│  • log_entries                  │  NICI │  • închizi tab-ul               │
│  • detected_violations          │  FOLOSIT│  • repornești backend          │
│  • compliance_reports           │       │  • cureți cache-ul              │
│  • audit_log                    │       └─────────────────────────────────┘
└─────────────────────────────────┘
```

**Detalii specifice:**
1. **Modelele ORM sunt definite** (`backend/app/models/orm.py`), dar **NICIODATĂ folosite** pentru scriere
2. **Toate endpoint-urile** (`/validate`, `/reports/generate`, `/logs/ingest`) doar returnează date - NU scriu în baza de date
3. **Frontendul folosește DOAR `sessionStorage`** - care se șterge automat când tab-ul este închis
4. **Consecință**: După repornirea backendului sau închiderea browserului, **TOATE datele dispar**, deși sistemul pare pregătit pentru persistență

**Impact pentru dispozitive medicale:**
- Pentru sisteme de monitorizare medicală, **istoricul trebuie să fie permanent**
- **Audit trail-ul** (care există definit ca model) trebuie să fie imutabil și disponibil
- Datele nu pot depinde de starea browserului sau a serverului

## What Changes

1. **Backend**: Adaugă logica de persistență în toate endpoint-urile
   - `/api/validate` → Salvează AnalysisSession + LogEntry + DetectedViolation
   - `/api/reports/generate` → Salvează ComplianceReport
   - `/api/logs/ingest` → Salvează LogEntry (deja parsat)

2. **Backend**: Creează endpoint-uri GET pentru citirea istoricului
   - `GET /api/analysis` → Lista tuturor analizelor
   - `GET /api/analysis/{id}` → Detalii analiză specifică
   - `GET /api/reports` → Lista rapoartelor
   - `GET /api/logs` → Cautare loguri

3. **Frontend**: Conectează AnalysisContext la backend
   - La pornire, încarcă istoricul din backend (NU doar din sessionStorage)
   - După fiecare analiză, salvează și în backend
   - `sessionStorage` devine doar cache, nu sursă unică de adevăr

4. **Backend**: Asigură imutabilitatea AuditLog
   - Adaugă trigger sau constraint ca `audit_log` să nu poată fi modificat niciodată

## Capabilities

### Modified Capabilities
- `log-storage`: De la "doar în memorie" la "persistent în PostgreSQL cu audit"
- `analysis-sessions`: De la "volatile" la "salvat automat în BD"
- `violation-tracking`: De la "pe durata sesiunii" la "istoric permanent"
- `compliance-reporting`: Adaugă generare + salvare + recuperare din BD

### New Capabilities
- `data-persistence-layer`: Strat unificat de salvare/recuperare date pentru toate modulele
- `audit-immutability`: Garanție că audit logul nu poate fi modificat niciodată

## Impact

- **Backend**:
  - `app/api/validate.py`: Adaugă DB session și salvare modele
  - `app/api/reports.py`: Adaugă salvare ComplianceReport
  - `app/api/logs.py`: Adaugă salvare LogEntry
  - **Noi endpoint-uri** GET pentru istoric
  - Poate un serviciu nou `app/services/persistence.py` pentru a evita duplicarea codului

- **Frontend**:
  - `lib/context/AnalysisContext.tsx`: La mount, fetch din backend
  - `lib/api/`: Noi funcții GET pentru `getAnalysisList()`, `getReportList()`, etc.
  - `sessionStorage`: Devine fallback/cache, nu sursă principală

- **Database**:
  - Nicio modificare schemă - toate modelele sunt deja definite!
  - Doar adăugare constraint pentru imutabilitate audit_log (opțional)
