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

## Pages

### Home

Shows project scope, FastAPI connectivity and database type.

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

### ETF Detail

The detail page is hidden from sidebar navigation and opened through:

```text
/etf-detail?code=0050
```

It shows:

- ETF identity and classifications
- Listing date, fund size and expense ratio
- Multi-period market-price performance
- Dividend summary
- Actual 76W summary
- Dividend events and estimated/actual components

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
