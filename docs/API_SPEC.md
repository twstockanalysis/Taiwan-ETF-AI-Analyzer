# API Specification

## Overview

Framework:

```text
FastAPI
```

Development base URL:

```text
http://127.0.0.1:8000
```

Interactive OpenAPI documentation:

```text
http://127.0.0.1:8000/docs
```

## System

```http
GET /
GET /health
```

`GET /health` returns:

```json
{
  "status": "healthy"
}
```

### System overview

```http
GET /api/v1/system/overview
```

The homepage uses this single read-only endpoint for:

```text
ETF totals and classifications
latest successful ETF-master import time
PRICE_RETURN coverage for 1M, 3M, 6M and 1Y
latest performance as-of date
dividend-event and ETF counts
ACTUAL, 76W and source-document coverage
latest dividend and ACTUAL source-document dates
five most recent import batches
```

Coverage percentages are `null` when the denominator is zero. Missing dates
remain `null`; the API does not substitute the current date.

## Public cash-flow planning baseline

```http
POST /api/v1/allocation-plans/baseline
```

V3-1 accepts a fixed TWD cash target for each selected month, one or more
months, a one-to-ten-year dividend-history window, a generic cash-deduction
percentage and zero to 500 unique existing ETF holdings. Each supplied holding
uses a positive whole-share quantity. The endpoint is public and stateless: it
does not require `X-Owner-Token`, does not update the single-user profile and
does not connect to a broker.

The response always returns January through December in order. It uses the
latest stored official close for current value and actual dividend payment
dates for the historical monthly cash baseline. A known no-event month is
zero; a holding with missing price, unusable payment data or incompatible
currencies keeps the dependent value `null` and returns explicit issues.

This endpoint does not yet select ETFs or recommend additional shares. Its
`AUTO_ALLOCATION_PENDING` next step reserves that boundary for V3-2 and V3-3.
Raw ETF-quality scores and assessment-confidence fields are not part of the
public response.

### Full-market eligibility index

```http
POST /api/v1/allocation-plans/eligibility-index
```

V3-2 applies fixed server-side product, reference-price, completeness,
freshness, payment stability, after-tax cash, total-return, downside,
composition and portfolio-overlap gates to every ETF in the master. Public
requests cannot override these thresholds.

The response includes the complete code-ordered universe, eligible/excluded
counts, source dates, stable payment months, ACTUAL versus estimated component
basis, overlap state, stable reasons and a reproducible `sha256:` snapshot ID.
Allocation-dependent concentration is returned as a mandatory V3-3 constraint.

The server retains a deterministic quality score and twelve Decimal-safe
cash-per-share values only in its internal index for the next solver stage.
V4-1 adds a nested `historical_quality_grade` to each public candidate. It
contains only a versioned `A+` through `F` grade or `UNRATED`, short evidence
and missing-data reasons. The complete market snapshot must pass minimum
sample, coverage and score-saturation gates before any letter is published.
Raw quality scores, components, internal ranks and confidence labels remain
absent. The endpoint remains stateless and requires no owner token.

### Public historical-quality grade lookup

```http
GET /api/v1/etfs/historical-quality-grades?codes=0050,0056
```

V4-5 lets public search, ranking, detail and comparison pages request one to
100 ETF grades in input order. The server builds the same full-market V4-1
catalog used by allocation eligibility and applies the same market-wide
publication gate. Each item contains only `etf_code` and the public-safe
`historical_quality_grade`; raw scores, score components, ranks and confidence
fields are never serialized. Unknown codes return `404`, invalid or oversized
requests return `422`, and the endpoint is read-only and stateless.

### Allocation results and long-term scenarios

```http
POST /api/v1/allocation-plans/allocation-results
POST /api/v1/allocation-plans/long-term-scenarios
POST /api/v1/allocation-plans/portfolio-projections
```

The V3-4 allocation endpoint returns one to three materially different
`RECOMMENDED`, `BALANCED` and `FOCUSED` whole-share configurations. Every plan
includes the required additional capital, selected-month cash and shortfall,
resulting holdings, assumptions and risks. It returns fewer plans rather than
fabricating duplicate alternatives.

