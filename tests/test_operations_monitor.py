"""Tests for M12-3 operational monitoring."""

from datetime import datetime, timezone
import json
from pathlib import Path
from shutil import _ntuple_diskusage
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from backend.app.database.deployment_readiness import (
    backup_database,
    initialize_deployment_database,
)
from backend.app.operations.monitor import (
    build_operations_report,
    check_backup_age,
    check_data_freshness,
    check_import_batches,
    check_restore_drill,
    check_scheduled_run,
    check_storage,
)


NOW = datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc)


class TestOperationsMonitor(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_directory.name)
        self.database = self.root / "database.db"
        initialize_deployment_database(self.database)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def _insert_success(self, completed_at: str = "2026-08-12T08:00:00+00:00") -> None:
        connection = sqlite3.connect(self.database)
        try:
            connection.execute(
                """INSERT INTO import_batch
                   (pipeline_name, source_id, endpoint_id, started_at,
                    completed_at, status)
                   VALUES ('etf_master_pipeline', 'source', 'endpoint', ?, ?, 'success');""",
                (completed_at, completed_at),
            )
            connection.execute(
                """INSERT INTO etf_master (code, name, is_active, is_bond)
                   VALUES ('0056', '元大高股息', 1, 0);"""
            )
            connection.execute(
                """INSERT INTO etf_performance
                   (etf_code, as_of_date, period_code, metric_code, return_pct,
                    source_id)
                   VALUES ('0056', '2026-08-12', '1Y', 'PRICE_RETURN', 1,
                           'source');"""
            )
            connection.commit()
        finally:
            connection.close()

    def test_pipeline_and_freshness_checks_detect_success(self) -> None:
        self._insert_success()

        pipeline = check_import_batches(self.database, 6, NOW)
        freshness = check_data_freshness(self.database, 168, NOW)

        self.assertEqual(pipeline.status, "ok")
        self.assertEqual(freshness.status, "ok")
        self.assertIn("performance_data", freshness.details["observations"])

    def test_failed_and_stale_running_batches_are_critical(self) -> None:
        connection = sqlite3.connect(self.database)
        try:
            connection.executemany(
                """INSERT INTO import_batch
                   (pipeline_name, source_id, endpoint_id, started_at,
                    completed_at, status, error_message)
                   VALUES (?, 'source', 'endpoint', ?, ?, ?, ?);""",
                [
                    ("failed_pipeline", "2026-08-12T10:00:00+00:00", "2026-08-12T10:01:00+00:00", "failed", "network"),
                    ("stuck_pipeline", "2026-08-11T00:00:00+00:00", None, "running", None),
                ],
            )
            connection.commit()
        finally:
            connection.close()

        result = check_import_batches(self.database, 6, NOW)

        self.assertEqual(result.status, "critical")
        self.assertEqual(len(result.details["failed"]), 1)
        self.assertEqual(len(result.details["stale_running"]), 1)

    def test_backup_and_restore_drill_age_checks(self) -> None:
        backup_directory = self.root / "backups"
        backup = backup_directory / "current.db"
        backup_database(self.database, backup)
        manifest = Path(f"{backup}.manifest.json")
        data = json.loads(manifest.read_text(encoding="utf-8"))
        data["created_at"] = "2026-08-12T08:00:00+00:00"
        manifest.write_text(json.dumps(data), encoding="utf-8")
        drill = self.root / "restore-drill.json"
        drill.write_text(
            json.dumps({"completed_at": "2026-08-01T00:00:00+00:00", "passed": True}),
            encoding="utf-8",
        )

        self.assertEqual(check_backup_age(backup_directory, 30, NOW).status, "ok")
        self.assertEqual(check_restore_drill(drill, 35, NOW).status, "ok")
        self.assertEqual(check_backup_age(backup_directory, 1, NOW).status, "critical")

    @patch("backend.app.operations.monitor.shutil.disk_usage")
    def test_storage_threshold(self, disk_usage) -> None:
        disk_usage.return_value = _ntuple_diskusage(10_000, 9_000, 1_000)
        result = check_storage(self.database, minimum_free_gib=1, now=NOW)
        self.assertEqual(result.status, "critical")

    def test_combined_report_is_critical_when_operational_evidence_missing(self) -> None:
        report = build_operations_report(
            database_path=self.database,
            backup_directory=self.root / "missing-backups",
            restore_drill_state=self.root / "missing-drill.json",
            scheduled_run_state=self.root / "missing-run.json",
            minimum_free_gib=0,
            now=NOW,
        )
        self.assertEqual(report.status, "critical")
        self.assertEqual(
            {item.name for item in report.checks},
            {"database", "storage", "pipelines", "data_freshness", "scheduled_run", "backup_age", "restore_drill"},
        )

    def test_missing_database_returns_report_instead_of_creating_file(self) -> None:
        missing = self.root / "missing.db"
        report = build_operations_report(
            database_path=missing,
            backup_directory=self.root / "backups",
            restore_drill_state=self.root / "drill.json",
            scheduled_run_state=self.root / "run.json",
            minimum_free_gib=0,
            now=NOW,
        )
        self.assertEqual(report.status, "critical")
        self.assertFalse(missing.exists())
        self.assertEqual(
            next(item for item in report.checks if item.name == "pipelines").status,
            "critical",
        )

    def test_scheduled_run_must_be_recent_and_successful(self) -> None:
        state = self.root / "latest-run.json"
        state.write_text(json.dumps({
            "status": "success",
            "completed_at": "2026-08-12T08:00:00+00:00",
            "jobs": [],
        }), encoding="utf-8")
        self.assertEqual(check_scheduled_run(state, 30, NOW).status, "ok")
        state.write_text(json.dumps({
            "status": "failed",
            "completed_at": "2026-08-12T08:00:00+00:00",
            "jobs": [],
        }), encoding="utf-8")
        self.assertEqual(check_scheduled_run(state, 30, NOW).status, "critical")


if __name__ == "__main__":
    unittest.main()
