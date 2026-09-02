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
- Kept the M12 direction-and-function audit mandatory

### M11-5 — Confirmed public cash-flow flow closure — Complete

Status: scope explicitly confirmed by the user on 2026-08-10; implementation
began after the confirmed M12 entry-audit change was merged. M11-5A1 implements
the dynamic holding and official-close boundary, and M11-5A2 exposes the visible
base-target output. M11-5B implements the final deterministic warning and
direct UI regression scope. All three changes are merged on main `1e0a920`.

Delivered in M11-5A1:

- Added the initially empty dynamic `0-N` holding editor with exactly
  `[ETF code] [held units]` as editable fields
- Added atomic batch replacement, unique-code and positive-whole-unit validation
- Persisted the performance Pipeline's downloaded TWSE daily closes with source
  and trade date, without another network request
- Derived read-only holding prices from the latest stored official close and
  preserved missing price as unavailable rather than zero
- Added a lossless upgrade for existing user-entered manual prices

Delivered in M11-5A2:

- Added a read-only latest stored official close endpoint for the base ETF
- Exposed target analysis before tax/reinvestment on ETF detail using that
  official price rather than a user-entered price
- Displayed required capital, funding shortfall, annual target coverage and
  January-December historical annualized gross/after-tax cash
- Preserved missing deduction assumptions and missing payment months as
  unavailable rather than formal zero

Delivered in M11-5B implementation:

- Added deterministic, source-dated negative-total-return, persistent-decline,
  weak-recovery and material-peer-underperformance warnings
- Added direct Streamlit result tests for target risks, four tax/reinvestment
  policies and monthly-combination anchoring/reasons
- Annualized selected multi-year price returns before scenario projection

Remaining: none. M12 entry still requires the refreshed audit-gate PR to merge.

## M12 — Automation and deployment

Entry gate:

- `docs/M12_ENTRY_AUDIT.md` was re-executed on 2026-08-12 against merged main
  `1e0a920`; it confirms that completed M11-5 matches the direction explicitly
  confirmed by the user after M9
- Use post-M9 direction commit `03a9635`, the current PRD and actual website
  behavior as the reconciliation baseline
- Begin M12 only after the refreshed 2026-08-12 audit gate is merged
- Keep M12 authentication to an operational single-owner gate; do not expand it
  into self-service accounts or a multi-user data model

Planned:

- Scheduled data Pipelines
- Failure monitoring and freshness checks
- Administration status
- Backup and recovery
- Public deployment, domain and HTTPS
- Protect every decision-profile read, write, record and export boundary before
  exposing the site to anonymous users

### M12-1 — Deployment database readiness — Completed

- Added explicit read-only Schema, integrity and foreign-key verification
- Added explicit deployment initialization followed by mandatory verification
- Added isolated SQLite-backup migration rehearsal with before/after row-count
  preservation checks
- Successfully rehearsed the 2026-08-01 deployment candidate on 2026-08-12;
  all 256 ETF, 205 performance, 288 dividend, 1,430 component and 576 review
  queue rows were preserved
- Kept recoverable backup retention and restore drills in M12-2

### M12-2 — Durable database backup and recovery — Completed

- Added `TW_ETF_DATABASE_PATH` as the production database-path contract;
  deployments must provide an absolute path outside the release tree
- Preserved `database/tw_etf.db` only as the no-environment local-development
  default
- Added transactionally consistent, no-overwrite SQLite backups with a
  neighboring versioned manifest containing SHA-256, size, UTC timestamp,
  schema readiness and row counts
- Added no-overwrite restore into a new path with pre-restore artifact checks
  and post-restore integrity, foreign-key, schema and exact row-count checks
- Documented initial daily/weekly retention and an operator recovery runbook;
  scheduled/off-host automation remains M12-3
- Completed a real backup/restore drill against the legacy deployment
  candidate: SHA-256 and all eight table counts matched, integrity was `ok`,
  and foreign-key violations were zero

### M12-3 — Scheduled pipelines and operational monitoring — Completed

- Added a declarative sequential job runner with no-shell execution, exclusive
  overlap lock, stop-on-failure behavior, per-job logs and atomic JSON status
- Added machine-readable database, storage, latest-pipeline, data-freshness,
  backup-age, restore-drill and optional API-health checks with non-zero critical
  exit status
- Defined initial production thresholds, escalation expectations and Windows
  Task Scheduler guidance without committing host credentials
- Kept reviewed ACTUAL ingestion explicit rather than automatically importing
  unreviewed notices; host-specific provisioning remains M12-5
- Exercised the monitor against the current candidate: it correctly identified
  the four pre-initialization tables still missing, data observations older than
  the 168-hour threshold and absent restore-drill state while confirming SQLite
  integrity, zero foreign-key violations and available storage

### M12-4 — Owner-only decision boundary — Completed

- Added one fail-closed, constant-time owner-token dependency to the complete
  decision-profile router, covering reads, writes, analyses, immutable records
  and Excel exports
- Kept public ETF analysis, rankings, comparisons, quality information and
  health endpoints anonymous
- Added a per-browser-tab Streamlit unlock/lock control and conditionally
  included the private page only after backend verification
- Kept private responses out of shared Streamlit caches and passed the owner
  header on every private frontend request
- Deferred accounts, roles, durable sessions, edge rate limiting and HTTPS
  binding to later scope as previously agreed

### M12-5A — Reproducible production deployment package — Completed locally

- Added one pinned Python runtime image shared by FastAPI and Streamlit
- Added a Compose topology where only Caddy publishes ports and application
  services remain private, with durable SQLite mounted outside releases
- Added Caddy domain routing, automatic HTTPS and baseline security headers
- Added mandatory deployment environment placeholders, service health checks,
  post-deployment public/private smoke checks and a restart/rollback runbook
- Kept real host purchase, DNS mutation, firewall access and public certificate
  proof pending explicit external infrastructure and credentials

