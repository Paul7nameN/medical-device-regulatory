## Context

The MED-THERM Compliance Platform has a fully functional FastAPI backend with regulatory analysis, VLLM integration, and PostgreSQL persistence. However, there is no user-facing frontend to:
- Upload log files, images, or documents for analysis
- Visualize compliance reports and detected violations
- Monitor temperature telemetry over time
- View severity-coded violations with REG-* code references

**Constraints**:
- Tech stack: React + TypeScript (per project context)
- Mobile-first responsive design required
- Backend APIs exist at `/api/*` endpoints
- No authentication for PoC (single-user mode)
- CORS already configured to allow all origins

## Goals / Non-Goals

**Goals:**
- Set up Vite + React + TypeScript project
- Implement responsive dashboard layout (desktop, tablet, mobile)
- Create drag-and-drop file upload for logs, images, documents
- Build violations data table with severity color coding
- Create temperature timeline chart
- Implement summary cards for REG category violation counts
- Build API client layer to communicate with FastAPI backend

**Non-Goals:**
- User authentication (PoC is single-user)
- Real-time data updates via WebSocket
- Multi-device management UI
- Report export functionality (future enhancement)
- Dark mode toggle (future enhancement)

## Decisions

### 1. Build Tool: Vite
**Decision**: Use Vite as the build tool
**Rationale**:
- Vite is the modern standard for React projects
- Faster development experience than Create React App
- Native TypeScript support
- Optimized production builds
**Alternatives considered**:
- Create React App (deprecated, slower)
- Next.js (overkill for client-only dashboard, backend already exists)
- Parcel (less configuration but less ecosystem support)

### 2. Styling: Tailwind CSS
**Decision**: Use Tailwind CSS for utility-first styling
**Rationale**:
- Fast UI development with utility classes
- Mobile-first responsive design built-in
- Consistent spacing and sizing
- Works well with shadcn/ui components
**Alternatives considered**:
- CSS Modules - More verbose
- Styled Components - Runtime overhead, slower DX
- Material UI - Opinionated, heavy bundle

### 3. Component Library: shadcn/ui
**Decision**: Use shadcn/ui for accessible, customizable components
**Rationale**:
- Built on Radix UI (accessible by default)
- Uses Tailwind CSS for styling
- Components installed as source code (not importable library)
- Table, Card, Dropzone, Button components needed
**Alternatives considered**:
- Mantine - Good but larger dependency
- Chakra UI - CSS-in-JS, conflicts with Tailwind approach
- Headless UI + own styling - More work

### 4. Charting Library: Recharts
**Decision**: Use Recharts for temperature timeline visualization
**Rationale**:
- Native React components
- Built with SVG
- Responsive charts out of the box
- Line chart perfect for temperature timeline
- Customizable tooltips and styling
**Alternatives considered**:
- Chart.js + react-chartjs-2 - Slightly heavier
- D3.js - Too low-level, more code
- ECharts - Feature rich but complex for simple line chart
- Tremor (built on Recharts) - Good but opinionated styling

### 5. API Client: Custom Fetch + React Query (TanStack Query)
**Decision**: Custom fetch wrapper + React Query for data fetching and caching
**Rationale**:
- React Query handles caching, loading states, error handling
- Automatic background refetching
- Simple integration with FastAPI REST endpoints
- TypeScript support
**Alternatives considered**:
- Axios - Good but heavier than fetch
- SWR - Similar to React Query, slightly smaller ecosystem
- RTK Query - Requires Redux, overkill for this project

### 6. Severity Color Coding
**Decision**: Standard traffic-light color scheme
- Critical: Red (#dc2626 / text-red-600)
- High: Orange (#ea580c / text-orange-600)
- Medium: Yellow (#ca8a04 / text-yellow-600)
- Low: Green (#16a34a / text-green-600)
- Info: Blue (#2563eb / text-blue-600)
**Rationale**: Intuitive, universally understood for severity levels

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Mobile chart readability | Use responsive container, allow zoom, simplify on small screens |
| File upload size limitations | Frontend validation of file size, display clear error messages |
| API endpoint changes | Centralized API client with typed interfaces, easy to update |
| Large violation tables causing lag | Virtualization (tanstack-virtual) or pagination |
| Tailwind learning curve for new devs | Use shadcn/ui components as foundation, consistent patterns |

## Migration Plan

1. **Initialize Vite project** in `frontend/` directory
2. **Install dependencies**: React, TypeScript, Tailwind, shadcn/ui, Recharts, React Query
3. **Configure shadcn/ui** with Tailwind
4. **Build components** in order: Layout → API Client → Upload → Table → Chart → Cards
5. **Integrate with backend** - test against running FastAPI server

**Rollback Strategy**: Since this is a new frontend directory, no rollback needed. Simply delete `frontend/` if issues arise.

## Open Questions

- None at this stage - all decisions reasonably scoped for PoC
