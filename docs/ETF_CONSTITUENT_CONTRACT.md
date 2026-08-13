# ETF Constituent Snapshot Contract

## Purpose

ETF constituent data is required before portfolio overlap can become an
automatic assessment input. User-entered overlap remains a scenario assumption
and must not be represented as issuer-sourced constituent overlap.

## Immutable snapshots

Each snapshot stores:

- ETF code
- Constituent-data effective date
- Source identifier and optional source URL
- Fetch timestamp
- Disclosed total weight and constituent count
- Constituent identifier, name, disclosed weight and optional rank

The `(etf_code, as_of_date, source_id)` tuple is unique. An existing snapshot is
never silently overwritten. A changed issuer file for the same effective date
must be investigated or preserved under a separately versioned source ID.

Constituent identifiers are normalized to uppercase. Duplicate identifiers and
total disclosed weights above `100.5%` are rejected. The small tolerance only
allows issuer rounding; it is not permission to normalize invalid source data.

## Weighted overlap

Pairwise overlap uses:

```text
overlap = sum(min(left disclosed weight, right disclosed weight))
          for every shared constituent identifier
```

The method identifier is `SUM_MIN_DISCLOSED_WEIGHTS_V1`. Both snapshot dates,
both disclosed total weights, the shared constituent count and each shared
weight contribution remain in the result.

Weights are not normalized to 100% when an issuer discloses only part of a
portfolio. Normalization would hide incomplete coverage and could overstate
overlap. A later assessment integration must apply an explicit minimum coverage
and freshness gate before using overlap as a scored metric.

## Current scope

This foundation does not yet fetch issuer files, expose a public endpoint or
replace the manual overlap field. The next data-source milestone must identify
official, automatable constituent sources and preserve their original dates and
provenance before candidate analysis consumes the calculated result.
