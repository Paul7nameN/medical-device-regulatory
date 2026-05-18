## 1. Scaffold AI Analyst Module (Prioritate înaltă) ✅

- [x] 1.1 Creează directorul și modulele:
  - `backend/app/ai/analyst/__init__.py`
  - `backend/app/ai/analyst/context_builder.py`
  - `backend/app/ai/analyst/prompts.py`
  - `backend/app/ai/analyst/engine.py`
  - `backend/app/ai/analyst/models.py` (pentru Pydantic schema)

- [x] 1.2 Adaugă constantele pentru thresholds:
  - safe_temp_range: [2.0, 8.0]
  - max_single_excursion_min: 5
  - max_recovery_min: 3
  - sensor_disagreement_max_celsius: 0.5
  - max_door_events_per_hour: 10
  - battery_backup_required_hours: 4
  - Folosește aceleași valori ca din `backend/app/regulatory/rules/`

---

## 2. ContextBuilder - Construiește contextul pentru LLM ✅

- [x] 2.1 Creează Pydantic models pentru răspunsul AI:
  ```python
  class RiskOverview(BaseModel):
      overall_risk_score: float
      risk_level: str  # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
      primary_risk_category: str
      imminent_concerns_count: int
      trend_indicator: str  # "STABLE" | "IMPROVING" | "DETERIORATING"

  class InsightRiskFactor(BaseModel):
      factor: str
      severity: str

  class Insight(BaseModel):
      id: str
      priority: str
      category: str
      title: str
      evidence: List[str]
      why_matters: str
      risk_score_contribution: float
      risk_factors: List[InsightRiskFactor]

  class Prediction(BaseModel):
      id: str
      scenario: str
      confidence: float
      timeframe: str
      estimated_probability: str
      risk_factors_driving_this: List[str]
      mitigation_potential: Optional[str]
      why_concerning: Optional[str]

  class ActionItem(BaseModel):
      action: str
      priority: str
      steps: Optional[List[str]]
      why_needed: Optional[str]
      rationale: Optional[str]

  class ActionPlan(BaseModel):
      summary: str
      immediate_actions_0_1h: List[ActionItem]
      short_term_24h: List[ActionItem]
      long_term_maintenance: List[ActionItem]

  class AIAnalysisResult(BaseModel):
      session_risk_overview: RiskOverview
      insights: List[Insight]
      predictions: List[Prediction]
      action_plan: ActionPlan
      natural_language_summary: str
  ```

- [x] 2.2 Implementează `build_context()` function:
  - Input: `log_entries: List[LogEntry]`, `report: ComplianceReport`, `normalizer_context: Dict`
  - Output: Dict structurat conform design.md
  - Include: `thresholds`, `session_overview`, `systems_status`, `operational_patterns`, `timeline_critical_events`, `rule_based_findings`

- [x] 2.3 Extrage `systems_status`:
  - sensors: disponibilitate, deviația maximă observată
  - power: voltage range, avg, battery drain rate
  - cooling: fan speed range, recovery activations
  - environmental: humidity range, avg

- [x] 2.4 Construiește `timeline_critical_events`:
  - Parcurge logurile în ordine
  - Extrage evenimentele cheie: ALARM_TRIGGERED, SENSOR_TIMEOUT, DOOR_OPEN, TEMP_READING în afara range-ului
  - Le sortează cronologic

- [x] 2.5 Construiește `operational_patterns`:
  - Numără evenimentele usa per oră
  - Identifică "suspicious gaps": DOOR_OPEN fără DOOR_CLOSE
  - Caută pattern-uri: usa deschisă urmată de creștere temperaturii

---

## 3. Prompts pentru LLM ✅

- [x] 3.1 Creează promptul principal pentru AI Analysis:
  - Rol: "Tu ești un AI Analyst expert pentru medical cold chain"
  - Context: Include structura JSON, thresholds, exemple
  - Instrucțiuni: Ce să analizeze (patterns, correlations, trends, anomalies)
  - Output format: JSON strict conform AIAnalysisResult
  - Include exemple de răspunsuri

- [x] 3.2 Creează promptul pentru Chat:
  - Include contextul din AI Analysis (dacă există)
  - Include istoricul conversației
  - Instrucțiuni: Răspunde în limbaj natural, citează surse (insights) când relevant

---

## 4. AnalystEngine - Interfață cu LLM ✅

