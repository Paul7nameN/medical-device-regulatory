# AI Integration

> Acest fisier a fost mutat din `docs/ai-analysis-module.md`.

---

## Overview

The AI Analysis Module provides multi-modal compliance analysis for medical device data by integrating with the ModelArk API (OpenAI-compatible). It enhances the existing regulatory engine with AI-powered visual chart analysis, log summarization, and compliance report generation.

## What It Does

The module performs three main functions:

### 1. Visual Chart Analysis (Dola-Seed-2.0-pro)
- Analyzes temperature profile chart images (PNG/JPG)
- Detects compliance violations from visual data
- Extracts time ranges and temperature ranges from charts
- Identifies excursions, gaps, slow recovery patterns, and frequent access events
- Provides confidence scores for detected violations

### 2. Log Analysis (GLM-4.7)
- Summarizes device log data in natural language
- Generates key findings and recommendations
- Performs risk assessment (low/medium/high/critical)
- Provides contextual insights beyond rule-based validation

### 3. Compliance Report Generation
- Creates audit-ready compliance reports
- Generates executive summaries
- Provides detailed findings with explanations
- Offers actionable recommendations
- Produces structured report sections with bullet points

### 4. Cross-Validation
- Correlates findings from log-based validation with visual chart analysis
- Calculates confidence scores based on agreement between sources
- Identifies matching and conflicting findings
- Provides validation summaries

---

## Architecture

```
backend/app/ai/
├── client.py              # ModelArk API client (OpenAI SDK wrapper)
├── image/
│   ├── analyzer.py        # Chart image analysis
│   ├── prompts.py         # System prompts for chart analysis
│   └── models.py          # Chart analysis data models
├── text/
│   ├── analyzer.py        # Log/text analysis
│   ├── prompts.py         # System prompts for text analysis
│   └── models.py          # Text analysis data models
└── integration/
    └── engine.py          # Integration with RegulatoryEngine
```

---

## Inputs and Outputs

### Chart Analysis

**Input:**
- Image file (PNG/JPG, max 10MB)
- Optional device_id parameter

**Output:**
```json
{
  "result": {
    "model_used": "ep-20260406181344-7fmp8",
    "analyzed_at": "2026-05-12T15:30:00",
    "duration_seconds": 8.5,
    "chart_type": "temperature_profile",
    "time_range_start": "2026-05-14T14:00:00",
    "time_range_end": "2026-05-14T18:00:00",
    "temp_range_min": 0.0,
    "temp_range_max": 12.0,
    "violations": [
      {
        "violation_type": "excursion",
        "timestamp_start": "2026-05-14T14:30:00",
        "timestamp_end": "2026-05-14T14:45:00",
        "description": "Temperature exceeded 8°C for 15 minutes",
        "confidence": 0.95,
        "extracted_value": 10.5
      }
    ],
    "summary": "Chart shows one temperature excursion violation...",
    "confidence": 0.90
  },
  "success": true
}
```

### Log Analysis

**Input:**
```json
{
  "logs": [
    {
      "timestamp": "2026-05-14T14:00:10",
      "log_type": "TEMP_READING",
      "raw_value": "4.3C",
      "parsed_value": 4.3,
      "sensor_id": "PRIMARY_SENSOR"
    }
  ],
  "findings": [
    {
      "rule_id": "REG-TEMP-1",
      "rule_description": "Temperature must stay within 2°C to 8°C",
      "category": "thermal_safety",
      "severity": "HIGH",
      "passed": false,
      "message": "Temperature reading 9.1°C exceeds maximum threshold"
    }
  ],
  "device_id": "CRYOSAFE-001"
}
```

**Output:**
```json
{
  "result": {
    "model_used": "ep-20260406181003-74jsw",
    "analyzed_at": "2026-05-12T15:30:00",
    "duration_seconds": 5.2,
    "summary": "Device operating within normal parameters with minor temperature excursions...",
    "key_findings": [
      "Temperature readings are stable within 2-8°C range for most of the period",
      "One brief excursion detected at 14:00:40, lasting less than 1 minute",
      "Secondary sensor timeout occurred but did not affect temperature monitoring"
    ],
    "recommendations": [
      "Monitor secondary sensor health for potential replacement",
      "Investigate cause of brief temperature excursion"
    ],
    "risk_assessment": "low"
  },
  "success": true
}
```

### Report Generation

