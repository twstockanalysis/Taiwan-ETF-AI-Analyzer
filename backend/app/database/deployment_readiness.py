"""M12-1 deployment database initialization and migration verification."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
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
    "etf_constituent_snapshot": frozenset(
        {"id", "etf_code", "as_of_date", "source_id", "total_weight_pct"}
    ),
    "etf_constituent_position": frozenset(
        {"snapshot_id", "constituent_id", "constituent_name", "weight_pct"}
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


@dataclass(frozen=True)
class DatabaseBackupReport:
    source_path: str
    backup_path: str
    manifest_path: str
    created_at: str
    sha256: str
    size_bytes: int
    row_counts: dict[str, int]
    schema_ready: bool


@dataclass(frozen=True)
class DatabaseRestoreReport:
    backup_path: str
    restored_path: str
    manifest_path: str
    sha256_verified: bool
    row_counts_verified: bool
    integrity_check: str
    foreign_key_violation_count: int
    schema_ready: bool


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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _default_manifest_path(backup: Path) -> Path:
    return Path(f"{backup}.manifest.json")


def backup_database(
    source_path: str | Path,
    backup_path: str | Path,
    manifest_path: str | Path | None = None,
) -> DatabaseBackupReport:
    """Create a transactionally consistent backup and a recovery manifest."""

    source = Path(source_path).resolve()
    backup = Path(backup_path).resolve()
    manifest = (
        Path(manifest_path).resolve()
        if manifest_path is not None
        else _default_manifest_path(backup)
    )
    if not source.is_file():
        raise FileNotFoundError(f"來源資料庫不存在：{source}")
    if source == backup:
        raise ValueError("來源與備份資料庫不得相同")
    if manifest in {source, backup}:
        raise ValueError("備份清單不得與來源或備份資料庫使用相同路徑")
    if manifest.exists():
        raise FileExistsError(f"備份清單已存在：{manifest}")
    source_report = verify_database_schema(source)
    if (
        source_report.integrity_check != "ok"
        or source_report.foreign_key_violation_count
    ):
        raise RuntimeError("來源資料庫未通過完整性或外鍵檢查")
    _sqlite_backup(source, backup)
    backup_report = verify_database_schema(backup)
    if (
        backup_report.integrity_check != "ok"
        or backup_report.foreign_key_violation_count
    ):
        raise RuntimeError("備份資料庫未通過完整性或外鍵檢查")
    if backup_report.row_counts != source_report.row_counts:
        raise RuntimeError("備份資料列數與來源不一致")
    created_at = datetime.now(timezone.utc).isoformat()
    report = DatabaseBackupReport(
        source_path=str(source),
        backup_path=str(backup),
        manifest_path=str(manifest),
        created_at=created_at,
        sha256=_sha256(backup),
        size_bytes=backup.stat().st_size,
        row_counts=backup_report.row_counts,
        schema_ready=backup_report.ready,
    )
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps(
            {"manifest_version": 1, **asdict(report)},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return report


def restore_database(
    backup_path: str | Path,
    restored_path: str | Path,
    manifest_path: str | Path | None = None,
) -> DatabaseRestoreReport:
    """Restore into a new path and verify it against the backup manifest."""

    backup = Path(backup_path).resolve()
    restored = Path(restored_path).resolve()
    manifest = (
        Path(manifest_path).resolve()
        if manifest_path is not None
        else _default_manifest_path(backup)
    )
    if not backup.is_file():
        raise FileNotFoundError(f"備份資料庫不存在：{backup}")
    if not manifest.is_file():
        raise FileNotFoundError(f"備份清單不存在：{manifest}")
    if backup == restored:
        raise ValueError("備份與還原目的地不得相同")
    if manifest in {backup, restored}:
        raise ValueError("備份清單不得與備份或還原資料庫使用相同路徑")
    if restored.exists():
        raise FileExistsError(f"還原目的地已存在：{restored}")
    metadata = json.loads(manifest.read_text(encoding="utf-8"))
    if metadata.get("manifest_version") != 1:
        raise ValueError("不支援的備份清單版本")
    expected_hash = str(metadata.get("sha256", ""))
    if not expected_hash or _sha256(backup) != expected_hash:
        raise RuntimeError("備份 SHA-256 與清單不一致")
    if backup.stat().st_size != int(metadata.get("size_bytes", -1)):
        raise RuntimeError("備份檔案大小與清單不一致")
    _sqlite_backup(backup, restored)
    restored_report = verify_database_schema(restored)
    expected_counts = {
        str(table): int(count)
        for table, count in dict(metadata.get("row_counts", {})).items()
    }
    counts_verified = restored_report.row_counts == expected_counts
    schema_verified = restored_report.ready == bool(metadata.get("schema_ready"))
    if (
        restored_report.integrity_check != "ok"
        or restored_report.foreign_key_violation_count
        or not counts_verified
        or not schema_verified
    ):
        raise RuntimeError("還原資料庫未通過完整性、外鍵、結構或資料列數驗證")
    return DatabaseRestoreReport(
        backup_path=str(backup),
        restored_path=str(restored),
        manifest_path=str(manifest),
        sha256_verified=True,
        row_counts_verified=True,
        integrity_check=restored_report.integrity_check,
        foreign_key_violation_count=restored_report.foreign_key_violation_count,
        schema_ready=restored_report.ready,
    )


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
    backup = subparsers.add_parser("backup")
    backup.add_argument("--source", required=True, type=Path)
    backup.add_argument("--backup", required=True, type=Path)
    backup.add_argument("--manifest", type=Path)
    restore = subparsers.add_parser("restore")
    restore.add_argument("--backup", required=True, type=Path)
    restore.add_argument("--restored", required=True, type=Path)
    restore.add_argument("--manifest", type=Path)
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
    elif args.command == "backup":
        report = backup_database(args.source, args.backup, args.manifest)
    elif args.command == "restore":
        report = restore_database(args.backup, args.restored, args.manifest)
    else:
        report = rehearse_database_migration(args.source, args.rehearsal)
    print(json.dumps(asdict(report), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
