# Streamlit Frontend

## Architecture

```text
Browser
-> Streamlit page
-> frontend/api_client.py
-> FastAPI
-> Repository
-> SQLite
```

The frontend never reads SQLite directly.

## Local startup

FastAPI terminal:

```powershell
python -m uvicorn backend.app.main:app --reload
```

Streamlit terminal:

```powershell
python -m streamlit run frontend/app.py
```

Default URLs:

```text
FastAPI   http://127.0.0.1:8000
Streamlit http://localhost:8501
```

Override the backend URL with:

```text
TW_ETF_API_URL
```

## Navigation and URL state

Page metadata is centralized in:

```text
frontend/navigation.py
```

Public pages:

```text
/
etf-search
performance-ranking
etf-comparison
dividend-data-quality
```

Hidden page:

```text
etf-detail
```

ETF search URLs preserve:

```text
keyword
active
bond
page
page_size
```

Performance ranking URLs preserve:

```text
period
active
bond
page
page_size
```

ETF detail URLs include `code`, the source page in `from`, and the source
page's canonical query state. Returning from detail therefore restores the
search or ranking context.

Invalid query values are normalized to safe defaults. Missing and zero values
retain their existing domain semantics.

Shared UI states are defined in:

```text
frontend/ui/states.py
```

They provide consistent loading, empty, not-found and API-error presentation.

## Pages

### Home

The homepage reads only:

```text
GET /api/v1/system/overview
```

It shows:

- Primary links to ETF search, performance ranking and dividend data quality
- FastAPI and SQLite status
- ETF totals and active/passive, bond/non-bond classifications
- ETFs with PRICE_RETURN data and ETFs with dividend history
- ACTUAL and official 76W event coverage
- Separate 1M, 3M, 6M and 1Y performance coverage
- ETF-master, performance, dividend and ACTUAL-document freshness
- Five most recent import batches, including failed-batch error summaries

Missing dates display `尚未取得`. A zero-event coverage ratio displays
`尚無資料`, while a formally calculated zero remains `0.00%`.

### ETF Search

Supports:

- Code/name keyword search
- Active/passive filter
- Bond/non-bond filter
- Page size and pagination
- Fully clickable ETF rows

### Performance Ranking

Supports:

- 1M, 3M, 6M and 1Y periods
- Active/passive and bond filters
- Pagination and fully clickable rows

M9-1 uses one fixed information order:

```text
rank and ETF code
-> performance period and return
-> ETF name
-> as-of date
-> active/passive
-> bond/non-bond
```

The period and return are visually emphasized near the left edge. Classification
labels remain on the right because users select those categories before
reviewing the ranked results.

### ETF Comparison

The public comparison page uses:

```text
/etf-comparison?codes=0050,0056
```

It accepts 2–4 unique ETF codes and compares:

- Management and asset classifications
- Listing date, fund size and expense ratio
- Independent 1M, 3M, 6M and 1Y `PRICE_RETURN` values
- Dividend-event count and latest distribution summary
- ACTUAL 76W availability, latest ratio and average ratio
- Five-section data completeness

The `codes` query parameter is canonical, ordered and deduplicated. Return-state parameters are namespaced with `return_`, allowing the page to return to ETF search, performance ranking or ETF detail without losing the source page state.

Missing periods display `歷史資料不足`. Missing ACTUAL 76W displays `尚未取得`; an official `76W = 0%` displays `0.00%`. Data completeness describes available data sections only and is not an investment score.

### ETF Detail

The detail page is hidden from sidebar navigation and opened through:

```text
/etf-detail?code=0050
```

M9-4 uses one fixed decision-oriented section order:

```text
ETF identity and classifications
-> core data overview
-> market-price performance
-> dividend summary
-> actual 76W
-> dividend events and components
-> data sources and freshness
-> ETF comparison entry
```

The page keeps each secondary API call isolated. A performance, dividend,
ACTUAL 76W or data-profile failure does not remove the ETF identity and other
successfully loaded sections.

Data sources and freshness come from:

```text
GET /api/v1/etfs/{code}/data-profile
```

The profile shows source IDs and display names, latest data dates, latest
successful import times and record counts. ETF-master import time is explicitly
labeled as dataset-level freshness. Missing dates display `尚未取得`; they are
not replaced with the current date.

The comparison entry is enabled and carries the current ETF plus the detail page return state into the public comparison page.

### Dividend Data Quality

Shows:

- Global ACTUAL, 76W and source-document coverage
- Single-ETF coverage
- Review-queue filters and pagination
- Read-only queue-item details

## Data semantics

Missing values are displayed as text such as:

```text
尚無資料
歷史資料不足
尚未取得正式 76W 收益分配資料
```

Missing values are not converted to numerical zero.

A formal `ACTUAL + 76W` record with a disclosed ratio of zero is displayed as
`0.00%` and remains covered data.

Estimated realized capital gains retain the label:

```text
EST_REALIZED_CAPITAL_GAIN
```

They are not displayed or counted as official `76W`.

## Caching and refresh

Pages use short `st.cache_data` TTLs. Refresh buttons clear relevant frontend
cache entries. They do not run backend Pipelines; data Pipelines must be run
separately.

## Tests

Frontend and AppTest coverage:

```powershell
python -m unittest `
    tests.test_frontend_api_client `
    tests.test_frontend_etf_api_client `
    tests.test_frontend_performance_api_client `
    tests.test_frontend_dividend_api_client `
    tests.test_frontend_dividend_quality_api_client `
    tests.test_frontend_dividend_ui `
    tests.test_frontend_dividend_quality_ui `
    tests.test_streamlit_app `
    -v
```
