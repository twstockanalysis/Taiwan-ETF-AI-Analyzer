# ETF Data Sources

## Purpose

This document records the approved data sources for the
TW ETF AI Analyzer.

The project prefers official and publicly documented sources.

Third-party finance websites must not be used as the canonical
source for ETF master data.

## Source Priority

1. Official OpenAPI
2. Official downloadable files
3. Official product web pages
4. ETF issuer disclosures
5. Manual review

## Approved Sources

### Taiwan Stock Exchange OpenAPI

Source ID:

```text
twse_openapi
```

Purpose:

- TWSE ETF master data
- TWSE market information
- Official public datasets

Documentation:

```text
https://openapi.twse.com.tw/
```

Base URL:

```text
https://openapi.twse.com.tw/v1
```

### Taipei Exchange OpenAPI

Source ID:

```text
tpex_openapi
```

Purpose:

- TPEx ETF master data
- TPEx market information
- Official public datasets

Documentation:

```text
https://www.tpex.org.tw/openapi/
```

## Secondary Official Sources

### TWSE ETF Product List

Used only when required information is not available from the
official API.

### TWSE ETF Dividend List

Planned for the dividend history module.

It is not part of the M6 ETF master import.

## Data Storage Policy

Downloaded source files are stored under:

```text
data/raw/
```

Normalized files are stored under:

```text
data/processed/
```

Rejected records are stored under:

```text
data/rejected/
```

Downloaded and generated data files are excluded from Git.

Small fixed test fixtures may be committed under:

```text
tests/fixtures/
```

## Data Governance Rules

Every import must record:

- Source ID
- Download time
- Source update time, when available
- Number of received records
- Number of accepted records
- Number of rejected records
- Error details
- Raw file location
- File checksum

## Licensing

Before a source is used in a public production website, its
license, attribution requirements and redistribution conditions
must be reviewed and recorded.

Public accessibility must not automatically be treated as
permission for unrestricted redistribution.

## OpenAPI Specification Snapshots

The project downloads and stores the official OpenAPI
specifications before implementing an endpoint adapter.

Snapshot location:

```text
data/raw/openapi/{source_id}/
```

Each snapshot includes:

- Original OpenAPI JSON
- Download timestamp
- SHA-256 checksum
- Number of documented paths
- Source specification URL

The project does not assume that an endpoint is suitable for
ETF master data merely because its name contains "fund".

Every candidate endpoint must be reviewed for:

- Whether it represents an exchange-traded ETF
- Whether it includes delisted products
- Whether it includes dual-currency listings
- Whether it contains active ETFs
- Whether it distinguishes stock and bond ETFs
- Available identifiers and listing dates

## TWSE ETF Master Dataset

Endpoint ID:

```text
twse_fund_master
```

Official API URL:

```text
https://openapi.twse.com.tw/v1/opendata/t187ap47_L
```

Dataset purpose:

- ETF and fund security codes
- Fund names
- Fund types
- Establishment dates
- Listing dates
- Other official fund master attributes

The source dataset is a fund master dataset and is not assumed
to contain only ETFs.

Records must pass the ETF normalization and validation process
before being imported into `etf_master`.

## Raw ETF Master Snapshots

Raw snapshots are stored under:

```text
data/raw/etf_master/twse_fund_master/
```

Each download creates:

- Timestamped JSON data
- Timestamped metadata
- `latest.json`
- `latest.meta.json`
- SHA-256 checksum
- Record count
- Source field list

These generated files are excluded from Git.

## HTTPS Compatibility

Python 3.13 enables strict X.509 certificate checks by default.

The current TWSE and TPEx certificate chains require the project
to disable only the strict X.509 formatting flag.

The downloader still retains:

- Certificate authority verification
- Hostname verification
- HTTPS encryption

The project must not use:

```python
verify=False
```

## ETF Master Import

Normalized ETF records are loaded from:

```text
data/processed/etf_master/twse_fund_master/latest.json
```

Before importing, every record is validated again with
`ETFImportRecord`.

The import is executed inside a SQLite transaction.

Import behavior:

- New ETF codes are inserted
- Existing ETF codes are updated
- ETF names and classification fields are refreshed
- Existing fund size values are preserved
- Existing expense ratio values are preserved
- M5 development records are removed
- Duplicate ETF codes abort the import

Development records removed by the importer:

```text
DEV001
DEV002A
```

The `is_active` column means actively managed ETF.

It must not be used as a listing-status or record-enabled flag.

## End-to-End ETF Master Pipeline

Run the full ETF master pipeline:

```powershell
python -m backend.app.data_sources.etf_master_pipeline