**Input:**
```json
{
  "device_id": "CRYOSAFE-001",
  "total_entries": 1500,
  "time_range_start": "2026-05-14T14:00:00",
  "time_range_end": "2026-05-14T18:00:00",
  "passed_count": 15,
  "failed_count": 2,
  "critical_count": 0,
  "summary": {
    "thermal_safety": {"passed": 3, "failed": 1, "total": 4},
    "sensor_redundancy": {"passed": 2, "failed": 0, "total": 2}
  },
  "findings": [...],
  "report_type": "compliance_summary"
}
```

**Output:**
```json
{
  "report": {
    "model_used": "ep-20260406181003-74jsw",
    "generated_at": "2026-05-12T15:30:00",
    "duration_seconds": 12.3,
    "report_type": "compliance_summary",
    "device_id": "CRYOSAFE-001",
    "title": "MED-THERM-2026 Compliance Report",
    "executive_summary": "Device CRYOSAFE-001 demonstrates overall compliance with MED-THERM-2026 requirements...",
    "sections": [
      {
        "title": "Executive Summary",
        "content": "Detailed summary paragraph...",
        "bullet_points": ["Point 1", "Point 2"]
      },
      {
        "title": "Compliance Status",
        "content": "Compliance breakdown paragraph...",
        "bullet_points": ["Thermal Safety: 3/4 passed", "Sensor Redundancy: 2/2 passed"]
      }
    ],
    "recommendations": "Detailed recommendations paragraph...",
    "conclusion": "Overall, the device maintains compliance with critical safety requirements..."
  },
  "success": true
}
```

---

## API Endpoints

### GET /api/ai/models
Lists available AI models and their status.

**Response:**
```json
{
  "models": [
    {
    "id": "ep-20260406181344-7fmp8",
    "name": "Dola-Seed-2.0-pro",
    "purpose": "chart_analysis",
    "status": "available"
    },
    {
    "id": "ep-20260406181003-74jsw",
    "name": "GLM-4.7",
    "purpose": "text_analysis",
    "status": "available"
    }
  ],
  "api_status": "connected",
  "config": {
    "base_url": "https://ark.ap-southeast.bytepluses.com/api/v3",
    "timeout": 60,
    "max_retries": 3,
    "ai_enabled": true
  }
}
```

### POST /api/ai/analyze-chart
Analyzes a temperature profile chart image.

**Request:**
- Content-Type: multipart/form-data
- file: Image file (PNG/JPG)
- device_id: Optional device identifier

**Response:** See Chart Analysis Output above

### POST /api/ai/analyze-logs
Analyzes logs with AI for insights and summaries.

**Request:** See Log Analysis Input above

**Response:** See Log Analysis Output above

### POST /api/ai/generate-report
Generates an AI-powered compliance report.

**Request:** See Report Generation Input above

**Response:** See Report Generation Output above

---

## MED-THERM-2026 Regulation Mapping

### Chart Analysis (Dola-Seed-2.0-pro)

The chart analyzer detects violations for these MED-THERM-2026 rules:

| Rule | Detection Method | Violation Type |
|------|-----------------|----------------|
| **REG-TEMP-1** | Temperature outside 2-8°C range | `excursion` |
| **REG-TEMP-2** | Excursion duration > 5min or cumulative > 10min/24h | `excursion` |
| **REG-TEMP-3** | Recovery time > 3 minutes after disturbance | `slow_recovery` |
| **REG-TEMP-4** | Sampling interval > 30 seconds (visible gaps) | `gap` |
| **REG-OPS-1** | Door events causing prolonged excursions | `frequent_access` |

### Log Analysis (GLM-4.7)

The log analyzer provides context for all MED-THERM-2026 rule categories.

**Risk Assessment Mapping:**
- **"low"**: No violations, all readings within limits
- **"medium"**: Minor violations (single temp excursion, one sensor timeout)
- **"high"**: Multiple violations, pattern of non-compliance
- **"critical"**: Critical violations (REG-TEMP-2 exceeded, dual sensor failure)

---

## Important Implementation Decisions

### 1. Model Selection
**Decision:** Use two specialized models instead of one general-purpose model
**Rationale:**
- Dola-Seed-2.0-pro is optimized for visual chart analysis
- GLM-4.7 excels at text analysis and report generation
- Specialized models provide better accuracy for specific tasks

### 2. OpenAI SDK Integration
**Decision:** Use official OpenAI SDK instead of direct HTTP calls
**Rationale:**
- ModelArk API is OpenAI-compatible
- SDK provides built-in retry logic, connection pooling, and error handling
- Reduces maintenance burden and improves reliability

