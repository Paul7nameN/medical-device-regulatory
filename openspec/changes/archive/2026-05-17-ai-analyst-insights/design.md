## Context

**Situația actuală:**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FLUX ACTUAL FĂRĂ AI ANALYST                       │
└─────────────────────────────────────────────────────────────────────────┘

  Utilizatorul încarcă un fișier:

  1. Frontend: FileUploadZone.tsx
     ┌──────────────────────────────────────────────────────────────┐
     │ .txt → reportsApi.generateFromLogs()                       │
     │ .png → aiApi.analyzeChart()                                 │
     └──────────────────────────────┬───────────────────────────────┘
                                    │
                                    ▼
  2. Backend: Rule-based Validation
     ┌──────────────────────────────────────────────────────────────┐
     │ RegulatoryEngine.validate()                                 │
     │ → ComplianceReport with findings[]                          │
     │                                                              │
     │ persistence.save_analysis_session()                         │
     │ → salvează în DB: config cu _latest_analysis_data          │
     └──────────────────────────────┬───────────────────────────────┘
                                    │
                                    ▼
  3. Frontend: refreshHistory()
     ┌──────────────────────────────────────────────────────────────┐
     │ GET /api/analysis                                            │
     │ → Încarcă doar ce a salvat Rule-based Engine               │
     └──────────────────────────────┬───────────────────────────────┘
                                    │
                                    ▼
  4. Dashboard: Static Display
     ┌──────────────────────────────────────────────────────────────┐
     │ • Chart temperatura                                          │
     │ • Violations Table (reguli)                                 │
     │ • Compliance Score                                           │
     │                                                              │
     │ ❌ FĂRĂ: Insights, Patterns, Correlations,                 │
     │          Predictions, Risk Scoring, Action Plan            │
     └──────────────────────────────────────────────────────────────┘
