# M12 Entry Audit Gate

Status: **re-executed on merged main `1e0a920` on 2026-08-12**. The user-confirmed
post-M9 direction is unchanged, M11-5 is complete and merged, and M12 may begin
only after this refreshed entry-gate change is merged.
This preserves the result explicitly confirmed by the user on 2026-08-10.

## Audit baseline and method

The audit started from post-M9 direction commit `03a9635`
(`docs: redefine ETF cash-flow decision roadmap`) and reconciled it against:

- Current merged `main` at `1e0a920`, including M11-5A1, M11-5A2 and M11-5B
- Current `docs/PRD.md`, `docs/ROADMAP.md` and calculation contracts
- Public Streamlit navigation and every page implementation
- The generated FastAPI OpenAPI path set
- Service, Repository and SQLite schema behavior
- The 613-test automated suite and targeted contract and Streamlit tests
- The local deployment candidate database, opened in SQLite read-only mode

The canonical direction remains a public Taiwan ETF cash-flow decision tool
for individual investors with limited professional information. ETF decisions
must continue to apply this order:

```text
total-return and principal-risk checks
-> after-tax cash-flow feasibility
-> tax-efficiency improvement
-> optional monthly-payment coverage
```

## Actual website inventory

### Streamlit pages and user actions

| Route | Visibility | Actual user actions and outputs |
| --- | --- | --- |
| `首頁` | Public | System coverage, freshness, import status and entry links |
| `ETF 查詢` | Public | Code/name search, filters, pagination and ETF-detail navigation |
| `績效排行榜` | Public | Period selection, classifications, pagination and detail navigation |
| `ETF 比較` | Public | Compare 2–4 ETFs and run the M10-5 monthly-payment candidate flow |
| `我的條件與持有部位` | Public today | Mutate singleton conditions and holdings; analyze current holdings and one candidate; save records and export Excel |
| `配息資料品質` | Public | Read ACTUAL/76W coverage and source-review queue state |
| `ETF 詳細資料` | Hidden route | ETF facts, price return, dividends, ACTUAL 76W, source freshness, official-close fixed-target analysis, January-December gross/after-tax cash, source-dated principal-risk warnings, comparison entry and four tax/reinvestment scenarios |

The latest Streamlit guidance was used as a review aid. The current callable
pages and `frontend/pages` layout differ from its preferred direct-script
`app_pages` structure, but centralized `st.navigation` and regression tests
make this technical debt rather than a product-entry blocker.

### FastAPI analysis and write boundaries

Website-used analysis boundaries include system overview, ETF read models,
performance, dividends, ACTUAL 76W, tax/reinvestment scenarios,
monthly-payment combinations, current holdings, candidate holdings and saved
decision records, including `POST /api/v1/etfs/{code}/target-analysis`.

One completed M10 read boundary remains an internal/source-data boundary rather
than a standalone Streamlit page:

```text
GET  /api/v1/etfs/{code}/monthly-income
```

The singleton boundary currently exposes unauthenticated reads and writes:

```text
GET/PUT/DELETE /api/v1/decision-profile/...
POST           /api/v1/decision-profile/candidate-analysis/.../decision-records
GET            /api/v1/decision-profile/decision-records/.../export.xlsx
```

Hiding a Streamlit page is not sufficient protection. Before anonymous public
deployment, the entire decision-profile boundary, including holdings, records
and exports, must require authenticated owner access at FastAPI and page level.
Anonymous visitors may continue to use stateless ETF analysis pages.

## Post-M9 objective mapping

| Objective or required output | Status | Evidence and reconciliation |
| --- | --- | --- |
| ETF-only public analysis site | `DELIVERED` | Public search, ranking, comparison, detail and quality pages; no stock model or route |
| Fixed cash target independent of added capital | `DELIVERED` | M10 calculators and M11 portfolio/candidate contracts preserve one fixed target |
| Gross and after-tax cash flow by payment month | `DELIVERED` | ETF detail shows a January–December historical annualized gross/after-tax table and preserves missing months rather than zero |
| Required capital, target coverage and funding shortfall for one base ETF | `DELIVERED` | ETF detail consumes target analysis using the latest stored official close and shows all three outputs |
| Distributions evaluated with market-value change and costs | `DELIVERED` | Target and tax/reinvestment calculators show after-tax total result and prevent double counting |
| Negative total-return, persistent-decline, recovery and peer warnings | `DELIVERED` | M11-5B emits deterministic warnings with observation date, source and threshold evidence; direct API-client and AppTest coverage is present |
| Four reinvestment policies | `DELIVERED` | ETF detail offers no reinvestment, excess-only, custom percentage and full reinvestment |
| Versioned Taiwan-individual tax explanation | `DELIVERED` | ETF detail exposes explicit 54C/76W/other assumptions, rule version, effective date and estimate warning |
| Official ACTUAL composition and 76W semantics | `PARTIAL` | Code, adapters and missing/zero tests are delivered; audited local data has no ACTUAL component rows and no source documents |
| Optional 1–3 ETF monthly-payment combination | `DELIVERED` | ETF comparison exposes base selection, explicit option, candidate inputs, gates, inclusions, exclusions and trade-offs |
| Current holdings and one-candidate before/after analysis | `DELIVERED` | M11 page and APIs reuse fixed-target and M10-5 contracts |
| Rationale, exclusions, alternatives, risk notes and Excel | `DELIVERED` | Append-only records and five-sheet typed Excel export are available in code |
| Formal zero versus missing data | `DELIVERED` | Models, Repository behavior, UI formatters and regression tests preserve the distinction |
| Currency and tax-basis separation | `DELIVERED` | Mixed currencies block aggregation; ACTUAL and estimated composition remain distinct |
| Source traceability and freshness | `DELIVERED` | Source documents, data profiles, quality views and import batches preserve provenance; actual data coverage remains a release-readiness issue |
| Public deployment, domain and HTTPS | `MISSING` | No committed hosting, container, workflow or production configuration exists; this is true M12 work |
| Broker, trading, real-time signals and opaque AI | `OUT_OF_SCOPE` | No account sync, broker integration, order route, signal engine or AI scoring is present |

