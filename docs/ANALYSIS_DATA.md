# ETF Analysis Data

## Purpose

Milestone 8 adds time-varying ETF performance, dividend composition and data
quality records. Time-varying values are stored outside `etf_master`.

## Tables

### `etf_performance`

One row represents one ETF performance snapshot.

Uniqueness:

```text
ETF code
+ as-of date
+ period
+ metric
+ source
```

Schema-supported periods:

```text
1D  1W  1M  3M  6M  1Y  3Y  5Y
```

Current calculated periods:

```text
1M  3M  6M  1Y
```

Metric codes:

```text
PRICE_RETURN
TOTAL_RETURN
NAV_RETURN
```

The current TWSE closing-price Pipeline writes `PRICE_RETURN`. It does not
include cash distributions or dividend reinvestment.

### `etf_dividend`

One row represents one distribution event. A source event is unique by:

```text
source_id + source_event_id
```

Stored fields include announcement, ex-dividend, record and payment dates,
amount per unit, currency, source and import batch.

### `etf_dividend_component`

One row represents one disclosed component for a distribution event.

Uniqueness:

```text
dividend_id
+ component_basis
+ component_code
+ source_id
```

`component_basis` is one of:

```text
ESTIMATED
ACTUAL
```

A component must provide an amount per unit, a ratio, or both.

### `dividend_source_document`

Stores immutable versions of official actual-composition source documents.

A version is identified by:

```text
source_id
+ source_document_id
+ SHA-256 checksum
```

Changed content creates a new version. Identical content reuses the existing
version.

### `dividend_source_review_queue`

Tracks unresolved actual-composition and source-document coverage issues.

Issue types:

```text
MISSING_ACTUAL_COMPONENTS
MISSING_SOURCE_DOCUMENT
```

States:

```text
PENDING
IN_REVIEW
RESOLVED
SKIPPED
```

One dividend event can have one row per issue type.

## Performance calculation

The multi-period price Pipeline:

1. Selects non-bond ETF candidates.
2. Downloads each ETF price history once.
3. Reuses that history for all requested periods.
4. Writes only periods with sufficient price history.
5. Records insufficient history separately from execution failures.
6. Ranks each period and metric independently.

Default download windows:

| Period | Download months |
| --- | ---: |
| 1M | 3 |
| 3M | 5 |
| 6M | 8 |
| 1Y | 14 |

A missing return is never converted to `0%`.

Run:

```powershell
python -m backend.app.data_sources.performance_pipeline
```

## Dividend composition policy

TWSE ETF e添富 percentages are stored as estimated categories:

```text
EST_DIVIDEND
EST_INTEREST
EST_EQUALIZATION
EST_REALIZED_CAPITAL_GAIN
EST_OTHER
```

The estimated realized-capital-gain category is not an official tax-source
code and is never converted to `76W`.

Only an explicitly actual source can create:

```text
component_basis = ACTUAL
component_code = 76W
```

A formally disclosed `76W = 0%` is an available record. Absence of an ACTUAL
76W row is missing data, not zero.

## Actual source processing

### Human-reviewed JSON

```powershell
python -m backend.app.data_sources.actual_dividend_pipeline `
    --input .\data\imports\actual_dividend_notice.json
```

Matching requires ETF code, ex-dividend date and amount per unit. Record date
and payment date are additional exact checks when supplied.

### Verified Cathay announcement Adapter

```powershell
python -m backend.app.data_sources.cathay_actual_dividend_pipeline `
    --url "https://www.cathaysite.com.tw/announcement/5141" `
    --etf-code 00878 `
    --input-html .\data\imports\cathay_5141.html
```

The Adapter requires explicit actual-composition wording and rejects estimated
wording before the ACTUAL Pipeline is called.

## Coverage and review queue

Run:

```powershell
python -m backend.app.data_sources.actual_dividend_coverage_pipeline
```

Coverage measures:

- Dividend events with estimated components
- Dividend events with ACTUAL components
- Dividend events with ACTUAL `76W`
- Dividend events linked to parsed ACTUAL source documents
- Missing ACTUAL and source-document events

The review queue is synchronized idempotently. Supplying missing data can
resolve an item automatically. An unresolved `SKIPPED` item remains skipped.

## APIs

Performance:

```text
GET /api/v1/performance/ranking
GET /api/v1/etfs/{code}/performance
```

Dividends:

```text
GET /api/v1/etfs/{code}/dividends
GET /api/v1/etfs/{code}/dividends/76w
GET /api/v1/dividends/{dividend_id}
GET /api/v1/dividends/{dividend_id}/components
```

Data quality:

```text
GET /api/v1/data-quality/dividends/actual-coverage
GET /api/v1/data-quality/dividends/review-queue
GET /api/v1/data-quality/dividends/review-queue/{queue_id}
```

## Current limitations

- Production calculations currently provide market-price return only.
- Actual-composition coverage is limited by available verified documents.
- The source-review queue and Streamlit quality page are read-only.
- Pipelines are manually started; scheduling belongs to M12.
- Recommendation, comparison and portfolio decisions belong to M9–M11.
- Broker and third-party market-data integrations are deferred optional work.
