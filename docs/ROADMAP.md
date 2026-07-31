# Project Roadmap

## Completed foundation

### M5 — FastAPI backend

Completed:

- Application factory, router architecture, health endpoints
- ETF Repository, list/detail APIs, filters and pagination
- Pydantic response validation, OpenAPI and automated tests

### M6 — ETF data engine

Completed:

- TWSE and TPEx source Registry
- Official ETF-master download and normalization
- Raw, processed, rejected and quality-report artifacts
- Safe SQLite upsert and import-batch audit trail
- Removal of development seed records

### M7 — Streamlit frontend

Completed:

- Streamlit application shell and configurable FastAPI URL
- ETF search, filters, pagination and hidden detail page
- Consistent Gregorian dates, missing-data display and AppTest coverage

## M8 — ETF analysis data — Completed

M8 was closed on 2026-07-31 after the M8-5A completion audit.

### M8-1 — Analysis schema and models

Completed:

- `etf_performance`
- `etf_dividend`
- `etf_dividend_component`
- Flexible source component codes, including official `76W`
- Foreign keys, indexes and repository-level upsert policies

### M8-2 — Performance

Completed:

- TWSE daily closing-price source
- `PRICE_RETURN`, `TOTAL_RETURN` and `NAV_RETURN` metric model
- Reusable 1M, 3M, 6M and 1Y price-return calculations
- Multi-period Pipeline with one download per ETF
- Period-specific coverage reports and insufficient-history handling
- Ranking and single-ETF APIs
- Streamlit ranking and ETF-detail performance views

Current production calculation:

```text
metric_code = PRICE_RETURN
includes_distributions = false
```

`TOTAL_RETURN` and `NAV_RETURN` are schema capabilities, not yet populated
calculation products.

### M8-3 — Dividend history and estimated composition

Completed:

- TWSE ETF e添富 dividend-event source
- ROC-to-Gregorian date normalization
- Estimated composition codes
- Safe duplicate-event and conflicting-composition handling
- Dividend history, detail, component-filter and actual-76W APIs
- ETF-detail dividend and 76W views

The following remains a strict invariant:

```text
EST_REALIZED_CAPITAL_GAIN != 76W
```

### M8-4 — Actual composition and data quality

Completed:

- Human-reviewed ACTUAL notice JSON import
- Verified official-source Registry and source-document versioning
- First verified Cathay actual-composition Adapter
- Official `76W` and `54C` preservation
- Actual-composition event matching and atomic upsert
- Actual, 76W and source-document coverage calculations
- Source-review queue and read-only data-quality APIs
- Streamlit dividend-data-quality page

Formal `76W = 0%` is covered data. Missing 76W remains missing.

### M8-5A — Completion audit

Completed:

- Added automatic performance-metric Migration to normal initialization
- Added fresh-schema, API-route, frontend-navigation and documentation smoke tests
- Reconciled M8 documentation with the implemented architecture
- Recorded current limitations and deferred work

## M9 — Website structure and page completeness

M9 contains website product work only. Broker and market-vendor APIs are not
part of M9.

### M9-1 — Performance ranking UX — Completed

Completed:

- Fixed the ranking row order as:

```text
rank and ETF code
-> performance period and return
-> ETF name
-> as-of date
-> active/passive
-> bond/non-bond
```

- Emphasized period and return near the left edge
- Moved management and asset classifications to the right
- Preserved full-row navigation to the hidden ETF detail page
- Added display-order, classification and return-format regression tests

### M9-2 — Navigation and information architecture — Completed

Completed:

- Centralized public and hidden page definitions in `frontend/navigation.py`
- Added stable URL state for ETF search and performance ranking filters
- Preserved page number and page size across refresh and shared links
- Added source-aware return behavior from ETF detail
- Added reusable loading, empty, not-found and API-error states
- Added invalid-query fallback and navigation regression tests

### M9-3 — Homepage and system overview

Planned:

- ETF totals and latest data dates
- Performance and dividend coverage
- Latest import batches
- Primary feature entry points

### M9-4 — ETF detail-page organization

Planned sections:

- Basic information
- Market-price performance
- Dividend summary
- Actual 76W
- Dividend events and components
- Data sources and freshness
- Comparison entry point

### M9-5 — ETF comparison page

Planned comparison fields:

- 1M, 3M, 6M and 1Y performance
- Management and asset classifications
- Listing date
- Dividend history and frequency
- Actual 76W availability
- Data completeness

### M9-6 — Shared frontend components

Planned:

- Percentage, money and date formatters
- ETF classification labels
- Clickable rows and pagination
- Empty, warning and error components

## M10 — Core analysis features

Planned after M9:

- Monthly-income allocation
- Dividend-month distribution
- Non-bond ETF selection
- Active/passive comparison
- Six-month performance and 76W scoring
- ETF combination analysis and explanation

## M11 — Decision platform

Planned:

- User conditions and manual holdings
- Candidate scoring, exclusions and alternatives
- Recommendation rationale and risk notes
- Decision records and Excel export

## M12 — Automation and deployment

Planned:

- Scheduled data Pipelines
- Failure monitoring and freshness checks
- Administration status
- Backup and recovery
- Public deployment, domain and HTTPS

## Optional external integrations — after the core website

Deferred until M9–M12 are complete:

- Third-party market-data evaluation
- Fugle market-data API
- Sinopac Shioaji read-only account synchronization
- Portfolio import
- Simulated or live order assessment

These optional integrations must not block the core website roadmap.
