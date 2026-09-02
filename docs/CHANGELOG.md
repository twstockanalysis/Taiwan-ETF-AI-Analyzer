# Changelog

## 2026-09-03 - V5-3D resumable full-market yield recovery

- Replayed all 263 ETFs across 18 detail fields and all eight planner cases
  against a separate refreshed candidate database.
- Replaced unbounded TWSE redirect following with bounded transient retries and
  backoff, then persisted downloaded official closes and calculated yields as
  resumable database checkpoints.
- Recovered 717 missing event yields, reaching 1,518/1,524 while retaining one
  future event and five unavailable reference closes as explicit missing data.
- Retained the constituent `NO_GO` decision at 120/157 calculation-quality ETFs
  and documented Cathay as the highest-impact next data cohort.

## 2026-09-02 — V5-4 complete-plan views

- Preserved every submitted existing ETF in each allocation result while
  limiting only newly added ETF codes to five.
- Added capital-efficient, monthly-balanced and diversified-protection
  post-feasibility views, with duplicate plans omitted rather than fabricated.
- Included existing position values in concentration comparisons and fixed a
  duplicate addition of solver-produced monthly cash in the response builder.
- Kept the MeowMeow planning-grade formula and public thresholds unimplemented
  because the accepted decision record defines the concept but explicitly
  defers those numeric choices to owner review of representative results.

## 2026-09-02 - V5-3A paid-dividend analysis cutoff

- Separated future scheduled dividend evidence from paid historical cash-flow
  projections by applying the explicit analysis date to all calculation and
  eligibility callers.
- Applied the same paid-date boundary to ACTUAL/eFortune component selection
  without relabeling either source basis or removing announced events.
- Added deterministic 00929 acceptance coverage for its July and August paid
  events and September scheduled payment, while preserving passive-management
  semantics and backward-compatible no-cutoff repository behavior.

## 2026-09-02 - SEC-3B Caddy gRPC dependency remediation

- Updated the Caddy build's explicit gRPC pin from `v1.82.1` to the fixed
  `v1.83.1` release after the required Trivy gate identified
  `CVE-2026-84304`.
- Preserved the released Caddy source commit, Go builder, Alpine runtime and
  existing edge hardening without adding a scanner exception.
- Updated deterministic deployment-contract and SEC-3 dependency evidence.

## 2026-09-02 - V5-3B zero shared constituent overlap

- Fixed pairwise overlap calculation for valid constituent snapshots with no
  shared disclosed constituents by preserving Decimal zero semantics.
- Added deterministic overlap and allocation-strategy regression coverage.
- Replayed representative 0050 and 00929 holding requests without the former
  `quantize()` exception while retaining the remaining V5-3 limitations.

## 2026-09-02 — V5-3C constituent recovery

- Added atomic official-constituent checkpoint and resume behavior that skips
  completed imports and retries only failed ETF codes.
- Recovered eight of thirteen measured automated-source failures while keeping
  the shared completeness gate and immutable snapshot rules unchanged.
- Added a Fubon-specific 85% lower bound only when its complete official asset
  page also discloses a separate non-stock table, and reconciled First formal-
  zero stock rows to the official stock-asset total.
- Improved the isolated full-market gate to 129/157 ETFs and 19/21 issuers,
  while retaining an honest `NO_GO` ETF-coverage decision and explicit
  unavailable reasons for the remaining sources.
- Replayed all eight V5 planner cases against the recovered candidate and the
  #94 zero-overlap correction; all cases completed, but normal plans still
  exceed the approved maximum of five additions.

## 2026-09-01 - V5-3 full-database readiness audit

- Added a reproducible full-database audit covering field availability, all
  planner exclusion codes, zero-to-N holdings, all-month targets, formal zero,
  missing-data cases and the 00929 paid-versus-future evidence boundary.
- Recorded that zero-holding calculations return results but existing-holding
  cases remain blocked by missing overlap data, while current target-met plans
  exceed the approved five-added-ETF V5 direction.
- Recorded the isolated 121-ETF official constituent import, the remaining
  116/157 quality coverage, and the zero-shared-constituent Decimal exception
  exposed by representative existing-holding replays.
- Made the audit matrix preserve allocator exceptions as explicit `ERROR`
  evidence instead of aborting the remaining cases.
- Expanded the consolidated audit to retain all 263 per-ETF field records and
  all 263 market candidates for each planner case, while keeping the broader
  V5-3 phase explicitly incomplete until normal holding requests are usable.

