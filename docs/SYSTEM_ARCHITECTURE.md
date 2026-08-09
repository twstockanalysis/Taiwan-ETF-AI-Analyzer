# System Architecture

## M11 decision-profile and current-holding flow

```text
Streamlit decision-profile page
    |
    v
FastAPI /api/v1/decision-profile
    |
    +--> Decision-profile Repository
    |
    +--> decision_profile (singleton conditions)
    +--> manual_holding (ETF-code keyed holdings)
    |
    +--> Current-holding analysis Service
             |
             +--> M10 target-analysis data loaders
             +--> portfolio aggregation
             +--> M10 pure target calculator (once per portfolio)
    |
    v
SQLite
```

The flow remains single-user and has no broker or order boundary. Reference
prices are user-entered assumptions, not live quotes. The mutable singleton is
not an anonymous-public boundary; M12 must restrict decision-profile writes
before public deployment.

The analysis route is read-only. It does not call its own HTTP API, duplicate
the monthly target per ETF or persist calculated results.

## Current website request flow

```text
User browser URL
    |
    v
Central Streamlit navigation
    |
    +--> URL query-state normalization
    |
    v
Streamlit page
    |
    +--> shared formatters and classification labels
    +--> shared clickable rows and pagination
    +--> shared loading / empty / warning / error states
    |
    v
Frontend API client
    |
    v
FastAPI router
    |
    v
Repository
    |
    v
SQLite
```


## Shared frontend UI layer

```text
frontend/ui/formatters.py
    |
    +--> numbers, percentages and amounts
    +--> dates and datetimes
    +--> ETF classification labels
    +--> source references and truncated text

frontend/ui/components.py
    |
    +--> full-row ETF detail links
    +--> pagination controls

frontend/ui/states.py
    |
    +--> loading
    +--> empty
    +--> not found
    +--> warning
    +--> API error
```

Page modules retain only domain-specific labels and wrapper defaults. This keeps
page wording stable while preventing separate implementations from changing
zero-versus-missing semantics.

`frontend/ui/theme.py` injects one responsive typography layer before navigation
runs. Metric values and page-link labels can wrap instead of being truncated,
while sidebar and heading sizes remain readable when the sidebar is expanded.

## Homepage overview flow

```text
Streamlit home
    |
    v
GET /api/v1/system/overview
    |
    v
System overview Repository
    |
    +--> ETF classifications
    +--> PRICE_RETURN period coverage
    +--> dividend and ACTUAL coverage
    +--> data freshness
    +--> recent import batches
    |
    v
SQLite read-only queries
```

The overview endpoint returns stored dates only. It does not replace missing
data dates with the request time or convert unavailable coverage into zero.

## Multi-period performance ranking read model

```text
Streamlit performance ranking
    |
    +--> selected sort period (default 6M)
    +--> one selected-period return displayed per row
    +--> former-name suffix removed only in the display layer
    |
    v
GET /api/v1/performance/multi-period-ranking
    |
    v
Performance Repository
    |
    +--> rank ETFs by one period
    +--> fetch latest available records for all four periods
    +--> preserve missing periods as absent
    |
    v
SQLite read-only queries
```

The endpoint avoids N+1 frontend requests and keeps all four period records
available. The ranking page displays only the selected period for clarity;
ETF detail and comparison pages continue to show all available periods. Stored
ETF names and API names remain unchanged.

## ETF detail read model

```text
ETF detail page
    |
    +--> GET /api/v1/etfs/{code}
    +--> GET /api/v1/etfs/{code}/performance
    +--> GET /api/v1/etfs/{code}/dividends
    +--> GET /api/v1/etfs/{code}/dividends/76w
    +--> GET /api/v1/etfs/{code}/data-profile
```

The data-profile endpoint is a read model only. It aggregates source IDs,
display names, record counts and freshness dates from existing tables without
creating a new persistence table. ETF-master freshness is dataset-level;
performance, dividend and ACTUAL freshness is calculated for the requested
ETF.

Each secondary detail request has an isolated frontend error boundary. The ETF
identity can remain visible when one analysis dataset is temporarily
unavailable.

## ETF comparison read model

```text
Streamlit comparison page
    |
    +--> canonical codes URL state (2–4 ETFs)
    +--> source-aware return state
    |
    v
GET /api/v1/etfs/comparison
    |
    v
ETF comparison Repository
    |
    +--> ETF master
    +--> latest period-specific PRICE_RETURN
    +--> dividend summary
    +--> ACTUAL 76W summary
    +--> per-ETF data profile and completeness
    |
    v
SQLite read-only queries
```

The comparison read model preserves request order. Missing periods and missing ACTUAL 76W stay unavailable; formal zero remains numerical zero. The completeness percentage measures five data sections and is not an investment recommendation.

## Data update flow

```text
Official source or reviewed local document
    |
    v
Downloader / source-document snapshot
    |
    v
Normalizer or verified Adapter
    |
    v
Validation and event matching
    |
    v
Repository transaction
    |
    v
SQLite
    |
    +--> processed artifact
    +--> rejected artifact
    +--> quality report
    +--> import-batch audit
```

## Layers

| Layer | Responsibility |
| --- | --- |
| `frontend/` | Public Streamlit pages and API clients |
| `backend/app/api/` | HTTP routing, validation and dependency injection |
| `backend/app/services/` | Reusable calculations |
| `backend/app/repositories/` | SQLite queries and transactions |
| `backend/app/data_sources/` | Download, normalization, Pipelines and reports |
| `backend/app/models/` | Pydantic and enum contracts |
| `backend/app/database/` | Connection, schema and idempotent Migrations |
| `data/` | Raw, processed, rejected and report artifacts |
| `tests/` | Unit, integration, API and Streamlit tests |

## Trust boundaries

- Streamlit does not receive database credentials or broker credentials.
- FastAPI is the only website data-access boundary.
- Source documents are preserved with checksums before ACTUAL interpretation.
- Official component codes are preserved; uncertain codes are not inferred.
- Network retrieval for issuer documents is explicit rather than automatic.

## Current deployment boundary

M8 is a local development architecture using SQLite and manually started
Pipelines. Scheduling, monitoring, authentication, production hosting and
backup/recovery belong to M12.

Broker and third-party market-data APIs are optional post-core integrations.
