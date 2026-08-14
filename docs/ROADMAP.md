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

- Decide whether to build self-service account aliases, passwords, login and
  per-user holding-data isolation
- Third-party market-data evaluation
- Fugle market-data API for quote/history enrichment only
- Sinopac Shioaji read-only account synchronization only
- Portfolio import
- Simulated or live order assessment

These optional integrations must not block the core website roadmap.
