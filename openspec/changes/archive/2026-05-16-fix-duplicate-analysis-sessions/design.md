## Context

**Probleme confirmate în timpul explorării:**

1. **Două timestamp-uri diferite** pentru aceeași analiză:
   - `base_report.analyzed_at` → când se salvează în BD
   - `datetime.now()` → când se returnează răspunsul frontendului
   - Diferența de câțiva ms sau chiar secunde = deduplicare eșuată

2. **Două structuri diferite** pentru aceeași dată:
   - Salvat în BD: `base_report.to_dict()` → `ComplianceReport`
   - Returnat frontendului: `AggregatedComplianceReport`
   - Frontendul EXTRAGE și RECONSTRUIEȘTE datele → pot apărea neconcordanțe

3. **Posibilitatea scorului 100%:**
   - Frontend calculează: `if (total === 0) return 100`
   - Aceasta se poate întâmpla dacă:
     - Findings nu sunt corect extrase
     - Sau există o analiză "partial" cu `findings: []`

---

## Goals / Non-Goals

**Goals:**
1. **Un singur timestamp** pentru aceeași analiză (atât la salvare, cât și la retur)
2. **O singură structură** de date între ce se salvează și ce se returnează
3. **Eliminați dublurile** din istoric
4. **Scorul corect** (fără 100% eronat)

**Non-Goals:**
1. Nu refacem întreaga arhitectură
2. Nu schimbăm logica de validare sau agregare
3. Nu modificăm schema bazei de date

---

## Decisions

### Decizia 1: Ce timestamp să folosim?

**Opțiuni:**
1. **`base_report.analyzed_at`** (când s-a făcut validarea)
2. **Un nou timestamp creat la începutul funcției**
3. **`datetime.now()`** dar rotunjit la secunda

**Decizie:** Opțiunea 1 - `base_report.analyzed_at`

**Rationale:**
- Acesta există deja și este consistent
- Este determinist (același raport va avea același timestamp)
- Nu depinde de când rulează funcția (poate fi mai târziu după validare)

---

### Decizia 2: Ce structură să returnăm frontendului?

**Opțiuni:**

**Opțiunea A (Minimală):** Adaugă `base_report.to_dict()` în răspuns
- Păstrăm `AggregatedComplianceReport` pentru Dashboard (are mai multe info: temporal analysis, recomandări)
- Dar adăugăm și un nou câmp: `raw_validation_result: base_report.to_dict()`
- Frontendul folosește acest câmp pentru adăugarea în istoric

**Opțiunea B (Mai curată):** Folosește același `analyzed_at` în `AggregatedComplianceReport`
- Nu schimbăm structura răspunsului
- Doar schimbăm `generated_at` să fie egal cu `base_report.analyzed_at`
- Frontendul va trebui să construiască `LatestAnalysis` consistent

**Opțiunea C (Compromis):** Fă ambele
- Folosește același timestamp (Opțiunea B)
- Și/sau adaugă un ID unic pentru sesiune (`analysis_session_id`)

**Decizie:** Opțiunea C (Compromis) - cele două schimbări minore:

1. **Folosește `base_report.analyzed_at` ca `generated_at`** (sau adaugă un nou câmp cu acel timestamp)
2. **(Opțional, pentru siguranță):** Adaugă `analysis_session_id` în răspuns și folosește-l pentru deduplicare

---

## Fluxul Corect (După Fix)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FLUX CORECT (DUPĂ FIXURI)                            │
└─────────────────────────────────────────────────────────────────────────┘

  User uploadă .txt:
  ─────────────────────────

  [Backend] reports.py
       │
       ├─► base_report = engine.validate()
       │       → analyzed_at: "2026-05-16T13:17:33.625281"
       │
       ├─► save_analysis_session(report=base_report, ...)
       │       → _latest_analysis_data.analyzedAt = același timestamp!
       │
       ├─► aggregated = aggregator.aggregate(base_report, ...)
       │
       └─► return {
              report: aggregated,
              generated_at: base_report.analyzed_at,  ← ACELAȘI TIMESTAMP!
              analysis_session_id: session.id,        ← (opțional) ID UNIC
           }

  [Frontend]
       │
       ├─► Primește generated_at = ACELAȘI timestamp cu cel din BD
       │
       ├─► La refresh:
       │     Din BD: analyzedAt = "2026-05-16T13:17:33.625281"
       │     Din localStorage: analyzedAt = "2026-05-16T13:17:33.625281"
       │
       └─► DEDUPLICARE REUȘEȘTE = NU MAI SUNT DOUBLE!
```

---

## Comparație: Înainte vs După

| Caz | Înainte | După |
|-----|---------|------|
| Timestamp salvat în BD | `base_report.analyzed_at` | `base_report.analyzed_at` (neschimbat) |
| Timestamp returnat frontend | `datetime.now()` (NOU!) | `base_report.analyzed_at` (ACELAȘI!) |
| Deduplicare | Eșuează (două timestamp-uri) | Reușește (un singur timestamp) |
| Dubluri în istoric | Da | Nu |
| Scor 100% eronat | Posibil | Eliminat (sau mult mai puțin probabil) |

---

## Risks / Trade-offs

| Risk | Mitigare |
|------|----------|
| Ce se întâmplă dacă doi rapoarte IDENTICI au același timestamp? | Adăugăm `analysis_session_id` (unic din BD) ca cheie suplimentară |
| Frontendul încă extrage findings din structura greșită | Opțional: Returnăm DIRECT `base_report.to_dict()` ca un nou câmp |
| `analyzed_at` poate fi null | Folosim fallback: dacă null, folosim `datetime.now()` |

---

## Open Questions

1. **Vrem să schimbăm numele câmpului `generated_at`?**
   - Păstrăm numele dar schimbăm valoarea?
   - Sau adăugăm un nou câmp `analyzed_at` cu valoarea corectă?

2. **Vrem să returnăm și `base_report.to_dict()` ca un câmp separat?**
   - Avantaj: Frontendul nu trebuie să construiască nimic
   - Dezavantaj: Răspunsul este mai mare (dar nu cu mult)

3. **Vrem să adăugăm `analysis_session_id` în `LatestAnalysis`?**
   - Avantaj: Deduplicare perfectă (ID unic din BD)
   - Dezavantaj: Mai multe modificări