### M12-5B — Native local deployment validation — Completed

- Started FastAPI and Streamlit as separate hidden local processes against an
  isolated, migrated candidate database
- Verified public health and frontend HTTP 200, anonymous/wrong-token HTTP 401,
  owner HTTP 200, current schema, integrity `ok` and zero foreign-key violations
- Wrote one isolated owner condition, restarted FastAPI and confirmed the same
  value persisted without modifying the source database
- Added a repeatable split-port local smoke command; browser automation was not
  available, so the owner completed the final visual interaction manually on
  localhost
- Owner browser acceptance completed on 2026-08-12: public pages, unlock UI,
  private navigation, persisted 4,321 TWD target and relock hiding all passed

### M12-6 — Launch-data threshold and decision — Completed locally

- Added a repeatable, machine-readable launch-data gate for reviewed ACTUAL
  components, official ACTUAL 76W and traceable parsed source documents
- The ordinary gate requires at least one event in each reviewed category and
  exits non-zero when the candidate is not ready
- A limited-coverage exception requires both a named approver and a recorded
  reason; it cannot be enabled by an unqualified boolean switch
- Evaluated the 2026-08-12 repository candidate: 288 dividend events exist,
  while all three reviewed coverage counts are zero, so the current decision
  is `NO_GO`
- The initial M12-6 implementation could merge while the `NO_GO` data result
  remained blocked; the reviewed seed below subsequently passed that gate
- Added bounded TWSE ETF/year history retrieval and an explicit event-only mode
  that preserves valid parent events while continuing to reject invalid
  estimated composition
- Imported one verified Cathay announcement after a successful isolated
  rehearsal and recoverable pre-import backup; the local candidate now has one
  ACTUAL event, one official 76W event and one traceable source document
- The final local gate is `READY` without an exception; coverage remains only
  0.342466% and 582 review items remain visible rather than being hidden

M12 implementation is complete for the available local environment. Public
host, domain, DNS and TLS evidence remain external deployment prerequisites,
not locally reproducible product work.

## Optional external integrations — after the core website

Deferred until M9–M12 are complete:

Second-version priorities confirmed from the updated website requirements:

1. Custom target payment months, including user-selected single-month,
   alternating-month, quarterly, annual and arbitrary month sets
2. Explainable AI assessment that remains subordinate to total-return,
   principal-risk, after-tax cash-flow and data-quality gates

These are post-M12 product upgrades. They must not delay or silently expand the
first public release, and AI output must not become opaque trading advice.

### V2-1 — Custom target payment months — Completed locally

- Kept the existing all-month target as the backward-compatible API default
- Added single-month, alternating-month, quarterly, annual fixed-month and
  arbitrary month-set goals to the monthly combination UI
- Restricted gap filling to the selected target months without weakening the
  existing total-return, principal-risk, data-quality or overlap gates
- Kept explainable AI assessment as the next separate second-version upgrade

### V2-2 — Explainable assessment baseline — Completed locally

- Added a deterministic four-factor assessment to candidate holding analysis
- Kept data quality, total return, principal risk and after-tax cash flow ahead
  of optional payment-month coverage
- Exposed observed evidence and stable reason codes without an opaque score or
  buy/sell label
- Established a structured baseline that a future language model may explain
  but may not override
- Added transparent ETF-quality and portfolio-fit scores led by total return;
  the page displays only portfolio fit, with ETF quality and confidence kept
  out of the user-facing score cards
- Kept manually entered overlap out of scoring pending automatic constituent
  ingestion and portfolio-weighted overlap calculation

### V2-3 — ETF constituent snapshot foundation — Completed locally

- Added immutable, source-dated ETF constituent snapshots and positions
- Added disclosed-weight coverage and duplicate/total-weight validation
- Added pairwise weighted overlap using the sum of smaller disclosed weights
- Kept incomplete snapshots unnormalized so missing coverage remains visible
- Deferred issuer-specific automatic ingestion and assessment integration to a
  separate data-source milestone

### V2-4 — First official constituent source — Completed locally

- Audited all 23 issuers in the TWSE ETF issuer universe and recorded their
  official source, locator method and automation status
- Verified a complete official holdings or PCF response for every applicable
  non-Yuanta issuer; JKO currently has no equity constituent portfolio
- Added complete Yuanta stock-weight ingestion through the issuer site's
  official `PCF/Daily` bridge
- Required matching ETF identity, a valid trading date and at least 90%
  disclosed stock-weight coverage before persistence
- Kept futures, bonds and nested ETF positions outside stock-overlap inputs
- Audited the published Fugle Market Data and Sinopac Shioaji APIs; neither
  currently publishes ETF constituent weights, so no account or API-key
  dependency was added
- Identified direct-code adapters, internal-ID discovery, antiforgery and
  short-lived system-token flows as separate follow-up implementation groups
- Deferred remaining issuer adapters and assessment integration to separate
  milestones without representing page discovery as completed automation

### V2-5 — Direct-code constituent sources — Completed locally

- Added official adapters for Fubon, SinoPac, Taishin, CTBC and Nomura
- Added one issuer-dispatched import interface while retaining the original
  Yuanta import wrapper for compatibility
- Required matching ETF identity, a valid official data date and at least 90%
  stock-weight coverage for every newly automated source
- Followed Fubon's official PCF link to the dated assets page and selected only
  stock tables from every source
- Deferred internal-ID, ISIN, token and form-backed issuers to the next source
  families

### V2-6 — Mapped constituent sources, batch one — Completed locally

- Added automatic official-directory mapping and holdings ingestion for Mega,
  Fuh Hwa, UOB and E.SUN
- Added official XLSX parsing for Fuh Hwa and reused the immutable snapshot
  contract for HTML, JSON and workbook sources
- Confirmed live stock coverage of 97.12%, 95.658%, 98.59% and 98.33%
  respectively before marking these sources automated
