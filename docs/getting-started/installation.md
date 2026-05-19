# Installation Guide

The easiest way to run the application on any device is with Docker.

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

- [Git](https://git-scm.com/)

---

## Installation Steps

### 1. Clone the project

```bash
git clone <repository-url>
cd medical-device-regulatory
```

### 2. Configure environment variables

Copy the template file and fill in the values:

```bash
# Windows (PowerShell)
Copy-Item .env.example .env

# Or Linux/Mac
cp .env.example .env
```

### 3. Start the services

```bash
docker-compose up --build
```

On first run:
- Docker images are downloaded (PostgreSQL, Python, Node.js)

- Database is created

- Migrations run automatically

- Backend and frontend are compiled

### 4. Access the application

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:5173 | Web interface |
| **Backend API** | http://localhost:8000 | API endpoints |
| **API Docs** | http://localhost:8000/docs | Swagger UI |
| **ReDoc** | http://localhost:8000/redoc | Alternative documentation |

---

## Useful Docker Commands

```bash
# Start services in background
docker-compose up -d --build

# View logs
docker-compose logs -f

# View logs for backend only
docker-compose logs -f backend

# Stop services
docker-compose down

# Stop and delete database volume (WARNING: data will be lost!)
docker-compose down -v

# Restart just one service
docker-compose restart backend
```
