# Setup Mediu de Dezvoltare

Ruleaza serviciile direct pe calculator (pentru dezvoltare mai rapida).

---

## Prerechizite

- Python 3.12+
- Node.js 20+
- PostgreSQL 16+ (sau foloseste doar container-ul pentru DB)

---

## 1. Baza de date

Ruleaza doar PostgreSQL in Docker:

```bash
docker-compose up -d db
```

Sau instaleaza PostgreSQL local si creaza baza de date:

```sql
CREATE DATABASE med_therm;
CREATE USER med_therm_user WITH PASSWORD 'med_therm_password';
GRANT ALL PRIVILEGES ON DATABASE med_therm TO med_therm_user;
```

---

## 2. Backend

```bash
cd backend

# Creeaza si activeaza virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate

# Instaleaza dependintele
pip install -r requirements.txt

# Copiaza variabilele mediu
Copy-Item .env.example .env

# Editeaza .env cu datele tale

# Ruleaza migrarile
alembic upgrade head

# Porneste serverul
uvicorn app.main:app --reload --port 8000
```

---

## 3. Frontend

```bash
cd frontend

# Instaleaza dependintele
npm install

# Porneste dev server
npm run dev
```

---

## Acceseaza

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Troubleshooting

### Port deja ocupat

Daca primesti eroare ca portul 5432, 8000 sau 5173 este ocupat:

```bash
# Vezi ce foloseste portul
netstat -ano | findstr :5432   # Windows
lsof -i :5432                   # Linux/Mac

# Opreste serviciul sau modifica porturile in docker-compose.yml
```

### Baza de date nu porneste

```bash
# Sterge volumul si reincearca (ATENTIE: se pierd datele!)
docker-compose down -v
docker-compose up --build
```

### Migrations esueaza

```bash
# Conecteaza-te la container si ruleaza migrarile manual
docker-compose exec backend alembic upgrade head
```

### Frontend nu vede backend-ul

Verifica ca:
- Backend ruleaza: http://localhost:8000/docs
- Variabila `VITE_API_TARGET` este corecta
- In docker-compose, `frontend` depinde de `backend`