### 3. Async Implementation
**Decision:** Use async/await throughout the module
**Rationale:**
- Non-blocking API calls prevent server timeouts
- Enables concurrent chart and log analysis
- Better performance under high load

### 4. Graceful Degradation
**Decision:** AI analysis is optional; system works without it
**Rationale:**
- Existing regulatory engine continues to function if AI is unavailable
- Users can enable AI by setting MODELARK_API_KEY
- No breaking changes to existing functionality
- Allows gradual rollout and testing

---

## Configuration

### Environment Variables

```env
# Required for AI functionality
MODELARK_API_KEY=your-api-key-here

# Optional overrides
MODELARK_BASE_URL=https://ark.ap-southeast.bytepluses.com/api/v3
MODELARK_TIMEOUT=60
MODELARK_MAX_RETRIES=3
```

### Settings (app/config.py)

```python
modelark_base_url: str = "https://ark.ap-southeast.bytepluses.com/api/v3"
modelark_api_key: Optional[str] = None
model_chart_analysis: str = "ep-20260406181344-7fmp8"  # Dola-Seed-2.0-pro
model_text_analysis: str = "ep-20260406181003-74jsw"  # GLM-4.7
modelark_timeout: int = 60
modelark_max_retries: int = 3
ai_enabled: bool = False  # Auto-enabled if API key is set
```

---

## Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| Chart analysis | < 30s | Includes image upload + model inference |
| Text analysis | < 15s | Log summary generation |
| Report generation | < 20s | Comprehensive report generation |
| Memory per request | < 50MB | Image + response handling |

---

## Error Handling

The module defines specific error types:

- **AIError**: Base exception for all AI errors
- **AIAPIError**: API call failed (includes status code)
- **AITimeoutError**: API call timed out
- **AIRateLimitError**: Rate limit exceeded (includes retry_after)
- **AIValidationError**: Input validation failed
- **AIImageError**: Image processing failed

All errors include:
- User-friendly error messages
- Retry availability indicators
- Retry-after timing when applicable
- Detailed logging for debugging

---

## Integration with Regulatory Engine

The `AIAugmentedRegulatoryEngine` class extends the base `RegulatoryEngine`:

```python
from app.ai.integration.engine import AIAugmentedRegulatoryEngine

engine = AIAugmentedRegulatoryEngine()
result = await engine.validate_with_ai(
    logs=log_entries,
    chart_image_bytes=chart_image,
    chart_format="png",
    device_id="CRYOSAFE-001",
    ai_required=False,  # Optional: fail if AI unavailable
    generate_ai_report=True  # Optional: generate AI report
)
```

---

## Testing

The module includes comprehensive tests:

- **Unit tests** for client, analyzers, and models
- **Integration tests** for API endpoints
- **Mock tests** for AI model responses
- **Error handling tests** for all error types

Run tests with:
```bash
pytest tests/test_ai_client.py
pytest tests/test_imageai_analyzer.py
pytest tests/test_text_analyzer.py
pytest tests/test_ai_integration.py
```

---

## Security Considerations

1. **API Key Storage**: Keys stored in environment variables, not in code
2. **Input Validation**: All inputs validated before processing
3. **Image Size Limits**: 10MB maximum to prevent DoS attacks
4. **Format Validation**: Only PNG/JPG images accepted
5. **Prompt Injection**: System prompts are hardcoded, not user-controlled
6. **Output Sanitization**: JSON responses validated before use
7. **Rate Limiting**: Respects API rate limits with exponential backoff

---

## Future Enhancements

Potential improvements for future iterations:

1. **Response Caching**: Cache identical chart images and log batches
2. **Batch Processing**: Process multiple charts/logs in parallel
3. **Custom Prompts**: Allow users to customize analysis prompts
4. **Additional Models**: Support for more specialized models
5. **Real-time Analysis**: Streaming analysis for live data
6. **Cost Tracking**: Track and report API usage costs
7. **Model Fine-tuning**: Fine-tune models on device-specific data
8. **Multi-language Support**: Support for non-English reports

---

## References

- **OpenSpec Change:** `openspec/changes/archive/2026-05-12-ai-analysis/`
- **Regulatory Engine:** `docs/architecture/regulatory-engine.md`
- **Sample Charts:** `docs/user-guide/examples/noncompliant_temperature_profile.png`
- **API Documentation:** http://localhost:8000/docs (when running)
