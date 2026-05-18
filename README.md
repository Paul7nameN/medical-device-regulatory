# MED-THERM Compliance Engine

Sistem de validare a conformitatii regulatorii pentru dispozitive medicale de transport cu control al temperaturii.

## Tehnologii

- **Backend**: FastAPI (Python 3.12), SQLAlchemy, Alembic, PostgreSQL
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui, TanStack Query
- **AI**: ModelArk API pentru analiza inteligenta a log-urilor si chart-urilor
- **DevOps**: Docker, Docker Compose

## Quick Start (cu Docker)

Cel mai simplu mod de a rula aplicatia pe orice dispozitiv.

### Prerechizite

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Git](https://git-scm.com/)

### 1. Cloneaza proiectul

```bash
git clone <repository-url>
cd medical-device-regulatory
```

### 2. Configurare variabile mediu

Copiaza fisierul template si completeaza valorile:

```bash
# Windows (PowerShell)
Copy-Item .env.example .env

# Sau Linux/Mac
cp .env.example .env
```

Editeaza `.env` si seteaza:

```env
# Optional: Adauga MODELARK_API_KEY pentru a activa AI features
MODELARK_API_KEY=your-api-key-here
```

Daca nu ai cheia ModelArk, aplicatia va functiona perfect in modul basic (fara AI).

### 3. Porneste serviciile

```bash
docker-compose up --build
```

La prima rulare:
- Se descarca imaginile Docker (PostgreSQL, Python, Node.js)
- Se creaza baza de date
- Se ruleaza migrarile automat
- Se compileaza backend-ul si frontend-ul

### 4. Acceseaza aplicatia

| Serviciu | URL | Descriere |
|----------|-----|-----------|
| **Frontend** | http://localhost:5173 | Interfata web |
| **Backend API** | http://localhost:8000 | API endpoints |
| **API Docs** | http://localhost:8000/docs | Swagger UI |
| **ReDoc** | http://localhost:8000/redoc | Documentatie alternativa |

### Comenzi Docker utile

```bash
# Porneste serviciile in background
docker-compose up -d --build

# Vezi log-urile
docker-compose logs -f

# Vezi log-urile doar pentru backend
docker-compose logs -f backend

# Opreste serviciile
docker-compose down

# Opreste si sterge volumul cu datele din BD (ATENTIE: se pierd datele!)
docker-compose down -v

# Restarteaza doar un serviciu
docker-compose restart backend
```

## Structura proiectului

```
medical-device-regulatory/
├── .env.example              # Template variabile mediu (foloseste Docker)
├── .gitignore                # Git ignore rules
├── docker-compose.yml        # Docker orchestration
├── README.md                 # Acest fisier
│
├── backend/
│   ├── app/                  # Cod FastAPI
│   │   ├── main.py           # Entry point
│   │   ├── config.py         # Settings (variabile mediu)
│   │   ├── api/              # API routes
│   │   ├── models/           # SQLAlchemy models
│   │   └── regulatory/       # Reguli de validare MED-THERM-2026
│   ├── migrations/           # Alembic migrations
│   ├── tests/                # Teste pytest
│   ├── .env.example          # Template pentru dezvoltare locala (fara Docker)
│   ├── Dockerfile
│   └── requirements.txt
│
└── frontend/
    ├── src/                  # Cod React + TypeScript
    │   ├── components/       # Componente UI
    │   ├── pages/            # Pagini
    │   ├── lib/              # Utilities (API client, etc.)
    │   └── hooks/            # Custom hooks
    ├── .env.example          # Template pentru dezvoltare locala
    ├── Dockerfile
    └── package.json
```

## Dezvoltare fara Docker

Daca vrei sa rulezi serviciile direct pe calculator (pentru dezvoltare mai rapida):

### Prerechizite

- Python 3.12+
- Node.js 20+
- PostgreSQL 16+ (sau foloseste doar container-ul pentru DB)

### 1. Baza de date

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

### 2. Backend

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
cp .env.example .env
# Editeaza .env cu datele tale

# Ruleaza migrarile
alembic upgrade head

# Porneste serverul
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend

# Instaleaza dependintele
npm install

# Porneste dev server
npm run dev
```

Acceseaza:
- Frontend: http://localhost:5173
- Backend: http://localhost:8000

## Variabile mediu

### Pentru Docker (.env din radacina)

| Variabila | Required | Default | Descriere |
|-----------|----------|---------|-----------|
| `MODELARK_API_KEY` | Nu | (gol) | Cheia API pentru ModelArk AI. Daca lipseste, AI features sunt dezactivate. |

### Pentru dezvoltare locala (backend/.env)

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

## Pentru GitHub

### Inainte de primul commit

Asigura-te ca:

1. **NU comiti fisierele .env** (ele sunt in .gitignore)
2. Ai copiat `.env.example` ca `.env` si ai completat valorile
3. Verifica git status:

```bash
git status
```

Nu ar trebui sa vezi niciun fisier `.env` in lista.

### Initializare git pe un dispozitiv nou

```bash
# 1. Cloneaza repo-ul
git clone <repository-url>
cd medical-device-regulatory

# 2. Creeaza fisierul .env din template
Copy-Item .env.example .env   # Windows
# sau
cp .env.example .env           # Linux/Mac

# 3. Editeaza .env si adauga MODELARK_API_KEY (daca ai nevoie de AI)

# 4. Porneste cu Docker
docker-compose up --build
```

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

## Licenta

Pentru uz intern.
