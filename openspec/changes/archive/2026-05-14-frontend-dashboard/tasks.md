## 1. Vite Project Setup

- [x] 1.1 Initialize Vite + React + TypeScript project in frontend/ directory
- [x] 1.2 Configure TypeScript compiler options (strict mode)
- [x] 1.3 Add environment variable support (VITE_API_URL)
- [x] 1.4 Configure Vite proxy for backend API in development

## 2. Tailwind CSS & shadcn/ui Setup

- [x] 2.1 Install and configure Tailwind CSS
- [x] 2.2 Configure Tailwind config with custom colors (severity colors)
- [x] 2.3 Initialize shadcn/ui CLI in frontend project
- [x] 2.4 Install shadcn/ui components: button, card, table, dropdown, dialog, badge, input, select, tabs
- [x] 2.5 Install lucide-react for icons

## 3. API Client Layer

- [x] 3.1 Create src/lib/api directory structure
- [x] 3.2 Define TypeScript interfaces for all API request/response types
- [x] 3.3 Create base fetch client with error handling
- [x] 3.4 Implement logs API client (ingest, upload endpoints)
- [x] 3.5 Implement validation API client (validate endpoint)
- [x] 3.6 Implement reports API client (generate, get status)
- [x] 3.7 Implement AI API client (models, analyze-chart, analyze-logs)
- [x] 3.8 Install and configure React Query (TanStack Query) for caching

## 4. Dashboard Layout & Navigation

- [x] 4.1 Create main App.tsx with provider setup (QueryClientProvider)
- [x] 4.2 Create responsive Layout component with sidebar/header
- [x] 4.3 Implement desktop sidebar navigation with icons
- [x] 4.4 Implement mobile hamburger menu with drawer
- [x] 4.5 Create active page highlighting in navigation
- [x] 4.6 Set up route structure (home, upload, violations, temperature, reports)

## 5. File Upload Component

- [x] 5.1 Create FileUploadZone component with drag-and-drop area
- [x] 5.2 Implement drag-over visual feedback (highlighting)
- [x] 5.3 Create browse button with file dialog
- [x] 5.4 Implement file type validation (.txt, .png, .jpg, .jpeg, .pdf)
- [x] 5.5 Create upload queue display component
- [x] 5.6 Implement progress bars for upload status
- [x] 5.7 Implement success/error states with retry option
- [x] 5.8 Implement remove file from queue functionality

## 6. Violations Table

- [x] 6.1 Create ViolationsTable component using shadcn/ui table + TanStack Table
- [x] 6.2 Define table columns: REG Code, Severity, Description, Timestamp, Device
- [x] 6.3 Implement severity badge component with color coding (Critical=red, High=orange, Medium=yellow, Low=green, Info=blue)
- [x] 6.4 Implement column sorting (timestamp, severity, reg_code)
- [x] 6.5 Create filter controls: severity dropdown, REG category dropdown
- [ ] 6.6 Implement date range filter component
- [x] 6.7 Create "Clear Filters" button
- [x] 6.8 Implement empty state display
- [x] 6.9 Create ViolationDetail modal/dialog component
- [x] 6.10 Implement evidence display in detail view

## 7. Temperature Chart

- [x] 7.1 Install recharts library (package.json dependency)
- [x] 7.2 Create TemperatureChart component with LineChart
- [x] 7.3 Implement 2-8°C safe range shaded band
- [x] 7.4 Implement excursion highlighting (red for >8°C, blue for <2°C)
- [x] 7.5 Create custom tooltip with timestamp, temperature, sensor
- [x] 7.6 Implement multi-sensor support (dual lines, legend toggle)
- [ ] 7.7 Add sensor discrepancy highlighting (>0.5°C difference)
- [x] 7.8 Implement zoom and pan interactions (Brush component)
- [ ] 7.9 Create "Reset Zoom" button
- [ ] 7.10 Implement responsive behavior for mobile (simplified ticks)

## 8. Compliance Visualization

- [x] 8.1 Create SummaryCard component for REG categories
- [x] 8.2 Implement severity breakdown display inside cards
- [x] 8.3 Add click-to-filter behavior for cards
- [x] 8.4 Create ComplianceScore component with circular progress indicator
- [x] 8.5 Implement score color coding (green≥90, yellow70-89, orange50-69, red<50)
- [ ] 8.6 Create PassFailSummary component with counts
- [x] 8.7 Install additional charting for reports (pie/bar charts via Recharts)
- [x] 8.8 Create SeverityDistribution chart (pie)
- [x] 8.9 Create CategoryComparison chart (bar)
- [x] 8.10 Create ComplianceTrend chart (line for historical)
- [x] 8.11 Create time period selector (24h, 7d, 30d, Custom)

## 9. Main Dashboard Page

- [x] 9.1 Create Dashboard page with responsive grid layout
- [x] 9.2 Arrange summary cards in responsive grid (4-col desktop, 2-col tablet, 1-col mobile)
- [x] 9.3 Add compliance score component
- [x] 9.4 Add temperature chart component
- [x] 9.5 Add violations table component
- [ ] 9.6 Implement loading states for all components (partial - skeleton exists)
- [ ] 9.7 Implement error states with retry buttons

## 10. Testing & Polish

- [ ] 10.1 Test all responsive breakpoints
- [ ] 10.2 Test file upload with various file types and sizes
- [ ] 10.3 Test violations table filtering and sorting
- [ ] 10.4 Test chart interactions (zoom, hover, legend toggle)
- [x] 10.5 Add loading skeletons for better UX
- [x] 10.6 Add proper TypeScript types throughout
- [ ] 10.7 Run build to ensure no TypeScript errors
