"""M12-3 machine-readable operational readiness checks."""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.database.deployment_readiness import verify_database_schema


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    message: str
    observed_at: str
    details: dict[str, Any]


@dataclass(frozen=True)
class OperationsReport:
    status: str
    generated_at: str
    checks: list[CheckResult]


def _now(value: datetime | None = None) -> datetime:
    return value or datetime.now(timezone.utc)


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _age_hours(value: str, now: datetime) -> float:
    return max(0.0, (now - _parse_time(value).astimezone(timezone.utc)).total_seconds() / 3600)


def _result(name: str, status: str, message: str, now: datetime, **details: Any) -> CheckResult:
    return CheckResult(name, status, message, now.isoformat(), details)


def check_database(database_path: str | Path, now: datetime | None = None) -> CheckResult:
    observed = _now(now)
    try:
        report = verify_database_schema(database_path)
    except Exception as error:
        return _result("database", "critical", str(error), observed)
    status = "ok" if report.ready else "critical"
    return _result(
        "database", status, "資料庫可用" if report.ready else "資料庫未通過部署驗證",
        observed, path=report.database_path, integrity=report.integrity_check,
        foreign_key_violations=report.foreign_key_violation_count,
        missing_tables=report.missing_tables, missing_columns=report.missing_columns,
    )


def check_storage(database_path: str | Path, minimum_free_gib: float, now: datetime | None = None) -> CheckResult:
    observed = _now(now)
    target = Path(database_path).resolve()
    existing = target if target.exists() else target.parent
    while not existing.exists() and existing != existing.parent:
        existing = existing.parent
    free_bytes = shutil.disk_usage(existing).free
    minimum_bytes = int(minimum_free_gib * 1024**3)
    status = "ok" if free_bytes >= minimum_bytes else "critical"
    return _result("storage", status, "儲存空間充足" if status == "ok" else "可用空間低於門檻", observed,
                   free_bytes=free_bytes, minimum_free_bytes=minimum_bytes, checked_path=str(existing))


def check_import_batches(database_path: str | Path, stale_running_hours: float, now: datetime | None = None) -> CheckResult:
    observed = _now(now)
    try:
        connection = sqlite3.connect(
            f"file:{Path(database_path).resolve().as_posix()}?mode=ro", uri=True
        )
        connection.row_factory = sqlite3.Row
        try:
            latest = connection.execute(
                """SELECT pipeline_name, status, started_at, completed_at, error_message
                   FROM import_batch WHERE id IN
                   (SELECT MAX(id) FROM import_batch GROUP BY pipeline_name)
                   ORDER BY pipeline_name;"""
            ).fetchall()
        finally:
            connection.close()
    except sqlite3.Error as error:
        return _result("pipelines", "critical", "無法讀取管線批次", observed, error=str(error))
    failures = [dict(row) for row in latest if row["status"] == "failed"]
    stale = [dict(row) for row in latest if row["status"] == "running" and _age_hours(row["started_at"], observed) > stale_running_hours]
    status = "critical" if failures or stale else ("warning" if not latest else "ok")
    return _result("pipelines", status, "最近管線批次正常" if status == "ok" else "管線需要檢查", observed,
                   latest=[dict(row) for row in latest], failed=failures, stale_running=stale)


def check_data_freshness(database_path: str | Path, maximum_age_hours: float,
                         now: datetime | None = None) -> CheckResult:
    """Check source-dated performance data and successful ingestion activity."""

    observed = _now(now)
    try:
        connection = sqlite3.connect(
            f"file:{Path(database_path).resolve().as_posix()}?mode=ro", uri=True
        )
        connection.row_factory = sqlite3.Row
        try:
            performance_date = connection.execute(
                "SELECT MAX(as_of_date) FROM etf_performance;"
            ).fetchone()[0]
            rows = connection.execute(
                """SELECT pipeline_name, MAX(completed_at) AS completed_at
                   FROM import_batch WHERE status = 'success'
                   GROUP BY pipeline_name ORDER BY pipeline_name;"""
            ).fetchall()
        finally:
            connection.close()
    except sqlite3.Error as error:
        return _result("data_freshness", "critical", "無法讀取資料新鮮度", observed, error=str(error))
    observations: dict[str, str] = {
        str(row["pipeline_name"]): str(row["completed_at"])
        for row in rows if row["completed_at"]
    }
    if performance_date:
        observations["performance_data"] = f"{performance_date}T23:59:59+00:00"
    ages = {name: _age_hours(value, observed) for name, value in observations.items()}
    stale = {name: age for name, age in ages.items() if age > maximum_age_hours}
    status = "critical" if not observations or stale else "ok"
    return _result("data_freshness", status,
                   "資料新鮮度正常" if status == "ok" else "資料來源過期或沒有成功紀錄",
                   observed, observations=observations, ages_hours=ages,
                   stale=stale, maximum_age_hours=maximum_age_hours)


def check_backup_age(backup_directory: str | Path, maximum_age_hours: float, now: datetime | None = None) -> CheckResult:
    observed = _now(now)
    directory = Path(backup_directory).resolve()
    manifests = list(directory.glob("*.db.manifest.json")) if directory.is_dir() else []
    valid: list[tuple[datetime, Path, dict[str, Any]]] = []
    for path in manifests:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            valid.append((_parse_time(str(data["created_at"])), path, data))
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            continue
    if not valid:
        return _result("backup_age", "critical", "找不到有效備份清單", observed, directory=str(directory))
    created, manifest, data = max(valid, key=lambda item: item[0])
    age = max(0.0, (observed - created.astimezone(timezone.utc)).total_seconds() / 3600)
    artifact = Path(str(data.get("backup_path", "")))
    status = "ok" if age <= maximum_age_hours and artifact.is_file() else "critical"
    return _result("backup_age", status, "備份時效正常" if status == "ok" else "備份過期或檔案遺失", observed,
                   manifest=str(manifest), backup_path=str(artifact), age_hours=age,
                   maximum_age_hours=maximum_age_hours)


