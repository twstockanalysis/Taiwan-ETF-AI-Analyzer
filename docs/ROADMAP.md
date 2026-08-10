# Project Roadmap

## Product direction

The website is a Taiwan ETF cash-flow decision tool for individual investors
with limited professional information. A user starts from one self-selected ETF
and a fixed monthly after-tax cash-flow target. The website then evaluates
required capital, tax effects, total return, reinvestment and optional monthly
payment coverage.

All new decision features follow this priority:

```text
total-return and principal-risk checks
-> after-tax cash-flow feasibility
-> tax-efficiency improvement
-> optional monthly-payment coverage
```

The decision layer remains stateless through M10. User conditions and holdings
are persisted only after the calculation contracts are stable in M11.

## Completed foundation

M1–M4 were restored from the 2026-07-27 Git history. They record the early
learning and project-structure foundation that preceded the production API.

### M1 — Repository initialization

Completed:

- Created the Git repository and initial project identity
- Established the Taiwan ETF analyzer as the project scope

### M2 — Python development bootstrap

Completed:

- Added the first Python entry point
- Added dependency and Git-ignore scaffolding
- Established the local Python development workflow

### M3 — Python foundations

Completed:

- Variables and data types
- Lists and dictionaries
- `for` loops and `if` conditions
- Reusable functions
- Preserved the learning exercises as milestone history until M10-R0A cleanup

### M4 — Modular prototype and web project structure

Completed:

- Added configuration and reusable calculation-module scaffolding
- Separated calculator, portfolio and scoring prototype responsibilities
- Created the backend, frontend and documentation directory structure
- Established the project skeleton used by M5 and later milestones

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

## M9 — Website structure and page completeness — Completed

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

### M9-3 — Homepage and system overview — Completed

Completed:

- Added `GET /api/v1/system/overview` as the homepage data boundary
- Added ETF totals and active/passive, bond/non-bond classifications
- Added PRICE_RETURN coverage for 1M, 3M, 6M and 1Y
- Added dividend-event, ACTUAL, 76W and source-document coverage
- Added ETF-master, performance, dividend and ACTUAL-document freshness
- Added the five most recent import batches with failure summaries
- Added primary entry points for search, ranking and dividend data quality
- Preserved null semantics for unavailable dates and zero-denominator rates

### M9-4 — ETF detail-page organization — Completed

Completed:

- Reorganized the detail page into a fixed decision-oriented section order
- Removed duplicated ETF identity and classification rows
- Kept 1M, 3M, 6M and 1Y market-price periods independent
- Preserved strict ACTUAL 76W versus estimated-capital-gain semantics
- Added `GET /api/v1/etfs/{code}/data-profile`
- Added ETF-master, performance, dividend and ACTUAL source/freshness display
- Isolated secondary API failures so successful sections remain visible
- Added a disabled M9-5 comparison entry point
- Added Repository, API, Client and information-architecture regression tests

### M9-5 — ETF comparison page — Completed

Completed:

- Added a public 2–4 ETF comparison page
- Added stable, ordered and deduplicated `codes` URL state
- Added source-aware return behavior for search, ranking and detail
- Added `GET /api/v1/etfs/comparison` as the comparison read-model boundary
- Compared management and asset classifications, listing date, fund size and expense ratio
- Compared independent 1M, 3M, 6M and 1Y `PRICE_RETURN` values
- Compared dividend history, latest distribution and ACTUAL 76W availability
- Added explainable five-section data completeness
- Preserved missing-versus-zero semantics
- Added Repository, API, Client, URL-state and frontend display tests

### M9-6 — Shared frontend components — Completed

Completed:

- Added shared percentage, number, money, date and datetime formatters
- Added shared active/passive and bond/non-bond labels
- Consolidated full-row ETF detail links and pagination controls
- Added a shared warning state alongside loading, empty, not-found and API errors
- Preserved page-specific missing-value wording through small compatibility wrappers
- Added formatter, component, state and architecture-contract regression tests

## M10 — Core analysis features

### M10-0 — Multi-period display foundation — Completed

Completed:

- Support 1M, 3M, 6M and 1Y ranking periods
- Keep 6M as the default and preferred ranking period
- Show only the selected ranking period in each ranking row
- Keep all available periods visible on ETF detail and comparison pages
- Hide trailing former-name annotations in ranking display names without changing source data
- Prevent missing periods from becoming zero
- Apply responsive metric, page-link and sidebar typography

### M10-1 — Dividend analysis summary — Completed

Completed:

- M10-1A: added a read-only monthly-income API without changing the database
  schema
- M10-1A: used actual `payment_date` to assign income months
- M10-1A: defaulted to a three-year lookback and always returned January through
  December
- M10-1A: kept missing payment dates separate from formal zero-event months
- M10-1A: prevented mixed currencies from being added into one amount
- M10-1B: retained the monthly-income API and its tested January–December data
  contract, but paused the ETF-detail chart after visual review
