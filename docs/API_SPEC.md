# API Specification

## Overview

The TW ETF AI Analyzer backend is built with FastAPI.

Development base URL:

```text
http://127.0.0.1:8000


## ETF Endpoints

### List ETFs

```http
GET /api/v1/etfs
```

Purpose:

Returns all ETF master records ordered by ETF code.

Example response:

```json
[
  {
    "code": "DEV001",
    "name": "開發測試被動式ETF",
    "is_active": false,
    "is_bond": false,
    "listing_date": null,
    "fund_size": null,
    "expense_ratio": null
  }
]
```

### Get ETF by Code

```http
GET /api/v1/etfs/{code}
```

Purpose:

Returns one ETF master record by security code.

ETF codes are normalized to uppercase before querying.

Successful response status:

```text
200 OK
```

Missing ETF response status:

```text
404 Not Found
```

Example missing response:

```json
{
  "detail": "找不到 ETF：UNKNOWN"
}
```

## Development Data

M5 uses non-production demonstration records:

```text
DEV001
DEV002A
```

These records are only used to verify the API workflow.

They will be replaced by the official ETF data import process in M6.


## ETF Endpoints

### List ETFs

```http
GET /api/v1/etfs
```

Returns a filtered and paginated ETF list.

#### Query Parameters

| Parameter | Type | Default | Description |
|---|---|---:|---|
| keyword | string | null | Search ETF code or name |
| is_active | boolean | null | Filter actively managed ETFs |
| is_bond | boolean | null | Filter bond ETFs |
| limit | integer | 20 | Number of records, from 1 to 100 |
| offset | integer | 0 | Number of records to skip |

Example:

```http
GET /api/v1/etfs?is_active=true&is_bond=false&limit=20&offset=0
```

Example response:

```json
{
  "items": [
    {
      "code": "DEV002A",
      "name": "開發測試主動式ETF",
      "is_active": true,
      "is_bond": false,
      "listing_date": null,
      "fund_size": null,
      "expense_ratio": null
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

Validation errors return:

```text
422 Unprocessable Entity
```

### Get ETF by Code

```http
GET /api/v1/etfs/{code}
```

ETF codes are normalized to uppercase before querying.

Successful response:

```text
200 OK
```

Missing ETF response:

```text
404 Not Found
```

Example:

```json
{
  "detail": "找不到 ETF：UNKNOWN"
}
```