Each added ETF carries the same public-safe `historical_quality_grade`. This
grade does not change the integer solution and remains distinct from the
owner-goal allocation result.

The V3-5 endpoint includes the same allocation response and one aligned
long-term-evidence record per returned strategy. Historical portfolio evidence
uses fixed resulting shares, compatible common official close dates, actual
TWD payment-date distributions and the request's generic cash-deduction rate.
It returns the maximum compatible history plus 3Y, 5Y and 10Y windows; a window
without enough data remains `UNAVAILABLE`.

Historical evidence uses raw official closes and a no-reinvestment cash policy.
It is an estimate, not an adjusted official total-return index, because ETF
split and reverse-split adjustments are not yet available. Ten-year scenarios
are produced only with at least two complete one-year observations. Their
conservative, base and optimistic annual assumptions are the 25th, 50th and
75th percentiles of those observations and are shown as a compounded index
starting at 100, not as a cash forecast.

The V3-6 endpoint nests the V3-5 response and adds one aligned portfolio-tax
projection per returned strategy. It accepts a 1-to-20-year horizon, one of two
dividend-tax methods, explicit tax-rate assumptions, remaining dividend-credit
cap, supplementary-premium exemption and custom reinvestment percentage. Each
available plan contains three market bands and four distribution-use results,
with annual points, ending holding value, usable cash, reinvested cash,
estimated individual income tax and estimated supplementary NHI.

Forward market returns are gross before portfolio tax. Official versus
estimated component provenance is preserved; missing positive-cash component
data makes the plan unavailable. Official `76W` and estimated realized capital
gain are excluded from the modeled personal dividend tax and premium base, and
estimated capital gain is never relabeled as official `76W`. Reinvested cash is
an internal transfer and is not counted twice in after-tax return.

All three endpoints are public and stateless. They do not expose internal ETF-quality
scores or assessment-confidence fields.

## Single-user decision profile

```http
GET /api/v1/decision-profile
GET /api/v1/decision-profile/current-holding-analysis
POST /api/v1/decision-profile/candidate-analysis/{etf_code}
POST /api/v1/decision-profile/candidate-analysis/{etf_code}/decision-records
GET /api/v1/decision-profile/decision-records
GET /api/v1/decision-profile/decision-records/{record_id}
GET /api/v1/decision-profile/decision-records/{record_id}/export.xlsx
PUT /api/v1/decision-profile/conditions
PUT /api/v1/decision-profile/holdings
PUT /api/v1/decision-profile/holdings/{etf_code}
DELETE /api/v1/decision-profile/holdings/{etf_code}
```

M11-1 exposes one `SINGLE_USER` profile and always returns
`broker_connected=false`. It does not create accounts, authenticate brokerage
connections or send orders.

Conditions persist the monthly after-tax cash target, analysis years, history
years and a nullable generic cash-deduction percentage. The batch holdings
`PUT` accepts `0-N` unique `{etf_code, held_units}` rows and atomically replaces
the saved set. It derives price, trade date and source from the latest stored
official close. Missing close data remains `null` and blocks dependent output.
The item `PUT` and `DELETE` remain compatibility operations. Missing deductions
remain `null`, while a formal `0%` deduction remains numerical zero.

Every operation in this section requires `X-Owner-Token`. Private responses,
including errors and Excel exports, return `Cache-Control: no-store, private`,
`Pragma: no-cache` and `Vary: X-Owner-Token`. Missing or wrong credentials
return `401`; a missing or invalid server token configuration returns `503`.
The batch holdings request accepts at most 500 rows.

The M11-2 current-holding endpoint is read-only. It returns per-ETF historical
facts, total saved holding value and one portfolio-level M10 target-analysis
result. The monthly target is applied once to the portfolio. Missing fixed
conditions or holdings return `UNAVAILABLE`; missing market data or assumptions
return `PARTIAL` with `null` results and explicit unavailable fields.

The base `POST /api/v1/etfs/{code}/target-analysis` response includes
source-dated principal-risk warnings. A warning may include `as_of_date`,
`source_id` and a typed `evidence` object containing the exact threshold facts
used by the deterministic rule. Missing facts do not produce a safe warning
result. Multi-year price returns are annualized before scenario projection.