- M10-1C: added traceable official distribution periods and per-event yields
- M10-1C: preferred official yield values and persisted calculated fallback
  prices
- M10-1C: expanded the ETF-detail dividend summary with a dual-axis trend and
  event detail table

### M10-2 — Cash-flow and total-return calculation contract — Completed

Completed:

- Defined deterministic domain models and a calculation contract for historical
  replay and scenario estimates
- Added fixed monthly after-tax cash-flow targets, target coverage, required
  capital and funding shortfall calculations
- Added gross distributions, after-tax usable cash, market-value results and
  after-tax total-return calculations
- Added non-reinvested distribution-ledger reconciliation to prevent cash
  distributions from being double-counted as profit
- Added explicit scenario assumptions for initial capital, cash yield, cash
  deductions, price return and analysis horizon
- Preserved missing values and formal zero values with machine-readable reasons
  for unavailable results
- Defined single-currency Decimal arithmetic, date-basis and public rounding
  rules
- Added 41 focused model, historical-calculation and scenario-estimation tests
- Kept the calculation layer independent from the database, API, frontend, user
  accounts and persisted profiles

### M10-3 — Single-ETF target analysis — Completed

Goal:

- Let a user select one base ETF and determine whether it can support the fixed
  cash-flow target without hiding total-return deterioration

Planned:

- Add a stateless analysis request for ETF, available capital, fixed monthly
  target and analysis horizon
- Calculate gross and after-tax cash flow by payment month
- Calculate annual target coverage, required capital and funding shortfall
- Show market-value result, cash received and total result together
- Add warnings for negative total return, persistent decline, weak recovery,
  insufficient history and stale or incomplete data
- Expose assumptions, source dates and calculation reasons through FastAPI
- Add a plain-language Streamlit result flow for non-professional users

Acceptance:

- A user can understand the base ETF result before any complementary ETF is
  suggested
- Missing data blocks or qualifies the affected conclusion instead of becoming
  zero
- The feature does not claim that historical distributions will continue

### M10-4 — Tax and reinvestment scenarios — Completed

Status: implementation completed on 2026-08-09; full-suite verification is
recorded in the changelog.

Goal:

- Compare usable cash and ending wealth under explicit Taiwan individual-tax
  assumptions and distribution-use choices

Planned:

- Scope the first estimator to Taiwan tax-resident individuals holding
  Taiwan-listed ETFs
- Preserve and explain ACTUAL `54C`, `76W` and other official components
- Keep official `76W` separate from estimated realized capital gains
- Model tax and applicable supplementary-premium assumptions with a visible
  rule version and effective date
- Avoid universal "tax free" or "higher 76W is always better" conclusions
- Compare no reinvestment, excess-only reinvestment, a custom percentage and
  full reinvestment
- Show usable cash, reinvested cash, ending units, ending value, modeled tax
  cost and after-tax total return
- Add boundary tests for formal zero, missing components and different user tax
  assumptions

Acceptance:

- Tax optimization cannot override a failed total-return check
- Reinvested cash is not double-counted
- Historical facts and forward-looking assumptions are visibly separate
- Results are labeled as estimates rather than tax advice

Delivered:

- Added a pure, Decimal-based four-policy reinvestment ledger
- Added versioned per-component tax, credit and supplementary-premium inputs
- Selected only traceable, complete ACTUAL component events while preserving
  formal zero ratios and excluding estimated capital gains
- Added a FastAPI endpoint and a Streamlit form with historical facts visibly
  separated from forward-looking assumptions
- Kept reinvested cash inside ending value and exposed a total-return gate

### M10-5 — Monthly-payment combination and candidate exclusions — Completed

Status: implementation completed on 2026-08-09; full-suite verification is
recorded in the changelog.

Goal:

- Starting from the user's base ETF, optionally add a small number of ETFs to
  improve monthly payment coverage without sacrificing total-return quality

Planned:

- Make monthly payment coverage an explicit option; retain it as the initial
  default planning goal
- Identify payment-month gaps in the base ETF
- Add at most one to three complementary ETFs
- Define eligibility rules for data completeness, freshness, distribution
  stability, downside risk and total return
- Evaluate after-tax cash-flow contribution, holding overlap and concentration
- Exclude high-distribution candidates whose total-return or data-quality rules
  fail
- Explain each inclusion, exclusion, supported month and remaining trade-off
- Compare active/passive and bond/non-bond classifications as transparent
  attributes rather than automatic quality labels

Acceptance:

- No ETF is selected only because it fills a missing payment month
- Every selected and rejected candidate has an explainable reason
- The base ETF remains visible as the anchor of every result
- The combination remains a scenario, not an investment guarantee

Delivered:

- Added a pure candidate-gating and month-gap calculation with deterministic,
  explainable ordering and a one-to-three ETF limit
- Derived payment stability and after-tax cash contribution from historical
  payment-date data while retaining explicit unit-price assumptions
- Applied total-return, downside, completeness, freshness, overlap and
  concentration rules before month coverage
- Kept missing overlap distinct from formal zero and exposed remaining
  limitations as trade-offs
