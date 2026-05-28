# AGENTS.md - MED-THERM Compliance Engine

## Structure
Simple dual-package repo, not a monorepo tool:
```
frontend/    # React 18 + TypeScript + Vite + Tailwind + shadcn/ui
backend/     # FastAPI 0.109+ + SQLAlchemy 2.0 + Pydantic 2.5 + Alembic
docker-compose.yml
```

---

## Frontend

**Entrypoint:** `frontend/src/App.tsx`
- All React Context providers wrap the entire app
- Routes: `/` (Dashboard), `/live` (LiveTransport), `/history`

**Context Providers** (global, available everywhere):
- `ThemeProvider` - dark/light mode with persistence
- `AnalysisProvider` - current analysis + history + isAnalyzing + refreshHistory
- `LiveTransportProvider` - persistent live transport (runs in background when navigating away)

**shadcn/ui Components:**
- Import from `@/components/ui` (re-exported via index.ts)
- Use the components, don't recreate raw HTML tables/buttons

**Commands:**
```bash
cd frontend
npm run build   # tsc + vite build (primary verification)
npm run lint    # eslint
npm run dev     # dev server
```

**Pattern to Follow for New Contexts:**
Follow `AnalysisContext.tsx` pattern:
1. Create interface `XxxContextType`
2. Use `createContext` + `useContext` custom hook
3. Provider wraps children in `App.tsx`

---

## Backend

**Entrypoint:** `backend/app/main:app`
- Uses uvicorn with hot reload in Docker
- PostgreSQL with asyncpg + psycopg2

**Commands:**
```bash
cd backend
pytest          # runs tests/ (pytest-asyncio required)
```

**Test Prerequisite:**
Tests expect PostgreSQL running at default localhost:5432, or use Docker compose.

---

## Docker (Development)

```bash
docker-compose up --build
```

**Ports:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432

**Hot Reload:**
- Volume mounts: `./frontend:/app` and `./backend:/app`
- Changes reflect without rebuild

**Required Env:**
```bash
MODELARK_API_KEY=your-key  # for AI analysis features
```

---

## Common Verification Sequence

When making changes:
```bash
cd frontend
npm run build    # catches TypeScript errors
npm run lint     # catches code issues
```

Backend: Start PostgreSQL, then:
```bash
cd backend
pytest
```

---

## Non-Obvious Conventions

1. **Colors:** Use `border-border`, `bg-muted`, `text-muted-foreground` - theme variables, NOT hardcoded `border-slate-100`

2. **Dark Mode:** When using text colors:
   ```typescript
   'text-green-600 dark:text-green-400'   // GOOD
   'text-yellow-600'                       // BAD - missing dark variant
   ```

3. **Touch Targets:** All interactive elements need:
   - `touch-target` class
   - Minimum 44x44px for accessibility

4. **Global State:** Use contexts, NOT component-local state, for:
   - Analysis switching
   - Live transport (must persist between navigation)
   - Theme

5. **Tables:** Use shadcn `<Table>` components, NOT raw `<table><tr><th>`
   - Mobile: Use `sm:hidden grid` + cards or `overflow-x-auto` wrapper
