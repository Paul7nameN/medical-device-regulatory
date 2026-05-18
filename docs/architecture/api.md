# API Documentation

## Acces la documentatia interactiva

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Endpoint-uri Principale

| Endpoint | Metoda | Descriere |
|----------|---------|-----------|
| `/api/health` | GET | Verifica daca serviciul ruleaza |
| `/api/health/db` | GET | Verifica conexiunea la BD |
| `/api/health/rules` | GET | Lista toate regulile incarcate |
| `/api/logs/ingest` | POST | Incarca fisiere de log |
| `/api/logs` | GET | Lista log-urile |
| `/api/validate` | POST | Ruleaza validarea regulatorie |
| `/api/validate/quick-test` | GET | Test rapid cu date preconfigurate |
| `/api/ai/models` | GET | Modele AI disponibile |
| `/api/ai/analyze-chart` | POST | Analizeaza un chart (AI) |
| `/api/ai/analyze-logs` | POST | Analizeaza log-uri (AI) |
| `/api/ai/generate-report` | POST | Genereaza raport AI |
| `/api/reports/generate` | POST | Genereaza un raport de conformitate |
| `/api/reports` | GET | Lista rapoartele |

---

## Exemplu Rapid

Pentru detalii complete, vezi Swagger UI la rulare.
