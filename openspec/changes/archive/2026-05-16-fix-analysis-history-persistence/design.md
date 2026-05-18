## Context

**Probleme confirmate:**
1. Frontend folosește `sessionStorage` în loc de `localStorage`
2. Răspunsul API `GET /api/analysis` NU include `latest_analysis_data`, deși datele sunt în BD
3. Consecință: După restart, istoricul dispare

**Ce există deja (nu trebuie reinventat):**
- Toate modelele sunt bune
- PersistenceService există și funcționează pentru scriere
- Endpoint-urile GET există
- Frontendul încearcă să încarce din backend

**Probleme:**
1. Scrierea merge, dar CITIREA nu returnează toate câmpurile
2. localStorage ar fi mai bun decât sessionStorage

---

## Goals / Non-Goals

**Goals:**
1. **Frontend:** Înlocuiește `sessionStorage` cu `localStorage` (100% sigur, fără riscuri)
2. **Backend:** Debughează și repară de ce `latest_analysis_data` nu apare în răspunsul API
3. **Frontend:** Adaugă logica de fallback - chiar dacă lipsește unele câmpuri, afișează ce există

**Non-Goals:**
1. Nu schimbăm logica de salvare în BD - aceasta funcționează
2. Nu schimbăm schema bazei de date
3. Nu refacem AnalysisContext - doar micșorări

---

## Decisions

### Decizia 1: Investighează Problema cu `config` în Backend

**Hipoteze:**

```
Hipoteza A: `config` este lazy loaded
═══════════════════════════════════════
Când facem:
  select(AnalysisSession).options(
    selectinload(AnalysisSession.device),
    selectinload(AnalysisSession.violations),
  )

Problema: `config` este un JSON coloană, dar poate că atunci când accesăm
`session.config` într-un context diferit (de ex. în funcția de serializare),
nu este încărcat.

Soluție:
  - Accesează `session.config` ÎN TIMP CE este încă în contextul DB session
  - Sau folosește umplere explicită: deferred / undeferred
```

```
Hipoteza B: `_latest_analysis_data` NU se salvează cu toate endpoint-urile
═══════════════════════════════════════════════════════════════════════════

Endpoint-uri:
  • POST /api/reports/generate → ✅ salvează _latest_analysis_data
  • POST /api/validate → ✅ salvează _latest_analysis_data
  • POST /api/logs/ingest → ???
  • POST /api/ai/analyze-chart → ❌ NU salvează deloc în AnalysisSession

Test: Sunt analizele din API create cu /api/reports/generate?
Răspuns: DA, numele device-ului este "medical_device_logs_1000" care vine
         din numele fișierului (fără extensia .txt)
```

```
Hipoteza C: `_latest_analysis_data` conține caracteristicile care produc
            probleme la serializare
═══════════════════════════════════════════════════════════════════════

Valoarea care se salvează:
{
  "deviceId": "...",
  "analyzedAt": "...",
  "rawLogs": ["..."],
  "validationResult": {
    "findings": [...],  // array mare
    "summary": {...}
  }
}

Problema: Nu cred - persistence.py folosește JSON normal.
```

**Plan de investigare:**

1. **Primul pas:** Adaugă logging în `_orm_session_to_list_item`:
   ```python
   def _orm_session_to_list_item(session) -> dict:
       print("DEBUG session.id:", session.id)
       print("DEBUG session.config:", session.config)
       print("DEBUG type(session.config):", type(session.config))
       
       config = session.config or {}
       latest_analysis_data = config.get("_latest_analysis_data")
       
       print("DEBUG latest_analysis_data exists:", latest_analysis_data is not None)
       ...
   ```

2. **Al doilea pas:** Verifică direct din BD cu SQL:
   ```sql
   SELECT id, config, config::text AS config_text 
   FROM analysis_sessions 
   ORDER BY created_at DESC 
   LIMIT 1;
   ```

3. **Al treilea pas:** Verifică dacă `config` este `deferred`:
   - Dacă modelul `AnalysisSession` are `deferred("config")`
   - Soluție: Adaugă `options(undefer(AnalysisSession.config))` în query

### Decizia 2: sessionStorage → localStorage ( fără întârziere )

**Acest lucru poate fi făcut IMEDIAT, fără aștepta investigația backend:**

| Avantaj localStorage | Dezavantaj (niciunul real) |
|---------------------|-----------------------------|
| Persistă după ce închizi tab-ul | Are limită de ~5MB (dar analyses nu sunt atât de mari) |
| Persistă după repornirea browserului | |
| Partajat între tab-uri | |

