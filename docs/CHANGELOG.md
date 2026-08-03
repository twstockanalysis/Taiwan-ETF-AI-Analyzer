# Changelog

Entries are ordered chronologically from oldest to newest.

## 2026-07-27 — M1–M4 early project foundation

### Added

- Initial repository and Taiwan ETF analyzer project identity
- Python entry point, dependency scaffolding and Git-ignore rules
- Python foundation exercises for variables, data types, lists, dictionaries,
  loops, conditions and functions
- Configuration, calculator, portfolio and scoring prototype modules
- Backend, frontend and documentation project structure

## 2026-07-28 — ETF API

### Added

- ETF list pagination
- Keyword, active/passive and bond filters
- API response metadata and automated tests

## 2026-07-29 — ETF data engine and frontend

### Added

- End-to-end ETF master update Pipeline
- Import-batch audit and quality reports
- Streamlit frontend, ETF search and hidden detail page
- Frontend API error handling and AppTest coverage

### Fixed

- ROC listing dates are normalized to Gregorian ISO dates

## 2026-07-30 — M8 performance and dividends

### Added

- Multi-period price-return Pipeline and ranking API
- Streamlit performance ranking
- TWSE dividend events and estimated composition
- Dividend history, detail and ACTUAL 76W APIs
- ETF-detail dividend and 76W views

## 2026-07-31 — M8 actual-dividend quality

### Added

- Human-reviewed ACTUAL dividend composition import
- Official source-document versioning
- Verified Cathay actual-composition Adapter
- ACTUAL and 76W coverage calculations
- Dividend source-review queue
- Read-only data-quality APIs
- Streamlit dividend-data-quality page

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

## 2026-07-31 — M9-1 performance ranking UX

### Changed

- Reordered ranking rows to show period return before ETF name
- Moved active/passive and bond/non-bond labels to the right
- Added an explicit bond/non-bond label to every ranking row
- Emphasized the selected period and return while preserving full-row links

### Added

- Regression tests for field order, classification labels and return formatting

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

## 2026-07-31 — M9-3 homepage system overview

### Added

- Read-only `GET /api/v1/system/overview` endpoint
- ETF classification, performance-period and dividend-quality summaries
- Data-freshness dates and five recent import-batch summaries
- Homepage feature entry points and data overview cards
- Repository, API, frontend Client and AppTest coverage

### Changed

- Homepage now loads operational data through FastAPI instead of showing only
  a static feature list and health check
- Empty coverage and missing dates retain null semantics

## 2026-07-31 — M9-4 ETF detail information architecture

### Added

- Read-only ETF data-profile API with source and freshness metadata
- ETF-master, performance, dividend and ACTUAL source references
- Latest import, as-of, event and official-document dates
- Reserved ETF comparison entry for M9-5
- Repository, API, frontend Client and page-architecture tests

### Changed

- ETF detail now follows one fixed decision-oriented section order
- Repeated identity and classification rows were consolidated
- Secondary API failures no longer prevent unrelated detail sections from
  rendering
- Missing dates remain unavailable rather than using the current date

## 2026-07-31 — M9-5 ETF comparison page

### Added

- Read-only `GET /api/v1/etfs/comparison` aggregation endpoint
- Public ETF comparison page with stable `codes` URL state
- 2–4 ETF comparison for identity, 1M/3M/6M/1Y PRICE_RETURN, dividends, ACTUAL 76W and data completeness
- Source-aware return behavior from search, ranking and ETF detail
- Comparison entry points on the homepage, search, ranking and detail pages
- Repository, API, frontend Client, URL-state and display-contract tests

### Changed

- The M9-4 detail-page comparison placeholder is now enabled
- Missing performance and missing ACTUAL 76W remain unavailable instead of becoming zero
- Formal ACTUAL `76W = 0%` remains an available record

## 2026-08-01 — M9-6 shared frontend UI

### Added

- Shared percentage, number, money, date and datetime formatters
- Shared ETF management and asset-classification labels
- Shared full-row ETF detail links and pagination controls
- Shared warning-state presentation with optional diagnostic details
- Formatter, component and architecture-contract tests

### Changed

- Search, ranking, detail, comparison, homepage and dividend-quality pages now reuse shared UI utilities
- Existing page-level formatter names remain available for regression compatibility
- Missing values remain distinct from formal numerical zero
- M9 website structure and page-completeness phase is complete

## 2026-08-01 — M10-0 multi-period performance display

### Added

- Read-only multi-period performance-ranking endpoint
- Ranking rows that display available 1M, 3M, 6M and 1Y PRICE_RETURN together
- Responsive Streamlit typography for metrics, page links and sidebar labels
- Repository, API, frontend Client, display and responsive-style tests

### Changed

- Six months remains the default and preferred ranking period
- Selecting another period changes ranking order without hiding other periods
- Homepage performance-coverage metrics use compact values to avoid ellipsis
- Missing period data remains `歷史資料不足` instead of numerical zero

## 2026-08-01 — M10-0R1 ranking display refinement

### Changed

- Performance ranking rows now show only the currently selected sort period
- Six months remains the default ranking period
- Other periods remain available through the sort-period selector and on ETF detail and comparison pages
- Ranking display names hide trailing `(原名：...)` annotations without changing stored or API names

## 2026-08-01 — M10-1C expanded dividend summary

### Added

- Traceable official distribution periods and per-event dividend yields
- Official-first yield policy with a persisted previous-trading-day fallback
- Dual-axis cash-dividend/yield trend and detailed dividend-summary table
- Database, pipeline, API, Client and frontend regression coverage

### Changed

- ETF detail no longer requests or renders the monthly-income distribution
- The monthly-income API and its tested data contract remain available
- Missing official distribution periods display `—` and are never inferred

## 2026-08-02 — M10-R0A legacy cleanup

### Removed

- Completed Python tutorial files and obsolete prototype entry points
- Unused ETF-detail monthly-income chart code

### Changed

- The monthly-income API and its regression-tested data contract remain
  available after the UI cleanup
- Production backend, frontend and data behavior remain unchanged

## 2026-08-03 — M10-R0B frontend API modularization

### Added

- Focused frontend API modules for errors, validators, normalizers and transport
- Domain modules for ETFs, performance, dividends, dividend quality and system
  overview
- Domain modules for ETF data profile, comparison and health checks
- Architecture-contract tests for module boundaries, compatibility exports and
  the established `httpx` mock path

### Changed

- `frontend/api_client.py` now acts as a compatibility facade for extracted
  modules and contains no function or class implementation
- Existing import names and `httpx` mock paths remain compatible
- Frontend architecture documentation now describes the facade, domain modules
  and shared transport boundary
- Every extraction passed the focused Client tests and full regression suite