- Kept Capital fail-closed because its current server-rendered response exposes
  only ten rows totaling 73.94%; incomplete rows are not persisted
- Deferred the remaining internal-ID, product-ID and ISIN sources to subsequent
  source-family batches

### V2-7 — Remaining internal-ID sources, batch two — Completed locally

- Added Franklin official ETF catalog mapping, available-date discovery and
  complete stock holdings ingestion
- Converted UTC disclosure timestamps to Taiwan dates and verified 00905 with
  139 stock rows totaling 97.59%
- Rechecked Cathay, First and KGI without enabling them: Cathay maps 00878 to
  its current fund code but the stock endpoint returns no data; First returns
  empty stock rows for the representative fund; KGI does not expose complete
  stock rows in its current server response
- Kept all three sources fail-closed pending a complete official payload

### V2-8 — Session-aware official constituent sources — Completed locally

- Added HN's official public short-lived system-token login and ETFID-based PCF
  ingestion with fractional-weight conversion and complete-stock validation
- Added Allianz's official antiforgery session, ETF overview mapping and fund-
  asset ingestion for current products with available holdings
- Verified HN `009808` and Allianz `00984A`, `00993A` and `00402A` against live
  official responses; `00412A` remains fail-closed until its fund-asset table
  becomes available
- Kept tokens and cookies ephemeral and persisted only validated source-dated
  constituent snapshots

### V2-9 — Form-backed official constituent source — Completed locally

- Added live discovery of every ETF code currently offered by the Union
  official purchase/redemption form instead of hard-coding one product
- Added bounded `FundNo` and official `sDate` submissions with response-domain,
  content-type, size, identity, date and minimum stock-weight validation
- Verified `009804` with 50 stock rows totaling `99.4138%` and `009825` with 30
  stock rows totaling `99.5039%` against the official production form
- Kept unknown ETF codes and changed or incomplete form responses fail-closed

### V2-10 — Constituent batch ingestion and calculation-data gates — Completed locally

- Added a repeatable full-market batch plan based on the stored 6M
  `PRICE_RETURN` calculation baseline
- Excluded bond, leveraged, inverse, futures and multi-asset products from
  stock-only overlap while keeping missing performance and unsupported issuer
  states visible
- Added official batch import with bounded ETF selection, explicit network
  permission and machine-readable output
- Made same-date, same-content imports idempotent while continuing to reject a
  changed payload for an immutable source identity
- Required ETF coverage, issuer coverage, freshness, disclosed stock weight
  and complete issuer mapping before constituent data can be marked `READY`
- Verified an isolated live fixture for `0050` and `00918`: 80 positions were
  imported from two issuers, both data dates passed the seven-day freshness
  gate, and the rerun returned two `UNCHANGED` results
- Kept full-market readiness honest: the current calculation universe contains
  132 automated-source ETFs and 22 Cathay/BlackRock ETFs whose official
  automation remains unavailable, so the default 90% ETF gate remains
  `NO_GO` until coverage improves

### V2-11 — Gated overlap in calculation flows — Completed locally

- Replaced manual overlap controls in monthly comparison and candidate-holding
  analysis with official constituent snapshot calculations
- Added pairwise base-ETF overlap and market-value-weighted current-portfolio
  overlap without normalizing incomplete disclosures to 100%
- Required every ETF in the requested calculation to pass the seven-day and
  85% disclosed-weight gates; unavailable data remains unknown rather than zero
- Added automatic overlap to the backend portfolio-fit score at a bounded 10%
  weight while ETF quality remains the primary component
- Preserved old request fields as ignored compatibility inputs and changed
  decision-record exports to show the calculated value

### V2-12 — Isolated calculation candidate — Completed locally

- Added a no-overwrite copy, schema upgrade, official refresh and strict check
  command for bounded or full calculation universes
- Separated core cash-flow/tax/performance readiness from optional constituent
  overlap readiness while preserving missing overlap as unknown
- Refreshed 0050, 0056 and 00918 to 100% four-period performance, official
  closes, dividend history and complete estimated component mixes
- Reached full overlap readiness for 0050 and 0056; kept 00918 fail-closed after
  its official PCF response exposed incompatible rows totaling only 49.20%
- Fixed rolling-window distribution stability exceeding 100% and verified live
  monthly-combination and tax/reinvestment API responses

### V2-13 — Calculation browser acceptance — Automated preflight complete

- Passed the six native public/private service boundaries against the isolated
  V2-12 database
- Exercised the saved 0050/00918 portfolio, 0050/0056/00918 monthly combination,
  0056 candidate addition and 0050 four-policy tax/reinvestment flow
- Fixed the candidate-analysis HTTP 500 caused by an annualized repeating
  decimal exceeding the money-model precision boundary
- Added explicit projection years and visible warnings when a 1Y historical
  return is mechanically compounded over a multi-year scenario
- Recorded remaining estimated-component, 00918 overlap and per-event-yield
  gaps without converting them to official or zero values
- Owner confirmed all seven browser checks on 2026-08-21, including current
  holdings, candidate comparison, monthly gaps, tax/reinvestment warnings and
  relocking the private navigation

V2 acceptance is complete. Independent security validation is active before
any `V3-X` feature work.

## Security validation — SEC-1–3 complete; SEC-4 required before launch

Security work remains an independent release gate and must not be treated as an
informal code review or folded silently into a feature PR. Security PR titles
use the `SEC-X` prefix. Third-version product PR titles use `V3-X`.

The owner changed the delivery order on 2026-08-25: real-domain deployment is
deferred until the V3 product flow and page-by-page information review are
complete. Local SEC-1 through SEC-3 controls remain mandatory during V3. SEC-4
`READY` is still required before public launch, but no longer blocks local V3
development.

### SEC-1 — Secret exposure and repository history

- Completed 2026-08-21: scanned worktree files, ignored deployment material,
  generated reports, logs, all fetched Git refs, commit messages and local
  unreachable blobs without printing matching values