**De schimbat în AnalysisContext.tsx:**

```typescript
// TOATE aparițiile:
sessionStorage.getItem(...)    → localStorage.getItem(...)
sessionStorage.setItem(...)    → localStorage.setItem(...)
sessionStorage.removeItem(...) → localStorage.removeItem(...)
```

### Decizia 3: Frontend - Logică de Fallback Robustă

**Problema actuală în `backendItemToLatestAnalysis`:**

```typescript
function backendItemToLatestAnalysis(item: AnalysisSessionListItem): LatestAnalysis | null {
  const data = itemRecord.latest_analysis_data
  
  if (!data) {
    console.log('⚠️ missing latest_analysis_data')
    return null  // ← PROBLEMA: returnează NULL!
  }
  ...
}
```

**Soluție:** Dacă `latest_analysis_data` lipsește, dar avem alte informații:

```
Ce avem în răspuns chiar fără latest_analysis_data:
  • id
  • device_name
  • status
  • created_at
  • completed_at
  • result_summary
  • violation_count

Ce putem afișa:
  • Istoricul cu nume, dată, număr de violations
  • Când userul dă click, încărcăm detaliile din GET /api/analysis/{id}
```

**Design fallback:**
```
Dacă latest_analysis_data există:
  → Creează LatestAnalysis complet (folosește-l direct)

Dacă latest_analysis_data NU există:
  → Creează un LatestAnalysis "parțial"
  → Folosește result_summary, violation_count, etc.
  → Marchează-l cu un flag: isPartial: true
  → Când userul dă click pe el, fetch-uiește GET /api/analysis/{id}
     (care va returna toate detaliile)
```

---

## Risks / Trade-offs

| Risk | Mitigare |
|------|----------|
| LocalStorage are limită de ~5MB | Fiecare analiză ~50-100KB. Poți avea 50-100 analize înainte de limită. Deja există și backend-ul ca sursă principală. |
| Downtime backend → frontendul nu vede istoricul | localStorage este acum backup. Dacă backendul nu răspunde, se folosește localStorage. |
| Conflict între localStorage și backend | La pornire: backend are prioritate, localStorage este fallback. Se mergează după `analyzedAt`. |

---

## Investigation Steps (Acțiune Imediată)

Înainte de a scrie cod, trebuie să înțelegem EXACT care este cauza problemei cu `latest_analysis_data`.

### Pasul 1: Verifică SQL direct

Rulează în PostgreSQL (sau în pgAdmin, sau în Docker):

```sql
-- Vezi ce este în coloana config
SELECT 
  id, 
  device_id, 
  created_at, 
  config IS NOT NULL AS has_config,
  jsonb_typeof(config) AS config_type,
  config ? '_latest_analysis_data' AS has_latest_data,
  left(config::text, 500) AS config_preview
FROM analysis_sessions 
ORDER BY created_at DESC 
LIMIT 3;
```

### Pasul 2: Adaugă logging temporar în backend

Editează `backend/app/api/validate.py`, funcția `_orm_session_to_list_item`:

```python
def _orm_session_to_list_item(session) -> dict:
    # DEBUG
    import sys
    print(f"\n{'═'*60}", file=sys.stderr)
    print(f"DEBUG _orm_session_to_list_item", file=sys.stderr)
    print(f"  session.id = {session.id}", file=sys.stderr)
    print(f"  session.config type = {type(session.config)}", file=sys.stderr)
    print(f"  session.config value = {session.config}", file=sys.stderr)
    print(f"{'═'*60}\n", file=sys.stderr)
    # END DEBUG
    
    # ... restul funcției
```

Apoi repornește backendul și accesează `/api/analysis`. Vezi ce apare în loguri.

### Pasul 3: Verifică modelul ORM

Verifică `backend/app/models/orm.py` la clasa `AnalysisSession`:

```python
class AnalysisSession(UUIDMixin, TimestampMixin, Base):
    # ...
    config: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )
    # Sau este ceva de genul deferred?
```

---

## Implementation Plan

### Ordinea recomandată:

```
FAZĂ ÎNTÂI: localStorage (sigur, fără risc)
    │
    ▼
INVESTIGHEAZĂ: Ce se întâmplă cu config-ul
    │
    ▼
REPARĂ: Backendul să returneze latest_analysis_data
    │
    ▼
OPȚIONAL: Fallback robust în frontend (pentru viitor)
```
