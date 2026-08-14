# Constituent data quality and local calculation data

## Purpose

V2-10 prevents an available issuer adapter from being mistaken for populated,
current calculation data. Constituent overlap may be used by a later assessment
only after the requested ETF universe passes explicit coverage, issuer,
freshness and disclosed-weight checks.

The default calculation universe contains stock ETFs that have a stored 6M
`PRICE_RETURN`. Bond, leveraged, inverse, futures and multi-asset products are
excluded because stock-only overlap is not a comparable measure for them. ETFs
without the performance baseline remain visible as
`MISSING_PERFORMANCE_BASELINE`; they are not silently counted as covered.

## Default gates

- At least 90% of eligible ETFs have usable snapshots.
- At least 90% of represented issuers have usable snapshots.
- A usable snapshot is no more than seven calendar days old.
- A usable snapshot discloses at least 85% stock weight. The lower bound
  accommodates sources whose validated stock allocation is below 90% while the
  issuer separately reconciles the remaining cash, futures or other assets.
- Every calculation-eligible ETF name resolves to one reviewed issuer.

Cathay and BlackRock remain in the denominator. Their current official
automation limitations therefore remain visible and can keep a full-market
run below the default threshold.

## Safe local workflow

Back up the candidate first and work on a copy. Initialize the copy so it has
the V2 constituent tables, then explicitly allow official network retrieval:

```powershell
Copy-Item database\tw_etf.db C:\absolute\test-data\tw_etf-calculation.db

.venv\Scripts\python.exe -m backend.app.database.deployment_readiness initialize `
  --database C:\absolute\test-data\tw_etf-calculation.db

.venv\Scripts\python.exe -m backend.app.data_sources.constituent_batch_pipeline `
  --database C:\absolute\test-data\tw_etf-calculation.db `
  --allow-network `
  --output C:\absolute\test-data\constituent-quality.json
```

For a bounded calculation fixture, repeat `--etf-code`:

```powershell
.venv\Scripts\python.exe -m backend.app.data_sources.constituent_batch_pipeline `
  --database C:\absolute\test-data\tw_etf-calculation.db `
  --etf-code 0050 `
  --etf-code 00918 `
  --allow-network `
  --output C:\absolute\test-data\0050-00918-quality.json
```

The command exits `0` only for `READY` and exits `1` for `NO_GO`. A same-day
rerun reuses equivalent position content as `UNCHANGED`. If an issuer changes
positions for an already stored ETF, source and effective date, the pipeline
refuses to overwrite the immutable snapshot.

Passing V2-10 proves constituent-data readiness only. Performance, dividend
events and ACTUAL/estimated dividend-composition coverage retain their own
separate gates.