- Confirmed zero findings and zero unscanned oversized objects; no credential
  rotation or history rewrite was required
- Expanded `.gitignore`, added a deny-by-default Docker build context and
  verified sensitive local paths are not served as files
- Evidence: `SECURITY_SECRET_EXPOSURE_AUDIT.md`

### SEC-2 — Authentication and API boundary testing

- Completed 2026-08-21: locked all 11 private operations behind the owner gate,
  fixed-size digest comparison and non-cacheable private responses
- Added redirect refusal, sanitized validation/internal errors and explicit
  target, header, body, numeric and holding-batch resource limits
- Verified direct API/export denial, CORS, injection, traversal, streamed and
  declared oversized bodies, extreme numbers and error-detail boundaries
- Evidence: `SECURITY_AUTH_API_BOUNDARY_AUDIT.md`

### SEC-3 — Dependency, container and runtime hardening

- Completed 2026-08-21: audited the complete pinned Python dependency graph,
  upgraded Python/Caddy base images and added CI high/critical image scanning
- Made every service non-root with read-only roots, bounded tmpfs/PIDs, dropped
  capabilities, no-new-privileges and only the database bind mount writable
- Removed public API docs, expanded Caddy security headers/body limits, added
  bounded public/private application rate limits and kept only 80/443 published
- Added immutable-action CI for secret history, dependency consistency, full
  regression, image UID, isolated health and container vulnerability gates
- Evidence: `SECURITY_DEPENDENCY_RUNTIME_AUDIT.md`

Next security milestone: `SEC-4` public-host and launch security acceptance.

### SEC-4 — Public-host and launch security acceptance

- Implemented locally 2026-08-21: added a fail-closed public-host probe for DNS,
  certificate lifetime, TLS negotiation, redirects, security headers, release
  identity, blocked docs, owner boundaries, private caching and body limits
- Added a fresh named-attestation contract for firewall/admin exposure, shared
  edge limits, secret injection/rotation, off-host backup/restore, certificate
  renewal alerts and exact application/edge container identity
- Changed deployment smoke checks to refuse redirects and keep the owner token
  out of command-line arguments
- Completed an isolated production-compose rehearsal on 2026-08-24 for exact
  commit `75722b0b3e2823430bf70e8e9d3716de4dc6e2ac`: all images built, services
  became healthy, HTTPS owner boundaries passed, restart preserved every
  database count, and the owner confirmed the calculation and export flows
- Kept the localhost CA outside the Windows trust store and used it only for
  the automated smoke process
- Current decision: `NO_GO`; no real host/domain exists, so DNS, public TLS,
  provider firewall/rate-limit and production-secret evidence are unavailable
- Required completion: deploy one exact commit, fill the external attestation
  from real evidence and obtain a `READY` SEC-4 report before public access
- Evidence contract: `SECURITY_PUBLIC_LAUNCH_ACCEPTANCE.md`

## V3 — GoodCat 股利喵 automatic allocation

V3 starts before real-domain deployment so the complete beginner flow can be
reviewed locally first. The core input is a fixed after-tax cash target,
selected payment months and zero to N existing ETF holdings. The core output is
which ETFs to add, how many whole shares to add and the required additional
capital, together with reasons, alternatives, exclusions and risks.

V3 remains deterministic and explainable. Internal ETF-quality scores may
support eligibility and ordering, but ETF-quality scores and assessment-
confidence labels are not shown in the frontend.

### V3-0 — Product, brand and allocation contract — Completed

- Rename the visible product to `GoodCat 股利喵` and use beginner-oriented wording
- Replace the base-ETF-first product flow with target-months-and-holdings-first
  planning
- Define the public stateless boundary for zero to N holdings
- Define full-market candidate gates, whole-share constraints, deterministic
  objective order and stable result semantics
- Keep real-domain SEC-4 acceptance as a pre-launch gate after V3
- Evidence: `V3_ALLOCATION_ENGINE_CONTRACT.md`

### V3-1 — Public zero-to-N holdings and target-month flow — Completed locally

- Add a public planner that starts empty and accepts zero to 500 ETF holdings
- Keep submitted targets and holdings out of the owner profile and persistence
- Support monthly, odd-month, even-month, quarterly, half-year, annual and
  arbitrary selected-month goals through one normalized month-set contract
- Show the current-portfolio baseline before automatic additions

Delivered:

- Added a public, owner-token-free `POST /api/v1/allocation-plans/baseline`
  request that is never written to the saved decision profile or holdings
- Added an initially empty dynamic holding editor for zero to 500 distinct ETF
  holdings with positive whole-share quantities
- Normalized monthly, odd-month, even-month, quarterly, half-year, annual and
  arbitrary selected-month goals to one ordered month set
- Used source-dated stored official closes and payment-date dividend history to
  show current value, historical monthly cash and each selected-month shortfall
- Preserved missing price, dividend and mixed-currency facts as partial `null`
  results with reasons; zero holdings remains a known-zero baseline
- Kept automatic market selection and whole-share additions visibly pending
  until V3-2 and V3-3

### V3-2 — Full-market eligibility and internal assessment index — Completed locally

- Build the server-side supported ETF universe without user-picked candidates
- Apply data freshness, distribution stability, total-return, downside,
  composition, overlap and concentration gates before optimization
- Keep unsupported product types and missing data visible through stable reason
  codes
- Expand reviewed ACTUAL dividend-composition coverage as a priority data track

Delivered:

- Built the candidate universe from every ETF master row without user-picked
  candidates and retained unsupported product types with stable reasons
- Applied fixed server-side price, completeness, freshness, payment stability,
  after-tax cash, total-return, downside, composition and overlap gates
- Kept allocation-dependent concentration as an explicit V3-3 hard constraint
  instead of evaluating a fabricated percentage before shares exist
- Added a deterministic internal ETF-quality ordering and twelve-month cash-
  per-share facts without returning scores, components, ranks or confidence
  labels through the public API