- Added a FastAPI endpoint and comparison-page Streamlit flow with the base ETF
  visibly retained as the result anchor
- Displayed active/passive and bond/non-bond classifications as transparent
  facts instead of automatic quality labels

### M10-R0 — Pre-M11 architecture stabilization — Completed

M10-R0 is placed after the planned M10 product features and before M11 because
it records architecture work required before the decision platform expands the
current codebase. It does not change the M10 calculation sequence.

#### M10-R0A — Legacy cleanup — Completed

Completed:

- Removed completed Python tutorial files and obsolete prototype entry points
- Removed the unused ETF-detail monthly-income chart while retaining its API
  contract and regression coverage
- Kept production backend, frontend and data behavior unchanged

#### M10-R0B — Frontend API client modularization — Completed

Completed:

- Extracted errors, response validators, date validators, datetime validators,
  normalizers and HTTP transport from `frontend/api_client.py`
- Extracted ETF, performance, dividend, dividend-quality and system-overview
  API domains into `frontend/api/`
- Extracted data-profile, comparison and health API domains, leaving
  `frontend/api_client.py` as an import-only compatibility facade
- Preserved all existing `frontend.api_client` imports and established mock
  paths for compatibility
- Added package-boundary tests that prevent implementation from returning to
  the facade, prevent reverse imports and protect compatibility exports
- Reconciled frontend architecture documentation with the modular Client
- Kept the focused Client and full regression suites passing after each
  extraction

Acceptance:

- No FastAPI schema, frontend response contract or database behavior changes
- Existing callers remain compatible throughout the migration
- Every extraction passes focused Client tests and the full regression suite
- The compatibility facade contains no function or class implementation

## M11 — Decision platform

### M11-1 — Single-user conditions and manual holdings — Completed

Status: implementation completed on 2026-08-09; full-suite verification is
recorded in the changelog.

Delivered:

- Added one explicit `SINGLE_USER` decision profile without user accounts
- Persisted a fixed monthly after-tax target, analysis horizon, history window
  and an optional generic cash-deduction assumption
- Added manual Taiwan ETF holdings with positive whole units, a user-supplied
  TWD reference price and an optional price date
- Added FastAPI read/upsert/delete contracts and a Streamlit management page
- Kept broker connectivity and automatic trading explicitly disabled
- Preserved missing cash-deduction assumptions separately from formal zero

### M11-2 — Current-holding analysis — Completed

Status: implementation completed on 2026-08-09; full-suite verification is
recorded in the changelog.

Delivered:

- Reused M10 data loaders and pure target calculations for all saved holdings
- Applied the monthly target once at portfolio level
- Annualized period price returns and weighted them by saved holding value
- Preserved missing deductions and incomplete ETF history as partial results
- Added a read-only FastAPI endpoint and Streamlit analysis dashboard

### M11-3 — Candidate holding analysis — Completed

Status: implementation completed on 2026-08-10; full-suite verification is
recorded in the changelog.

Delivered:

- Compared the saved current portfolio with one non-persisted candidate addition
- Reused the same M11-2 portfolio aggregation before and after the candidate
- Reused M10-5 eligibility gates, stable reason codes and payment-month logic
- Kept the fixed monthly target unchanged when candidate capital was added
- Preserved missing deduction and overlap assumptions instead of using zero
- Added a read-only FastAPI scenario and Streamlit comparison flow

### M11-4 — Decision records and export — Completed

Status: implementation completed on 2026-08-10; full-suite verification is
recorded in the changelog.

Delivered:

- Preserved candidate assessment rationale, exclusions, alternatives and risk
  notes in append-only decision snapshots
- Reran candidate analysis on the server before saving instead of trusting a
  frontend result
- Added record list/detail and five-sheet Excel export
- Kept the initial release single-user and excluded broker connectivity and
  automatic trading
- Kept the M12 direction-and-function audit unexecuted and mandatory

## M12 — Automation and deployment

Entry gate:

- `docs/M12_ENTRY_AUDIT.md` was executed on 2026-08-10 against merged main
  `f07b279`; it is awaiting the user's explicit direction/function confirmation
- Use post-M9 direction commit `03a9635`, the current PRD and actual website
  behavior as the reconciliation baseline
- Do not begin M11-5 or M12 until the user explicitly confirms the reconciled
  scope and owner-only decision-profile boundary
- The audit recommends M11-5 visible-flow and principal-warning closure before
  M12; that recommendation is not approved merely by this documentation change

Planned:

- Scheduled data Pipelines
- Failure monitoring and freshness checks
- Administration status
- Backup and recovery
- Public deployment, domain and HTTPS
- Protect decision-profile writes before exposing the site to anonymous users

## Optional external integrations — after the core website

Deferred until M9–M12 are complete:

- Third-party market-data evaluation
- Fugle market-data API
- Sinopac Shioaji read-only account synchronization
- Portfolio import
- Simulated or live order assessment

These optional integrations must not block the core website roadmap.
