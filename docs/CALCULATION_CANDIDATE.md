# Isolated calculation candidate

## Purpose

V2-12 provides a no-overwrite workflow for copying the local SQLite database,
upgrading its schema, refreshing official calculation inputs and producing a
machine-readable readiness decision. The repository development database is
never updated in place.

The gate distinguishes two levels:

- `READY`: every requested ETF has core calculation data and usable official
  constituent snapshots.
- `CORE_READY`: every requested ETF has four-period performance, an official
  close, dividend history and a complete ACTUAL or estimated component mix,
  but at least one ETF cannot provide safe constituent overlap.
- `NO_GO`: at least one requested ETF is missing core calculation data.

`CORE_READY` exits successfully because cash-flow, tax and performance testing
can proceed. Missing overlap remains unavailable and is never converted to
zero.

## Prepare a new candidate

The destination database, artifact directory and report must not already
exist. Network retrieval also requires an explicit flag:

```powershell
.venv\Scripts\python.exe -m deployment.calculation_candidate prepare `
  --source database\tw_etf.db `
  --database database\tw_etf-v2-12-20260820.db `
  --artifacts data\processed\v2-12-calculation-candidate `
  --etf-code 0050 `
  --etf-code 0056 `
  --etf-code 00918 `
  --history-years 3 `
  --allow-network `
  --output data\processed\v2-12-calculation-candidate\candidate-report.json
```

Omitting `--etf-code` requests the full non-bond calculation universe. That is
substantially slower and can remain below full constituent coverage while an
issuer's official source is unavailable or fails validation.

## Recheck without network writes

```powershell
.venv\Scripts\python.exe -m deployment.calculation_candidate check `
  --database database\tw_etf-v2-12-20260820.db `
  --etf-code 0050 `
  --etf-code 0056 `
  --etf-code 00918 `
  --history-years 3 `
  --output data\processed\v2-12-calculation-candidate\recheck.json
```

The report exposes stable per-ETF `core_reasons` and `overlap_reasons`, source
dates, component basis and disclosed constituent weight. It reports only the
database filename, not an absolute workstation path.

## 2026-08-20 bounded candidate result

The isolated candidate preserved all 12 source tables, upgraded to the current
schema and produced:

| Data family | 0050 | 0056 | 00918 |
|---|---|---|---|
| 1M / 3M / 6M / 1Y performance | Ready | Ready | Ready |
| Official daily close | Ready | Ready | Ready |
| Dividend history | 7 events | 13 events | 13 events |
| Calculation component basis | Estimated fallback | Estimated fallback | Estimated fallback |
| Constituent snapshot | 99.71% | 98.37% | Unavailable |
| Core calculation | Ready | Ready | Ready |
| Automatic overlap | Ready | Ready | Unavailable |

The combined decision is `CORE_READY`: all three ETFs can be used for
cash-flow, tax and performance calculations, while 00918 overlap remains
unknown. The UOB official 00918 fund page and PCF link were identity-matched,
but the current PCF response exposed foreign-stock rows totaling only 49.20%.
The existing 85% disclosed-weight safeguard correctly rejected that response.

An API smoke run against this candidate returned HTTP 200 for both monthly
combination and tax/reinvestment scenarios. The 0050-to-0056 automatic overlap
was 17.17%; 00918 remained an explicit overlap tradeoff.

## Local website use

Use the candidate's absolute path for both backend and frontend processes:

```powershell
$env:TW_ETF_DATABASE_PATH = (Resolve-Path `
  database\tw_etf-v2-12-20260820.db).Path
$env:TW_ETF_OWNER_TOKEN = '<local-only-random-token-at-least-32-characters>'
$env:TW_ETF_API_URL = 'http://127.0.0.1:8000'

.venv\Scripts\python.exe -m uvicorn backend.app.main:app `
  --host 127.0.0.1 --port 8000
```

Start Streamlit in a second PowerShell window with the same three environment
variables:

```powershell
.venv\Scripts\python.exe -m streamlit run frontend/app.py `
  --server.address 127.0.0.1 --server.port 8501
```

Open `http://127.0.0.1:8501`. Keep the token local and never commit it to Git.