- Added a public code-ordered safety projection with source dates, ACTUAL versus
  estimated composition, exclusions and a reproducible snapshot identity
- Kept estimated composition visibly downgraded and exposed ACTUAL coverage
  counts so the formal-data expansion track cannot be overstated
- Confirmed three eligible ETFs against the isolated V2-12 calculation data;
  the older default database remains zero-eligible until its official market
  and calculation facts are refreshed
- Evidence: `V3_MARKET_ELIGIBILITY_INDEX_CONTRACT.md`

### V3-3 — Automatic ETF and whole-share allocation engine — Completed locally

- Solve non-negative whole-share additions from the eligible market universe
- Minimize selected-month shortfall before minimizing required capital
- Preserve existing holdings without silently selling or replacing them
- Return reproducible optimality status and bounded best-effort results without
  false precision

Delivered:

- Added public stateless `POST /api/v1/allocation-plans/integer-allocation`
  orchestration from the existing-holding baseline through the full-market
  eligibility index to whole-share additions
- Implemented a dependency-free Decimal-safe bounded solver that never solves
  fractional shares and rounds them afterward
- Minimized selected-month shortfall first, used capital efficiency for the
  deterministic construction order and enforced the fixed 20% resulting-value
  concentration limit with whole-share dilution
- Preserved existing holdings as fixed inputs and returned current cash, added
  cash, shortfall, additions, capital and resulting concentration without
  writing the request or result to a profile
- Reported ordinary non-zero results as `BOUNDED_BEST_EFFORT`, reserved
  `PROVED_OPTIMAL` for provable zero-addition cases and failed closed when
  required baseline data or a concentration-feasible structure was absent
- Kept transaction costs explicitly fixed at 0 TWD for this methodology
  version instead of inventing broker-specific fees
- Kept internal quality scores and confidence labels out of the public payload
- Evidence: `V3_ALLOCATION_ENGINE_CONTRACT.md`

### V3-4 — Result, alternatives and exclusions — Completed locally

- Show ETFs to add, whole shares, reference prices and required capital
- Show month-by-month current cash, added cash, target and remaining shortfall
- Explain inclusion, exclusion, trade-offs, assumptions and principal risks
- Provide materially different alternatives when available
- Do not display ETF-quality scores or confidence labels

Delivered:

- Added public stateless `POST /api/v1/allocation-plans/allocation-results`
  with one to three non-duplicate strategies
- Kept `推薦配置` as the default best-fit result while preserving honest
  bounded optimality language
- Added evidence-dependent `平衡配置` for lower constituent overlap and
  `集中配置` for stronger recent total return with more similar constituents
- Returned fewer strategies with a simple reason when formal constituent data
  is insufficient or an alternative is not materially different
- Added source-dated reference prices, whole-share additions, required capital,
  selected-month cash and shortfalls, resulting holdings, risks and exclusions
- Replaced the baseline-only public page result with a beginner-facing strategy
  selector and expandable secondary evidence
- Confirmed active equity ETF codes ending in `A` are not excluded by suffix
- Kept internal quality scores and confidence labels out of the API and page
- Evidence: `V3_ALLOCATION_RESULTS_CONTRACT.md`

### V3-5 — Three-, five- and ten-year evidence and long-term scenarios — Completed locally

- Populate compatible 3Y, 5Y and 10Y total-return evidence where history allows
- Keep price return, total return and scenario estimates distinct
- Add long-term scenario assumptions without presenting forecasts as facts
- Use all compatible history available for each ETF rather than forcing a
  uniform history longer than the Taiwan ETF market provides
- Produce conservative, base and optimistic scenarios and connect them to the
  later one-to-twenty-year portfolio model

Delivered:

- Added public stateless `POST /api/v1/allocation-plans/long-term-scenarios`
  while preserving the exact V3-4 allocation response and strategy order
- Rebuilt portfolio historical evidence from each plan's resulting whole
  shares, compatible common official close dates and actual TWD payment-date
  distributions instead of relabeling stored 1Y price return as long-term
  total return
- Returned the maximum compatible history plus independent 3Y, 5Y and 10Y
  windows; insufficient history remains unavailable instead of becoming zero
- Kept historical distributions in a no-reinvestment cash ledger and applied
  the request's generic cash-deduction assumption exactly once
- Added conservative, base and optimistic ten-year index scenarios from the
  25th, 50th and 75th percentiles of complete trailing one-year observations,
  with a minimum of two observations and an index base of 100
- Added a beginner-facing table and native line chart synchronized to the
  selected recommended, balanced or focused allocation
- Disclosed that stored official closes are raw and do not yet adjust ETF
  splits or reverse splits; the result is an estimate rather than an official
  adjusted total-return series
- Kept scores, confidence labels, forecasts, trading signals and persisted
  planner inputs out of the public contract
- Evidence: `V3_LONG_TERM_SCENARIO_CONTRACT.md`

### V3-6 — Portfolio tax and one-to-twenty-year reinvestment

- Extend tax and reinvestment from one ETF to the complete resulting portfolio
- Preserve official versus estimated component provenance
- Show spend, partial-reinvest, excess-only and full-reinvest outcomes without
  double-counting internal cash flows
- Limit the beginner-facing tax output to estimated supplementary NHI and
  estimated dividend-related individual income tax; keep legal citations and
  detailed rule text out of the main page
- Reconfirm the applicable treatment of official `54C` and `76W` against the
  then-current rules before implementing the portfolio tax model

Delivered:

- Added public stateless `POST /api/v1/allocation-plans/portfolio-projections`
  and retained the aligned V3-5 allocation and historical evidence
- Added 1-to-20-year conservative, base and optimistic portfolio projections,
  each with spend, excess-only, custom-percentage and full-reinvestment results
- Estimated dividend-related individual income tax and supplementary NHI once
  for the complete resulting portfolio, with explicit user tax assumptions