- [x] 4.1 Implementează clasa `AIAnalystEngine`:
  - Constructor: primește un client LLM (ModelArkClient)
  - Metodă: `analyze(context: Dict) -> AIAnalysisResult`

- [x] 4.2 Implementează fluxul:
  1. Încarcă prompt-ul
  2. Injectează contextul
  3. Apelează LLM cu `chat_completion()`
  4. Parsează JSON-ul din răspuns
  5. Validează cu Pydantic

- [x] 4.3 Adaugă fallback-uri și error handling:
  - Dacă JSON parsing eșuează → reîncearcă cu reminder despre format
  - Dacă validare Pydantic eșuează → valori default
  - Max 3 reîncercări

- [x] 4.4 Implementează metodă pentru chat:
  - `chat(ai_analysis: Optional[AIAnalysisResult], message: str, history: List[ChatMessage]) -> str`

---

## 5. Modifică PersistenceService ✅

- [x] 5.1 Verifică că `save_analysis_session()` returnează `AnalysisSession`:
  - (Ar trebui să returneze deja, conform codului existent)

- [x] 5.2 Adaugă metodă pentru a actualiza cu AI analysis:
  ```python
  async def update_analysis_with_ai(
      self,
      session_id: uuid.UUID,
      ai_analysis: AIAnalysisResult
  ) -> AnalysisSession:
  ```
  - Actualizează `config` cu `{"_ai_analysis": ai_analysis.dict()}`
  - Salvează în DB

---

## 6. Integrează în Endpoint-uri ✅

### Pentru .txt (reports/generate):

- [x] 6.1 Modifică `backend/app/api/reports.py`:
  - După `session = await persistence.save_analysis_session(...)`
  - Construiește context:
    - Ai deja `entries: List[LogEntry]`
    - Ai deja `base_report: ComplianceReport`
    - Ai nevoie de normalizer context (caută în RegulatoryEngine sau LogNormalizer)
  - Rulează AI Analyst
  - Actualizează session cu `update_analysis_with_ai()`

### Pentru .png (ai/analyze-chart):

- [x] 6.2 Modifică `backend/app/api/ai.py`:
  - Similar cu reports.py
  - Context va fi mai limitat (doar ChartAnalysisResult)
  - Dar tot avem: violations, data_points, chart_type
  - Construiește un context compatibil

- [x] 6.3 Asigură-te că AI Analysis rulează și pentru imagini:
  - Creează un context adapter pentru ChartAnalysisResult
  - Sau folosește un prompt separat pentru imagini

---

## 7. Actualizează GET /api/analysis ✅

- [x] 7.1 Modifică `backend/app/api/validate.py`:
  - În `_orm_session_to_list_item()`:
  - Extrage `_ai_analysis` din `config`
  - Include în răspuns dacă există

- [x] 7.2 Adaugă câmpuri noi în răspuns:
  - `ai_analysis` (dacă există)
  - Sau câmpuri separate: `ai_risk_overview`, `ai_insights`, etc.

---

## 8. Endpoint Chat (POST /api/ai/chat) ✅

- [x] 8.1 Creează request/response models:
  ```python
  class ChatMessage(BaseModel):
      role: str  # "user" | "assistant"
      content: str

  class ChatRequest(BaseModel):
      analysis_session_id: Optional[str] = None
      message: str
      chat_history: List[ChatMessage] = []

  class ChatResponse(BaseModel):
      message: str
      sources: List[Dict] = []  # insights referite
      suggested_actions: List[str] = []
  ```

- [x] 8.2 Implementează endpoint-ul:
  ```python
  @router.post("/ai/chat")
  async def chat_with_ai(
      request: ChatRequest,
      db: AsyncSession = Depends(get_async_db),
  ):
  ```

- [x] 8.3 Flux endpoint:
  1. Dacă `analysis_session_id` există:
     - Încarcă session din DB
     - Extrage `_ai_analysis` din config
  2. Construiește prompt cu:
     - Contextul AI Analysis (dacă există)
     - Istoricul conversației
     - Mesajul curent
  3. Apelează LLM
  4. Parsează răspunsul
  5. Returnează ChatResponse

---

## 9. Frontend: API Client ✅

- [x] 9.1 Actualizează `frontend/src/lib/api/client.ts`:
  - Adaugă tipuri pentru AI Analysis
  - Adaugă metodă: `aiApi.chat(request)`

