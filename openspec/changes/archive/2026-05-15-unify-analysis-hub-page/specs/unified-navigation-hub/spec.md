## ADDED Requirements

### Requirement: Unified Analysis Hub
The system SHALL provide a single unified interface for viewing all analysis data, rather than splitting it across multiple pages.

#### Scenario: Single entry point for analysis
- **WHEN** user uploads or loads an analysis
- **THEN** all data (compliance score, temperature, violations) is accessible from one page

#### Scenario: Tab-based navigation within hub
- **WHEN** user wants to switch between different data views
- **THEN** tab controls allow switching without page navigation

#### Scenario: Persistent context header
- **WHEN** viewing any tab within the hub
- **THEN** the analysis header (score, device ID, timestamp) remains visible

### Requirement: Simplified sidebar navigation
The system SHALL reduce navigation options to only what's necessary for the single-active-analysis use case.

#### Scenario: Minimal sidebar
- **WHEN** viewing any page
- **THEN** sidebar shows only "Home" (Analysis Hub) and "Upload"

#### Scenario: Route redirection for old paths
- **WHEN** user navigates to old paths like `/violations`, `/temperature`, `/reports`
- **THEN** they are redirected to the unified hub at `/`

### Requirement: Accessible analysis history
The system SHALL make previous analyses accessible from within the unified hub.

#### Scenario: History tab in hub
- **WHEN** user wants to load a previous analysis
- **THEN** a "History" tab within the hub lists all stored analyses

#### Scenario: Load previous analysis
- **WHEN** user selects an analysis from history
- **THEN** the hub switches to display that analysis's data
