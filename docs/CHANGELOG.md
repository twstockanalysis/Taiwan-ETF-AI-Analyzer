# Changelog

## 2026-08-14 — Union official constituent adapter

- Added automatic discovery of current Union ETF codes and official form-
  backed constituent ingestion.
- Added support for both 009804 and the newly listed 009825 without a hard-
  coded product mapping.
- Enforced the official POST contract, response domain, content type, size,
  identity, date and minimum stock-weight coverage before persistence.

## 2026-08-14 — Session-aware official constituent adapters

- Added automatic HN constituent ingestion through its official public short-
  lived system-token and ETFID-based PCF flow.
- Added automatic Allianz fund mapping and constituent ingestion through its
  official antiforgery cookie/header session.
- Enforced response size, identity, date, stock-weight coverage and declared-
  total reconciliation before persistence; unavailable Allianz assets remain
  fail-closed.

## 2026-08-14 — Franklin official constituent adapter

- Added automatic Franklin ETF-code-to-fund-ID discovery through the official
  ETF catalog and complete holdings ingestion through the official API.
- Converted the official UTC disclosure timestamps to Taiwan calendar dates
  before selecting and persisting a snapshot.
- Kept Cathay, First and KGI fail-closed after live checks returned no complete
  stock payload through their currently exposed application responses.

## 2026-08-14 — Mapped official constituent adapters

- Added automatic ETF-code-to-fund-ID discovery and official constituent
  ingestion for Mega, Fuh Hwa, UOB and E.SUN.
- Added support for Fuh Hwa's official asset Excel while keeping the same
  identity, date and 90% stock-weight validation as HTML and JSON sources.
- Kept Capital in verified-only status because its current server-rendered
  response exposes ten stock rows totaling 73.94%, which fails the completeness
  gate and must not be persisted as a full snapshot.

## 2026-08-14 — Direct-code official constituent adapters

- Added official constituent ingestion for Fubon, SinoPac, Taishin, CTBC and
  Nomura through one issuer-dispatched import interface.
- Enforced ETF identity, official data date, stock-table selection and at least
  90% disclosed stock-weight coverage before snapshots can be persisted.
- Kept futures, cash and other non-stock rows outside constituent overlap data.

## 2026-08-13 — Yuanta official constituent ingestion

- Audited all 23 issuers in the TWSE ETF issuer universe and added a
  machine-readable status registry without overstating page discovery as
  automated support.
- Verified complete official holdings or PCF responses for all 21 applicable
  non-Yuanta issuers, and classified JKO outside equity-overlap scope because
  its current products are commodity futures trusts.
- Added complete Yuanta ETF stock weights from the same official `PCF/Daily`
  bridge used by the issuer product page.
- Rejected mismatched ETF codes, invalid trading dates, missing rows and stock
  weight coverage below 90% before creating an immutable snapshot.
- Excluded futures, bonds and ETF positions from stock-overlap inputs while
  preserving the official product page as source provenance.
- Confirmed that the documented Fugle Market Data and Sinopac Shioaji APIs
  identify and quote ETFs but do not expose ETF constituent weights.

## 2026-08-13 — ETF constituent snapshot foundation

- Added immutable, source-dated ETF constituent snapshots and weighted
  positions to SQLite and deployment-readiness checks.
- Added atomic repository writes with duplicate identifier and total-weight
  validation.
- Added transparent pairwise overlap as the sum of smaller disclosed weights,
  without normalizing incomplete issuer disclosures to 100%.
- Kept manual overlap separate pending official issuer-source automation.

## 2026-08-13 — Explainable multi-score assessment baseline

- Added a deterministic four-factor assessment to candidate holding analysis.
- Preserved data-quality, total-return, principal-risk and after-tax cash-flow
  gates ahead of optional payment-month coverage.
- Exposed factor evidence and stable reason codes without an opaque score,
  buy/sell label, external model or paid API dependency.
- Added a Streamlit summary table with expandable evidence and explicit limits.
- Added separate ETF-quality and current-portfolio-fit scores with total return
  as the largest component; the UI intentionally has no confidence badge.
