"""M12-1 deployment database initialization and migration verification."""

from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path

from backend.app.database.init_db import initialize_database


REQUIRED_SCHEMA: dict[str, frozenset[str]] = {
    "etf_master": frozenset({"code", "name", "is_active", "is_bond"}),
    "import_batch": frozenset({"id", "pipeline_name", "status"}),
    "etf_performance": frozenset(
        {"etf_code", "as_of_date", "period_code", "metric_code", "return_pct"}
    ),
    "etf_daily_close": frozenset(
        {"etf_code", "trade_date", "close_price", "source_id"}
    ),
    "etf_dividend": frozenset(
        {"id", "etf_code", "payment_date", "amount_per_unit", "currency"}
    ),
    "etf_dividend_summary_metric": frozenset(
        {"dividend_id", "yield_pct", "yield_basis", "reference_trade_date"}
    ),
    "etf_dividend_component": frozenset(
        {"dividend_id", "component_code", "component_basis", "source_id"}
    ),
    "dividend_source_document": frozenset(
        {"id", "source_id", "source_document_id", "information_basis"}
    ),
    "dividend_source_review_queue": frozenset(
        {"id", "dividend_id", "issue_type", "status"}
    ),
    "decision_profile": frozenset(
        {"id", "monthly_after_tax_target", "analysis_years", "history_years"}
    ),
    "manual_holding": frozenset(
        {"etf_code", "held_units", "unit_price", "price_source_id"}
    ),
    "decision_record": frozenset(
        {"id", "candidate_etf_code", "analysis_json", "created_at"}
    ),
}


@dataclass(frozen=True)
class DatabaseReadinessReport:
    database_path: str
    ready: bool
    integrity_check: str
    foreign_key_violation_count: int
    missing_tables: list[str]
    missing_columns: dict[str, list[str]]
    row_counts: dict[str, int]


@dataclass(frozen=True)
class MigrationRehearsalReport:
    source_path: str
    rehearsal_path: str
    source_row_counts: dict[str, int]
    upgraded_row_counts: dict[str, int]
    preserved_tables: list[str]
    readiness: DatabaseReadinessReport


def _connect(path: Path, *, read_only: bool) -> sqlite3.Connection:
    if read_only:
        connection = sqlite3.connect(
            f"file:{path.resolve().as_posix()}?mode=ro", uri=True
        )
    else:
        connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def _user_tables(connection: sqlite3.Connection) -> list[str]:
    return [
        str(row["name"])
        for row in connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name;
            """
        ).fetchall()
    ]


def _row_counts(connection: sqlite3.Connection) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table in _user_tables(connection):
        quoted = table.replace('"', '""')
        counts[table] = int(
            connection.execute(f'SELECT COUNT(*) FROM "{quoted}";').fetchone()[0]
        )
    return counts


def verify_database_schema(database_path: str | Path) -> DatabaseReadinessReport:
    """Verify the current deployment schema without mutating the database."""

    path = Path(database_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"資料庫不存在：{path}")
    connection = _connect(path, read_only=True)
    try:
        tables = set(_user_tables(connection))
        missing_tables = sorted(set(REQUIRED_SCHEMA) - tables)
        missing_columns: dict[str, list[str]] = {}
        for table, required_columns in REQUIRED_SCHEMA.items():
            if table not in tables:
                continue
            columns = {
                str(row["name"])
                for row in connection.execute(
                    f'PRAGMA table_info("{table}");'
                ).fetchall()
            }
            missing = sorted(required_columns - columns)
            if missing:
                missing_columns[table] = missing
        integrity = str(connection.execute("PRAGMA integrity_check;").fetchone()[0])
        foreign_key_violations = connection.execute(
            "PRAGMA foreign_key_check;"
        ).fetchall()
        counts = _row_counts(connection)
    finally:
        connection.close()
    ready = (
        integrity == "ok"
        and not foreign_key_violations
        and not missing_tables
        and not missing_columns
    )
    return DatabaseReadinessReport(
        database_path=str(path),
        ready=ready,
        integrity_check=integrity,
        foreign_key_violation_count=len(foreign_key_violations),
        missing_tables=missing_tables,
        missing_columns=missing_columns,
        row_counts=counts,
    )


def initialize_deployment_database(
    database_path: str | Path,
) -> DatabaseReadinessReport:
    """Initialize or migrate one explicit deployment database, then verify it."""

    path = Path(database_path).resolve()
    initialize_database(path)
    report = verify_database_schema(path)
    if not report.ready:
        raise RuntimeError("部署資料庫初始化後未通過 Schema 驗證")
    return report


def _sqlite_backup(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(f"演練資料庫已存在：{destination}")
    source_connection = _connect(source, read_only=True)
    destination_connection = _connect(destination, read_only=False)
    try:
        source_connection.backup(destination_connection)
    finally:
        destination_connection.close()
        source_connection.close()


def rehearse_database_migration(
    source_path: str | Path,
    rehearsal_path: str | Path,
) -> MigrationRehearsalReport:
    """Upgrade an isolated SQLite backup and prove existing rows are preserved."""

    source = Path(source_path).resolve()
    rehearsal = Path(rehearsal_path).resolve()
    if not source.is_file():
        raise FileNotFoundError(f"來源資料庫不存在：{source}")
    if source == rehearsal:
        raise ValueError("來源與演練資料庫不得相同")
    source_connection = _connect(source, read_only=True)
    try:
        source_counts = _row_counts(source_connection)
    finally:
        source_connection.close()
    _sqlite_backup(source, rehearsal)
    readiness = initialize_deployment_database(rehearsal)
    decreased = {
        table: (before, readiness.row_counts.get(table))
        for table, before in source_counts.items()
        if readiness.row_counts.get(table, -1) < before
    }
    if decreased:
        details = ", ".join(
            f"{table}: {before}->{after}"
            for table, (before, after) in decreased.items()
        )
        raise RuntimeError(f"演練發現既有資料列減少：{details}")
    return MigrationRehearsalReport(
        source_path=str(source),
        rehearsal_path=str(rehearsal),
        source_row_counts=source_counts,
        upgraded_row_counts=readiness.row_counts,
        preserved_tables=sorted(source_counts),
        readiness=readiness,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="部署資料庫初始化與遷移驗證")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("verify", "initialize"):
        command = subparsers.add_parser(name)
        command.add_argument("--database", required=True, type=Path)
    rehearse = subparsers.add_parser("rehearse")
    rehearse.add_argument("--source", required=True, type=Path)
    rehearse.add_argument("--rehearsal", required=True, type=Path)
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "verify":
        report = verify_database_schema(args.database)
        print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
        if not report.ready:
            raise SystemExit(1)
        return
    if args.command == "initialize":
        report = initialize_deployment_database(args.database)
    else:
        report = rehearse_database_migration(args.source, args.rehearsal)
    print(json.dumps(asdict(report), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
