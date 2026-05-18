# Tasks: AI Analysis Module

## Implementation Tasks

### Phase 1: Project Setup & Configuration

- [x] **1.1** Update dependencies in `requirements.txt`
  - Add `openai` (for OpenAI-compatible API client)
  - Add `httpx` (already may be present via OpenAI SDK)
  - Add `tenacity` (for retry logic)
  - Add `Pillow` (optional, for image format detection)

- [x] **1.2** Update configuration in `app/config.py`
  - Add ModelArk API settings: `modelark_base_url`, `modelark_api_key`
  - Add model IDs: `model_chart_analysis`, `model_text_analysis`
  - Add timeout/retry settings: `modelark_timeout`, `modelark_max_retries`
  - Add `ai_enabled` flag (auto-enabled when API key present)
  - Update `.env` template with new environment variables

- [x] **1.3** Create AI module directory structure
  - Create `app/ai/` directory
  - Create `app/ai/image/` subdirectory
  - Create `app/ai/text/` subdirectory
  - Create `app/ai/integration/` subdirectory
  - Create `__init__.py` files in all directories

---

### Phase 2: ModelArk API Client

- [x] **2.1** Implement custom exception classes
  - `app/ai/client.py`: Define exception hierarchy
  - `AIError` (base)
  - `AIAPIError` (HTTP errors)
  - `AITimeoutError` (timeout errors)
  - `AIRateLimitError` (rate limiting)
  - `AIValidationError` (input validation)
  - `AIImageError` (image processing)

- [x] **2.2** Implement ModelArk API client
  - `app/ai/client.py`: `ModelArkClient` class
  - Initialize OpenAI AsyncClient with base URL and API key
  - Implement `chat_completion()` method with retry logic
  - Implement `analyze_image()` method for visual chart analysis
  - Implement `analyze_text()` method for text/log analysis
  - Handle response parsing and validation

- [x] **2.3** Implement retry and error handling
  - Use `tenacity` for exponential backoff retry
  - Retry on API errors, timeouts, connection errors
  - Max 3 retries with increasing delays (2s, 4s, 8s)
  - Graceful degradation on failure

- [x] **2.4** Create data models for AI analysis
  - `app/ai/image/models.py`: Chart analysis models
  - `ChartViolationType`, `ChartViolation`, `ChartAnalysisResult`
  - `app/ai/text/models.py`: Text analysis models
  - `LogAnalysisResult`, `ComplianceReportSection`, `GeneratedReport`
  - `CrossValidationResult`, `AIError`

---

### Phase 3: Image Analysis Module (Dola-Seed-2.0-pro)

- [x] **3.1** Create image analysis prompts
  - `app/ai/image/prompts.py`
  - `SYSTEM_PROMPT_CHART_ANALYSIS`: Detailed system prompt
  - Include MED-THERM-2026 requirements
  - Define JSON output format
  - Include instructions for violation detection

- [x] **3.2** Implement chart analyzer
  - `app/ai/image/analyzer.py`: `ChartAnalyzer` class
  - `analyze()` method: accepts image bytes, returns `ChartAnalysisResult`
  - Encode image to base64
  - Call ModelArk API with image
  - Parse JSON response
  - Validate and convert to structured model

- [x] **3.3** Implement response parsing
  - `_parse_json_response()`: Parse JSON from response
  - `_extract_json_from_text()`: Fallback for malformed JSON
  - `_build_result()`: Convert parsed JSON to `ChartAnalysisResult`
  - `_parse_datetime()`: Safe datetime parsing
  - Handle partial/incomplete responses gracefully

- [x] **3.4** Add image utility functions
  - Image format detection (PNG/JPG)
  - Optional: Image resizing for API limits
  - Base64 encoding/decoding
  - Validate image size and format

---

### Phase 4: Text Analysis Module (GLM-4.7)

- [x] **4.1** Create text analysis prompts
  - `app/ai/text/prompts.py`
  - `SYSTEM_PROMPT_LOG_ANALYSIS`: Log analysis prompt
  - `SYSTEM_PROMPT_REPORT_GENERATION`: Report generation prompt
  - Include log type descriptions
  - Define JSON output format