- Added official ACTUAL 76W as a bounded tax-efficiency component while keeping
  missing official data unscored rather than converting it to zero.
- Excluded manual overlap assumptions from scoring until automatic ETF
  constituent ingestion can calculate weighted portfolio overlap.
- Kept ETF-quality scores and components in the backend while showing only the
  final portfolio-fit score on the page.

## 2026-08-13 — Custom target payment months

- Added backward-compatible target payment months to monthly combination requests;
  omitted targets still mean all twelve calendar months.
- Added single-month, alternating-month, quarterly, annual fixed-month and
  arbitrary-month Streamlit controls in the existing batched analysis form.
- Limited gap selection and candidate contribution to user-selected months
  while preserving data-quality, total-return, downside-risk and overlap gates.
- Added target-month normalization, validation, response display and tests.

## 2026-08-13 — KGI dividend announcement discovery

- Added ETF-code searches against KGI SITE's official `ArticleVC` endpoint
  using the same bounded ETF tag and function identifier as the public page.
- Accepted only official PDF links titled as post-distribution announcements,
  while retaining rejection reasons for pre-announcements, no-distribution
  decisions, unrelated ETF codes and unrelated notices.
- Kept every discovered PDF at `UNKNOWN` information basis until an
  issuer-specific content parser verifies formal ACTUAL composition.
- Added a read-only JSON CLI and official-domain, input-validation, response-
  size and content-type safeguards.

## 2026-08-13 — Multi-issuer dividend source framework

- Registered explicit discovery capabilities and official domains for Cathay,
  CTBC, KGI and UPAM dividend-document sources.
- Added deterministic, ETF-code-based HEAD discovery for CTBC's official
  `ETFLatestDividend` PDF path without downloading or snapshotting the file.
- Kept CTBC, KGI and UPAM in discovery-only status until their document content
  parsers independently prove ACTUAL versus estimated semantics.
- Added path-injection, redirect-domain, content-type, missing-document and
  source-capability tests.

## 2026-08-12 — Cathay actual-dividend announcement discovery

- Added bounded ETF-code searches against Cathay SITE's public announcement
  JSON API instead of scraping interactive announcement buttons.
- Added official-domain validation for the Cathay API and uploaded-document
  host, with explicit network permission required.
- Added deterministic rejection of pre-announcements, estimated notices,
  unrelated titles and non-PDF documents before ACTUAL parsing.
- Added a JSON CLI that exposes accepted PDF candidates and rejected items with
  reasons without persisting source snapshots.

## 2026-08-12 — Estimated component calculation fallback

- Made tax and reinvestment scenarios prefer the latest complete official
  `ACTUAL` component event and automatically fall back to the latest complete
  `ESTIMATED` event when official composition is unavailable.
- Kept estimated component codes as `EST_*` throughout calculation instead of
  relabeling them as official `54C` or `76W`.
- Added explicit `ACTUAL` versus `ESTIMATED_FALLBACK` basis metadata to API
  results and a visible Streamlit warning when fallback assumptions are used.
- Added explicit, user-adjustable tax-treatment assumptions for estimated
  dividend, interest, realized-gain, equalization and other categories.

## 2026-08-12 — Estimated dividend component amounts

- Converted e添富 estimated component ratios into per-unit amounts when the
  parent dividend amount is available and the component amount is absent.
- Labeled converted values as derived from total dividend times estimated
  ratio, while preserving official amounts when supplied.
- Kept estimated dividend, interest and realized capital gain separate from
  official tax codes such as `54C` and `76W`.
- Verified the stored 0050 example: 0.6 TWD × 26% = 0.156 TWD and 0.6 TWD ×
  74% = 0.444 TWD.

## 2026-08-12 — M12 reviewed ACTUAL launch seed

- Added bounded ETF/year queries to the TWSE dividend pipeline while keeping
  the existing unfiltered default unchanged.
- Added an explicit mode that preserves independently valid parent dividend
  events while rejecting incomplete or abnormal estimated composition.