## 2026-08-27 — V4-7 page experience review started

- Added the owner-led V4 page acceptance record and fixed review order.
- Kept all page adjustments on one V4-7 branch and reserved merge until every
  public and owner-administration page is accepted.
- Started with the running home page; automated tests remain supporting
  evidence and do not replace owner UI/UX approval.
- Shortened the ETF search label to `搜尋` and aligned its results with the
  borderless, whole-row detail links used by the performance ranking, without
  changing the requested data-column order; each search column now keeps a
  fixed content-derived width based on its heading or longest visible value.
- Shortened the comparison page to `比較`, clarified its primary action and
  placed the minimum-input hint beside that action; shortened the planner
  holding-row action to `持股`.
- Expanded comparison input from code-only entry to ETF code or name lookup;
  exact codes, exact names and unique name keywords resolve deterministically,
  while ambiguous names require a more complete entry. The hint now states the
  two-to-four ETF comparison limit.
- Moved private login out of the sidebar into a top-right `喵窩` dialog,
  defaulted public navigation to collapsed and retained the native sidebar
  control and per-session owner verification behavior.
- Tightened the search result summary so its existing divider immediately
  follows the result count, page and page-size metrics.
- Renamed the public historical-quality presentation to `喵喵評等` across
  planner, search, ranking, detail and comparison views without changing the
  underlying grade contract.
- Moved search and performance-ranking clear/reload actions into their filter
  cards directly below the primary action, tightened their spacing and aligned
  their left edge; renamed the primary actions to `搜尋` and `篩選`.
- Shortened the ETF detail heading to `詳細資料`, removed the repeated query-code
  caption and aligned its renamed `更新` action beside the return control.
- Added a broker-style price trend chart to the detail performance card using
  only saved official TWSE daily closes, placed it before the renamed
  `資料來源於證交所` caption, and kept insufficient history visibly pending
- Connected the ETF-detail `76W 與資本利得分析` to the shared composite
  component selector on a per-dividend basis: complete ACTUAL composition is
  preferred, while complete e添富 realized-capital-gain composition is used as
  an explicitly labelled fallback without changing formal 76W coverage.
  without filling missing dates or prices with zero.
- Tightened the detail identity card, moved classification beside the ETF name,
  removed its redundant core-data heading and standardized quality badges with
  a colon plus `暫無` for unrated ETFs.
- Kept public missing-data explanations concise while restricting detailed
  evidence gaps and master-data diagnostics to verified `喵窩` sessions.
- Aligned the desktop sidebar navigation start with the main return-home action
  without changing navigation-item order or relative spacing on any page.
- Restricted the unrated data-gate explanation to `喵窩` sessions and changed
  detail-page missing-value copy to `資料抓取中`, preserving missing values in
  the API and database rather than converting them to zero.
- Tightened the ETF detail code/name spacing without changing card alignment.
- Moved the top-right `喵窩` action into the same header row as the home brand
  title or each inner page's return-home action, removing its former standalone
  row; recalibrated the desktop sidebar so its home item stays vertically
  aligned with the return action.
- Removed the legacy target-cash-flow section from ETF detail and restricted
  its separate single-ETF tax/reinvestment scenario tool to verified `喵窩`
  sessions while preserving the public planner's portfolio tax calculation.
- Simplified the detail performance heading and source copy, and grouped its
  period metrics into a single bordered card.
- Reworked the detail dividend summary as a compact card with three primary
  metrics, a yearly stacked cash/stock dividend chart beside a separate yield
  line chart, and concise TWSE source/fallback copy; missing stock-dividend data
  remains explicit and is never converted to zero.
- Removed redundant divider lines between consecutive ETF detail cards.
- Removed the technical yield-basis column from the public dividend summary
  table without changing source provenance or fallback calculations.
- Combined dividend summary rows with event-composition disclosures so each row
  expands in place, removing the duplicated lower history section.
- Fixed dividend charts to a rolling five-year axis, simplified chart labels,
  separated same-year payments with dashed stacked-bar borders and restricted
  the stock-dividend ingestion notice to verified owner sessions.
- Renamed the detail dividend card to `配息資料`; combined cash and stock
  amounts as `現金/股票`, preserving unavailable stock data as `—` while
  displaying a confirmed zero as `0`. Missing official periods now fall back
  to the ex-dividend calendar quarter such as `2026/Q3`.
- Matched the dividend-chart legend swatches to the exact bar colors, hid the
  Streamlit chart toolbar, and made the expandable history list a compact
  static-width presentation with a shaded header and no horizontal viewport.
