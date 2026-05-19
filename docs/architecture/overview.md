# Architectural Overview

MED-THERM

---

## General Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MED-THERM ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Frontend (React 18 + TypeScript + Vite)                            │
│       │                                                             │
│       │ HTTP/HTTPS (TanStack Query)                                  │
│       ▼                                                             │
│  Backend (FastAPI + Python 3.12)                                     │
│       │                                                             │
│       ├──► Log Parser                                              │
│       ├──► Regulatory Engine (21 rules)                            │
│       └──► AI Integration (ModelArk)                               │
│       │                                                             │
│       │ SQLAlchemy ORM + asyncpg                                    │
│       ▼                                                             │
│  PostgreSQL 16                                                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Technologies Used

| Component | Technology | Version |
|-----------|------------|---------|
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
| Database | PostgreSQL | 16 |
| AI | ModelArk API | - |
| DevOps | Docker, Docker Compose | - |

---

## Workflow

```
User uploads file (.txt / .png / .jpg)
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

## Rule Categories

| Code | Description | Number of Rules |
|------|-------------|-----------------|
| TEMP | Temperature control | 4 |
| SENS | Sensors | 3 |
| ALARM | Alarms | 3 |
| DATA | Data integrity | 3 |
| POWER | Power system | 2 |
| COOL | Cooling | 2 |
| INS | Insulation | 2 |
| OPS | Operations | 2 |
| **Total** | **8 categories** | **21 rules** |
