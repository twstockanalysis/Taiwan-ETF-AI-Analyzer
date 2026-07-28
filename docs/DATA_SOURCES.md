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