- Stabilized expandable dividend row columns with shared visual widths and a
  header offset matching the disclosure arrow gutter.
- Narrowed the dividend history `年/季` column, renamed `股利發放日` to
  `發放日`, and replaced tab stops with display-width padding so every header
  and row separator shares the same position.
- Standardized every titled card, including the detail-page cards, to a compact
  `10px` top inset, while leaving untitled containers and metric cards
  unchanged.
- Removed the standalone ETF-comparison section from the detail-page footer
  then moved the shortened `加入比較` action to the identity card's upper-right
  corner, aligned with the ETF code/name and restored to an unframed page link.
- Renamed the expanded e添富 section to `現金股利組成`, reduced its public
  table to composition, ratio and amount, and removed estimated wording from
  component descriptions while retaining e添富 as the official fallback when
  formal ACTUAL income composition is unavailable.
- Removed the explanatory e添富 amount-conversion caption below the cash
  dividend composition table while retaining raw provenance in the API.
- Added a shared composite dividend-component service used by the event API,
  tax/reinvestment, portfolio projection and market eligibility: it selects
  one complete ACTUAL mix first, otherwise one complete e添富 fallback, and
  never mixes bases. The detail page now renders only this selected mix under
  `現金股利組成` and removes the separate `實際所得組成` block.
- Added a distinct completed-work GoodCat reward state for successful and
  partial planner results: the cat looks happy and raises one paw while the
  reward itself remains intentionally absent from the transparent artwork.
- Completed owner-led acceptance for every V4-7 page and global responsive
  behavior, then passed Python compilation and the complete 1,040-test suite.

## 2026-08-27 — V4-6 functional integration acceptance

- Added a bounded functional-integration acceptance matrix that separates
  automated contract evidence from the later owner-led page experience review.
- Defined the first smoke-test slice for public planning, whole-share results,
  dual assessment, ETF grade lookup and public/private API boundaries.
- Verified portfolio tax, reinvestment, long-term, data-quality, local-security
  and deployment contracts with 76 additional focused tests.
- Passed six native FastAPI/Streamlit health and access-boundary smoke checks,
  Python compilation and the complete 985-test regression.
- Closed V4-6 locally while keeping all visible page and user-experience
  decisions reserved for the owner-led V4-7 review.

## 2026-08-26 — V4-5 explore and evidence pages

- Added one batch ETF historical-quality-grade endpoint for search, ranking,
  detail and comparison pages, reusing the V4-1 publication gate and never
  exposing raw score, rank or confidence fields.
- Added consistent `A+` through `F` or `暫不評等` presentation to public ETF
  discovery tables, detail evidence and comparison summary cards.
- Separated code and name columns and made performance-ranking rows selectable
  as a whole, matching the existing search-result interaction.
- Moved operational data freshness and completeness displays out of public ETF
  detail and comparison pages while preserving their backend/admin contracts.
- Kept primary ETF content available when the independent grade request fails.
- Split post-V4 development into functional integration acceptance, a separate
  owner-led page-by-page UI/UX adjustment stage, and the final real-environment
  release-candidate and SEC-4 gate.

## 2026-08-26 — V4-4 allocation result and assessment experience

- Added compact comparison cards for every materially different recommended,
  balanced or concentrated plan and a focused detail card for the selected
  plan.
- Separated owner-goal fit from each ETF's historical quality grade, with
  public-safe `A+` through `F` or explicit `暫不評等` semantics and no raw score,
  rank or confidence output.
- Replaced the dense addition table with per-ETF cards showing whole shares,
  required capital, supported months, inclusion reasons and the primary risk.
- Kept target-month coverage and remaining shortfall in the primary result and
  moved holdings, assumptions, exclusions, history and long-term projections
  into labeled secondary disclosures.
- Preserved the existing deterministic allocation engine and public stateless
  FastAPI response boundary.

## 2026-08-26 — V4-3 home and planning journey

- Rebuilt the consumer home page around one primary GoodCat planning action
  and three short preparation cards for payment months, cash target and
  optional existing holdings.
- Reordered the public planner into one beginner-facing five-step input card
  while preserving the fixed-width zero-to-N holdings editor and deliberate
  selection-before-delete interaction.
- Added attentive, working, ready and caution GoodCat feedback for input,
  calculation, target-met, partial, no-allocation and service-error states.
- Added session-only input signatures so changing any submitted condition
  immediately hides the old result instead of presenting a stale allocation.
