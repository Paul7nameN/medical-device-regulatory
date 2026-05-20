# CHANGELOG

History of all significant changes in the project.

---

## [Unreleased]

### Added

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
  - `docs/architecture/api.md` - All new endpoints documented with examples

- Dark Mode complete with persistence and toggle

- Documentation restructuring according to best practices

- Custom branding with MED-THERM logo

### Fixed

- Fixed category inconsistency between backend and frontend

- Disabled click on category cards in Overview

- Fixed React closure issue: `useRef` for `extractedRulesRef` to preserve rules between file uploads

- Fixed `.md` file support: now visible in file browser, detected as text, auto-detected as constraints document

---

## [1.0.0] - 2026-05-12

### Added

- Initial release

- Regulatory Engine with 21 rules

- Log Parser

- AI Integration (ModelArk)

- Frontend Dashboard

- PostgreSQL database
