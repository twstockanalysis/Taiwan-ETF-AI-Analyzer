# Deployment database initialization and migration

M12-1 separates read-only verification, isolated rehearsal and the explicit
deployment mutation. Never use the application startup as an implicit migration
step.

## Verify without writing

```powershell
.venv\Scripts\python.exe -m backend.app.database.deployment_readiness verify `
  --database D:\durable-data\tw_etf.db
```

The command exits non-zero unless every required table and column exists,
`PRAGMA integrity_check` returns `ok`, and `PRAGMA foreign_key_check` returns no
rows.

## Rehearse against an isolated SQLite backup

The rehearsal destination must not already exist and must not equal the source.
The command uses SQLite's backup API, migrates only the copy, verifies the
result, and fails if any pre-existing table has fewer rows afterward.

```powershell
.venv\Scripts\python.exe -m backend.app.database.deployment_readiness rehearse `
  --source D:\durable-data\tw_etf.db `
  --rehearsal D:\migration-rehearsal\tw_etf.db
```

The 2026-08-12 rehearsal against `database/tw_etf.db` passed with all existing
rows preserved: 256 ETF master rows, 205 performance rows, 288 dividend rows,
1,430 estimated component rows and 576 review-queue rows. The upgraded copy
added the missing M11/M11-5 tables and passed integrity and foreign-key checks.

## Initialize the deployment database

Run this as an explicit release step only after a successful rehearsal and a
recoverable backup. Backup and restore automation belongs to M12-2.

```powershell
.venv\Scripts\python.exe -m backend.app.database.deployment_readiness initialize `
  --database D:\durable-data\tw_etf.db
```

The command initializes or migrates the explicit path and immediately applies
the same readiness verification. Do not start FastAPI if this command fails.
