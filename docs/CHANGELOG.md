# Changelog

## 2026-08-12 — Refreshed M12 entry gate after M11-5 merge

- Reconciled merged main `1e0a920` against the post-M9 confirmed direction,
  current PRD, actual Streamlit flow, API boundaries and deployment database.
- Recorded M11-5A1, M11-5A2 and M11-5B as complete and merged.
- Closed the former base-target and principal-risk product gaps without adding
  account, broker, trading, real-time or AI scope.
- Ordered M12 from schema/migration safety through durability, scheduling,
  owner protection, deployment and the final launch-data decision.

## 2026-08-12 — M11-5B deterministic principal-risk warnings

- Added source-dated negative-total-return, persistent-decline, weak-recovery
  and material-peer-underperformance warnings to base-ETF target analysis.
- Defined fixed thresholds and preserved missing risk facts without inferring a
  safe or zero result.
- Added visible warning evidence and direct AppTests for target-risk,
  tax/reinvestment and monthly-combination result sections.
- Annualized multi-year price-return inputs before scenario projection.

## 2026-08-10 — M11-5A2 visible base ETF cash-flow analysis

- Added a read-only latest-close API returning the stored official price,
  trading date and source, while preserving a missing price as null.
- Exposed the existing base-ETF target analysis on ETF detail before the
  tax/reinvestment section without allowing the official price to be overridden.
- Added required capital, funding shortfall, annual target coverage and a
  January-December historical annualized gross/after-tax cash table.
- Moved generic cash-deduction application into the backend calculation path;
  omitted assumptions and no-event months remain unavailable rather than zero.
- Added API client, contract, information-architecture and Streamlit regression
  coverage for the visible flow.

## 2026-08-10 — M11-5A1 dynamic holdings and official close boundary

- Added an idempotent `etf_daily_close` store populated from the existing TWSE
  performance download without an additional market-data request.
- Added an atomic batch holding API accepting zero to any number of rows with
  only ETF code and positive whole units.
- Changed the Streamlit holding editor to an initially empty, dynamic two-column
  grid with native row addition and deletion controls.
- Derived saved holding prices, dates and sources from the latest stored
  official close; missing prices remain null and block value-dependent results.
- Added a lossless legacy manual-price migration and Repository, Pipeline, API,
  analysis, client and AppTest regression coverage.

## 2026-08-10 — M11-4 decision records and Excel export

- Added append-only candidate assessment snapshots containing the original
  request, full analysis, rationale, exclusions, alternatives and risk notes.
- Added server-side re-analysis before persistence and intentionally omitted
  record update/delete operations.
- Added list/detail/export APIs and a five-sheet typed `.xlsx` workbook.
- Added Streamlit save, record-list, prepare and native download actions.
- Preserved single-user, no-broker, no-trading and pre-M12 audit boundaries.

## 2026-08-10 — M11-3 candidate holding analysis

- Added a read-only candidate ETF scenario comparing the saved current
  portfolio with the same portfolio after a proposed addition
- Reused M11-2 portfolio aggregation and M10-5 eligibility, exclusion and
  payment-month reason contracts
- Kept the fixed monthly target unchanged as candidate capital increased
- Preserved missing deduction and holding-overlap assumptions instead of zero
- Added FastAPI, frontend client, native Streamlit comparison and integration
  coverage confirming that candidate analysis does not persist a holding
- Added a mandatory pre-M12 audit gate based on post-M9 direction commit
  `03a9635`, the current PRD and explicit user confirmation

## 2026-08-09 — M11-2 current-holding analysis

- Added a read-only analysis that aggregates every saved manual holding and
  applies the fixed monthly target once at portfolio level
- Annualized selected period PRICE_RETURN values before current-value weighting
- Reused the existing M10 target calculator for cash-flow coverage and the
  no-reinvestment scenario instead of duplicating formulas
- Preserved missing deductions, distributions and performance as explicit
  partial results rather than zero
- Added FastAPI, frontend client, native Streamlit metrics/table and focused
  service, integration and AppTest coverage

## 2026-08-09 — M11-1 single-user conditions and manual holdings

- Added SQLite persistence for one fixed decision profile and manual ETF
  holdings without adding accounts or broker connectivity
- Added conditions for monthly after-tax target, analysis/history years and an
  optional generic cash-deduction rate
- Added idempotent holding upserts and explicit deletes using positive whole
  units, user-entered TWD reference prices and optional price dates
- Added `GET/PUT/DELETE` decision-profile FastAPI contracts
- Added a Streamlit management page using native forms, a static holdings table
  and a delete-confirmation dialog
- Added Schema, Repository, API, frontend client, navigation and AppTest
  coverage

## 2026-08-09 — M10-5 monthly-payment combination

- Added a base-anchored, Decimal-based candidate eligibility and month-gap
  calculation that selects at most one to three complementary ETFs
- Added explicit completeness, freshness, distribution-stability, after-tax
  cash, total-return, downside, holding-overlap and concentration gates
- Preserved missing overlap as an explicit limitation and formal zero as data
- Added `POST /api/v1/etfs/{code}/monthly-payment-combination`
- Added a comparison-page Streamlit form with separate selected and rejected
  candidates, supported months, classifications and plain-language reasons
- Added focused calculation, data conversion, API, frontend client and display
  tests

## 2026-08-09 — M10-4 tax and reinvestment scenarios

- Added a versioned Taiwan-individual tax assumption contract for official
  ACTUAL component codes, income-tax credits and supplementary premiums
- Added no-reinvestment, excess-only, custom-percentage and full-reinvestment
  projections with usable cash, ending units/value and after-tax total return
- Preserved formal ACTUAL zero ratios and kept missing composition or tax rules
  unavailable instead of treating them as zero
- Added `POST /api/v1/etfs/{code}/tax-reinvestment-scenarios`
- Added the ETF-detail Streamlit estimator with an explicit estimate/not-tax-
  advice label and total-return failure warning
- Added focused calculation, ACTUAL selection, API and frontend client tests

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
