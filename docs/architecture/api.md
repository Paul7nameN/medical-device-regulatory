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
| `/api/ai/analyze-chart` | POST | Analyze a chart (AI) |
| `/api/ai/analyze-logs` | POST | Analyze logs (AI) |
| `/api/ai/generate-report` | POST | Generate AI report |
| `/api/reports/generate` | POST | Generate a compliance report |
| `/api/reports` | GET | List reports |

---

## Quick Example

For complete details, see Swagger UI when running.
