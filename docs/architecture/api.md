# API Documentation

## Access Interactive Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Main Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Check if service is running |
| `/api/health/db` | GET | Check database connection |
| `/api/health/rules` | GET | List all loaded rules |
| `/api/logs/ingest` | POST | Upload log files |
| `/api/logs` | GET | List logs |
| `/api/validate` | POST | Run regulatory validation |
| `/api/validate/quick-test` | GET | Quick test with pre-configured data |
| `/api/ai/models` | GET | Available AI models |
| `/api/ai/rules-info` | GET | Dynamic rule extraction capability info |
| `/api/ai/extract-rules` | POST | Extract regulatory rules from text document |
| `/api/ai/analyze-chart` | POST | Analyze a chart (AI) |
| `/api/ai/analyze-logs` | POST | Analyze logs (AI) |
| `/api/ai/generate-report` | POST | Generate AI report |
| `/api/reports/generate` | POST | Generate a compliance report |
| `/api/reports` | GET | List reports |
| `/api/analysis` | GET | List analysis sessions |
| `/api/analysis/{id}` | GET | Get analysis session detail |
| `/api/analysis/{id}` | DELETE | Delete analysis session |
| `/api/analysis/all` | DELETE | Delete all analysis sessions |

---

## Dynamic Rule Extraction Endpoints (New)

### GET `/api/ai/rules-info`

Check dynamic rule extraction capability.

**Response:**
```json
{
  "extraction_available": true,
  "default_ruleset_name": "MED-THERM-2026",
  "auto_execute_confidence_threshold": 0.7,
  "supported_rule_types": [
    "threshold_range",
    "duration_limit", 
    "frequency_limit",
    "presence_check",
    "inspection_only"
  ],
  "data_sources": ["logs", "inspection", "combined"]
}
```

---

### POST `/api/ai/extract-rules`

Extract regulatory rules from a text document using AI.

**Request Body:**
```json
{
  "document_text": "REG-TEMP-1: Temperature must be 2-8°C\nREG-TEMP-2: Max excursion 5 minutes...",
  "filename": "Medical Device Regulatory Constraints.md"
}
```

**Response (Success):**
```json
{
  "success": true,
  "rules": [
    {
      "id": "REG-TEMP-1",
      "name": "Operating Temperature Range",
      "category": "TEMP",
      "description": "The device shall maintain internal storage temperature within 2°C to 8°C",
      "type": "threshold_range",
      "severity": "high",
      "confidence": 0.95,
      "thresholds": {
        "min": 2.0,
        "max": 8.0,
        "unit": "°C"
      },
      "data_source": "logs"
    },
    {
      "id": "REG-TEMP-2",
      "name": "Excursion Limits",
      "category": "TEMP",
      "description": "Temperature excursions limited to 5 minutes single event",
      "type": "duration_limit",
      "severity": "critical",
      "confidence": 0.92,
      "thresholds": {
        "max_duration_seconds": 300
      },
      "data_source": "logs",
      "inspection_hint": "Check temperature log for excursions"
    }
  ],
  "meta": {
    "extracted_at": "2026-05-19T20:00:00.123456",
    "model_used": "seed-2-0-pro",
    "average_confidence": 0.93,
    "rule_count": 2
  }
}
```

**Response (Error):**
```json
{
  "success": false,
  "rules": [],
  "error": "AI extraction failed: No rules found in document"
}
```

---

## Rule Types

| Type | Description | Example Thresholds |
|------|-------------|---------------------|
| `threshold_range` | Value must be within min/max | `min: 2.0, max: 8.0, unit: "°C"` |
| `duration_limit` | Event must not exceed time limit | `max_duration_seconds: 300` |
| `frequency_limit` | Events limited within time window | `max_count: 10, time_window_seconds: 3600` |
| `presence_check` | Verify field exists/has value | `required_state: "CONNECTED"` |
| `inspection_only` | Information only, not validated from logs | No thresholds - uses `inspection_hint` |

---

## Validation with Custom Rules

### POST `/api/validate`

Run validation with optional custom rules.

**Request Body (with custom rules):**
```json
{
  "raw_logs": [
    "2026-05-14 14:00:10 TEMP_READING 4.3C",
    "2026-05-14 14:00:40 TEMP_READING 9.1C"
  ],
  "device_id": "test-device-001",
  "extracted_rules": [
    {
      "id": "REG-TEMP-1",
      "name": "Operating Range",
      "category": "TEMP",
      "description": "2-8°C range",
      "type": "threshold_range",
      "severity": "high",
      "confidence": 0.95,
      "thresholds": { "min": 2.0, "max": 8.0 },
      "data_source": "logs"
    }
  ],
  "ruleset_meta": {
    "source": "extracted",
    "filename": "My Constraints.md",
    "rule_count": 1,
    "ruleset_name": "Custom Rules"
  },
  "merge_with_default_rules": false
}
```

**Response Includes:**
- `analysis_session_id` - For later reference
- Standard validation report structure

---

## Analysis Session Response Fields

When listing analysis sessions (`GET /api/analysis`), each item includes:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Session UUID |
| `device_name` | string | Device identifier |
| `status` | string | pending/completed/failed |
| `created_at` | string | ISO timestamp |
| `has_custom_rules` | boolean | True if custom rules were used |
| `ruleset_name` | string | Name of ruleset (if custom) |
| `extracted_rules` | array | Full rule definitions (if custom) |
| `ruleset_meta` | object | Metadata about rules extraction |
| `latest_analysis_data` | object | Device logs, validation result, temp data |
| `ai_analysis` | object | AI-generated insights, predictions, action plan |

---

## Image Analysis with Custom Rules

### POST `/api/ai/analyze-chart` (FormData)

Accepts custom rules as additional FormData fields.

**FormData Fields:**
| Field | Type | Required |
|-------|------|----------|
| `file` | binary | Yes |
| `extracted_rules` | string (JSON) | No |
| `ruleset_meta` | string (JSON) | No |

**Example (JavaScript):**
```javascript
const formData = new FormData();
formData.append('file', imageFile);
formData.append('extracted_rules', JSON.stringify([
  { id: 'REG-TEMP-1', ... }
]));
formData.append('ruleset_meta', JSON.stringify({
  source: 'extracted',
  filename: 'My Constraints.md',
  rule_count: 1
}));

const response = await fetch('/api/ai/analyze-chart', {
  method: 'POST',
  body: formData
});
```

---

## Quick Example

For complete details, see Swagger UI when running.

### Complete Custom Rules Workflow

```bash
# 1. Check if extraction is available
curl http://localhost:8000/api/ai/rules-info

# 2. Extract rules from document
curl -X POST http://localhost:8000/api/ai/extract-rules \
  -H "Content-Type: application/json" \
  -d '{
    "document_text": "REG-TEMP-1: Temperature 2-8°C\nREG-TEMP-2: Max 5 min excursion",
    "filename": "my-constraints.md"
  }'

# 3. Run validation with extracted rules
curl -X POST http://localhost:8000/api/validate \
  -H "Content-Type: application/json" \
  -d '{
    "raw_logs": ["2026-05-14 14:00:10 TEMP_READING 4.3C"],
    "extracted_rules": [...],  # from step 2
    "ruleset_meta": {...}        # from step 2
  }'
```
