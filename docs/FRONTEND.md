# Streamlit Frontend

## Purpose

The Streamlit frontend provides the first public-facing user
interface for the TW ETF AI Analyzer.

The frontend does not connect directly to SQLite.

All ETF data is requested through the FastAPI backend.

## Architecture

```text
Web Browser
    |
    v
Streamlit Frontend
    |
    v
FastAPI Backend
    |
    v
SQLite Database
```

## Local URLs

FastAPI:

```text
http://127.0.0.1:8000
```

Streamlit:

```text
http://localhost:8501
```

## Start FastAPI

Open the first terminal:

```powershell
python -m uvicorn backend.app.main:app --reload
```

## Start Streamlit

Open the second terminal:

```powershell
python -m streamlit run frontend/app.py
```

## Frontend Pages

### Home

Displays:

- Project introduction
- FastAPI connection status
- Database type
- Backend connection error messages

### ETF Search

Supports:

- ETF code and name search
- Active and passive ETF filtering
- Bond and non-bond filtering
- Page size selection
- Previous and next page navigation
- Single-row ETF selection

### ETF Detail

Displays:

- ETF code
- ETF name
- Active or passive management
- Bond or non-bond classification
- Gregorian listing date
- Fund size
- Expense ratio

The detail page is hidden from the sidebar and is opened from
the ETF search page.

Example route:

```text
/etf-detail?code=0050
```

## API URL Configuration

The default FastAPI URL is:

```text
http://127.0.0.1:8000
```

Production environments can override it with:

```text
TW_ETF_API_URL
```

Example:

```powershell
$env:TW_ETF_API_URL = "https://api.example.com"
```

## Date Standard

All ETF listing dates shown by the frontend must use the
Gregorian ISO 8601 format:

```text
YYYY-MM-DD
```

Example:

```text
2003-06-30
```

Republic of China calendar values must be converted during the
data normalization stage before they are stored in SQLite.

The frontend must not perform calendar conversion.

## Missing Data

A value of `null` for fund size or expense ratio is displayed as:

```text
尚無資料
```

This indicates that the current official source has not yet
provided or imported that metric.

## Automated Tests

Run frontend API client tests:

```powershell
python -m unittest tests.test_frontend_api_client -v
python -m unittest tests.test_frontend_etf_api_client -v
python -m unittest tests.test_frontend_etf_detail_client -v
```

Run Streamlit AppTest:

```powershell
python -m unittest tests.test_streamlit_app -v
```

Run all project tests:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```