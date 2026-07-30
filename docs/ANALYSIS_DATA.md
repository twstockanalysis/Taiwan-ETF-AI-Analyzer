# ETF Analysis Data

## Purpose

Milestone 8 adds time-varying ETF analysis data.

ETF analysis data must not be stored directly in `etf_master`.

## Data Tables

### etf_performance

Stores ETF performance snapshots by:

- ETF code
- Data date
- Performance period
- Return percentage
- Source
- Import batch

Supported periods:

```text
1D
1W
1M
3M
6M
1Y
3Y
5Y
```

The six-month period is the primary period used by the first
recommendation-ranking model.

### etf_dividend

Stores one record for each ETF distribution event.

Possible dates include:

- Announcement date
- Ex-dividend date
- Record date
- Payment date

Every event includes:

- Distribution amount per unit
- Currency
- Source event identifier
- Source and import batch

### etf_dividend_component

Stores the source composition of one distribution event.

Examples of source component codes may include:

```text
54C
76W
```

The database preserves the source code and source description.

It does not infer the meaning of a code solely from its spelling.

## 76W Analysis

`76W` is stored as a normal distribution component:

```text
component_code = 76W
```

Possible values include:

```text
amount_per_unit
ratio_pct
```

A distribution may contain multiple component records.

The application can later calculate:

- 76W ratio for one distribution
- Average 76W ratio
- Latest 76W ratio
- Percentage of distributions with 100% 76W
- Six-month performance combined with 76W quality

## Data Integrity

Performance uniqueness:

```text
ETF + date + period + source
```

Dividend-event uniqueness:

```text
source + source event ID
```

Dividend-component uniqueness:

```text
dividend event + component code
```

Deleting an ETF deletes its performance and dividend history.

Deleting a dividend event deletes all associated components.

## Source Policy

Official or explicitly permitted data sources have priority.

HTML pages must not be scraped when their terms prohibit
unauthorized automated retrieval.

Source component codes and descriptions must be stored before
the project applies analytical classifications.

## Six-Month Price Return

The first M8 performance metric is the six-month market-price
return.

Source:

```text
twse_stock_day

## Six-Month Performance Pipeline

Run a small validation batch:

```powershell
python -m backend.app.data_sources.performance_pipeline --limit 10

## Performance Metric Types

Each ETF performance record includes a metric type.

Supported metric codes:

```text
PRICE_RETURN
TOTAL_RETURN
NAV_RETURN
```

The current TWSE closing-price pipeline produces:

```text
PRICE_RETURN
```

Future dividend-adjusted calculations will use:

```text
TOTAL_RETURN
```

Future NAV-based calculations will use:

```text
NAV_RETURN
```

Performance record uniqueness is:

```text
ETF code
+ as-of date
+ period
+ metric type
+ source
```

## Supported Price-Return Periods

The reusable market-price calculator currently supports:

```text
1M
3M
6M
1Y
```

The six-month period remains the primary recommendation period.

Shorter periods allow recently listed ETFs to show meaningful
performance without treating missing six-month history as zero.

Performance periods must be ranked separately. Returns from different
periods must not be combined into one ranking.

## Multi-Period Performance Pipeline

The price-return pipeline supports:

```text
1M
3M
6M
1Y

## Performance API

The backend exposes two performance endpoints.

### Ranking

```text
GET /api/v1/performance/ranking

## Frontend Performance Views

The Streamlit frontend includes a performance-ranking page.

Supported periods:

```text
1M
3M
6M
1Y

## Dividend Component Basis

Dividend components are classified by information basis:

```text
ESTIMATED
ACTUAL
```

TWSE ETF e添富 composition percentages are stored as
`ESTIMATED`. Official distribution-notice codes such as `76W`
are stored as `ACTUAL`.

Estimated realized capital gains are preserved as:

```text
EST_REALIZED_CAPITAL_GAIN
```

They are not converted to `76W`.

Dividend-component uniqueness is:

```text
dividend event
+ component basis
+ component code
+ component source
```

This allows estimated disclosure and actual tax-source records
to coexist without overwriting each other.

Older component rows are migrated to `ACTUAL`. Database
initialization runs this migration automatically.

## Dividend Repository

The dividend Repository supports:

```text
upsert_dividend_records
upsert_dividend_component_records
upsert_dividend_dataset
get_dividend_id
list_etf_dividends
list_dividend_components
```

`upsert_dividend_dataset` writes events and components in one
transaction. A component error rolls back the entire dataset,
so the database never retains a partially imported dividend
event.

## Dividend Pipeline

Run the TWSE ETF dividend pipeline:

```powershell
python -m backend.app.data_sources.dividend_pipeline
```

The pipeline performs:

```text
official HTML download
raw HTML snapshot
event and component normalization
ETF-master validation
processed and rejected artifacts
atomic SQLite upsert
import-batch completion
quality-report generation
```

Artifacts are written under:

```text
data/raw/dividends
data/processed/dividends
data/rejected/dividends
data/processed/reports/dividends
```

The import-batch `accepted_record_count` counts accepted dividend
events. `inserted_record_count` and `updated_record_count` combine
dividend-event and component rows.

Events whose ETF code is absent from `etf_master` are written to the
rejected artifact without failing other valid events.

TWSE composition rows are validated as `ESTIMATED`. The pipeline
rejects any attempt to create `ACTUAL` components or `76W` from the
TWSE estimated-composition source.

## Dividend API

The backend exposes ETF dividend history and component queries.

```text
GET /api/v1/etfs/{code}/dividends
GET /api/v1/etfs/{code}/dividends/76w
GET /api/v1/dividends/{dividend_id}
GET /api/v1/dividends/{dividend_id}/components
```

ETF dividend history supports `limit` and `offset` pagination.

Component queries support:

```text
component_basis
component_code
source_id
```

The 76W endpoint only includes records where:

```text
component_basis = ACTUAL
component_code = 76W
```

`EST_REALIZED_CAPITAL_GAIN` is never included in 76W
statistics.

When an ETF has no actual 76W disclosure,
`latest_76w_ratio_pct` and `average_76w_ratio_pct` are `null`.
Missing data is not represented as zero percent.

## Frontend Dividend Views

The Streamlit ETF detail page includes:

```text
dividend-event summary
actual 76W summary
dividend-event history
estimated component details
actual component details
```

The frontend loads dividend data independently from ETF
performance. A dividend API error does not prevent the ETF master
data or performance section from rendering.

Estimated and actual composition are displayed separately:

```text
ESTIMATED
ACTUAL
```

`EST_REALIZED_CAPITAL_GAIN` is labeled as estimated realized
capital gain. It is never relabeled as `76W`.

The actual 76W summary only displays data returned by the
`ACTUAL + 76W` endpoint. When no official actual record is
available, the interface displays an explicit missing-data message
instead of `0%`.

A disclosed `0%` actual ratio remains distinguishable from missing
data.
