# Actual Dividend Composition Import

## Purpose

This import path stores official actual distribution-source codes such as:

```text
76W
54C
```

It is separate from the TWSE ETF e添富 estimated-composition pipeline.

The following estimated code is never converted to `76W`:

```text
EST_REALIZED_CAPITAL_GAIN
```

## Source Acceptance Policy

Use this import only when the source document explicitly provides actual
distribution composition or is an official distribution notice.

The input must declare:

```text
information_basis = ACTUAL
```

Estimated announcements must remain in the existing TWSE estimated pipeline.

## JSON Format

```json
{
  "schema_version": 1,
  "notices": [
    {
      "source_id": "official_distribution_notice",
      "source_document_id": "issuer-document-stable-id",
      "source_document_url": "https://issuer.example/official-document",
      "source_document_date": "2026-07-30",
      "information_basis": "ACTUAL",
      "etf_code": "00918",
      "announcement_date": "2026-07-30",
      "ex_dividend_date": "2026-07-15",
      "record_date": "2026-07-21",
      "payment_date": "2026-08-10",
      "amount_per_unit": "0.70",
      "currency": "TWD",
      "components": [
        {
          "component_code": "76W",
          "component_name": "Official source description",
          "amount_per_unit": "0.70",
          "ratio_pct": "100"
        }
      ]
    }
  ]
}
```

The source description must be preserved as published. Do not infer a tax code
from a general description.

## Matching Policy

The importer links the notice to an existing `etf_dividend` event using:

```text
ETF code
+ ex-dividend date
+ amount per unit
```

When supplied, record date and payment date must also match.

Results:

```text
one match    -> import ACTUAL components
zero matches -> reject the notice
many matches -> reject the notice
```

The importer never chooses one ambiguous event automatically.

## Validation

The importer rejects:

```text
ESTIMATED information basis
EST_ component codes
blank component codes
negative amounts
ratios outside 0 to 100
duplicate component codes in one notice
abnormal ratio totals
abnormal component-amount totals
missing or ambiguous parent dividend events
```

When all component ratios are supplied, their total must be between 99% and
101% to allow published rounding.

When all component amounts are supplied, their total must match the
distribution amount within the configured rounding tolerance.

## Run

Prepare a reviewed JSON file outside the test fixtures, then run:

```powershell
python -m backend.app.data_sources.actual_dividend_pipeline `
    --input .\data\imports\actual_dividend_notice.json
```

Do not import the automated test fixture into the production database.

## Artifacts

The pipeline writes audit artifacts under:

```text
data/raw/dividends/actual
data/processed/dividends/actual
data/rejected/dividends/actual
data/processed/reports/dividends/actual
```

Raw and processed artifacts preserve:

```text
source document ID
source document URL
source document date
matched dividend database ID
matched source event ID
official component codes and descriptions
```

SQLite stores the matched ACTUAL components. The existing dividend API and
Streamlit detail page then expose actual `76W` data.

## Current Boundary

M8-4A accepts human-reviewed structured JSON.

It does not perform:

```text
OCR
PDF extraction
automatic issuer-site crawling
automatic inference of tax-source codes
```

Public official-source adapters can be added after each issuer format and
usage policy are verified.

## M8-4B Official Source Adapters

M8-4B adds source-document versioning and the first verified issuer adapter.

The Cathay adapter converts explicitly actual official announcements into this
same M8-4A JSON format. It does not bypass the existing validation, event
matching or ACTUAL-only rules.

See:

```text
docs/ACTUAL_DIVIDEND_SOURCES.md
```
