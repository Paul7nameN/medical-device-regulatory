## Why

**Problema actuală:** Dashboard-ul doar afișează rezultatele validării bazate pe reguli, dar nu oferă insights inteligente.

```
┌─────────────────────────────────────────────────────────────────────────┐
│         SITUAȚIA ACTUALĂ                                              │
└─────────────────────────────────────────────────────────────────────────┘

  Utilizatorul încarcă un fișier:
  ┌─────────────────┐
  │  .txt sau .png  │
  └────────┬────────┘
           │
           ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │  Rule-based Validation (EXISTENT - deja funcționează)             │
  │                                                                       │
  │  Output:                                                              │
  │  • violations[]: [REG-TEMP-1, REG-SENS-3, ...]                     │
  │  • compliance_score: 65%                                              │
  │  • counts: passed=23, failed=5, critical=2                          │
  └─────────────────────────────────────┬───────────────────────────────┘
                                        │
                                        ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │  Dashboard (static)                                                  │
  │                                                                       │
  │  ┌──────────┐ ┌──────────┐ ┌──────────┐                           │
  │  │  Chart   │ │Violations│ │  Score   │                           │
  │  │ (temp)   │ │  Table   │ │  65%     │                           │
  │  └──────────┘ └──────────┘ └──────────┘                           │
  │                                                                       │
  │  PROBLEMĂ:                                                            │
  │  ❌ Utilizatorul trebuie să INTERPRETEZE singur datele              │
  │  ❌ Nu vede PATTERN-URI ascunse (ex: usa → incălzire)              │
  │  ❌ Nu are CORELAȚII între variabile                                 │
  │  ❌ Nu are PREDICȚII ("ce se va întâmpla?")                          │
  │  ❌ Nu are un PLAN DE ACȚIUNE structurat                             │
  │  ❌ Nu poate pune ÎNTREBĂRI suplimentare                            │
  └─────────────────────────────────────────────────────────────────────┘
```

**Ce lipsește:**

| Lipsă | Impact |
|-------|--------|
| Nu identifică pattern-uri ascunse | Utilizatorul nu vede că "usa deschisă → excursie termică în 15min" |
| Nu face corelații | Nu realizează că "voltage scăzut + temp crescută = baterie mode + eșec" |
| Nu are trend analysis | Nu observe că "senzorul B se îndepărtează de A cu 0.1°C → 0.8°C în 4h" |
| Nu are predictii | Nu poate anticipa "următoarea excursie ~ în 3 ore" |
| Nu are risk scoring | Doar spune "critical violation", nu "riscul total este 0.87, din care 40% din cauza senzorului" |
| Nu are action plan | Nu spune "ce trebuie să fac ACUM, în 24h, și pe termen lung" |
| Nu are interfață conversațională | Utilizatorul nu poate întreba "de ce e asta critic?" sau "compară cu ultima dată" |

---

## What Changes

**Soluția:** Adaugă un **AI Analyst Automat** care rulează după fiecare încărcare, plus un **Chat Bot Conversațional** pentru urmărire.