- Preserved the anonymous, non-persistent FastAPI request boundary and kept all
  calculation, whole-share and data-missing semantics unchanged.

## 2026-08-26 — V4-2 GoodCat theme and shared components

- Added five original flat gray-and-white GoodCat state illustrations with
  real alpha transparency, a consistent big-head/small-body identity, sleepy
  idle eyes, restrained feline body language and repository-local provenance
  documentation.
- Added the approved light neutral palette through native Streamlit theme
  configuration without external fonts or a programming-language migration.
- Added reusable GoodCat companion and beginner explanation cards that keep
  character state independent from backend calculations and always pair images
  with visible Traditional Chinese state descriptions.
- Added a limited idle-state integration to the existing home page; the full
  consumer landing and guided planning rebuild remains V4-3.

## 2026-08-26 — V4-1 assessment calibration and grade gate

- Added a versioned public-safe `A+` through `F` historical quality grade while
  keeping raw scores, ranks and confidence labels private.
- Added explicit `UNRATED` semantics and market-wide publication gates for
  sample size, supported-universe coverage and score saturation.
- Added a read-only calibration report and command with aggregate factor
  coverage, score distribution, boundary sensitivity and adoption decisions.
- Confirmed the current database has only six trustworthy provisional grades
  across 192 supported products and a saturated total-return factor, so no
  consumer-facing letter grade is published yet.
- Kept the current deterministic risk gates, deferred fill scoring and retained
  constituent concentration as separate ETF and portfolio risk evidence.

## 2026-08-26 — V4-0 product experience contract

- Closed further V3-8 page acceptance after the owner accepted its cleanup as
  the baseline for the V4 redesign.
- Defined separate ETF historical-quality grades and owner-goal allocation-fit
  results without exposing raw scores, ranks or confidence labels.
- Kept the current risk gates and allocation engine while treating fill and
  concentration ideas from the external formula as calibration candidates.
- Defined the relaxed gray-and-white GoodCat direction, accessible character
  states and native Streamlit implementation boundary.
- Kept real-domain deployment and SEC-4 `READY` as mandatory pre-launch gates,
  not blockers for local V4 development.

## 2026-08-25 — V3-8 home-page acceptance

- Made the public cash-flow planner the home page's primary action and reduced
  ETF search, ranking, comparison and data completeness to secondary paths.
- Replaced backend URL, database engine, import-batch and detailed pipeline
  coverage output with a beginner-readable public data snapshot.
- Added concise public boundaries for persistence, order placement, real-time
  signals and performance guarantees.
- Replaced remaining navigation emoji with Material Symbols and recorded the
  page-by-page acceptance order and relocation decisions.

## 2026-08-25 — V3-6 portfolio tax and reinvestment

- Added a public stateless portfolio projection endpoint for 1-to-20-year
  conservative, base and optimistic market scenarios.
- Extended tax and reinvestment from one ETF to every resulting allocation
  holding, with spend, excess-only, custom-percentage and full-reinvestment
  outcomes.
- Modeled dividend-related individual income tax and supplementary NHI while
  preserving ACTUAL versus estimated composition and official `76W` zero or
  unavailable semantics.
- Prevented double counting by treating forward return bands as gross before
  portfolio tax and reinvested distributions as internal cash flow.
- Added beginner-facing public controls, comparison results and a native
  portfolio-value-plus-usable-cash chart without legal text or internal scores.

## 2026-08-25 — V3-5 portfolio history and long-term scenarios

- Added maximum-compatible, 3Y, 5Y and 10Y portfolio evidence based on the
  selected allocation's whole shares, common official closes and actual TWD
  payment-date distributions.
- Kept insufficient periods unavailable and disclosed that raw official closes
  do not yet adjust ETF splits or reverse splits.
- Added conservative, base and optimistic ten-year total-value-index scenarios
  from complete trailing one-year observations without presenting them as
  forecasts or actual cash amounts.
- Connected the public planner's selected allocation to a beginner-facing
  historical table and native scenario chart while keeping internal scores and
  confidence labels out of the response.

## 2026-08-25 — V3-2 full-market eligibility index

- Added a server-built index over every ETF master row with explicit product-
  scope exclusions for unsupported bond, leveraged, inverse, futures,
  commodity and multi-asset products.
- Applied fixed reference-price, completeness, freshness, payment-stability,
  after-tax cash, total-return, downside, dividend-component and portfolio-
  overlap gates before integer optimization.