## Core-flow reconciliation

| Required flow step | Status | Actual behavior |
| --- | --- | --- |
| Select one base ETF | `DELIVERED` | Search/ranking lead to a hidden ETF detail route |
| Enter current units and fixed target | `DELIVERED` | ETF detail accepts zero or more current units and a fixed monthly target while using a read-only stored official close |
| Review the base ETF alone | `DELIVERED` | Required capital, funding shortfall, coverage, month-by-month cash, total return and principal-risk evidence are shown before tax scenarios |
| Compare after-tax cash and total return | `DELIVERED` | Tax/reinvestment and current-holding results show both dimensions |
| Compare four reinvestment scenarios | `DELIVERED` | Available on ETF detail |
| Optionally request monthly coverage | `DELIVERED` | Available on ETF comparison |
| Review candidates, exclusions and trade-offs | `DELIVERED` | Comparison and M11 candidate flows expose stable reasons |
| Save holdings, decisions and Excel | `DELIVERED` in code | Requires schema initialization and authenticated owner access before deployment |

The flow remains intentionally split across ETF detail, ETF comparison and the
singleton owner profile. The base-target result is now visible on ETF detail;
the split matches the confirmed progressive flow and is no longer a pre-M12
product gap.

## Data and runtime audit

The local deployment candidate database was inspected without writing to it:

```text
file modified:               2026-08-01 (rechecked 2026-08-12 read-only)
ETF master rows:             256
performance rows:            205
latest performance date:     2026-07-29
dividend rows:               288
latest dividend event date:  2026-08-26
component rows:               1430 (`ESTIMATED`; `ACTUAL` rows: 0)
source-document rows:         0
review-queue rows:            576
```

It predates M11-5 and lacks `decision_profile`, `manual_holding`,
`decision_record` and `etf_daily_close`. The reviewed ACTUAL document and queue
schema exists, but contains no source documents or ACTUAL component rows.
`create_app()` still does not run `initialize_database()`, so the decision page
and official-close flow will fail against this file until an explicit migration
step is executed. The database and downloaded artifacts are intentionally
ignored by Git, so deployment also needs an explicit build/restore and
durable-storage plan.

These are deployment/data-readiness gaps, not evidence that the tested schema
or M11 services are absent.

## Closed product gaps before M12

The following M11 product work is now closed and must not be reopened or
mislabeled as M12 deployment automation:

### M11-5A — Complete the visible base-ETF cash-flow flow

Implementation status: completed and merged through PRs #18 and #19.

- Start the cash-flow flow with a dynamic current-holdings editor that accepts
  zero to any number (`0-N`) of Taiwan ETFs; zero rows is the valid initial state
- Let the user add each row with a `+` action and remove a row with a `-` action;
  each row has exactly two editable fields: `[ETF code] [held units]`
- Reject duplicate ETF codes and non-positive or non-whole held units with
  row-specific validation; an empty editor represents no current holdings
- Resolve each holding's reference price, price date and source from the latest
  stored official close and show them as read-only context. A missing price must
  make value-dependent output unavailable and must never be treated as zero;
  the website must not claim that the price is real-time
- Add a Streamlit client and result section for the existing target-analysis API
- Show required capital, funding shortfall and annual target coverage for the
  selected base ETF
- Present January–December gross and after-tax cash values, preserving missing
  months and mixed-currency semantics
- Link the section naturally from ETF detail before tax/reinvestment and
  complementary-ETF analysis

### M11-5B — Complete principal-risk warnings

Implementation status: completed and merged through PR #20 (`1e0a920`) with
fixed, source-dated rules and direct UI regression coverage.