```
┌─────────────────────────────────────────────────────────────────────────┐
│         SOLUȚIA NOUĂ                                                  │
└─────────────────────────────────────────────────────────────────────────┘

  Utilizatorul încarcă un fișier:
  ┌─────────────────┐
  │  .txt sau .png  │
  └────────┬────────┘
           │
           ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │  Rule-based Validation (EXISTENT - neschimbat)                    │
  │                                                                       │
  │  Output:                                                              │
  │  • violations[]                                                      │
  │  • compliance_score                                                  │
  │  • counts                                                            │
  └─────────────────────────────────────┬───────────────────────────────┘
                                        │
                                        ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │  🤖 AI ANALYST AUTOMAT (NOU)                                        │
  │                                                                       │
  │  Input: Toate datele + thresholds + context normalizat             │
  │                                                                       │
  │  Ce analizează AUTOMAT:                                              │
  │  ┌─────────────┐  ┌─────────────┐  ┌───────────────────┐         │
  │  │ 🕵️ PATTERNS │  │ 🔗 CORRELA- │  │ 🔮 PREDICTIONS   │         │
  │  │ DETECTION   │  │    TIONS    │  │ & RISK SCORING    │         │
  │  └─────────────┘  └─────────────┘  └───────────────────┘         │
  │                                                                       │
  │  Output structurat:                                                  │
  │  • session_risk_overview (overall_score, risk_level, trend)        │
  │  • insights[] (cu priority, category, evidence, risk_contribution)  │
  │  • predictions[] (cu confidence, timeframe, risk_factors)           │
  │  • action_plan (immediate, short_term, long_term)                   │
  │  • natural_language_summary                                          │
  └─────────────────────────────────────┬───────────────────────────────┘
                                        │
                                        ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │  Dashboard NOU (cu AI)                                              │
  │                                                                       │
  │  ┌───────────────────────────────────────────────────────────────┐ │
  │  │  📊 Statics (vechiul dashboard)                                │ │
  │  │  • Chart temperatura                                           │ │
  │  │  • Violations table                                            │ │
  │  │  • Compliance score                                            │ │
  │  └───────────────────────────────────────────────────────────────┘ │
  │                                                                       │
  │  ┌───────────────────────────────────────────────────────────────┐ │
  │  │  🤖 AI INSIGHTS (NOU)                                          │ │
  │  │                                                                 │ │
  │  │  "Risc general: 0.87 (CRITICAL)                               │ │
  │  │   Trend: DETERIORATING                                         │ │
  │  │                                                                 │ │
  │  │   🔴 Senzorul SECONDARY a esuat (40% din risc)               │ │
  │  │      14 timeouts de la 14:32. SINGLE POINT OF FAILURE.        │ │
  │  │                                                                 │ │
  │  │   🟡 Pattern: Usa → Încălzire (25% din risc)                 │ │
  │  │      7 deschideri. În 5 cazuri: temp +2-3°C în 15min.        │ │
  │  │                                                                 │ │
  │  │   🔮 Predicție: 82% șansă de excursie >5min în ~3h           │ │
  │  │      Factorii: sistemul de racire stresat, pattern usa→temp" │ │
  │  └───────────────────────────────────────────────────────────────┘ │
  │                                                                       │
  │  ┌───────────────────────────────────────────────────────────────┐ │
  │  │  💬 Chat (NOU)                                                 │ │
  │  │                                                                 │ │
  │  │  [ "De ce e senzorul un risc critic?"             ] [ Trimite ]│ │
  │  │                                                                 │ │
  │  │  [ Sugestii rapide: ]                                          │ │
  │  │  [ Compară cu ultima săptămână ] [ Ce trebuie să fac? ]      │ │
  │  └───────────────────────────────────────────────────────────────┘ │
  │                                                                       │
  └─────────────────────────────────────────────────────────────────────┘
```

---

## Changes Detaliate

### 1. AI Analyst Engine (Backend)

**Ce va analiza:**

| Categorie | Ce caută | Exemplu |
|-----------|----------|---------|
| **Pattern Detection** | Relații cauza-efect | "Usa deschisă → temperatura crește cu 2-3°C în 15min" |
| **Correlations** | Corelații între variabile | "Voltage scăzut (~12V) + temp crescută = baterie mode + risc de eșec" |
| **Trend Analysis** | Tendințe în timp | "Deviatia senzori: 0.1°C → 0.8°C în 4h (deteriorare)" |
| **Anomaly Detection** | Deviații de la normal | "Fan speed 3000RPM dar temperatura tot crește (racire neeficientă)" |
| **Risk Scoring** | Scor de risc elaborat | "Risc total: 0.87, din care 40% senzor, 25% operational" |
| **Predictions** | Predicții pe baza pattern-urilor | "82% șansă de excursie >5min în următoarele 3h" |
| **Action Plan** | Plan de acțiune structurat | "Immediat: Verifică senzorul. Pe 24h: Monitorizează bateria." |

**Input către LLM (structurat JSON):**
```javascript
{
  "thresholds": {
    "safe_temp_range": [2.0, 8.0],
    "max_single_excursion_min": 5,
    "sensor_disagreement_max_celsius": 0.5,
    // ... toate pragurile din reguli
  },
  "systems_status": {
    "sensors": { primary_available, secondary_available, max_disagreement },
    "power": { voltage_range, voltage_avg, battery_drain_rate },
    "cooling": { fan_speed_range, recovery_activations },
    "environmental": { humidity_range, humidity_avg }
  },
  "operational_patterns": {
    "door_events": { count, events_per_hour, suspicious_gaps }
  },
  "timeline_critical_events": [
    { time, type, context, value }
  ],
  "rule_based_findings": [
    { rule_id, severity, message }
  ]
}
```

