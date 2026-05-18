# Ghid de Instalare

Cel mai simplu mod de a rula aplicatia pe orice dispozitiv este cu Docker.

---

## Prerechizite

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Git](https://git-scm.com/)

---

## Pasii de Instalare

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

---

## Comenzi Docker Utile

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