def check_restore_drill(state_path: str | Path, maximum_age_days: float, now: datetime | None = None) -> CheckResult:
    observed = _now(now)
    path = Path(state_path).resolve()
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
        age_days = _age_hours(str(state["completed_at"]), observed) / 24
        passed = bool(state["passed"])
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        return _result("restore_drill", "critical", "還原演練狀態無效或不存在", observed, path=str(path), error=str(error))
    status = "ok" if passed and age_days <= maximum_age_days else "critical"
    return _result("restore_drill", status, "還原演練有效" if status == "ok" else "還原演練失敗或過期", observed,
                   path=str(path), age_days=age_days, maximum_age_days=maximum_age_days, passed=passed)


def check_scheduled_run(state_path: str | Path, maximum_age_hours: float,
                        now: datetime | None = None) -> CheckResult:
    observed = _now(now)
    path = Path(state_path).resolve()
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
        age = _age_hours(str(state["completed_at"]), observed)
        succeeded = state["status"] == "success"
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        return _result("scheduled_run", "critical", "排程執行狀態無效或不存在", observed,
                       path=str(path), error=str(error))
    status = "ok" if succeeded and age <= maximum_age_hours else "critical"
    return _result("scheduled_run", status, "排程最近執行成功" if status == "ok" else "排程執行失敗或過期",
                   observed, path=str(path), age_hours=age,
                   maximum_age_hours=maximum_age_hours, run_status=state["status"])


def check_api(url: str, timeout_seconds: float, now: datetime | None = None) -> CheckResult:
    observed = _now(now)
    try:
        with urllib.request.urlopen(url, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
            healthy = response.status == 200 and payload.get("status") == "healthy"
    except Exception as error:
        return _result("api", "critical", "API 健康檢查失敗", observed, url=url, error=str(error))
    return _result("api", "ok" if healthy else "critical", "API 健康" if healthy else "API 回應不符合契約", observed,
                   url=url, http_status=response.status, payload=payload)


def build_operations_report(*, database_path: str | Path, backup_directory: str | Path,
                            restore_drill_state: str | Path, scheduled_run_state: str | Path,
                            api_url: str | None = None,
                            minimum_free_gib: float = 2.0, maximum_backup_age_hours: float = 30.0,
                            maximum_data_age_hours: float = 168.0,
                            maximum_restore_drill_age_days: float = 35.0,
                            maximum_scheduled_run_age_hours: float = 30.0,
                            stale_running_hours: float = 6.0, now: datetime | None = None) -> OperationsReport:
    observed = _now(now)
    checks = [check_database(database_path, observed), check_storage(database_path, minimum_free_gib, observed),
              check_import_batches(database_path, stale_running_hours, observed),
              check_data_freshness(database_path, maximum_data_age_hours, observed),
              check_scheduled_run(scheduled_run_state, maximum_scheduled_run_age_hours, observed),
              check_backup_age(backup_directory, maximum_backup_age_hours, observed),
              check_restore_drill(restore_drill_state, maximum_restore_drill_age_days, observed)]
    if api_url:
        checks.append(check_api(api_url, 10.0, observed))
    status = "critical" if any(item.status == "critical" for item in checks) else (
        "warning" if any(item.status == "warning" for item in checks) else "ok")
    return OperationsReport(status, observed.isoformat(), checks)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="M12-3 營運狀態檢查")
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--backup-directory", required=True, type=Path)
    parser.add_argument("--restore-drill-state", required=True, type=Path)
    parser.add_argument("--scheduled-run-state", required=True, type=Path)
    parser.add_argument("--api-url")
    parser.add_argument("--minimum-free-gib", type=float, default=2.0)
    parser.add_argument("--maximum-backup-age-hours", type=float, default=30.0)
    parser.add_argument("--maximum-data-age-hours", type=float, default=168.0)
    parser.add_argument("--maximum-restore-drill-age-days", type=float, default=35.0)
    parser.add_argument("--maximum-scheduled-run-age-hours", type=float, default=30.0)
    parser.add_argument("--stale-running-hours", type=float, default=6.0)
    parser.add_argument("--output", type=Path)
    return parser


def main() -> None:
    args = _parser().parse_args()
    report = build_operations_report(database_path=args.database, backup_directory=args.backup_directory,
        restore_drill_state=args.restore_drill_state, api_url=args.api_url,
        scheduled_run_state=args.scheduled_run_state,
        minimum_free_gib=args.minimum_free_gib, maximum_backup_age_hours=args.maximum_backup_age_hours,
        maximum_data_age_hours=args.maximum_data_age_hours,
        maximum_restore_drill_age_days=args.maximum_restore_drill_age_days,
        maximum_scheduled_run_age_hours=args.maximum_scheduled_run_age_hours,
        stale_running_hours=args.stale_running_hours)
    rendered = json.dumps(asdict(report), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_suffix(args.output.suffix + ".tmp")
        temporary.write_text(rendered, encoding="utf-8")
        temporary.replace(args.output)
    print(rendered, end="")
    if report.status == "critical":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
