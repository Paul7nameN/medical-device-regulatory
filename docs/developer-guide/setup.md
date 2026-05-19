# Development Environment Setup

Run services directly on your machine (for faster development).

---

## Prerequisites

- Python 3.12+

- Node.js 20+

- PostgreSQL 16+ (or just use container for DB)

---

## 1. Database

Run only PostgreSQL in Docker:

```bash
docker-compose up -d db
```

Or install PostgreSQL locally and create database:

```sql
CREATE DATABASE med_therm;
CREATE USER med_therm_user WITH PASSWORD 'med_therm_password';
GRANT ALL PRIVILEGES ON DATABASE med_therm TO med_therm_user;
```

---

## 2. Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
Copy-Item .env.example .env

# Edit .env with your values

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```

---

## 3. Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

---

## Access

- Frontend: http://localhost:5173

- Backend: http://localhost:8000

- API Docs: http://localhost:8000/docs

---

## Troubleshooting

### Port already in use

If you get error that port 5432, 8000 or 5173 is in use:

```bash
# See what's using the port
netstat -ano | findstr :5432   # Windows
lsof -i :5432                   # Linux/Mac

# Stop the service or modify ports in docker-compose.yml
```

### Database not starting

```bash
# Delete volume and retry (WARNING: data will be lost!)
docker-compose down -v
docker-compose up --build
```

### Migrations failing

```bash
# Connect to container and run migrations manually
docker-compose exec backend alembic upgrade head
```

### Frontend cannot see backend

Verify that:
- Backend is running: http://localhost:8000/docs

- `VITE_API_TARGET` variable is correct

- In docker-compose, `frontend` depends on `backend`
