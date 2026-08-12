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

## Candidate result on 2026-08-12

The repository candidate `database/tw_etf.db` produced:

| Check | Actual | Minimum | Result |
|---|---:|---:|---|
| Dividend events | 288 | 1 | Pass |
| Reviewed ACTUAL component events | 0 | 1 | Fail |
| Official ACTUAL 76W events | 0 | 1 | Fail |
| Traceable parsed ACTUAL source-document events | 0 | 1 | Fail |

Decision: `NO_GO`. No limited-coverage approval has been supplied or inferred.

M12-6 implementation can be merged because the threshold is now executable,
tested and documented, but public launch remains blocked until either the
ordinary gate passes or the owner explicitly approves a limited-coverage
release with a recorded reason. Domain, TLS and public-host evidence remain the
separate external M12-5 launch dependency.
