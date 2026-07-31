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
