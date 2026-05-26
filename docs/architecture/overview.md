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
│       ├──► Multi-Modal Pipeline                                    │
│       │       ├──► Log Parser (merge, dedupe)                     │
│       │       ├──► Chart Alignment (time synchronization)          │
│       │       └──► Temporal Correlation (cross-source analysis)   │
│       │                                                             │
│       ├──► Regulatory Engine (21 rules)                            │
│       ├──► AI Integration (ModelArk)                               │
│       └──► Unified Report Generation                               │
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
User uploads file (.txt / .png / .jpg / .md)
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     File Upload Zone                                      │
└─────────────────────────────────────────────────────────────────────┘
       │
       ├──► If .txt ──► Log Parser (merge, dedupe, source tracking)
       │
       ├──► If .png/.jpg ──► AI Image Analysis (chart data extraction)
       │
       └──► If .md/.txt (constraints) ──► Dynamic Rule Extraction
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Multi-Modal Processing                             │
│  ├──► Chart Time Alignment (align chart data to log timestamps)    │
│  ├──► Regulatory Validation (apply rules to all data sources)       │
│  └──► Temporal Correlation (cross-check findings across sources)    │
└─────────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Unified Report Generation                          │
│  ├──► Combine findings from all sources                              │
│  ├──► Add correlation insights (strong/weak/conflicting)            │
│  └──► Include source badges (Logs / Chart / Correlated)             │
└─────────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Database (PostgreSQL)                           │
│  • devices                                                           │
│  • analysis_sessions                                                 │
│  • log_entries                                                       │
│  • detected_violations                                               │
│  • compliance_reports                                                │
│  • audit_log                                                         │
└─────────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Frontend Dashboard                                 │
│  • Overview                                                           │
│  • Temperature Chart                                                  │
│  • Violations Table (severity-sorted: CRITICAL → HIGH → ...)        │
│  • Unified Timeline (with source badges)                              │
│  • Correlation Insights                                               │
│  • Rules Reference                                                    │
│  • History                                                            │
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
