# Production scheduling and monitoring

M12-3 provides two operating-system-neutral commands. The host scheduler owns
the clock; the repository owns job ordering, overlap prevention, reporting and
health thresholds.

## Scheduled pipeline run

Copy `deployment/schedule.example.json` outside the release directory and pin
each `argv` to the deployed virtual environment. Keep ETF master first because
the later pipelines depend on its active universe. The example intentionally
does not automate `actual_dividend_pipeline`: ACTUAL input must first be
reviewed and supplied through its explicit `--input` contract.

```powershell
$env:TW_ETF_DATABASE_PATH = 'D:\tw-etf-data\current\tw_etf.db'
Set-Location 'D:\tw-etf-app\current'
.venv\Scripts\python.exe -m backend.app.operations.scheduled_run `
  --config D:\tw-etf-ops\schedule.json `
  --report D:\tw-etf-ops\state\latest-run.json `
  --lock D:\tw-etf-ops\state\pipeline.lock `
  --log-directory D:\tw-etf-ops\logs
```

The executor passes argument arrays directly without a shell, stops after the
first failure, writes one log per job and atomically replaces the latest JSON
report. An exclusive lock rejects overlapping runs. A stale lock after a host
crash must only be removed after confirming no pipeline process is active.
Restrict the configuration, state and log directories to the operating identity;
job output can contain source paths and operational error details.

Use Windows Task Scheduler (or the production host's equivalent) with:

- a dedicated least-privilege operating identity;
- “run whether user is logged on or not”;
- no parallel instance;
- a daily trigger after official source updates, initially 03:30 Asia/Taipei;
- working directory fixed to the current release path;
- non-zero exit code treated as failure;
- credentials and environment configured outside the repository.

Do not schedule a new release until its manual pipeline smoke test succeeds.

## Machine-readable monitoring

Run this after the pipelines and at least every 15 minutes for API/storage
checks:

```powershell
.venv\Scripts\python.exe -m backend.app.operations.monitor `
  --database D:\tw-etf-data\current\tw_etf.db `
  --backup-directory D:\tw-etf-backups `
  --scheduled-run-state D:\tw-etf-ops\state\latest-run.json `
  --restore-drill-state D:\tw-etf-ops\state\restore-drill.json `
  --api-url https://example.com/health `
  --output D:\tw-etf-ops\state\health.json
```

Exit code `0` means no critical check; exit code `2` means at least one critical
check. The default critical thresholds are:

- database schema/integrity/foreign keys fail;
- less than 2 GiB free on the database volume;
- latest batch for any recorded pipeline is failed, or running over 6 hours;
- latest complete scheduled run failed or is over 30 hours old;
- latest successful import/performance observation is over 168 hours old;
- latest valid backup manifest is over 30 hours old or its artifact is missing;
- last successful restore drill is over 35 days old;
- `/health` is unavailable, non-200, or does not return `{"status":"healthy"}`.

Alerts should include the full JSON report, host, release SHA and timestamp.
Page the operator immediately for database, storage, failed/stuck pipeline,
backup, restore-drill or API failures. Data freshness is also launch-blocking;
inspect source availability and the latest per-job log before retrying.

After every successful monthly restore drill, atomically write:

```json
{
  "completed_at": "2026-08-12T09:00:00+00:00",
  "passed": true,
  "backup_manifest": "D:\\tw-etf-backups\\tw_etf.db.manifest.json"
}
```

External notification delivery and provider-specific scheduler provisioning are
deployment-environment responsibilities; M12-5 will bind these commands to the
selected host.
