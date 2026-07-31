# Changelog

## 2026-07-31 — M8 completion audit

### Added

- M8 architecture smoke tests
- M8 completion-audit document
- Current API, schema, frontend, source and architecture documentation

### Changed

- Normal database initialization now runs the performance-metric Migration
- Roadmap now marks M8 completed and identifies M9 as the next website phase

### Fixed

- Stale and duplicated API documentation
- Unbalanced Markdown code fences in legacy documents
- Missing automatic upgrade path for pre-`metric_code` performance tables

## 2026-07-31 — M8 actual-dividend quality

### Added

- Human-reviewed ACTUAL dividend composition import
- Official source-document versioning
- Verified Cathay actual-composition Adapter
- ACTUAL and 76W coverage calculations
- Dividend source-review queue
- Read-only data-quality APIs
- Streamlit dividend-data-quality page

## 2026-07-30 — M8 performance and dividends

### Added

- Multi-period price-return Pipeline and ranking API
- Streamlit performance ranking
- TWSE dividend events and estimated composition
- Dividend history, detail and ACTUAL 76W APIs
- ETF-detail dividend and 76W views

## 2026-07-29 — ETF data engine and frontend

### Added

- End-to-end ETF master update Pipeline
- Import-batch audit and quality reports
- Streamlit frontend, ETF search and hidden detail page
- Frontend API error handling and AppTest coverage

### Fixed

- ROC listing dates are normalized to Gregorian ISO dates

## 2026-07-28 — ETF API

### Added

- ETF list pagination
- Keyword, active/passive and bond filters
- API response metadata and automated tests
