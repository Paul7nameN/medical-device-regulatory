# Overview Arhitectural

MED-THERM

---

## Arhitectura Generala

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ARHITECTURA MED-THERM                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                         │
│  Frontend (React 18 + TypeScript + Vite)                        │
│       │                                                        │
│       │ HTTP/HTTPS (TanStack Query)                             │
│       ▼                                                        │
│  Backend (FastAPI + Python 3.12)                                  │
│       │                                                        │
│       ├──► Log Parser                                       │
│       ├──► Regulatory Engine (21 de reguli)                       │
│       └──► AI Integration (ModelArk)                              │
│       │                                                        │
│       │ SQLAlchemy ORM + asyncpg)                                │
│       ▼                                                        │
│  PostgreSQL 16)                                              │
│                                                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Tehnologii Folosite

| Componenta | Tehnologie | Versiune |
|-------------|-------------|----------|
| Frontend | React | 18 |
| Frontend | TypeScript | 5.x |
| Frontend | Vite | 5.x |
| Frontend | Tailwind CSS | 3.x |
| Frontend | shadcn/ui | - |
| Frontend | TanStack Query | 5.x |
| Frontend | Recharts | 2.x |
| Backend | FastAPI | - |
| Backend | Python | 3.12 |
| Backend | SQLAlchemy | - |
| Baza de date | PostgreSQL | 16 |
| AI | ModelArk API | - |
| DevOps | Docker, Docker Compose | - |

---

## Flow de Lucru

```
User upload fisier (.txt / .png / .jpg)
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     File Upload Zone                                      │
└─────────────────────────────────────────────────────────────────────┘
       │
       ├──► Daca este .txt ──► Log Parser ──► Regulatory Engine
       │
       ├──► Daca este .png/.jpg ──► AI Image Analysis (ModelArk)
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Baza de Date (PostgreSQL)                      │
│  • devices                                                  │
│  • analysis_sessions                                          │
│  • log_entries                                            │
│  • detected_violations                                       │
│  • compliance_reports                                      │
│  • audit_log                                               │
└─────────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Frontend Dashboard                             │
│  • Overview                                                 │
│  • Temperature Chart                                    │
│  • Violations Table                                     │
│  • Rules Reference                                │
│  • History                                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Categorii de Reguli

| Cod | Descriere | Numar Reguli |
|-----|-----------|---------------|
| TEMP | Controlul temperaturii | 4 |
| SENS | Senzori | 3 |
| ALARM | Alarme | 3 |
| DATA | Date | 3 |
| POWER | Alimentare | 2 |
| COOL | Răcire | 2 |
| INS | Insulatie | 2 |
| OPS | Operatiuni | 2 |
| **Total** | **8 categorii** | **21 reguli** |
