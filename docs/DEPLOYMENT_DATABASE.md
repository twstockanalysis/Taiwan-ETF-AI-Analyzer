# Deployment database operations

## Durable production path

Production must keep SQLite outside the application release directory and set
an absolute path before every API or pipeline command:

```powershell
$env:TW_ETF_DATABASE_PATH = 'D:\tw-etf-data\current\tw_etf.db'
```

A relative `TW_ETF_DATABASE_PATH` is rejected because its meaning changes with
the process working directory. If the variable is absent, the existing
`database/tw_etf.db` path remains available for local development only. The
durable directory must be mounted independently from application releases and
writable only by the API/pipeline operating identity and backup operator.

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

## Create a verified backup

Stop scheduled writers for the short cutover window, then create a backup with
a new timestamped filename. The SQLite backup API keeps the copy transactionally
consistent even if a read connection remains open.

```powershell
.venv\Scripts\python.exe -m backend.app.database.deployment_readiness backup `
  --source D:\tw-etf-data\current\tw_etf.db `
  --backup D:\tw-etf-backups\tw_etf-20260812T170000Z.db
```

The command refuses overwrite and writes a neighboring
`.db.manifest.json` file containing SHA-256, byte size, UTC creation time,
schema readiness and table row counts. A backup is successful only when the
copy passes SQLite integrity checks and its row counts match the source. Store
the database and manifest together on storage independent from the live volume.

Retention policy for the first public release:

- retain the latest 7 daily backups;
- retain 4 weekly backups after daily rotation;
- always retain the immediate pre-migration backup until the following release
  and restore drill both pass;
- never delete the only verified backup during an incident.

Automated retention and off-host scheduling are part of M12-3. Until then,
rotation is an explicit operator action after confirming another verified copy
exists.

## Restore drill and recovery

Restore always targets a path that does not exist. It never overwrites the live
database:

```powershell
.venv\Scripts\python.exe -m backend.app.database.deployment_readiness restore `
  --backup D:\tw-etf-backups\tw_etf-20260812T170000Z.db `
  --restored D:\tw-etf-data\restore-drill\tw_etf.db
```

Before writing, the command verifies manifest version, SHA-256 and byte size.
After restoring, it verifies SQLite integrity, foreign-key status, schema state
and exact table row counts. For incident recovery:

1. stop FastAPI and all scheduled writers;
2. preserve the failed live database for investigation;
3. restore the selected backup to a new path and require a successful report;
4. run the read-only `verify` command against the restored path;
5. change `TW_ETF_DATABASE_PATH` to the restored absolute path;
6. start the API, perform health/data smoke checks, then re-enable writers;
7. record the backup filename, manifest hash, operator, timestamps and outcome.

Do not copy a raw live `.db` file with filesystem copy tools and do not point
production at a rehearsal database.

The 2026-08-12 restore drill against the current deployment candidate passed:
the 954,368-byte backup matched SHA-256
`1fe1c0e3e4a3c3421d1d79bb95bf9c3169c7922ebd47d49176fb1c40b8b8bd39`,
all eight existing-table row counts matched, integrity returned `ok`, and no
foreign-key violations were found. `schema_ready` remained false as expected
because this was a pre-M12-1 legacy candidate; it must be backed up before the
separate initialization/migration step.
