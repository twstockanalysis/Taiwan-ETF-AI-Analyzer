# M8 Completion Audit

## Baseline

Audit bundle:

```text
Git branch: feature/etf-analysis-data
Git commit: 42eb33f
Audit date: 2026-07-31
```

The working tree contained only the temporary bundle-builder script.

## Result

Status after applying M8-5A and passing the acceptance tests:

```text
M8 READY TO CLOSE
```

M8 has complete implementation paths for:

- Analysis schema and Pydantic models
- ETF performance calculation, storage, APIs and frontend
- Dividend events and estimated composition
- ACTUAL composition and official source documents
- Actual `76W` statistics
- Coverage, review queue, APIs and Streamlit quality page
- Unit, repository, Pipeline, API and frontend tests

## Findings and corrections

### 1. Performance Migration was not in normal initialization

`migrate_performance_metric.py` existed and had direct tests, but
`initialize_database()` did not call it. A database created before
`metric_code` could therefore remain on the old performance schema unless the
Migration was run manually.

Correction:

```text
initialize_database
-> migrate_performance_metric
-> migrate_dividend_component_basis
-> migrate_dividend_source_document
-> migrate_dividend_review_queue
```

A regression test now verifies automatic upgrade and preservation of legacy
records as `PRICE_RETURN`.

### 2. Architecture smoke coverage was fragmented

Individual features had strong tests, but there was no single M8 contract test
for the final table set, API route set, frontend navigation and documentation
integrity.

Correction:

```text
tests/test_m8_architecture_smoke.py
```

### 3. Documentation had drifted behind implementation

Several legacy documents still described M5–M7 behavior, duplicated ETF API
sections, omitted M8 routes and tables, or contained unclosed Markdown fences.

Correction:

- Reconciled Roadmap, PRD and Changelog
- Rebuilt API, schema, frontend, source and architecture documentation
- Added a Markdown-fence smoke check

## Preserved M8 invariants

```text
EST_REALIZED_CAPITAL_GAIN != 76W
```

```text
actual 76W coverage =
component_basis=ACTUAL
and component_code=76W
```

```text
formal 0% = available data
missing row = missing data
```

```text
performance rankings never mix periods or metrics
```

```text
insufficient price history != 0% return
```

## Known limitations accepted at M8 closure

- The populated performance metric is market-price return only.
- Actual-dividend coverage remains limited by verified official documents.
- The quality queue is read-only in the public API and frontend.
- Data Pipelines are started manually.
- SQLite remains the development database.
- ETF comparison, recommendation and decision workflows are not part of M8.
- Broker and third-party market-data APIs are deferred optional integrations.

These limitations are roadmap items, not M8 defects.

## Acceptance commands

Compile:

```powershell
python -m compileall backend frontend tests
```

Focused M8 audit:

```powershell
python -m unittest `
    tests.test_performance_metric_migration `
    tests.test_m8_architecture_smoke `
    -v
```

M8 regression:

```powershell
python -m unittest `
    tests.test_multi_period_performance `
    tests.test_multi_period_performance_pipeline `
    tests.test_performance_api `
    tests.test_dividend_pipeline `
    tests.test_dividend_api `
    tests.test_actual_dividend_pipeline `
    tests.test_cathay_actual_dividend_pipeline `
    tests.test_actual_dividend_coverage_pipeline `
    tests.test_dividend_quality_api `
    tests.test_frontend_performance_ranking `
    tests.test_frontend_dividend_ui `
    tests.test_frontend_dividend_quality_ui `
    -v
```

Full project:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

All commands must finish with `OK` before M8 is treated as closed.