- [x] 9.2 Actualizează `AnalysisSessionListItem`:
  - Include câmpurile noi din răspunsul API

---

## 10. Frontend: AI Insights Component ✅

- [x] 10.1 Creează directorul: `frontend/src/components/AIAnalysis/`

- [x] 10.2 Creează `RiskOverviewCard.tsx`:
  - Afișează: overall_risk_score (cu indicator vizual)
  - risk_level (cu culoare: green/yellow/orange/red)
  - trend_indicator (stable/improving/deteriorating cu iconiță)
  - primary_risk_category

- [x] 10.3 Creează `InsightsList.tsx`:
  - Listă de insights
  - Fiecare insight cu: priority badge, title, category
  - Expandable pentru: evidence, why_matters, risk_factors
  - Indicator vizual pentru `risk_score_contribution`

- [x] 10.4 Creează `PredictionsList.tsx`:
  - Listă de predicții
  - Fiecare cu: scenario, confidence (bar indicator), timeframe
  - Expandable pentru: risk_factors, mitigation_potential

- [x] 10.5 Creează `ActionPlanCard.tsx`:
  - 3 tabs: "Immediate (0-1h)", "Short Term (24h)", "Long Term"
  - Fiecare tab cu listă de ActionItem
  - Afișează: priority, action, steps (expandable), rationale

- [x] 10.6 Creează `NaturalLanguageSummary.tsx`:
  - Simplu: un card cu textul formatat frumos
  - Poate include un AI badge/iconiță

- [x] 10.7 Creează componenta principală `AIAnalysisSection.tsx`:
  - Orchestrează toate componentele
  - Arată doar dacă `ai_analysis` există

---

## 11. Frontend: Chat Component ✅

- [x] 11.1 Creează directorul: `frontend/src/components/AIChat/`

- [x] 11.2 Creează `ChatMessageBubble.tsx`:
  - Stil diferențiat pentru user vs assistant
  - Formatare text (markdown?)

- [x] 11.3 Creează `QuickSuggestions.tsx`:
  - Butoane cu sugestii rapide:
    - "Ce trebuie să fac?"
    - "De ce e asta un risc critic?"
    - "Explică-mi în termeni simpli"
    - "Compară cu..."

- [x] 11.4 Creează componenta principală `AIChat.tsx`:
  - Input + submit button
  - Listă de mesaje (cu scroll)
  - Quick suggestions
  - Istoric în state (local)
  - Loading indicator când se așteaptă răspuns

---

## 12. Integrează în Dashboard ✅

- [x] 12.1 Modifică pagina relevantă (probabil `Dashboard.tsx` sau Analysis Hub):
  - Adaugă `AIAnalysisSection` după secțiunile statice
  - Adaugă `AIChat` la final sau într-un colț/modal

- [x] 12.2 Asigură-te că datele ajung:
  - Din `useAnalysis()` context
  - Sau din props

---

## 13. Testare

- [x] 13.1 Test cu logurile din sample:
  - `docs/client/medical_device_logs_1000.txt`
  - Așteptări:
    - Ar trebui să detecteze Secondary sensor timeout
    - Ar trebui să detecteze Battery mode (voltage ~12V)
    - Ar trebui să detecteze pattern usa → incalzire

- [x] 13.2 Test manual:
  - Încarcă un .txt
  - Verifică că apare AI Analysis
  - Verifică că chat funcționează

- [x] 13.3 Test cu .png:
  - Încarcă un grafic
  - Verifică că AI Analysis rulează și pentru imagini

---

## Ordinea de Implementare (Recomandată)

```
ÎNTÂI (Backend):
  → Task 1: Scaffold module + constants
  → Task 2: ContextBuilder + Pydantic models
  → Task 3: Prompts
  → Task 4: AnalystEngine
  → Task 5: Persistence updates
  → Task 6: Integrate în endpoints
  → Task 7: Update GET /api/analysis
  → Task 8: Chat endpoint

APOI (Frontend):
  → Task 9: API Client updates
  → Task 10: AI Insights components
  → Task 11: Chat component
  → Task 12: Integrate în Dashboard

LA FINAL:
  → Task 13: Testare
```

---

## Ce NU trebuie modificat

- ❌ Rule-based Regulatory Engine - rămâne neschimbat
- ❌ Log Parser - rămâne neschimbat
- ❌ Schema DB - folosim coloana `config` existentă
- ❌ Fluxul existent - doar adăugăm peste el