- Preserved ACTUAL and ESTIMATED component provenance, formal zero values and
  unavailable states; estimated capital gain is never labeled official `76W`
- Changed forward scenario observations to gross-before-portfolio-tax and kept
  reinvested distributions as internal cash flow to prevent double counting
- Added a beginner-facing public result table and chart without legal text,
  internal quality scores, confidence labels or persisted inputs
- Evidence: `V3_PORTFOLIO_TAX_REINVESTMENT_CONTRACT.md`

### V3-7 — Optional accounts and imports after core acceptance

- Evaluate account isolation and portfolio import only after the public
  stateless allocation flow is stable
- Keep automatic orders and real-time trading signals out of scope
- Do not let this optional milestone block core V3 acceptance
- Do not implement broker API connectivity before real-domain testing; assess
  it later only when a concrete need exists

### V3-8 — Page-by-page and release acceptance — Closed for V4 transition

- Review every page with the owner before launch
- Remove fields that do not help the page's beginner decision task
- Add missing decision evidence and move misplaced fields to the page where
  they are needed
- Recheck navigation, terminology, responsive behavior and public/private data
  boundaries after the information-architecture changes
- Pass functional, calculation, data-quality and local security regression
  gates before selecting the exact public-release commit
- Complete real-host deployment and obtain SEC-4 `READY` only after this local
  acceptance is complete

Acceptance log:

- Home page: core public planner promoted to the primary action; backend URL,
  database engine, import batches and detailed pipeline coverage removed from
  the beginner view. Public data counts, dates and safety boundaries retained.
- Remaining page decisions and order are tracked in `V3_PAGE_ACCEPTANCE.md`.
- On 2026-08-26 the owner accepted the completed cleanup as the V3 baseline and
  closed further V3 page acceptance because V4 will replace the page experience.

## V4 — GoodCat consumer experience and dual assessment

V4 rebuilds the visible Streamlit experience around ETF beginners while
preserving the V3 FastAPI contracts, deterministic gates, whole-share solver
and stateless public-planner boundary. Local V4 implementation and page review
come before real-domain deployment; SEC-4 `READY` remains mandatory before
public launch.

### V4-0 — Product experience and dual-assessment contract

- Define the relaxed gray-and-white GoodCat character and state-driven role
- Define the light neutral visual direction and accessible presentation rules
- Separate ETF historical quality grade from owner-goal allocation fit
- Permit `A+` through `F` grades while hiding raw scores, ranks and confidence
- Define `暫不評等` for missing core evidence rather than treating it as `F`
- Preserve current hard gates and treat the external score formula as research
  input pending replay and sensitivity evidence
- Confirm Streamlit implementation boundaries and page-level acceptance rules
- Evidence: `V4_PRODUCT_EXPERIENCE_CONTRACT.md`

### V4-1 — Assessment calibration and grade contract — Completed locally

- Replay the current methodology and candidate revisions over dated evidence
- Evaluate fill success, fill duration and survivorship-safe observation rules
- Add individual-ETF and resulting-portfolio concentration evidence
- Test missing ACTUAL composition and weight sensitivity before changing weights
- Version fixed grade thresholds and expose grades without public raw scores

Delivered:

- Added fixed `A+` through `F` grade thresholds over the existing deterministic
  quality score while keeping raw scores, ranks and confidence private
- Added `UNRATED` semantics so missing evidence and a complete low `F` grade
  cannot be confused
- Added a read-only calibration report with factor coverage, aggregate score
  distribution, boundary sensitivity and explicit factor-adoption decisions
- Added publication gates requiring 30 trustworthy samples, 20% supported-
  market coverage and no more than 50% total-return score saturation
- Measured the current database at 6 provisional grades across 192 supported
  products, with the total-return component saturated; public grades therefore
  correctly remain `UNRATED`
- Deferred fill scoring until adjusted event evidence exists and retained ETF
  and portfolio concentration as risk evidence rather than a blunt score
- Added the safe grade object to eligibility candidates and allocation additions
- Evidence: `V4_ASSESSMENT_CALIBRATION.md`

### V4-2 — Brand theme and shared GoodCat components — Completed locally

- Create original, licensed gray-and-white GoodCat assets for idle, attentive,
  working, ready and caution states
- Add a native Streamlit light theme and reusable beginner-facing containers
- Keep character state, accessibility text and backend calculation independent
- Recheck navigation and responsive behavior against the new visual hierarchy

Delivered:

- Added five original flat gray-and-white GoodCat PNG assets with documented
  provenance, sleepy idle eyes, natural feline state cues and verified alpha
  transparency for idle, attentive, working, ready and caution states
- Added a native Streamlit light theme using the approved canvas, surface,
  text, cat-gray, soft-pink and border palette without external web fonts
- Added reusable state-driven GoodCat and beginner explanation cards built
  from native Streamlit containers, images and text elements
- Kept character state isolated from FastAPI and calculation code, and paired
  every image with visible Traditional Chinese state and accessibility text
- Added the idle companion to the existing home page as a limited integration;
  the full consumer home and planning-flow rebuild remains V4-3
- Rechecked the existing fixed navigation order, non-collapsible public sidebar
  contract and narrow-screen typography through frontend regression tests
- Evidence: `frontend/ui/goodcat.py`, `.streamlit/config.toml` and
  `frontend/assets/goodcat/README.md`

### V4-3 — Home and planning journey — Completed locally

- Rebuild the home page as a consumer landing and immediate planning entry
- Present months, target and zero-to-N holdings as one guided Streamlit form
- Use GoodCat states to support input, calculation, empty and error feedback
- Preserve stateless submission and existing FastAPI boundaries

Delivered:

- Rebuilt the home page around one primary GoodCat planning action and three
  beginner preparation cards for months, target cash and optional holdings
- Reordered the public planner into one bordered five-step journey beginning
  with payment months and retaining the approved fixed-width, zero-to-N
  holdings editor with deliberate selection-before-delete behavior