- Preserved ACTUAL versus estimated component basis, missing and future-dated
  facts, source dates and stable exclusion/trade-off reasons.
- Reused the deterministic ETF-quality calculation only for internal eligible-
  candidate ordering and kept all scores, score components, ranks and
  confidence labels out of the public API response.
- Added a reproducible input-and-facts snapshot identity plus internal twelve-
  month Decimal cash-per-share inputs for V3-3.
- Verified the existing V2-12 isolated data snapshot yields three eligible
  candidates while the older default database honestly yields none until its
  official prices and calculation data are refreshed.

## 2026-08-25 — V3-1 public stateless planning baseline

- Added a public `POST /api/v1/allocation-plans/baseline` boundary that accepts
  a fixed cash target, selected months and zero to 500 existing ETF holdings
  without requiring an owner token or writing the request to profile tables.
- Added monthly, odd-month, even-month, quarterly, half-year, annual and custom
  month presets through one normalized January-to-December request contract.
- Calculated the existing portfolio's source-dated official-close value and
  payment-date historical cash baseline while preserving missing values,
  incompatible currencies and formal zero months.
- Added a public Streamlit flow with an initially empty dynamic holdings table,
  a twelve-month target-gap result and beginner-facing data warnings.
- Kept ETF selection, whole-share additions and required-capital optimization
  explicitly deferred to V3-2 and V3-3, with internal quality and confidence
  fields absent from the public response.

## 2026-08-25 — V3-0 product direction and allocation contract

- Renamed the visible product to `ETF奈米戶` and centered the PRD on ETF
  beginners, selected payment months and zero to N existing holdings.
- Changed SEC-4 from a pre-V3 gate to a mandatory pre-public-launch gate so V3
  and page-by-page information review can be completed locally first.
- Defined the public stateless full-market allocation boundary, whole-share
  model, deterministic objective order, result statuses and required
  explanations.
- Added the V3-1 through V3-8 delivery sequence, including a dedicated
  page-by-page field and navigation review before real-domain deployment.
- Kept internal ETF-quality scores and confidence labels out of the frontend.

## 2026-08-24 — SEC-4 local production-compose rehearsal

- Built and started the exact backend, Streamlit frontend and Caddy images on
  Windows 11 with WSL 2 and Docker Desktop from commit `75722b0`.
- Verified isolated database readiness, container health, HTTPS smoke checks,
  owner boundaries, HTTP redirect and full restart persistence without
  modifying the source database or Windows certificate trust store.
- Recorded owner-confirmed ETF lookup, dividend composition, holdings cash
  flow, Excel export, private access and refresh persistence.
- Kept public launch at `NO_GO`; localhost evidence cannot replace a real
  domain, publicly trusted TLS or provider firewall and operational evidence.

## 2026-08-21 — SEC-4 public-host acceptance gate implementation

- Added a fail-closed external probe for public DNS, certificate lifetime, TLS
  negotiation, HTTP-to-HTTPS redirects, security headers, release identity,
  blocked API docs, owner boundaries, private caching and edge body limits.
- Added a 24-hour operator-attestation contract for firewall/admin exposure,
  shared edge rate limits, production-secret injection and rotation, off-host
  backup/restore, certificate renewal alerting and exact deployed containers.
- Added `X-Release-Sha` at the edge and made the exact 40-character release SHA
  a mandatory deployment setting and automated acceptance check.
- Changed the production smoke test to refuse redirects and read the owner
  token from an environment variable instead of a process-list-visible CLI
  argument.
- Kept the gate at `NO_GO` until a real host, domain and complete external
  evidence produce a `READY` report for the exact deployed commit.

## 2026-08-21 — SEC-3 dependency, container and runtime gate

- Upgraded the pinned Python and Caddy base images and added Python dependency
  auditing plus high/critical application and edge image scanning in CI.
- Applied current Debian security updates during application-image builds
  instead of accepting fixable operating-system advisories from the base tag.
- Rebuilt the exact Caddy 2.11.4 source commit with Go 1.27.0 and patched
  `x/net`, `x/text` and gRPC modules, then used an updated Alpine 3.24 runtime
  to remove newly disclosed fixable edge-image vulnerabilities without
  adopting unreleased Caddy functionality.
- Hardened all services with non-root users, read-only root filesystems,
  bounded temporary storage/process counts, dropped capabilities and
  no-new-privileges; only Caddy retains `NET_BIND_SERVICE`.
- Removed public API documentation routes, enforced proxy and application body
  limits, and added CSP, clickjacking, permissions and server-header controls.
