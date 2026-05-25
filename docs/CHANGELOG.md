# CHANGELOG

History of all significant changes in the project.

---

## [Unreleased]

### Added

- **Multi-Modal Analysis Pipeline**
  - Unified analysis of log files (.txt), chart images (.png, .jpg), and constraints documents (.md)
  - Multi-modal ingestion: merge, dedupe, and track sources across file types
  - Chart time alignment: synchronize chart data points with log timestamps
  - Temporal correlation: cross-check findings from logs and charts
  - Unified report generation: combine all sources with correlation insights

- **Unified Timeline**
  - Single chronological view of all violations
  - Source badges: Logs (blue), Chart (green), Correlated (orange)
  - Filter by source, zoom, pan, and hover for details

- **Correlation Insights**
  - Strong correlation: same violation detected in both sources
  - Weak correlation: violation in one source, timing mismatch in other
  - Conflicting findings: one source shows violation, other shows compliant
  - Correlation summary with counts and confidence scores

- **Severity-Based Violations Sorting**
  - Default sort: CRITICAL → HIGH → MEDIUM → LOW → INFO
  - Custom severity comparator for consistent ordering
  - Temperature severity mapping: T<0°C or T>10°C = CRITICAL, 0≤T<2 or 8<T≤10 = HIGH

- **New Multi-Modal API Endpoints**
  - `POST /api/multimodal/analyze` - Start multi-modal analysis (FormData)
  - `GET /api/multimodal/status/{session_id}` - Poll analysis status
  - `GET /api/multimodal/results/{session_id}` - Get final results
  - Background task processing with progress tracking

- **Alignment Uncertainty Banner**
  - Warning when chart/log time alignment confidence < 0.7
  - Appears when time ranges don't match or gaps exist
  - Guidance for users to verify data coverage

- **Dynamic Regulatory Rules Engine**
  - Upload custom regulatory constraints documents (.md, .txt)
  - AI extracts rules automatically using `/api/ai/extract-rules`
  - 5 rule type handlers: `threshold_range`, `duration_limit`, `frequency_limit`, `presence_check`, `inspection_only`
  - Confidence-based filtering: rules < 0.7 confidence skipped from auto-validation
  - Rules can be merged with default MED-THERM-2026 ruleset
  - Custom rules stored in `analysis_session.config._extracted_rules`
  - API responses include `has_custom_rules`, `ruleset_name`, `extracted_rules`, `ruleset_meta`
  - Rules tab displays custom rules with source indicator and confidence levels

- **New API Endpoints**
  - `GET /api/ai/rules-info` - Dynamic rule extraction capability info
  - `POST /api/ai/extract-rules` - Extract rules from text document
  - Updated: `/api/validate`, `/api/reports/generate`, `/api/ai/analyze-chart` accept `extracted_rules` parameter

- **Updated Documentation**
  - `docs/user-guide/uploading-files.md` - Complete custom rules workflow guide
  - `docs/user-guide/analyzing-results.md` - Unified timeline, correlation insights, severity sorting
  - `docs/architecture/api.md` - All new endpoints (multi-modal + dynamic rules) documented
  - `docs/architecture/overview.md` - Updated architecture diagram with multi-modal pipeline
  - `docs/architecture/regulatory-engine.md` - Corrected rule count (21 rules)
  - `docs/developer-guide/testing.md` - 231 passing tests, pytest-asyncio requirement

- Dark Mode complete with persistence and toggle

- Documentation restructuring according to best practices

- Custom branding with MED-THERM logo

### Fixed

- **Rule Count Correction**: Changed all references from 25 rules to 21 rules (MED-THERM-2026 has 21 rules)
- **Test Suite**: All 231 tests now passing (previously 15 failing)
  - Fixed category names: `"thermal"` → `"TEMP"`, `"sensor"` → `"SENS"`, etc.
  - Fixed log file path: `docs/client/` → `docs/user-guide/examples/`
  - Added `pytest-asyncio>=0.21.0` to dependencies
  - Fixed `IndentationError` in `app/api/ai.py` (space/tab mixing)
  - Fixed missing `AITimeoutError` import
  - Fixed missing `ModelArkClient._extract_response_content` method
  - Fixed `_extract_json_from_text` regex greedy issue

- **Category Inconsistency**: Fixed category name mismatch between backend and frontend
- **Chart Source Detection**: Fixed "Chart" badge in timeline (detects `"images"` source in addition to `"chart_image"`)
- **React Closure Issue**: Fixed `useRef` for `extractedRulesRef` to preserve rules between uploads
- **MD File Support**: Fixed `.md` file visibility and detection as constraints documents
- **Disabled Click**: Disabled click on category cards in Overview (prevents navigation issues)
- **AI Analysis for Chart-Only Mode**: Multi-modal endpoint `/api/multimodal/analyze` now runs AI analysis for chart-only uploads (previously AI only ran when log files were present). Uses `AIAnalystEngine.analyze_chart()` for chart data, matching behavior of standalone `/api/ai/analyze-chart` endpoint.

---

## [1.0.0] - 2026-05-12

### Added

- Initial release

- Regulatory Engine with 21 rules

- Log Parser

- AI Integration (ModelArk)

- Frontend Dashboard

- PostgreSQL database