- Connected attentive, working, ready and caution GoodCat states to input,
  calculation, target-met, partial, no-allocation and error outcomes without
  changing the backend calculation contract
- Added a session-only input signature that removes stale visible results as
  soon as months, target, holdings, tax or reinvestment assumptions change
- Kept public requests anonymous and non-persistent, preserved the existing
  FastAPI portfolio-projection boundary and added plain-language limitations
- Evidence: `frontend/pages/home.py`, `frontend/pages/public_planner.py` and
  focused Streamlit information-architecture tests

### V4-4 — Allocation result and assessment experience — Completed locally

- Present recommended, balanced and concentrated plans as clear result cards
- Show whole shares, capital, cash coverage, shortfall, reasons and primary risk
- Show ETF grade separately from owner-goal fit without recommendation language
- Move detailed assumptions, exclusions and evidence into secondary disclosure

Delivered:

- Added compact cards for every materially different recommended, balanced or
  concentrated plan, followed by one selected plan's complete detail card
- Added a separate owner-goal fit presentation for target met, partial,
  unavailable and no-eligible-allocation outcomes without treating it as ETF
  historical quality
- Replaced the dense addition table with per-ETF cards showing whole shares,
  required capital, supported months, inclusion reasons and the primary risk
- Added public-safe `A+` through `F` or `暫不評等` historical-quality badges and
  evidence disclosures without exposing raw score, rank or confidence fields
- Kept monthly coverage and total remaining shortfall in the primary result,
  while moving holdings, assumptions, excluded ETFs, historical evidence and
  tax/reinvestment scenarios into labeled secondary disclosures
- Preserved the existing V3 allocation API and deterministic calculation
  engine; V4-4 changes presentation semantics only
- Evidence: `frontend/ui/assessment.py`,
  `frontend/pages/public_planner.py` and focused assessment/AppTest coverage

### V4-5 — Explore and evidence pages — Completed locally

- Redesign search, ranking, detail and comparison around consistent ETF cards
- Apply the same grade semantics and missing-data states across every page
- Keep operational data-quality fields in owner-only administration

Delivered:

- Added a batch public historical-quality-grade endpoint that reuses the V4-1
  full-market publication gate and returns only versioned letter-grade evidence
- Added the same `A+` through `F` or `暫不評等` semantics to search results,
  performance ranking, ETF detail and comparison without exposing score, rank
  or confidence
- Kept search and ranking as aligned, whole-row selectable lists with code
  before name, and added consistent ETF identity and evidence cards to detail
  and comparison
- Removed operational freshness and completeness rendering from public detail
  and comparison while retaining those data contracts for owner administration
- Made the grade lookup non-blocking so an unavailable grade service does not
  hide the primary ETF data
- Evidence: `frontend/ui/quality_grade.py`,
  `frontend/pages/etf_search.py`, `frontend/pages/performance_ranking.py`,
  `frontend/pages/etf_detail.py` and `frontend/pages/etf_comparison.py`

### V4-6 — Functional integration acceptance — Completed locally

- Verify the complete V4 journey from public input through allocation results,
  ETF exploration, evidence and owner administration
- Pass frontend, API, calculation, data-quality and local security regression
- Recheck grade, missing-data, tax, risk and stateless-request contracts across
  page boundaries
- Record functional defects and resolve them before starting subjective page
  review; this milestone does not select a release candidate
- Track bounded verification slices, unresolved gates and final evidence in
  `V4_FUNCTIONAL_ACCEPTANCE.md`

Delivered:

- Verified 37 core public-planning, allocation, dual-assessment, ETF-grade and
  API-boundary smoke tests
- Verified 76 focused long-term, portfolio-tax, reinvestment, data-quality,
  local-security and deployment-contract tests
- Started temporary native FastAPI and Streamlit services and passed all six
  health, availability and public/private access smoke checks
- Passed Python compilation and the complete 985-test automated regression
- Kept page wording, visible fields, hierarchy, responsive behavior and owner
  experience explicitly unaccepted until V4-7
- Evidence: `V4_FUNCTIONAL_ACCEPTANCE.md`

### V4-7 — Page-by-page UI and UX acceptance — Complete

- Start the local frontend and backend so the owner can inspect the real
  Streamlit experience without waiting for a public domain
- Review home, planner input, allocation result, search, ranking, detail,
  comparison and owner-administration pages one at a time
- For each page, decide which fields should be removed, added, renamed,
  reordered or moved to another page before marking that page accepted
- Review beginner comprehension, visual hierarchy, GoodCat interaction,
  primary actions, responsive behavior and empty, loading, error and missing-
  data states
- Track page decisions and acceptance evidence in `V4_PAGE_ACCEPTANCE.md`
- Keep all accepted page adjustments in one V4-7 pull request and merge only
  after every in-scope page has been reviewed
- Owner accepted all in-scope pages on 2026-08-30 after the final planner
  reward-state artwork adjustment
- Passed Python compilation and the complete 1,040-test automated regression
- Evidence: `V4_PAGE_ACCEPTANCE.md`

## V5 — Data-first result iteration

V5 pauses release-candidate selection and uses measured data enrichment,
algorithm correction and real-page review to determine whether GoodCat
produces useful public planning results. The allocation engine and accepted V4
page structure remain frozen during the first data round so data effects can be
separated from algorithm changes. Owner-approved post-review decisions are
recorded in `docs/V5_ALLOCATION_ASSESSMENT_DECISIONS.md`.

### V5-0 — Scope, field manifest and reproducible baseline

- Inventory every fact actually rendered by the ETF detail page
- Map each visible field to its API, database storage, source and current
  coverage
- Freeze representative detail-page and zero-to-N planner inputs
- Record the pre-enrichment database snapshot and result baseline
- Evidence: `docs/V5_DATA_RESULT_ITERATION.md`

### V5-1 — First-round detail-page data acquisition

- Acquire the complete available official data needed by the currently
  rendered detail page across the ETF universe
