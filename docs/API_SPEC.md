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

## Single-user decision profile

```http
GET /api/v1/decision-profile
PUT /api/v1/decision-profile/conditions
PUT /api/v1/decision-profile/holdings/{etf_code}
DELETE /api/v1/decision-profile/holdings/{etf_code}
```

M11-1 exposes one `SINGLE_USER` profile and always returns
`broker_connected=false`. It does not create accounts, authenticate brokerage
connections or send orders.

Conditions persist the monthly after-tax cash target, analysis years, history
years and a nullable generic cash-deduction percentage. Manual holdings persist
positive whole units, a user-supplied positive TWD reference price and an
optional price date. Repeating a holding `PUT` updates that ETF; `DELETE`
removes only the website's manual record. Missing deductions remain `null`,
while a formal `0%` deduction remains numerical zero.

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
and selects the newest complete ACTUAL component event.

The response keeps `historical_facts` separate from `calculation`, returns all
four reinvestment policies, and includes usable cash, reinvested cash, ending
units, ending value, modeled income tax, supplementary premium and after-tax
total return. `PARTIAL` means one or more outputs remain unavailable; missing
ACTUAL components or tax assumptions are not converted to zero.
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
404  ETF, dividend event or queue item not found
422  invalid path or query parameter
```

All API database access is injected through `get_database_path`, allowing tests
to use isolated temporary SQLite databases.