- [x] **4.2** Implement text analyzer
  - `app/ai/text/analyzer.py`: `TextAnalyzer` class
  - `analyze_logs()` method: Analyze logs and findings
  - `generate_report()` method: Generate compliance reports
  - `_build_log_analysis_prompt()`: Construct prompt from logs
  - `_build_report_prompt()`: Construct prompt from compliance report

- [x] **4.3** Implement log summarization
  - `_summarize_logs()`: Summarize log entries for prompt
  - Count log types
  - Identify time range
  - Highlight key events (alarms, sensor timeouts)
  - Keep prompt within token limits

- [x] **4.4** Implement findings summarization
  - `_summarize_findings()`: Summarize regulatory findings
  - Count pass/fail by category
  - Highlight critical violations
  - Extract remediation hints

---

### Phase 5: API Endpoints

- [x] **5.1** Create AI API router
  - `app/api/ai.py`: FastAPI router
  - Include router in `app/main.py`
  - Add CORS support if needed

- [x] **5.2** Implement chart analysis endpoint
  - `POST /api/ai/analyze-chart`
  - Accept multipart form with image file
  - Optional `device_id` parameter
  - Return `ChartAnalysisResult` JSON
  - Handle file upload validation (size, format)

- [x] **5.3** Implement log analysis endpoint
  - `POST /api/ai/analyze-logs`
  - Accept logs array or reference to validation result
  - Return `LogAnalysisResult` JSON

- [x] **5.4** Implement report generation endpoint
  - `POST /api/ai/generate-report`
  - Accept compliance report data
  - Optional `report_type` parameter
  - Return `GeneratedReport` JSON

- [x] **5.5** Implement models status endpoint
  - `GET /api/ai/models`
  - Return available models
  - Return API status (connected/disconnected)
  - Return configuration (timeout, retry settings)
  - Optionally: Test API connectivity

---

### Phase 6: Integration with Regulatory Engine

- [x] **6.1** Create integration module
  - `app/ai/integration/engine.py`
  - `AIAugmentedRegulatoryEngine` class
  - Wraps existing `RegulatoryEngine`

- [x] **6.2** Implement enhanced validation
  - `validate_with_ai()` method
  - Run base validation first
  - Optional: Analyze chart image
  - Optional: Cross-validate findings
  - Generate AI-enhanced report

- [x] **6.3** Implement cross-validation logic
  - `_cross_validate()` method
  - Compare log-based findings with chart-based findings
  - Calculate confidence score based on agreement
  - Identify matching vs conflicting violations

- [x] **6.4** Implement fallback behavior
  - Handle AI API errors gracefully
  - Return base validation result when AI unavailable
  - Add warning to result when AI analysis failed
  - Allow optional flag: `ai_required=True` for strict mode

- [x] **6.5** Update existing validation endpoint
  - Note: Existing AI endpoints provide separate AI functionality
  - Use `/api/ai/analyze-chart`, `/api/ai/analyze-logs` for AI analysis
  - Use `AIAugmentedRegulatoryEngine` programmatically for combined validation

---

### Phase 7: Unit Tests

- [x] **7.1** Create API client tests
  - `tests/test_ai_client.py`
  - Test chat completion with mock
  - Test retry behavior on API errors
  - Test timeout handling
  - Test rate limit error handling

- [x] **7.2** Create image analyzer tests
  - `tests/test_image_analyzer.py`
  - Test JSON response parsing
  - Test JSON extraction from text fallback
  - Test result building with valid data
  - Test result building with partial/invalid data
  - Test violation type parsing

- [x] **7.3** Create text analyzer tests
  - `tests/test_text_analyzer.py`
  - Test log summary generation
  - Test findings summary generation
  - Test report section parsing
  - Test prompt building

- [x] **7.4** Create integration tests
  - `tests/test_ai_integration.py`
  - Test `validate_with_ai()` flow
  - Test cross-validation (matching findings)
  - Test cross-validation (conflicting findings)
  - Test fallback on API error

- [x] **7.5** Create API endpoint tests
  - `tests/test_ai_api.py`
  - Test `/api/ai/models` endpoint
  - Test `/api/ai/analyze-chart` with mock image
  - Test `/api/ai/analyze-logs` with sample data
  - Test error responses

---

### Phase 8: Error Handling & Polish