```

---

## Goals / Non-Goals

**Goals:**
1. **AI Analyst Automat** - Rulează după fiecare upload, fără intervenție
2. **Context Builder** - Transformă datele brute în structură JSON pentru LLM
3. **Rich Analysis** - Patterns, correlations, trends, anomalies
4. **Risk Scoring Elaborat** - Cu breakdown pe categorii și contribuții
5. **Predictions** - Pe baza pattern-urilor din sesiunea curentă
6. **Action Plan** - Structurat pe 3 niveluri: imediat, 24h, lungă durată
7. **Chat Bot** - Interfață conversațională pentru urmărire
8. **Compatibilitate** - Nu modifică fluxul existent, doar adaugă peste el

**Non-Goals:**
1. **Nu compară cu istoricul** - Doar sesiunea curentă (conform discuției)
2. **Nu modifică regulile existente** - Rule-based engine rămâne neschimbat
3. **Nu RAG (momentan)** - Fără baza de cunoștințe regulatorii indexată
4. **Nu streaming** - Doar request-response complet (simplu pentru început)
5. **Nu chat persistent între sesiuni** - Doar în sesiunea curentă

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                         ARHITECTURA AI ANALYST                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────┘

     ┌───────────────────────────────────────────────────────────────────────────────────────┐
     │                              FRONTEND                                                  │
     └───────────────────────────────────────────────────────────────────────────────────────┘

     ┌──────────────────────┐      ┌──────────────────────┐      ┌──────────────────────┐
     │  FileUploadZone      │      │  Dashboard (cu AI)   │      │  Chat Component      │
     │  (neschimbat)        │      │                      │      │  (NOU)               │
     └──────────┬───────────┘      └───────────┬──────────┘      └───────────┬──────────┘
                │                              │                              │
                │ .txt/.png upload            │ Afișează:                    │ Trimitere:
                │                              │ • Static dashboard            │ POST /api/ai/chat
                ▼                              │ • AI Insights                 │
     ┌───────────────────────────────────────────┐     ┌─────────────────────────────────┐
     │        REFRESH HISTORY                    │     │  AFIȘEAZĂ DIN RĂSPUNS:        │
     │  GET /api/analysis                        │     │                                │
     │                                            │     │  • risk_overview              │
     │  Include ACUM și:                         │     │  • insights[]                 │
     │  • ai_risk_overview                       │     │  • predictions[]              │
     │  • ai_insights[]                          │     │  • action_plan                │
     │  • ai_predictions[]                       │     │  • natural_language_summary   │
     │  • ai_action_plan                         │     │                                │
     │  • ai_generated_at                        │     └─────────────────────────────────┘
     └──────────────────────┬─────────────────────┘
                            │
                            ▼
     ┌───────────────────────────────────────────────────────────────────────────────────────┐
     │                              BACKEND                                                   │
     └───────────────────────────────────────────────────────────────────────────────────────┘

     ┌───────────────────────────────────────────────────────────────────────────────────────┐
     │  1. EXISTENT (neschimbat):                                                            │
     │                                                                                        │
     │  .txt → POST /api/reports/generate                                                    │
     │  .png → POST /api/ai/analyze-chart                                                   │
     │                                                                                        │
     │  Ambele trec prin:                                                                    │
     │  • Rule-based Validation → ComplianceReport                                           │
     │  • persistence.save_analysis_session() → salvează în DB                             │
     └──────────────────────────────┬────────────────────────────────────────────────────────┘
                                    │
                                    ▼ (ADĂUGARE NOUĂ - după salvare)
     ┌───────────────────────────────────────────────────────────────────────────────────────┐
     │  2. AI ANALYST ENGINE (NOU):                                                          │
     │                                                                                        │
     │  După ce Rule-based a salvat, ACUM se execută și AI Analyst:                        │
     │                                                                                        │
     │  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
     │  │  A. ContextBuilder (NOU: app/ai/analyst/context_builder.py)                  │ │
     │  │                                                                                   │ │
     │  │  Input: LogEntry[] + Normalizer Context + ComplianceReport                      │ │
     │  │  Output: Structured JSON context pentru LLM                                      │ │
     │  │                                                                                   │ │
     │  │  {                                                                                 │ │
     │  │    "thresholds": { safe_temp_range, max_excursion, ... },  // praguri constante │ │
     │  │    "session_overview": { duration_hours, counts },                              │ │
     │  │    "systems_status": { sensors, power, cooling, environmental },               │ │
     │  │    "operational_patterns": { door_events },                                    │ │
     │  │    "timeline_critical_events": [ {time, type, context} ],                     │ │
     │  │    "rule_based_findings": [ {rule_id, severity, message} ]                    │ │
     │  │  }                                                                                 │ │
     │  └─────────────────────────────────────────────────────────────────────────────────┘ │
     │                                    │                                                   │
     │                                    ▼                                                   │
     │  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
     │  │  B. AnalystEngine (NOU: app/ai/analyst/engine.py)                             │ │
     │  │                                                                                   │ │
     │  │  Interfață cu LLM (folosește ModelArkClient existent):                          │ │
     │  │                                                                                   │ │
     │  │  Flow:                                                                             │ │
     │  │  1. Încarcă prompt-ul specializat (din prompts.py)                               │ │
     │  │  2. Injectează contextul structurat în prompt                                    │ │
     │  │  3. Apelează LLM cu format JSON strict pentru output                             │ │
     │  │  4. Parsează răspunsul JSON                                                      │ │
     │  │  5. Validează schema de răspuns                                                  │ │
     │  │  6. Salvează în DB (împreună cu analysis_session)                               │ │
     │  └─────────────────────────────────────────────────────────────────────────────────┘ │
     │                                                                                        │
     └──────────────────────────────┬────────────────────────────────────────────────────────┘
                                    │
                                    ▼
     ┌───────────────────────────────────────────────────────────────────────────────────────┐
     │  3. PERSISTENCE (MODIFICAT):                                                          │
     │                                                                                        │
     │  save_analysis_session() ACUM include și AI analysis:                                │
     │                                                                                        │
     │  În config:                                                                            │
     │  {                                                                                     │
     │    "_latest_analysis_data": { ... },  // existent                                     │
     │    "_ai_analysis": {                // NOU                                             │
     │      "risk_overview": { overall_score, risk_level, trend },                          │
     │      "insights": [ ... ],                                                             │
     │      "predictions": [ ... ],                                                          │
     │      "action_plan": { ... },                                                          │
     │      "natural_language_summary": "..."                                                │
     │    }                                                                                   │
     │  }                                                                                     │
     │                                                                                        │
     │  SAU: O coloană separată `ai_analysis` în `analysis_sessions`?                       │
     │  Decizie: Folosim config pentru simplitate (ca și _latest_analysis_data)            │
     └──────────────────────────────┬────────────────────────────────────────────────────────┘
                                    │
                                    ▼
     ┌───────────────────────────────────────────────────────────────────────────────────────┐
     │  4. API ENDPOINTS (MODIFICAȚI + NOI):                                                 │
     │                                                                                        │
     │  MODIFICATE:                                                                           │
     │  • POST /api/reports/generate - include AI analysis după rule-based                  │
     │  • POST /api/ai/analyze-chart - include AI analysis după rule-based                 │
     │  • GET /api/analysis - include ai_analysis din config în răspuns                    │
     │                                                                                        │
     │  NOI:                                                                                  │
     │  • POST /api/ai/chat - pentru interfața conversațională                              │
     │                                                                                        │
     │    POST /api/ai/chat                                                                   │
     │    {                                                                                   │
     │      "analysis_session_id": "uuid",     // opțional - pentru context                 │
     │      "message": "De ce e asta un risc?",                                             │
     │      "chat_history": [                    // pentru conversații cu multiple tururi    │
     │        {"role": "user", "content": "..."},                                           │
     │        {"role": "assistant", "content": "..."}                                        │
     │      ]                                                                                 │
     │    }                                                                                   │
     │                                                                                        │
     │    Răspuns:                                                                            │
     │    {                                                                                   │
     │      "message": "Răspunsul AI-ului în limbaj natural",                               │
     │      "sources": [...],                    // referințe la insights dacă e cazul      │
     │      "actions": [...]                     // acțiuni sugerate dacă e cazul           │
     │    }                                                                                   │
     └───────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Decisions

### Decizia 1: Când rulează AI Analyst?

**Opțiuni:**

| Opțiune | Când rulează | Avantaje | Dezavantaje |
|---------|--------------|----------|-------------|
| **A (Recomandată)** | După fiecare upload, imediat după rule-based | Utilizatorul vede rezultatele imediat | Mai multe cheltuieli API |
| B | La cererea utilizatorului ("Analyze with AI" button) | Mai puține cheltuieli | Utilizatorul poate nu știe că există |
| C | Async, după răspuns | Utilizatorul primește răspuns rapid | Complexitate suplimentară |

**Decizie FINALĂ: Opțiunea A**

**Rationale:**
1. Utilizatorul vrea AI AUTOMAT (conform discuției)
2. Experiența este mai bună când totul este disponibil imediat
3. Cheltuielile API sunt acceptabile pentru un tool de acest tip
4. Pattern: Asemănător cu cum rule-based rulează automat

### Decizia 2: Unde injectăm AI Analyst în flux?

**Opțiuni:**

```
Opțiunea A: În interiorul persistence.save_analysis_session()

  + Un singur loc pentru toate upload-urile
  - Nu are acces la context complet (log entries, normalizer)