- Added bounded per-source public/private request limits with private no-store
  behavior and explicit 429 retry guidance.
- Added isolated container health, UID, secret-history, dependency and complete
  regression gates using actions pinned to immutable commit SHAs.

## 2026-08-21 — SEC-2 authentication and API boundary gate

- Locked the complete 11-operation private API inventory behind the owner gate
  and added non-cacheable headers to every private success and error response.
- Changed owner-token comparison to fixed-size SHA-256 digests with constant-
  time comparison and a bounded submitted-token length.
- Added application limits for request targets, headers, bodies, calculation
  numbers and manual-holding batches, including streamed-body enforcement.
- Stopped frontend API redirects while carrying custom headers and sanitized
  validation and unexpected-error responses so inputs and internals are not
  reflected.
- Added adversarial coverage for direct API/export access, CORS, injection,
  traversal, redirect, oversized payload, caching and error leakage boundaries.

## 2026-08-21 — SEC-1 secret exposure and history gate

- Recorded owner confirmation that all seven V2 calculation browser checks
  passed and closed V2 acceptance.
- Added a sanitized scanner for worktree files, ignored runtime artifacts, all
  fetched Git refs, commit messages and local unreachable blobs.
- Found zero credential or sensitive-filename exposures and zero unscanned
  oversized objects; no rotation or history rewrite was required.
- Expanded secret, key, log, report, backup and source-snapshot ignore rules.
- Restricted the Docker build context to locked dependencies plus backend and
  frontend source, and made the full secret scan a release prerequisite.

## 2026-08-20 — V2-13 calculation browser acceptance preflight

- Ran the isolated candidate through public/private smoke checks, saved-holding
  analysis, monthly combination, candidate addition and four tax/reinvestment
  scenarios.
- Fixed a live HTTP 500 caused by an unbounded repeating decimal during annual
  dividend-cash aggregation.
- Added explicit projection years and prominent warnings when a 1Y price return
  is mechanically compounded across a multi-year scenario.
- Recorded the calculation evidence, known data gaps and final owner browser
  checklist; visible owner confirmation remains pending.

## 2026-08-20 — V2-12 isolated calculation candidate

- Added a no-overwrite command that copies, migrates, refreshes and verifies an
  isolated calculation database against explicit ETF codes.
- Added separate core-calculation and constituent-overlap readiness so missing
  optional overlap cannot masquerade as zero or block valid cash-flow testing.
- Refreshed 0050, 0056 and 00918 to complete four-period performance, official
  closes, dividend history and estimated component mixes.
- Kept 00918 overlap unavailable after its current official PCF response
  exposed only 49.20% incompatible foreign-stock weight.
- Capped rolling-window distribution stability at 100% after live data exposed
  a four-calendar-year boundary inside a three-year rolling window.
- Verified real monthly-combination and tax/reinvestment API calculations
  against the isolated candidate.

## 2026-08-14 — V2-11 calculation data integration

- Replaced Streamlit's manual overlap inputs with fail-closed automatic
  constituent overlap for monthly ETF comparison and candidate-holding analysis.
- Added market-value-weighted current-portfolio overlap while retaining the
  existing pairwise disclosed-weight method for a single base ETF.
- Included automatic overlap as a bounded portfolio-fit component only when
  every required snapshot passes freshness and disclosed-weight gates.
- Kept the old request fields as ignored compatibility inputs; missing or
  rejected constituent data remains unknown rather than becoming zero.

## 2026-08-14 — V2-10 constituent data gates

- Added full-market and bounded official constituent batch ingestion.
- Added calculation-universe mapping, freshness, disclosed-weight, ETF and
  multi-issuer coverage gates with machine-readable `READY`/`NO_GO` output.
- Made identical immutable snapshot imports safely repeatable and documented
  the post-V2 security validation milestones.

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
- removed the repeated event-detail table from each dividend expander; the
  summary row already carries period, amount, yield, ex-date and payment date,
  so expanded content now starts with the useful composition details.
- renamed the public dividend-expander heading from `預估配息組成` to the
  shorter `股利組成`; the underlying estimated-basis semantics are unchanged.
- replaced dashed outlines around every dividend-bar segment with horizontal
  dashed rules only at internal cumulative-payment boundaries; the outside of
  each annual bar is now unoutlined.
- moved the cash/stock dividend legend inline to the right of the `股利`
  heading, removed both chart y-axis titles while retaining numeric ticks, and
  renamed the right chart heading to `殖利率(%)`.