- [x] **8.1** Implement comprehensive error handling
  - All API endpoints return structured error responses
  - `AIError` responses include: `error_type`, `message`, `retry_available`
  - HTTP status codes: 400 (validation), 408 (timeout), 429 (rate limit), 503 (unavailable)
  - Log all API errors with context

- [x] **8.2** Add logging
  - Log all API requests (without sensitive data)
  - Log API response times
  - Log errors with full context
  - Use structured logging format

- [x] **8.3** Add request validation
  - Validate image format (PNG/JPG only)
  - Validate image size (max 10MB)
  - Validate log entry format
  - Validate all request parameters

- [x] **8.4** Update module exports
  - `app/ai/__init__.py`: Export main classes
  - `ModelArkClient`, `ChartAnalyzer`, `TextAnalyzer`
  - All data models
  - Exceptions

---

## Dependencies

| Task | Depends On |
|------|------------|
| All API client tasks (2.x) | 1.1, 1.2 (dependencies, config) |
| All image analysis tasks (3.x) | 2.1, 2.2 (client, exceptions) |
| All text analysis tasks (4.x) | 2.1, 2.2 (client, exceptions) |
| All API endpoints (5.x) | 3.2, 4.2 (analyzers complete) |
| All integration tasks (6.x) | 3.2, 4.2, existing RegulatoryEngine |
| All tests (7.x) | All implementation tasks complete |
| All polish tasks (8.x) | All implementation complete |

---

## Estimated Complexity

| Phase | Complexity | Notes |
|-------|------------|-------|
| Phase 1 | Low | Dependencies and config |
| Phase 2 | Medium | API client with retry logic |
| Phase 3 | Medium | Image analysis + prompt engineering |
| Phase 4 | Medium | Text analysis + report generation |
| Phase 5 | Low-Medium | FastAPI endpoints |
| Phase 6 | Medium | Integration with existing engine |
| Phase 7 | Medium | Comprehensive tests with mocks |
| Phase 8 | Low | Error handling and polish |

---

## Notes

### API Authentication

- API key passed via `Authorization: Bearer <key>` header
- Key stored in environment variable `MODELARK_API_KEY`
- Never log or expose API key in responses

### Model IDs

| Model | ID | Use Case |
|-------|-----|----------|
| Dola-Seed-2.0-pro | `ep-20260406181344-7fmp8` | Visual chart analysis |
| GLM-4.7 | `ep-20260406181003-74jsw` | Text analysis, reports |

### Prompt Engineering Guidelines

1. **Be specific** - Clearly state what you want the model to do
2. **Define format** - Specify JSON schema for output
3. **Provide context** - Explain MED-THERM-2026 requirements
4. **Give examples** - Include sample inputs/outputs when helpful
5. **Validate output** - Always parse and validate responses

### Safety Considerations

1. **Input sanitization** - Never pass untrusted input directly to prompts
2. **Output validation** - Always parse and validate JSON responses
3. **Rate limiting** - Implement client-side rate limiting
4. **Cost tracking** - Monitor API usage (future enhancement)
5. **Prompt injection** - Consider potential for prompt injection attacks

### Fallback Strategy

```
AI Analysis Request
    │
    ├─► Success? ──► Return AI-enhanced result
    │       │
    │       No
    │       │
    │       ├─► Transient error? ──► Retry (max 3 times)
    │       │       │
    │       │       No
    │       │       │
    │       │       ├─► ai_required=True? ──► Return error
    │       │       │
    │       │       No
    │       │       │
    │       │       └─► Return base result + warning
    │
    └─► Done
```

### Testing with Real API

For integration tests that need real API access:
1. Set `MODELARK_API_KEY` environment variable
2. Mark tests with `@pytest.mark.integration`
3. Skip in CI/CD unless API key is configured
4. Use small/simple test images to minimize cost

---

## Checkpoints

- [x] Dependencies added and installable
- [x] Configuration updated with new settings
- [x] ModelArk client implemented
- [x] Chart analysis endpoint implemented
- [x] Log analysis endpoint implemented
- [x] Integration with RegulatoryEngine implemented
- [x] All unit tests created
- [x] Error handling comprehensive
- [x] Structured logging implemented
- [x] API documentation available in `/docs`