Opțiunea B: După persistence, în fiecare endpoint separat

  POST /api/reports/generate:
    1. Rule-based → ComplianceReport
    2. persistence.save_analysis_session()
    3. 🔴 NOU: AIAnalystEngine.analyze()
    4. Actualizează session cu ai_analysis
    5. Returnează răspuns

  POST /api/ai/analyze-chart:
    1. ChartAnalyzer → ChartAnalysisResult
    2. Conversie → ComplianceReport
    3. persistence.save_analysis_session()
    4. 🔴 NOU: AIAnalystEngine.analyze()
    5. Actualizează session cu ai_analysis
    6. Returnează răspuns

  + Are acces la tot contextul
  + Mai flexibil
  - Cod duplicat în 2 endpoints (puțin, se poate extrage într-un helper)
```

**Decizie FINALĂ: Opțiunea B**

**Rationale:**
1. AI Analyst are nevoie de context COMPLET (LogEntry[], Normalizer Context, etc.)
2. persistence.save_analysis_session() nu are acces la toate acestea
3. Putem extrage logica într-un helper separat: `run_ai_analysis_and_save()`
4. Codul va fi similar în ambele endpoint-uri, dar puțin

### Decizia 3: Formatul răspunsului de la LLM

**Structura JSON (strictă):**

```javascript
{
  "session_risk_overview": {
    "overall_risk_score": 0.87,           // float 0.0-1.0
    "risk_level": "CRITICAL",              // "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    "primary_risk_category": "SENSOR_FAILURE",
    "imminent_concerns_count": 2,
    "trend_indicator": "DETERIORATING"     // "STABLE" | "IMPROVING" | "DETERIORATING"
  },

  "insights": [
    {
      "id": "insight_1",
      "priority": "CRITICAL",             // "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
      "category": "sensor",               // "sensor" | "power" | "cooling" | "operational" | "environmental"
      "title": "Senzorul SECONDARY a esuat",
      "evidence": [
        "14 timeouts înregistrate de la 14:32",
        "Senzorul PRIMARY rămâne singurul"
      ],
      "why_matters": "REG-SENS-1 cere redundanță. SINGLE POINT OF FAILURE.",
      "risk_score_contribution": 0.40,    // cât contribuie la riscul total
      "risk_factors": [
        {"factor": "No redundancy", "severity": "CRITICAL"},
        {"factor": "Pre-calibration drift", "severity": "HIGH"}
      ]
    }
  ],

  "predictions": [
    {
      "id": "pred_1",
      "scenario": "Excursie termică depășind 5 minute",
      "confidence": 0.82,
      "timeframe": "Următoarele 2.5 - 3.5 ore",
      "estimated_probability": "82%",
      "risk_factors_driving_this": [
        "Sistemul de racire sub stres (3 activări Recovery)",
        "Pattern: usa deschisa → excursie in ~15min",
        "Posibilă blocare a unei usi"
      ],
      "mitigation_potential": "Daca se reduce accesul, probabilitatea scade la ~15%",
      "why_concerning": "Daca are loc, violeaza REG-TEMP-2 (max 5min excursie)"
    }
  ],

  "action_plan": {
    "summary": "Situatie CRITICAL. Senzorul SECONDARY a esuat.",

    "immediate_actions_0_1h": [
      {
        "action": "Verifica senzorul SECONDARY",
        "priority": "CRITICAL",
        "steps": [
          "1. Verifica cablul",
          "2. Inspecteaza daune fizice",
          "3. Restarteaza daca posibil"
        ],
        "why_needed": "Redundanta este pierduta. Orice esuire a PRIMARY = catastrofa."
      }
    ],

    "short_term_24h": [
      {
        "action": "Monitorizeaza tensiunea si bateria",
        "priority": "HIGH",
        "rationale": "Voltajul indica modul baterie. Rata de descarcare: ~1%/ora."
      }
    ],

    "long_term_maintenance": [
      {
        "action": "Revizuire procedura SOP acces",
        "priority": "MEDIUM",
        "rationale": "7 deschideri in 2.5h. Considera: training, minimizare timp usa deschisa."
      }
    ]
  },

  "natural_language_summary": "In aceasta sesiune, am identificat doua probleme CRITICE: ..."
}
```

**Validare:**
- Folosim JSON Schema pentru a valida răspunsul
- Dacă un câmp lipsește sau are format greșit, avem fallback-uri
- `natural_language_summary` este important pentru UX - afișat direct în dashboard

### Decizia 4: Chat Bot - Context și Memorie

**Ce context are chat-ul la dispoziție:**

| Context | Disponibil | Note |
|---------|------------|------|
| AI Analysis curent | ✅ | insights, predictions, action_plan, risk_overview |
| Rule-based findings | ✅ | Din compliance report |
| Istoric conversație | ✅ | Doar în sesiunea curentă (memorie) |
| Analize din trecut | ❌ | Conform deciziei - nu comparăm cu istoric |
| Reguli MED-THERM | ⚠️ | Parțial, prin prompt-uri (nu RAG) |

**Memorie:**
- Doar în sesiunea curentă (în memoria browserului)
- Nu salvăm chat history în DB (pentru simplitate)
- Frontendul trimite `chat_history` la fiecare request

**Flow Chat:**
```
Frontend:
  • Arată mesajele
  • Menține history în state
  • La submit: trimite message + history + analysis_session_id

