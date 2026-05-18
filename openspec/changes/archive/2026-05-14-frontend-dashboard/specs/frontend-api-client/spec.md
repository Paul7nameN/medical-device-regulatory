## ADDED Requirements

### Requirement: API client architecture
The frontend SHALL use a centralized API client layer for all backend communication with TypeScript type definitions.

#### Scenario: Centralized client
- **WHEN** making API calls
- **THEN** all components use the same API client rather than direct fetch calls

#### Scenario: Base URL configuration
- **WHEN** in development vs production
- **THEN** API base URL is configurable via environment variable

#### Scenario: TypeScript interfaces
- **WHEN** defining API contracts
- **THEN** TypeScript interfaces exist for all request/response payloads

### Requirement: Logs and analysis endpoints
The API client SHALL provide methods for uploading files, ingesting logs, and running validation.

#### Scenario: File upload endpoint
- **WHEN** uploading files for analysis
- **THEN** client uses `POST /api/logs/ingest` endpoint with multipart/form-data

#### Scenario: Log ingestion
- **WHEN** sending log text directly
- **THEN** client sends JSON payload to appropriate endpoint

#### Scenario: Validation endpoint
- **WHEN** running compliance validation
- **THEN** client calls `POST /api/validate` endpoint

### Requirement: Report endpoints
The API client SHALL provide methods for generating and retrieving compliance reports.

#### Scenario: Generate report
- **WHEN** user requests a compliance report
- **THEN** client calls `POST /api/reports/generate` endpoint

#### Scenario: Get report status
- **WHEN** report is generating
- **THEN** client can poll for status or receive completion notification

#### Scenario: Get recent analyses
- **WHEN** viewing analysis history
- **THEN** client fetches list of recent analysis sessions and reports

### Requirement: AI/VLLM endpoints
The API client SHALL provide methods for AI-powered document/image analysis.

#### Scenario: Available AI models
- **WHEN** checking AI capabilities
- **THEN** client calls `GET /api/ai/models` for available models

#### Scenario: Chart analysis
- **WHEN** analyzing temperature chart images
- **THEN** client calls `POST /api/ai/analyze-chart` endpoint

#### Scenario: Log analysis
- **WHEN** analyzing log data with AI
- **THEN** client calls `POST /api/ai/analyze-logs` endpoint

### Requirement: Error handling and loading states
The API client SHALL provide consistent error handling and support loading states for UI feedback.

#### Scenario: Request loading state
- **WHEN** API request is in-flight
- **THEN** client provides loading indicator via hook or promise state

#### Scenario: Error response handling
- **WHEN** API returns error status (4xx, 5xx)
- **THEN** client parses error message and provides typed error object

#### Scenario: Network error handling
- **WHEN** network request fails (no connection)
- **THEN** client provides user-friendly network error message

#### Scenario: Request retries
- **WHEN** transient error occurs
- **THEN** client automatically retries request (configurable)