- Implement or explicitly remove from the PRD the promised persistent-decline,
  weak-recovery and material-peer-underperformance checks
- Keep every warning deterministic, source-dated and covered by calculation,
  API-client and AppTest regression tests
- Add direct UI tests for the tax/reinvestment and monthly-combination sections

The M11-5 implementation now matches the user-approved amendment and the
post-M9 product direction. No remaining product feature gap blocks M12 entry.

## True M12 scope after M11-5

M11-5 is complete and merged. M12 remains limited to:

1. Scheduled ETF-master, performance, dividend and reviewed ACTUAL pipelines
2. Deployment-time schema initialization and migration verification
3. Durable SQLite storage, backup, restore drill and recovery documentation
4. Freshness, pipeline-failure, API-health and storage monitoring
5. One operational, owner-only authentication gate for every decision-profile
   read/write/export endpoint and conditional removal of that page for
   anonymous visitors. This is not a self-service user-account system
6. Production configuration, secrets, domain, HTTPS and public deployment
7. A documented launch data threshold, including non-zero reviewed ACTUAL/76W
   coverage or an explicitly approved limited-coverage launch

M12 must not add broker connectivity, trading, real-time signals, individual
stocks, AI scores, AI portfolios or opaque optimization.

## Blocking release-readiness items inside M12

- The deployment database must be initialized to the current schema without
  losing imported data.
- Anonymous users must be unable to read or mutate singleton holdings and
  decision records; frontend hiding alone is insufficient.
- The database must be created or restored in durable storage because it is not
  shipped by Git.
- Data pipelines and freshness monitoring must prevent a silently stale public
  site.
- The launch decision must explicitly address zero current ACTUAL/76W coverage.

## Non-blocking findings

- Streamlit callable pages, the `frontend/pages` package and global responsive
  CSS differ from the latest preferred structure but are covered by tests and
  do not block product completion.
- The original single-period ranking endpoint remains for compatibility while
  the website uses the multi-period read model.
- Missing real-time quotes and broker data are intentional product boundaries.

## Proposed direction and function list for confirmation

The first public version should contain exactly these product capabilities:

1. ETF search, detail, source/freshness profile, ranking and 2–4 ETF comparison
2. Dividend history, official-versus-estimated composition, ACTUAL 76W and data
   quality visibility
3. One-base-ETF fixed-target analysis with required capital, shortfall,
   month-by-month after-tax cash and total-return/principal warnings
4. Four explicit Taiwan-individual tax/reinvestment scenarios
5. Optional 1–3 complementary ETFs with eligibility gates and explanations
6. Owner-only manual holdings, current/candidate analysis, immutable records and
   Excel export
7. Scheduled data, monitoring, backup/recovery and public HTTPS deployment

AI scoring, AI portfolios and broader decision automation remain after the
first public website is operating.

## User confirmation and amendment recorded

On 2026-08-10, the user explicitly confirmed the reconciled direction and
seven-function first-release list, and approved M11-5 before M12 with these
clarifications:

1. Before cash-flow calculation, the user can enter `0-N` currently held ETFs.
   The editor starts empty; `+` adds a `[ETF code] [held units]` row below the
   existing rows, and `-` removes an individual row.
2. The two fields above are the only user-editable holding inputs. Reference
   price, as-of date and source are system-derived, read-only and explicitly
   unavailable when no trustworthy stored price exists.
3. M12 protects the entire singleton decision-profile boundary for one
   operational owner, while anonymous visitors retain stateless ETF analysis.
4. Self-service account aliases, passwords, login and per-user holding data are
   explicitly deferred until after M12, when they require a separate go/no-go
   decision. They are not implicitly authorized by this confirmation.

## Final M12 entry decision and sequence

The 2026-08-12 re-audit confirms that the product direction and seven-function
first-release list remain the same as the explicitly confirmed post-M9 result.
M11-5 is complete on merged main `1e0a920`; therefore no additional product
scope is authorized or required before M12.

M12 may begin only after this refreshed gate is merged, in this dependency
order:

1. `M12-1` deployment-time schema initialization, migration verification and
   lossless rehearsal against a copy of the legacy deployment candidate
2. `M12-2` durable SQLite path, backup, restore verification and recovery guide
3. `M12-3` scheduled pipelines plus freshness, failure, API-health and storage
   monitoring
4. `M12-4` one operational owner-only gate across every decision-profile API
   and conditional Streamlit navigation; no self-service account system
5. `M12-5` production configuration, secrets, domain and HTTPS deployment
6. `M12-6` launch-data threshold verification, including reviewed ACTUAL/76W
   coverage, followed by a documented launch decision

Do not combine self-service accounts, broker connectivity, trading, real-time
signals or AI decision features into M12.

After M12 is complete and before the final M12 merge, refresh the second-version
roadmap from the updated website requirements. The first two priorities are
custom target payment months and explainable AI assessment; neither is part of
M12 implementation.