- Preserve `ACTUAL`, estimated fallback, formal zero and unavailable semantics
- Reconcile source dates, import evidence, rejected rows and coverage after
  every pipeline run
- Do not change the allocation objective or public page merely to improve the
  measured outcome

### V5-2 — First page and automatic-planning review

- Review representative detail pages using the first-round database snapshot
- Replay the frozen zero-, one- and multiple-holding planning cases
- Measure candidate count, exclusions, whole-share results, capital, monthly
  shortfall, component basis, overlap and long-term availability
- Let the owner judge usefulness before choosing the second-round scope

### V5-3 — Result-driven remaining data acquisition

- Rank remaining data work by the blockers observed in V5-2
- Reconcile active-product status and announced-versus-paid dividend semantics,
  with 00929 as the first acceptance case
- Add constituent, adjusted history, broader ACTUAL evidence or other facts
  only when they materially improve explainability or planning usefulness
- Keep data completeness and source reliability as internal calculation gates,
  not rating-score factors
- Keep data-source changes separate from calculation-method changes

Audit evidence started:

- Rebuilt a no-overwrite 263-ETF candidate at
  `sha256:6e245b0bd79d43a19bc38dee4e7f6e4672a5a2140e6ffd15087ea00f19349e95`
  and verified SQLite integrity plus zero foreign-key violations.
- Confirmed zero-holding requests can produce modeled results, but the
  all-month TWD 3,000 result uses thirteen added ETFs and more than TWD 4.15
  million, outside the approved V5 result direction.
- Confirmed every audited existing-holding request has zero eligible additions
  because 198 otherwise supported candidates lack portfolio-overlap evidence.
- Imported official constituent snapshots for 121 ETFs and 9,049 positions;
  the gate remains `NO_GO` at 116/157 ETFs and 18/21 issuers, with 23 sources
  not automated and 13 automated retrievals failing.
- Confirmed populated overlap data exposes a Decimal-zero defect that crashes
  representative 0050 and 00929 holding requests when a valid pair has no
  shared disclosed constituents.
- Confirmed 00929 is a passive listed ETF and that its future scheduled
  2026-09-14 payment is incorrectly entering the current historical
  `as_of_date` projection.
- Evidence: `docs/V5_3_FULL_DATABASE_AUDIT.md`

The Issue #90 audit pass is complete. Its snapshot preserves 263 ETFs by 18
fields and the complete 263-candidate evidence for each of eight planner
requests. At that snapshot, representative normal holding requests still
raised an allocator error or returned no eligible allocation.

Current constituent recovery evidence:

- Added atomic checkpoint/resume so completed official imports are not fetched
  again when a full-market batch is resumed.
- Recovered eight of thirteen measured automated-source failures without
  lowering the shared completeness threshold.
- Improved the isolated calculation-quality candidate from 116/157 ETFs and
  18/21 issuers to 129/157 ETFs and 19/21 issuers. ETF coverage remains
  `NO_GO`; issuer coverage now passes 90%.
- Kept Cathay, BlackRock, nested-ETF portfolios, unverified currency share
  classes and unreconciled low-weight disclosures unavailable.
- Confirmed with the full planner matrix that data recovery removes the 0050
  and 00929 allocator crash when combined with this #94 correction, but
  current plans still exceed five additions. Evidence:
  `V5_3C_CONSTITUENT_RECOVERY.md`.

V5-3B calculation prerequisite:

- Treat an empty intersection between two valid, quality-gated constituent
  snapshots as formal Decimal zero overlap while preserving missing evidence as
  unavailable.
- Confirmed isolated 0050 and 00929 holding replays no longer raise the
  pairwise-overlap `quantize()` exception; 00929 still exceeds the approved
  maximum-five-ETF direction and remains dependent on Issue #91 semantics.
- Evidence: `docs/V5_3B_ZERO_OVERLAP_FIX.md`

The broader V5-3 phase remains in progress while the documented data coverage,
dividend-history semantics and allocation-size limitations remain unresolved.

### V5-4 — Allocation-result algorithm

- Solve the complete zero-to-N holding and one-to-five added-ETF portfolio
  before calculating a planning grade
- Support exact whole shares, cash-target and investable-budget modes, existing
  holding contribution and non-dominated plan selection
- Separate historical ETF quality, ETF risk and request-specific plan fit
- Add deterministic replay and 00929 evidence-convention acceptance cases
- Keep the result-page layout out of this milestone

### V5-5 — Result-page integration and second review

- Integrate two or three materially distinct compact and expandable result
  cards, with no more than five added ETFs per plan
- Require every requested month to meet the target for a normal cash-target
  card; omit achieved-month count from the collapsed card
- Keep source dates out of the expanded result card while retaining cash-flow,
  tax, holding contribution, risk and limitation evidence
- Review representative real pages before finalizing titles and capital bands

### V5-6 — V5 closeout and owner acceptance

- Resolve accepted data and calculation findings with deterministic tests
- Record unavailable official data and remaining limitations without treating
  them as zero
- Pass complete regression against one exact commit and database snapshot
- Obtain owner acceptance of usefulness before resuming V4-8

### V4-8 — Pre-launch candidate and real-environment gate — Paused for V5

- Run the final frontend, API, calculation, data-quality and local security
  regression after V4-7 page acceptance
- Select one exact release candidate only after both functional and page-level
  experience acceptance are complete
- Deploy that exact candidate to the real host and domain
- Complete SEC-4 on the deployed candidate before public launch

V4-8 must not resume until V5-6 data, allocation and page acceptance is
complete.

## Post-security optional integrations

- Decide whether to build self-service account aliases, passwords, login and
  per-user holding-data isolation
- Third-party market-data evaluation
- Fugle market-data API for quote/history enrichment only
- Sinopac Shioaji read-only account synchronization only
- Portfolio import
- Simulated or live order assessment

These optional integrations must not block the core website roadmap.
