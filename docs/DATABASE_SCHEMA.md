# Database Schema

## Database

The first version uses SQLite as its development database.

- Database engine: SQLite
- Database file: `database/tw_etf.db`
- Character encoding: UTF-8
- Foreign key enforcement: enabled for every application connection

The SQLite database file and its `-shm` and `-wal` sidecar files are excluded
from Git. The application creates the `database` directory when necessary.

## Initialization

Run the initialization module from the project root:

```powershell
python -m backend.app.database.init_db
```

Initialization reads `backend/app/database/schema.sql`. All schema statements
use `IF NOT EXISTS`, so running the command repeatedly is safe and does not
remove existing data.

The application connects through
`backend.app.database.connection.get_connection`. Query results use
`sqlite3.Row`, allowing columns to be accessed by name.

## ETF Master Table

Table name: `etf_master`

The table stores the basic information needed to identify and filter a Taiwan
ETF. Boolean values are represented by SQLite integers: `0` is false and `1`
is true.

| Column | SQLite type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `code` | `TEXT` | Yes | None | ETF security code and primary key. |
| `name` | `TEXT` | Yes | None | ETF name. |
| `is_active` | `INTEGER` | Yes | `0` | Whether the ETF is currently active; only `0` or `1` is valid. |
| `is_bond` | `INTEGER` | Yes | `0` | Whether the ETF is a bond ETF; only `0` or `1` is valid. |
| `listing_date` | `TEXT` | No | `NULL` | Listing date. Date-format validation is handled by the application. |
| `fund_size` | `REAL` | No | `NULL` | Fund size; when present, it must be zero or greater. |
| `expense_ratio` | `REAL` | No | `NULL` | Expense ratio percentage; when present, it must be between 0 and 100. |

### Constraints

- `code` is unique because it is the primary key.
- `name` cannot be `NULL`.
- `is_active` and `is_bond` accept only `0` or `1`.
- `fund_size` cannot be negative.
- `expense_ratio` must be between `0` and `100`, inclusive.

The current schema intentionally permits an empty string for text columns and
does not enforce the format of `listing_date`. Those validations belong to the
future API/service input boundary.

### Indexes

| Index | Columns | Purpose |
| --- | --- | --- |
| `sqlite_autoindex_etf_master_1` | `code` | SQLite-generated primary-key index. |
| `idx_etf_master_name` | `name` | Speeds up ETF name lookups. |

## Schema Verification

After initialization, inspect the table with:

```powershell
python -m backend.app.database.check_schema
```

Automated tests create an isolated temporary database and never read or write
`database/tw_etf.db`.

## ETF Master Upsert Policy

The official master import updates:

- `name`
- `is_active`
- `is_bond`
- `listing_date`

The import does not overwrite:

- `fund_size`
- `expense_ratio`

This prevents a master-data import that lacks financial metrics
from clearing values obtained from other official sources.