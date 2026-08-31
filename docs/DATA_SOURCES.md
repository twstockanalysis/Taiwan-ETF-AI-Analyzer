# Data Sources

## Policy

The project prioritizes official or explicitly permitted sources. Every source
has a stable identifier, provenance metadata and a defined use.

An available page is not automatically an acceptable ACTUAL source. The
information basis and retrieval policy must be verified first.

## ETF master

Source ID:

```text
twse_openapi
```

Endpoint:

```text
/opendata/t187ap47_L
```

Use:

- ETF code and name
- Active/passive classification
- Bond/non-bond classification
- Listing date

The Pipeline stores raw snapshots, normalized records, rejected records,
checksums and import-batch results. The official `出表日期` is parsed as the
dataset-level source date in processed/import evidence; it is not presented as
an independently observed update timestamp for every ETF.

## Historical market price

Source ID:

```text
twse_stock_day
```

Use:

- Daily closing prices
- 1M, 3M, 6M and 1Y market-price returns

Current performance records are `PRICE_RETURN` and exclude distributions.
The standard calculation excludes bond ETFs. A full detail-page coverage run
must opt in to bonds explicitly and keeps insufficient listing history separate
from retrieval failures.

## Estimated dividend information

Source ID:

```text
twse_etfortune_dividend
```

Use:

- Dividend events
- Estimated composition percentages

Estimated component codes:

```text
EST_DIVIDEND
EST_INTEREST
EST_EQUALIZATION
EST_REALIZED_CAPITAL_GAIN
EST_OTHER
```

This source must not create ACTUAL `76W`.

## Actual dividend composition

### Human-reviewed notice input

Source ID:

```text
manual_actual_dividend_notice
```

Retrieval policy:

```text
MANUAL_ONLY
```

The structured JSON must identify an official document and explicitly use
`information_basis=ACTUAL`.

### Verified Cathay announcement Adapter

Source ID:

```text
cathay_actual_dividend_announcement
```

Allowed official domains:

```text
cathaysite.com.tw
www.cathaysite.com.tw
```

Retrieval policy:

```text
EXPLICIT_NETWORK
```

The Adapter requires explicit actual-composition wording and rejects estimated
wording. Network access must be enabled explicitly or replaced by a reviewed
local HTML file.

## Official source-document retention

Official HTML is stored by content checksum. Metadata includes:

- Source and stable document IDs
- Official URL
- Download timestamp
- Content type
- SHA-256
- Snapshot and metadata paths
- Parse status and error
- Linked import batch

## Detail-page source display

M9-4 exposes traceable source references through:

```text
GET /api/v1/etfs/{code}/data-profile
```

Display names are resolved from the official-source registries while stable
`source_id` values remain visible. The endpoint does not infer a missing source
or substitute the current date for unavailable freshness metadata.

ETF-master freshness uses the latest successful `etf_master_pipeline` batch for
the whole dataset. Performance, dividend and ACTUAL counts and dates are scoped
to the requested ETF.

## Current limitations

- TWSE ETF e添富 composition is estimated, not ACTUAL.
- Only verified issuer formats receive an automated Adapter.
- No OCR or tax-code inference is performed.
- Actual coverage depends on publicly available or manually reviewed official
  documents.
- Vendor and broker APIs are deferred until after the core website roadmap.
- Fund size, total expense ratio, distribution period and stock dividend do not
  yet have a verified project source; they remain unavailable rather than zero.
