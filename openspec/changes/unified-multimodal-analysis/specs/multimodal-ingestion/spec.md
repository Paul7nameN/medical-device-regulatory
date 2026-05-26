## ADDED Requirements

### Requirement: Multi-modal batch ingestion
The system SHALL accept batch upload of multiple files (logs, charts, constraints documents) and process them together in a single unified analysis session.

#### Scenario: Detect multiple file intents
- **WHEN** user uploads multiple files in batch
- **THEN** each file's intent is detected using existing `detectFileIntent` logic (filename patterns + content preview)

#### Scenario: Merge multiple log files
- **WHEN** batch includes 2+ log files
- **THEN** all log entries are parsed, sorted by timestamp, and deduplicated by (timestamp, log_type, raw_value) tuple

#### Scenario: Deduplicate overlapping log entries
- **WHEN** merged log files contain overlapping time ranges with identical entries
- **THEN** duplicate entries are removed, keeping one copy per unique tuple

#### Scenario: Extract rules from constraints document
- **WHEN** batch includes a constraints document
- **THEN** rules are extracted and available for the entire unified analysis

#### Scenario: Track all source files
- **WHEN** batch upload completes ingestion
- **THEN** `AnalysisSession.config._sources` array contains metadata about all uploaded files (name, type, entry_count, time_range)

### Requirement: Unified analysis session creation
The system SHALL create exactly ONE AnalysisSession for a multi-modal batch upload, containing all ingested data sources.

#### Scenario: Single session for batch
- **WHEN** user runs unified analysis on a batch of files
- **THEN** exactly one AnalysisSession record is created

#### Scenario: Session config contains sources
- **WHEN** unified session is created
- **THEN** `config._sources` array is populated with file metadata

#### Scenario: Backward compatible single-file
- **WHEN** user uploads just one file using existing endpoints
- **THEN** behavior is unchanged (isolated session, no `_sources` required)

### Requirement: Multi-modal API endpoints
The system SHALL expose REST API endpoints for batch multi-modal analysis with status polling.

#### Scenario: Submit batch for analysis
- **WHEN** client calls `POST /api/multimodal/analyze` with files and options
- **THEN** analysis is queued/started, returns session_id for polling

#### Scenario: Poll analysis status
- **WHEN** client calls `GET /api/multimodal/status/{id}`
- **THEN** returns current status (pending, processing, completed, failed) with progress details

#### Scenario: Retrieve unified results
- **WHEN** client calls `GET /api/multimodal/results/{id}` after completion
- **THEN** returns unified report with all multi-modal enhancements