**Output de la LLM (structurat JSON):**
```javascript
{
  "session_risk_overview": {
    "overall_risk_score": 0.87,
    "risk_level": "CRITICAL",
    "primary_risk_category": "SENSOR_FAILURE",
    "trend_indicator": "DETERIORATING"
  },
  "insights": [
    {
      "id": "insight_1",
      "priority": "CRITICAL",
      "category": "sensor",
      "title": "Senzorul SECONDARY a esuat",
      "evidence": ["14 timeouts", "single point of failure"],
      "why_matters": "REG-SENS-1 cere redundanță",
      "risk_score_contribution": 0.40
    }
  ],
  "predictions": [
    {
      "scenario": "Excursie >5min",
      "confidence": 0.82,
      "timeframe": "~2.5-3.5h",
      "risk_factors": ["racire stresată", "pattern usa→temp"]
    }
  ],
  "action_plan": {
    "immediate_actions_0_1h": [...],
    "short_term_24h": [...],
    "long_term_maintenance": [...]
  },
  "natural_language_summary": "..."
}
```

### 2. Chat Bot Conversațional (Frontend + Backend)

**Ce va permite:**

| Capabilitate | Exemplu |
|--------------|---------|
| Întrebări despre insights | "De ce e asta un risc critic?" |
| Întrebări despre acțiuni | "Ce trebuie să fac mai întâi?" |
| Explicații ale regulilor | "Ce spune REG-TEMP-2 despre excursii?" |
| Comparații (opțional) | "Compară cu analiza de marti" |
| Generare conținut | "Scrie un email pentru manager" |

**Flow:**
```
Frontend Chat → POST /api/ai/chat → 
{
  "context": { current_analysis_session },
  "message": "De ce e senzorul un risc?"
}
  ↓
Backend trimite LLM:
  - Contextul analizei curente (insights, predictions)
  - Mesajul utilizatorului
  - Istoricul conversației (pentru context)
  ↓
Răspunsul ajunge înapoi la Frontend
```

### 3. Stocare în Bază de Date

**Ce va fi stocat:**
- `ai_analysis` tabel nou sau coloană în `analysis_sessions`
- `insights[]` - array JSON
- `predictions[]` - array JSON
- `risk_overview` - object JSON
- `action_plan` - object JSON
- `chat_history[]` - pentru conversații (dacă există)

---

## Capabilities Modificate

- `chart-image-data-extraction`: Include și AI analysis
- `analysis-sessions`: Include AI insights, risk scoring
- `compliance-reporting`: Include acțiuni recomandate de AI

---

## Impact

### Frontend
- **Nou: AI Insights Section** - afișează insights, predictions, risk score
- **Nou: Chat Component** - interfață conversațională
- **Modificat: Dashboard** - include secțiunea AI după upload

### Backend
- **Nou: `app/ai/analyst/`** - AI Analyst engine
  - `context_builder.py` - construiește contextul structurat pentru LLM
  - `analyst_engine.py` - interfața cu LLM
  - `prompts.py` - prompt-urile specializate
- **Nou: `POST /api/ai/chat`** - endpoint pentru chat
- **Modificat: `POST /api/ai/analyze-chart`** - include AI analysis
- **Modificat: `POST /api/reports/generate`** - include AI analysis
- **Modificat: `GET /api/analysis`** - include AI insights în răspuns

### Database
- **Nouă coloană sau tabelă** - pentru AI analysis data
- **Structură JSON** - pentru insights, predictions, action_plan

---

## Open Questions

1. **Chat history - între sesiuni?**
   - Opțiunea A: Doar în sesiunea curentă (memorie temporară)
   - Opțiunea B: Salvat în DB, persistent între sesiuni
   - **Decizie: A** - pentru început, simplu

2. **Format predictions - ce nivel de detaliu?**
   - Opțiunea A: Doar "82% în ~3h"
   - Opțiunea B: Elaborat, cu risk factors, mitigation potential
   - **Decizie: B** - conform discuției, vrei risk scoring elaborat

3. **Action plan - automat sau doar la cerere?**
   - Opțiunea A: Generat automat cu fiecare upload
   - Opțiunea B: Doar când utilizatorul cere
   - **Decizie: A** - conform discuției, vrei totul automat