The M11-3 candidate endpoint accepts proposed positive whole units, a positive
TWD reference price, optional holding overlap and the existing M10-5 rules. It
returns current and proposed portfolio snapshots, calculable deltas and the
M10-5 selected/rejected candidate result with stable reasons. The scenario is
read-only and never updates the saved holding.

The same response includes `explainable_assessment` when eligibility can be
evaluated. Its deterministic `DETERMINISTIC_MULTI_SCORE_V2` methodology returns
an ETF quality score, a current-portfolio fit score and ordered evidence
factors. Total return is the largest quality component; dividend cash, official
ACTUAL 76W and overlap cannot independently determine a high score. Missing
official 76W remains unscored. User-entered overlap remains a risk assumption
and is excluded from scoring until automatic constituent data is available.
The UI exposes only the final portfolio-fit score. ETF quality and its
components remain backend data, and no separate confidence label is shown.
The response remains free of buy/sell signals, performance forecasts and gate
overrides.

M11-4 reruns the candidate analysis on the server before saving an immutable
record. Records preserve the original request, full analysis snapshot,
rationale, exclusions, deterministic alternatives and risk notes. The record
API has no update or delete operation. Excel export uses the saved snapshot and
returns a five-sheet `.xlsx`; later profile or market-data changes do not alter
existing records. Unknown record IDs return `404`.

## ETF master data

### List ETFs

```http
GET /api/v1/etfs
```

Query parameters:

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `keyword` | string or null | null | ETF code or name |
| `is_active` | boolean or null | null | Active/passive filter |
| `is_bond` | boolean or null | null | Bond/non-bond filter |
| `limit` | integer | 20 | 1–100 |
| `offset` | integer | 0 | Non-negative |

Response fields:

```text
items
total
limit
offset
```

### ETF detail

```http
GET /api/v1/etfs/{code}
```

ETF codes are normalized to uppercase. Missing ETFs return `404`.

### ETF comparison

```http
GET /api/v1/etfs/comparison?codes=0050,0056
```

The endpoint accepts 2–4 unique ETF codes and preserves request order. It returns:

```text
ETF master identity and classifications
latest available 1M, 3M, 6M and 1Y PRICE_RETURN records
dividend-event count and latest event summary
ACTUAL 76W record count and latest/average ratio
per-ETF source and freshness profile
five-section data-completeness explanation
```

One code or more than four codes returns `422`. Missing ETF codes return `404`.
Missing performance or ACTUAL 76W values remain `null` or absent; formal `76W = 0%` remains numerical zero.

### ETF data profile

```http
GET /api/v1/etfs/{code}/data-profile
```

Returns the detail page's traceable data profile:

```text
ETF-master source and latest successful dataset import
PRICE_RETURN source, available periods and latest as-of date
dividend-event sources, count and latest event date
ACTUAL composition sources, 76W count and latest official-document date
```

Missing dates remain `null`. An ETF without performance, dividend or ACTUAL
records returns zero counts and empty source lists rather than fabricated dates
or percentages.

## Performance

### Ranking

```http
GET /api/v1/performance/ranking
```

Query parameters:

| Parameter | Type | Default |
| --- | --- | --- |
| `period` | `1M`, `3M`, `6M`, `1Y` | `6M` |
| `metric` | `PRICE_RETURN`, `TOTAL_RETURN`, `NAV_RETURN` | `PRICE_RETURN` |
| `is_active` | boolean or null | null |
| `is_bond` | boolean or null | false |
| `limit` | integer | 20 |
| `offset` | integer | 0 |

Ranking is calculated within one period and one metric. Global rank numbers
include the pagination offset.

### Multi-period ranking

```http
GET /api/v1/performance/multi-period-ranking
```

Query parameters match the existing ranking filters, with `sort_period`
replacing `period`. The default `sort_period` is `6M`.

The selected period controls ranking order only. Every item also returns the
latest available `1M`, `3M`, `6M` and `1Y` records in `performance_items`.
A missing period is absent and is never represented as `0%`.

The original single-period ranking endpoint remains available for compatible
clients.

### Single ETF performance

```http
GET /api/v1/etfs/{code}/performance
```

Returns the latest available records per supported period for one metric.
Missing periods are absent rather than represented as zero.

