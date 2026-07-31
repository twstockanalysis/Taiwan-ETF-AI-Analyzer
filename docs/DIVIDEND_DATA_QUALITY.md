# Dividend Data Quality

M8-4C measures actual-dividend coverage and maintains a review queue.

## Coverage definitions

A dividend event has estimated composition when at least one component uses:

```text
component_basis = ESTIMATED
```

It has actual composition when at least one component uses:

```text
component_basis = ACTUAL
```

It has an actual 76W record only when a component uses both:

```text
component_basis = ACTUAL
component_code = 76W
```

A formally disclosed `76W = 0%` is still covered because the official record
exists. Missing 76W data is not converted to zero.

`EST_REALIZED_CAPITAL_GAIN` never counts as 76W.

A source document is covered when an ACTUAL component import batch is linked to
a parsed `dividend_source_document` whose information basis is ACTUAL.

## Review queue

The table is:

```text
dividend_source_review_queue
```

Issue types:

```text
MISSING_ACTUAL_COMPONENTS
MISSING_SOURCE_DOCUMENT
```

Statuses:

```text
PENDING
IN_REVIEW
RESOLVED
SKIPPED
```

The queue is unique by dividend event and issue type. Running the coverage
pipeline repeatedly does not create duplicates.

When missing data is supplied, the related item is automatically marked
`RESOLVED`. A still-missing `SKIPPED` item remains skipped.

## Run the pipeline

```powershell
python -m backend.app.data_sources.actual_dividend_coverage_pipeline
```

The pipeline writes:

```text
data/processed/dividends/review_queue/
data/processed/reports/dividends/coverage/
```

## API

```text
GET /api/v1/data-quality/dividends/actual-coverage
GET /api/v1/data-quality/dividends/review-queue
GET /api/v1/data-quality/dividends/review-queue/{queue_id}
```

The queue endpoint supports:

```text
status
etf_code
issue_type
limit
offset
```

M8-4C exposes read-only HTTP endpoints. Administrative status changes remain a
Repository operation until the management interface is designed.
