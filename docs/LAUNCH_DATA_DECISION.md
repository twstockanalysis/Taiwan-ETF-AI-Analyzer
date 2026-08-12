# M12-6 launch-data decision

## Gate

The ordinary first-release data gate requires all of the following in the
deployment candidate database:

- at least one dividend event;
- at least one event with reviewed `ACTUAL` components;
- at least one event with an official `ACTUAL + 76W` record; and
- at least one event linked to a parsed, traceable `ACTUAL` source document.

A formally disclosed `76W = 0%` passes the 76W-record check because the
official record exists. Estimated capital-gain composition never passes it.

Run the repeatable gate with the exact deployment candidate:

```powershell
.venv\Scripts\python.exe -m deployment.launch_data_check `
  --database C:\absolute\path\to\tw_etf.db `
  --output C:\absolute\path\to\launch-data-decision.json
```

`READY` and explicitly approved `LIMITED_APPROVED` return exit code 0.
`NO_GO` returns exit code 1 so deployment automation can stop safely.

## Limited-coverage exception

The gate may only issue `LIMITED_APPROVED` when both a named approver and a
non-empty reason are recorded:

```powershell
.venv\Scripts\python.exe -m deployment.launch_data_check `
  --database C:\absolute\path\to\tw_etf.db `
  --limited-approved-by "site owner" `
  --limited-reason "Approved reason shown with the release evidence"
```

This is an explicit release decision, not a technical default. The command
rejects partial approval metadata. The approval does not change missing-data
semantics: the website must continue to show unavailable ACTUAL/76W data as
missing and must not convert estimates into official values.

## Initial candidate result on 2026-08-12

The repository candidate `database/tw_etf.db` produced:

| Check | Actual | Minimum | Result |
|---|---:|---:|---|
| Dividend events | 288 | 1 | Pass |
| Reviewed ACTUAL component events | 0 | 1 | Fail |
| Official ACTUAL 76W events | 0 | 1 | Fail |
| Traceable parsed ACTUAL source-document events | 0 | 1 | Fail |

Initial decision: `NO_GO`. No limited-coverage approval was supplied or
inferred.

## Reviewed-data seed and final local candidate result

The ordinary path was completed without a limited-coverage exception:

1. TWSE ETF e添富 was queried explicitly for ETF `00878`, 2023 through 2023.
2. Four official parent dividend events were accepted. Two incomplete or
   abnormal estimated-composition disclosures remained rejected while their
   independently valid dates and amounts were preserved.
3. Cathay's official announcement `5141` was downloaded through the verified
   adapter. It uniquely matched the 2023-08-16, 0.35 TWD event and imported the
   published `76W` 97.14% and `54C` 2.86% components.
4. The review queue, database integrity, foreign keys and launch-data gate were
   rerun after import.

Before the local candidate changed, the M12-2 backup command created a SQLite
backup and manifest. A restore into a separate temporary path subsequently
verified its SHA-256, exact row counts, integrity `ok` and zero foreign-key
violations. The backup intentionally records the pre-migration candidate's
`schema_ready=false`; the imported candidate was initialized and separately
verified as deployment-ready.

| Check | Actual | Minimum | Result |
|---|---:|---:|---|
| Dividend events | 292 | 1 | Pass |
| Reviewed ACTUAL component events | 1 | 1 | Pass |
| Official ACTUAL 76W events | 1 | 1 | Pass |
| Traceable parsed ACTUAL source-document events | 1 | 1 | Pass |

Final local candidate decision: `READY`, with no exception. SQLite integrity
is `ok`, foreign-key violations are zero, and the deployment schema is ready.

Coverage is intentionally described as minimal, not broad: each reviewed
coverage ratio is `0.342466%` (1 of 292 events), and 582 review-queue items
remain. The website must keep its existing missing-data disclosure and must not
present this gate as a completeness score.

The ordinary M12-6 gate now passes for the local candidate. Domain, TLS and
public-host evidence remain the separate external M12-5 launch dependency.
