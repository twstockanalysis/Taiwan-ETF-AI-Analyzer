# System Architecture

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
    +--> shared loading / empty / error states
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
