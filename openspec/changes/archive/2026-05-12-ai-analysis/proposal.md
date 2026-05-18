# Proposal: AI Analysis Module

## What

Build a Python **AI Analysis Module** that integrates with **ModelArk API** (OpenAI-compatible) for multi-modal compliance analysis of medical device data.

The module will use two specialized models:

### 1. Dola-Seed-2.0-pro (ep-20260406181344-7fmp8)

**Purpose:** Analyze temperature profile chart images and detect compliance violations

**Capabilities:**
- **Visual analysis of temperature charts** - Extract time-series data from PNG/JPG chart images
- **Violation detection from visuals** - Identify excursions, gaps, and patterns not visible in structured logs
- **Cross-validation** - Compare chart visual data with parsed log data for consistency

### 2. GLM-4.7 (ep-20260406181003-74jsw)

**Purpose:** Log analysis and compliance text generation

**Capabilities:**
- **Log summarization** - Generate human-readable summaries of device log behavior
- **Compliance report generation** - Create detailed audit-ready compliance reports
- **Regulatory text analysis** - Analyze requirement documents and map to validation rules
- **Explainable AI findings** - Generate remediation suggestions and compliance explanations

### Integration Points

1. **Multi-modal validation** - Combine log-based validation (existing) with visual chart analysis (new)
2. **Enhanced findings** - Generate detailed compliance reports with AI-generated explanations
3. **Cross-source validation** - Correlate log data with chart visualizations for confidence scoring

---

## Why

### Problem Being Solved

The current regulatory engine only validates **structured log data**. However:

1. **Visual chart data is critical** - Auditors often provide temperature profile charts as PNG/JPG images that contain valuable compliance evidence
2. **Log data may be incomplete or manipulated** - Visual charts provide independent verification
3. **Compliance reports need human-readable explanations** - Engineers need more than just "PASS/FAIL" - they need context and remediation guidance
4. **Regulatory requirements from documents** - PDF/Word requirement documents need to be parsed and mapped to validation rules

### Business Need

MED-THERM-2026 compliance requires:
- Multi-source verification (logs + charts + documents)
- Audit-ready documentation with clear explanations
- Ability to analyze heterogeneous data formats

### User Benefits

| Stakeholder | Benefit |
|-------------|---------|
| **QA Team** | Analyze chart images without manual data extraction |
| **Engineers** | AI-generated remediation suggestions and compliance summaries |
| **Regulatory Team** | Audit-ready reports with explainable AI findings |
| **Management** | Cross-source validation confidence scores |

---

## Goals

1. **Build ModelArk API client** - OpenAI-compatible client for ModelArk API
   - Base URL: `https://ark.ap-southeast.bytepluses.com/api/v3`
   - Support for both models: Dola-Seed-2.0-pro and GLM-4.7

2. **Implement image analysis module** - Temperature chart analysis
   - Extract time-series data from chart images
   - Detect excursions, gaps, and patterns from visuals
   - Cross-validate with log-based findings

3. **Implement text analysis module** - Log analysis and report generation
   - Summarize log behavior in natural language
   - Generate compliance reports with explanations
   - Analyze regulatory requirement documents

4. **Create FastAPI endpoints** - Expose AI analysis functionality
   - POST `/api/ai/analyze-chart` - Analyze uploaded chart image
   - POST `/api/ai/analyze-logs` - Analyze logs with AI
   - POST `/api/ai/generate-report` - Generate compliance report
   - GET `/api/ai/models` - List available models and status

5. **Integrate with existing engine** - Enhance validation pipeline
   - Add AI analysis as optional validation step
   - Cross-reference log-based findings with visual analysis
   - Generate confidence scores for multi-source validation

---

## Non-Goals

- **Model training/fine-tuning** - Use pre-trained models only
- **Real-time streaming** - Batch analysis only for this phase
- **Local model deployment** - API-based inference only
- **Document OCR beyond charts** - Focus on temperature profile charts first
- **Multi-language support** - English-only for initial implementation
- **Custom model fine-tuning** - Use provided model endpoints as-is

---

## Success Metrics

| Metric | Target |
|--------|--------|
| API Response Time | < 30s for chart analysis, < 15s for text analysis |
| Model Availability | Both models reachable 99%+ |
| Error Handling | All API errors gracefully handled with user-friendly messages |
| Integration | Works seamlessly with existing RegulatoryEngine |
| Test Coverage | 80%+ on client and analysis modules |

---

## Model Configuration

| Model | ID | Purpose | API Endpoint |
|-------|-----|---------|--------------|
| **Dola-Seed-2.0-pro** | `ep-20260406181344-7fmp8` | Visual chart analysis | `/v1/chat/completions` |
| **GLM-4.7** | `ep-20260406181003-74jsw` | Text analysis, report generation | `/v1/chat/completions` |

**Base URL:** `https://ark.ap-southeast.bytepluses.com/api/v3`

**Authentication:** API key via `Authorization: Bearer <key>` header

**Compatibility:** OpenAI API compatible - can use `openai` Python SDK

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| ModelArk API downtime | Medium | High | Implement retry logic, fallback to log-only analysis, cache API responses |
| Image analysis accuracy | Medium | Medium | Provide confidence scores, allow human override, cross-validate with log data |
| API rate limits | Medium | Medium | Implement exponential backoff, batch requests, queue system |
| Cost per API call | Low | Medium | Track usage, implement usage limits, provide cost estimation |
| Prompt injection/safety | Low | High | Use system prompts carefully, validate inputs, sanitize outputs |

---

## Dependencies

- **Python 3.11+**
- **httpx** - Async HTTP client for API calls
- **openai** - Official OpenAI SDK (ModelArk is OpenAI-compatible)
- **Pillow** - Image processing (optional, for basic image info)
- **FastAPI** - Existing in project for API endpoints
- **Pydantic** - Existing in project for data modeling
- **python-multipart** - Existing in project for file uploads

---

## Configuration

New settings to add to `app/config.py`:

```python
class Settings(BaseSettings):
    # Existing settings...
    
    # ModelArk API Configuration
    modelark_base_url: str = "https://ark.ap-southeast.bytepluses.com/api/v3"
    modelark_api_key: Optional[str] = None
    
    # Model IDs
    model_chart_analysis: str = "ep-20260406181344-7fmp8"  # Dola-Seed-2.0-pro
    model_text_analysis: str = "ep-20260406181003-74jsw"  # GLM-4.7
    
    # API settings
    modelark_timeout: int = 60
    modelark_max_retries: int = 3
    modelark_retry_delay: float = 1.0
    
    class Config:
        env_file = ".env"
        env_prefix = "MODELARK_"
```

**Environment Variables:**
- `MODELARK_API_KEY` - API key for authentication
- `MODELARK_BASE_URL` - Override default base URL

---

## Open Questions

1. **API Key Management:** How should API keys be stored and rotated?
   - *Recommendation:* Environment variables via `.env` file for now, add secrets manager integration later

2. **Image Format Support:** What image formats need support?
   - *Recommendation:* Start with PNG and JPG, add others based on requirements

3. **Cost Tracking:** Should we track and report API usage costs?
   - *Recommendation:* Basic usage logging for now, add cost dashboard if needed

4. **Caching Strategy:** Should we cache API responses for identical inputs?
   - *Recommendation:* Yes, cache identical chart images and log batches to reduce costs

5. **Fallback Behavior:** What happens if ModelArk API is unavailable?
   - *Recommendation:* Fall back to log-only analysis, warn user, allow retry
