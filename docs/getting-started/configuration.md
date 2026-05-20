# Configuration

Environment variables used by MED-THERM.

---

## Environment Variables

### For Docker (root `.env` file)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MODELARK_API_KEY` | No | (empty) | ModelArk API key. If missing, AI features are disabled. |

If you don't have a ModelArk key, the application will work perfectly in basic mode (without AI).

### For local development (without Docker)

Edit `backend/.env`:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL sync connection |
| `DATABASE_URL_ASYNC` | Yes | - | PostgreSQL async connection |
| `DEBUG` | No | `true` | Debug mode |
| `CORS_ORIGINS` | No | `["*"]` | Allowed origins for CORS |
| `MODELARK_BASE_URL` | Yes (if AI) | - | ModelArk API base URL |
| `MODELARK_API_KEY` | No | - | ModelArk API key |
| `MODEL_CHART_ANALYSIS` | Yes (if AI) | - | Model for chart analysis |
| `MODEL_TEXT_ANALYSIS` | Yes (if AI) | - | Model for text analysis |
| `AI_ENABLED` | No | `false` | Enable/disable AI |

---

## Example `.env`

```env
# Optional: Add MODELARK_API_KEY to enable AI features
MODELARK_API_KEY=your-api-key-here
```