- Rehearsed the official TWSE 00878 2023 history and Cathay announcement 5141
  flow against a fresh candidate copy before changing the local candidate.
- Created a verified pre-import backup and manifest, then imported four parent
  events, one traceable source document and the official 76W/54C components.
- Restored the pre-import backup to a separate temporary path and verified its
  SHA-256, exact row counts, SQLite integrity and foreign keys.
- Re-synchronized the review queue and moved the ordinary launch-data decision
  from `NO_GO` to `READY` without a limited-coverage exception.
- Kept the minimal 0.342466% coverage and 582 remaining review items explicit.

## 2026-08-12 — M12-6 launch-data threshold and decision

- Added an executable ACTUAL/76W/source-document launch gate with a
  machine-readable decision and deployment-safe exit code.
- Required named approval and a reason for any limited-coverage exception.
- Tested the ready, no-go, limited-approved and invalid-approval paths.
- Evaluated the current 288-event candidate as `NO_GO`: reviewed ACTUAL,
  official 76W and traceable ACTUAL source-document counts are all zero.
- Documented that M12-6 implementation is mergeable while public launch remains
  blocked pending reviewed data or an explicit limited-coverage decision.

## 2026-08-12 — M12-5B native local deployment validation

- Added a repeatable native FastAPI/Streamlit split-port smoke command.
- Validated the public/private boundary, both service health endpoints and the
  Streamlit root against an isolated migrated database.
- Restarted FastAPI and proved the isolated owner condition persisted while
  schema integrity and foreign keys remained valid.
- Recorded owner-confirmed browser acceptance for public navigation, owner
  unlock, private route visibility, persisted target display and relock.

## 2026-08-12 — M12-5A reproducible production deployment package

- Added pinned Python dependencies and a non-root application container.
- Added private FastAPI/Streamlit services behind a Caddy HTTPS reverse proxy
  with durable SQLite storage and mandatory deployment secrets.
- Added container health checks, public/owner smoke verification, restart and
  rollback guidance, and static deployment contract tests.
- Recorded that this workstation has no Docker installation and no authorized
  host/domain, so public infrastructure proof remains an external M12-5 step.

## 2026-08-12 — M12-4 owner-only decision boundary

- Protected every decision-profile read, write, analysis, record and export
  endpoint with a fail-closed, constant-time owner token gate.
- Added a backend-verified Streamlit unlock flow, session-only token storage,
  explicit relock and conditional private navigation.
- Kept public ETF functionality anonymous and removed shared caching from
  private profile responses.
- Documented secret rotation, HTTPS dependency and the boundary between this
  operational gate and a future account system.

## 2026-08-12 — M12-3 scheduling and operational monitoring

- Added a locked, declarative scheduled pipeline runner with per-job logs,
  atomic run reports and stop-on-first-failure behavior.
- Added machine-readable database, disk, pipeline, freshness, backup, restore
  drill and API health checks with deployment-safe exit codes.
- Documented initial alert thresholds, Task Scheduler setup and reviewed-ACTUAL
  handling while keeping host credentials and provider binding out of source.

## 2026-08-12 — M12-2 durable SQLite backup and recovery

- Added an absolute `TW_ETF_DATABASE_PATH` production contract while retaining
  the repository database only as the local-development default.
- Added no-overwrite SQLite backup and restore commands with SHA-256, byte-size,
  schema, integrity, foreign-key and exact row-count verification.
- Added a versioned backup manifest, initial retention policy and recovery
  runbook that restores to a new path before operational cutover.
- Kept backup scheduling, off-host automation and monitoring in M12-3.

## 2026-08-12 — M12-1 deployment database readiness

- Added explicit deployment database `verify`, `initialize` and isolated
  `rehearse` commands.
- Added current-table and required-column checks, SQLite integrity and foreign
  key validation, and before/after row preservation evidence.
- Used SQLite's backup API for a transactionally consistent rehearsal copy and
  refused in-place or pre-existing rehearsal destinations.
- Recorded custom target months and explainable AI assessment as the first two
  second-version priorities after M12, without expanding M12 scope.

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
