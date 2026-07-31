# Changelog

## 2026-07-31 — M9-2 navigation and URL state

### Added

- Central Streamlit route definitions for public and hidden pages
- URL-backed ETF search and performance ranking state
- Source-aware return behavior from ETF detail
- Shared loading, empty, not-found and API-error components
- Query-state, navigation and shared-state regression tests

### Changed

- Search and ranking links now preserve filters and pagination
- Invalid URL parameters now fall back to canonical safe defaults

## 2026-07-31 — M9-1 performance ranking UX

### Changed

- Reordered ranking rows to show period return before ETF name
- Moved active/passive and bond/non-bond labels to the right
- Added an explicit bond/non-bond label to every ranking row
- Emphasized the selected period and return while preserving full-row links

### Added

- Regression tests for field order, classification labels and return formatting

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
