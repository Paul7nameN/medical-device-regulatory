# Configurare

Variabile mediu folosite de MED-THERM.

---

## Variabile Mediu

### Pentru Docker (`.env` din radacina)

| Variabila | Required | Default | Descriere |
|-----------|----------|---------|-----------|
| `MODELARK_API_KEY` | Nu | (gol) | Cheia API pentru ModelArk. Daca lipseste, AI features sunt dezactivate. |

Daca nu ai cheia ModelArk, aplicatia va functiona perfect in modul basic (fara AI).

### Pentru dezvoltare locala (fara Docker)

Editeaza `backend/.env`:

| Variabila | Required | Default | Descriere |
|-----------|----------|---------|-----------|
| `DATABASE_URL` | Da | - | Conexiune PostgreSQL sync |
| `DATABASE_URL_ASYNC` | Da | - | Conexiune PostgreSQL async |
| `DEBUG` | Nu | `true` | Debug mode |
| `CORS_ORIGINS` | Nu | `["*"]` | Origins permise pentru CORS |
| `MODELARK_BASE_URL` | Da (daca AI) | - | URL baza ModelArk API |
| `MODELARK_API_KEY` | Nu | - | Cheia API ModelArk |
| `MODEL_CHART_ANALYSIS` | Da (daca AI) | - | Model pentru analiza chart-uri |
| `MODEL_TEXT_ANALYSIS` | Da (daca AI) | - | Model pentru analiza text |
| `AI_ENABLED` | Nu | `false` | Activeaza/dezactiveaza AI |

---

## Exemplu .env

```env
# Optional: Adauga MODELARK_API_KEY pentru a activa AI features
MODELARK_API_KEY=your-api-key-here
```
