# Constituent data quality and local calculation data

## Purpose

V2-10 prevents an available issuer adapter from being mistaken for populated,
current calculation data. V2-11 uses constituent overlap only after every ETF
required by that calculation passes explicit coverage, freshness and
disclosed-weight checks.

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

For an interrupted or partially failed full-market refresh, write an atomic
checkpoint and resume from it:

```powershell
.venv\Scripts\python.exe -m backend.app.data_sources.constituent_batch_pipeline `
  --database C:\absolute\test-data\tw_etf-calculation.db `
  --checkpoint C:\absolute\test-data\constituent-checkpoint.json `
  --allow-network `
  --output C:\absolute\test-data\constituent-quality.json

.venv\Scripts\python.exe -m backend.app.data_sources.constituent_batch_pipeline `
  --database C:\absolute\test-data\tw_etf-calculation.db `
  --checkpoint C:\absolute\test-data\constituent-checkpoint.json `
  --resume `
  --allow-network `
  --output C:\absolute\test-data\constituent-quality-resumed.json
```

Resume skips checkpointed `IMPORTED` and `UNCHANGED` codes and retries only
failed codes. A checkpoint names one database and contains bounded result
metadata, not source payloads or credentials.

Passing V2-10 proves constituent-data readiness only. Performance, dividend
events and ACTUAL/estimated dividend-composition coverage retain their own
separate gates.

## Calculation behavior

- ETF comparison calculates pairwise overlap as the sum of the smaller
  disclosed weight for each shared constituent.
- Candidate-holding analysis first weights every current ETF constituent by
  that holding's current market-value allocation, then compares the aggregated
  portfolio weights with the candidate ETF.
- A snapshot older than seven days, below 85% disclosed stock weight or missing
  for any required ETF makes overlap unavailable for that calculation.
- Deprecated manual overlap request values are ignored. Unknown overlap is
  never converted to zero.
- Automatic overlap contributes 10% of the backend portfolio-fit score. ETF
  quality remains the largest component, so diversification cannot compensate
  for weak historical return or downside evidence.

## Refresh the isolated calculation candidate

Set the database environment variable before starting each Pipeline process so
performance and dividend writes target the isolated copy rather than the
repository development database:

```powershell
$env:TW_ETF_DATABASE_PATH = 'C:\absolute\test-data\tw_etf-calculation.db'

.venv\Scripts\python.exe -m backend.app.data_sources.performance_pipeline `
  --periods 1M 3M 6M 1Y `
  --no-raw-snapshot

.venv\Scripts\python.exe -m backend.app.data_sources.dividend_pipeline `
  --preserve-event-on-invalid-estimates

.venv\Scripts\python.exe -m backend.app.data_sources.constituent_batch_pipeline `
  --database $env:TW_ETF_DATABASE_PATH `
  --allow-network `
  --output C:\absolute\test-data\constituent-quality.json

Remove-Item Env:TW_ETF_DATABASE_PATH
```

The 2026-09-02 V5-3C candidate covers 129/157 target ETFs and 19/21 issuers.
Issuer coverage passes 90%, but ETF coverage remains `NO_GO` at 82.165605%
because Cathay and BlackRock are fail-closed and five automated-source products
remain explicitly unavailable. This does not prevent a bounded pair or saved
portfolio from calculating when every ETF in that specific set passes the
gates. See `V5_3C_CONSTITUENT_RECOVERY.md`.