Backend POST /api/ai/chat:
  1. Încarcă AI Analysis din DB (după analysis_session_id)
  2. Construiește prompt-ul cu:
     • Contextul AI Analysis (insights, predictions, etc.)
     • Istoricul conversației
     • Mesajul curent
  3. Apelează LLM
  4. Parsează răspunsul
  5. Returnează către frontend

Frontend:
  • Adaugă răspunsul în history
  • Afișează
```

---

## Implementation Plan

### Etapa 1: Construiește ContextBuilder

**Creează:** `backend/app/ai/analyst/`

1. **`context_builder.py`**
   - Ia LogEntry[] + Normalizer Context + ComplianceReport
   - Construiește structura JSON pentru LLM
   - Include thresholds (din constantă)
   - Include systems_status (sensors, power, cooling, environmental)
   - Include operational_patterns (door events)
   - Include timeline_critical_events
   - Include rule_based_findings

2. **`prompts.py`**
   - Prompt specializat pentru AI Analysis
   - Include instrucțiuni pentru format JSON strict
   - Include exemple de răspunsuri corecte
   - Prompt pentru chat (separat)

### Etapa 2: Construiește AnalystEngine

3. **`engine.py`**
   - Folosește ModelArkClient existent
   - Implementează: `analyze_logs(context)`
   - Implementează: `analyze_chart(context)` 
   - Validează JSON-ul întors
   - Fallback-uri pentru câmpuri lipsă

4. **`schemas.py`** (opțional)
   - JSON Schema pentru validare
   - Sau folosește Pydantic models

### Etapa 3: Modifică Endpoint-urile

5. **`backend/app/api/reports.py`**
   - După `persistence.save_analysis_session()`:
   - Construiește context
   - Rulează AI Analyst
   - Actualizează analysis_session cu ai_analysis

6. **`backend/app/api/ai.py`**
   - Similar cu reports.py
   - După ce salvează, rulează AI Analyst
   - Actualizează session

7. **`backend/app/services/persistence.py`**
   - Adaugă metodă: `update_analysis_with_ai()`
   - Sau modifică `save_analysis_session()` să returneze session

### Etapa 4: API Chat

8. **Nou endpoint: `POST /api/ai/chat`**
   - Primțe: analysis_session_id, message, chat_history
   - Încarcă AI Analysis din DB
   - Construiește prompt cu context + history
   - Apelează LLM
   - Returnează răspuns

### Etapa 5: Frontend

9. **Dashboard AI Insights Section**
   - Componentă nouă pentru:
     - Risk Overview (score, level, trend)
     - Insights List (cu expandare pentru evidence)
     - Predictions List
     - Action Plan (3 tabs: Immediate, 24h, Long Term)
     - Natural Language Summary

10. **Chat Component**
    - Interfață de chat (similară cu ChatGPT, dar simplă)
    - Sugestii rapide ("Ce trebuie să fac?", "De ce e asta un risc?")
    - Istoric local în state

11. **API Client**
    - Adaugă în `frontend/src/lib/api/client.ts`:
    - `aiApi.chat()` pentru POST /api/ai/chat

### Etapa 6: Testare

12. **Teste cu loguri reale**
    - Folosește `docs/client/medical_device_logs_1000.txt`
    - Verifică că AI Analyst identifică:
      - Secondary sensor timeout
      - Voltage scăzut (baterie mode)
      - Pattern usa → incalzire
      - Etc.

---

## Risks

| Risk | Mitigare |
|------|----------|
| LLM nu returnează JSON valid | Schema validation + multiple reîncercări + fallback |
| Cheltuieli API prea mari | De rezolvat în producție: caching, rate limiting |
| Răspunsuri inconsistente | Prompt foarte specific cu exemple și format strict |
| Nu detectează pattern-uri corect | Teste cu loguri cunoscute, iterare pe prompt |
| Chat folosește context greșit | Include întotdeauna contextul complet în prompt |

---

## Dependencies

**Modificări:**
- `backend/app/api/reports.py` - Adaugă AI Analysis
- `backend/app/api/ai.py` - Adaugă AI Analysis + Chat endpoint
- `backend/app/services/persistence.py` - Metodă pentru update
- `frontend/src/lib/api/client.ts` - Adaugă chat

**Fișiere NOI:**
- `backend/app/ai/analyst/__init__.py`
- `backend/app/ai/analyst/context_builder.py`
- `backend/app/ai/analyst/engine.py`
- `backend/app/ai/analyst/prompts.py`

**Frontend Components NOI:**
- `frontend/src/components/AIAnalysis/`
- `frontend/src/components/AIChat/`