## Dividends

### ETF dividend history

```http
GET /api/v1/etfs/{code}/dividends
```

Supports `limit` and `offset`. Missing ETFs return `404`; an ETF without
dividend events returns an empty list.

Each event also returns nullable summary fields:

```text
distribution_period
distribution_period_source_id
yield_pct
yield_basis
yield_source_id
reference_trade_date
reference_close_price
```

`distribution_period` accepts only an official `YYYYQ1`–`YYYYQ4` value.

### Tax and reinvestment scenarios

```text
POST /api/v1/etfs/{code}/tax-reinvestment-scenarios
```

The request supplies holdings, cash target, projection horizon, payment-count
assumption, custom reinvestment percentage and a versioned Taiwan-individual
tax rule. The server supplies historical distribution and price-return inputs
and selects the newest complete ACTUAL component event, or a complete estimated
fallback when no qualifying ACTUAL event is available.

The response keeps `historical_facts` separate from `calculation`, returns all
four reinvestment policies, echoes `projection_years`, and includes usable cash,
reinvested cash, ending units, ending value, modeled income tax, supplementary
premium and after-tax total return. The explicit horizon lets clients warn when
a 1Y historical return is mechanically applied to a longer scenario. `PARTIAL`
means one or more outputs remain unavailable; missing component data or tax
assumptions are not converted to zero. Estimated components remain labeled as
fallbacks and are not relabeled as official tax codes.
`yield_basis` is `OFFICIAL` or `CALCULATED`. A calculated value includes the
previous trading date and close; an official value never carries a calculated
price reference.

### Monthly-payment combination

```text
POST /api/v1/etfs/{code}/monthly-payment-combination
```

The path ETF is the visible base anchor. The request supplies one to three
candidate codes, each candidate's explicit unit-price and allocation
assumptions, an optional holding-overlap estimate, lookback years, cash
deduction rate and eligibility rules. A candidate cannot repeat the base ETF.

The server derives payment-month recurrence and cash distributions from actual
`payment_date` records and uses the latest `1M`, `3M`, `6M` and `1Y`
`PRICE_RETURN` records. It applies data completeness, freshness, distribution
stability, after-tax cash, total-return, downside, overlap and concentration
gates before considering payment-month coverage. Active/passive and bond/non-
bond fields are returned as attributes, not quality scores.

Every selected or rejected candidate contains machine-readable and plain-
language reasons. Missing holding overlap remains `null` and produces a
trade-off (or exclusion when explicitly required); formal zero remains zero.
The response keeps historical facts separate from cash-deduction assumptions
and labels the combination as a scenario rather than a guarantee.

### Actual 76W history

```http
GET /api/v1/etfs/{code}/dividends/76w
```

Only `component_basis=ACTUAL` and `component_code=76W` are counted. Missing
actual data produces `null` ratios, not zero.

### Dividend event detail

```http
GET /api/v1/dividends/{dividend_id}
```

Returns one dividend event and all component records.

### Filter dividend components

```http
GET /api/v1/dividends/{dividend_id}/components
```

Optional query filters:

```text
component_basis
component_code
source_id
```

## Dividend data quality

### Coverage

```http
GET /api/v1/data-quality/dividends/actual-coverage
```

Optional `etf_code` limits the summary to one existing ETF.

### Review queue

```http
GET /api/v1/data-quality/dividends/review-queue
```

Optional query filters:

```text
status
etf_code
issue_type
limit
offset
```

### Review queue item

```http
GET /api/v1/data-quality/dividends/review-queue/{queue_id}
```

The M8 data-quality API is read-only.

## Status behavior

```text
200  successful response
400  malformed request framing such as invalid Content-Length
401  missing or incorrect owner credential on a private endpoint
413  request body exceeds 64 KiB
414  path plus query exceeds 8 KiB
404  ETF, dividend event or queue item not found
422  invalid path, query parameter or JSON body
431  request headers exceed 32 KiB
500  sanitized unexpected server error without exception details
503  owner-only API is not safely configured
```

Validation errors return only stable error types and locations; submitted input
values are not reflected. Frontend API transport does not follow redirects.

All API database access is injected through `get_database_path`, allowing tests
to use isolated temporary SQLite databases.
