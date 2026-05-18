## Why

The MED-THERM Compliance Platform currently lacks a user interface for visualizing compliance data. Users need an intuitive dashboard to upload log files, view temperature telemetry, and understand detected regulatory violations at a glance. A frontend dashboard will bridge the backend regulatory engine with human-readable insights.

## What Changes

- Create a new Vite + React + TypeScript frontend project in `frontend/` directory
- Implement fully responsive, mobile-first dashboard layout
- File upload component supporting logs (text), images, and documents
- Compliance report visualization with summary statistics
- Violations data table with severity-based color coding
- Temperature timeline chart for visualizing thermal excursions
- Summary cards showing violation counts grouped by REG category
- API client layer to communicate with FastAPI backend

## Capabilities

### New Capabilities
- `dashboard-layout`: Responsive mobile-first dashboard layout and navigation
- `file-upload`: Multi-file upload component with drag-and-drop support
- `violations-table`: Interactive data table for detected violations with filtering
- `temperature-chart`: Timeline visualization of temperature telemetry data
- `compliance-visualization`: Summary cards and compliance score display
- `frontend-api-client`: API client layer for backend communication

### Modified Capabilities
- None

## Impact

- New `frontend/` directory with Vite React project
- New npm dependencies: React, TypeScript, Vite, recharts (or similar charting), shadcn/ui components
- Backend APIs accessed via new frontend client layer
- CORS configuration already supports frontend access (backend config has `cors_origins: ["*"]`)
