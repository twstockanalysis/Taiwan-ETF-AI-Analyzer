"""測試 M12-1 部署資料庫初始化、驗證與無損演練。"""

from pathlib import Path
import sqlite3
import tempfile
import unittest

from backend.app.database.deployment_readiness import (
    initialize_deployment_database,
    rehearse_database_migration,
    verify_database_schema,
)


class TestDeploymentDatabaseReadiness(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_directory.name)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_initialize_creates_verified_current_schema(self) -> None:
        database = self.root / "deployment.db"

        report = initialize_deployment_database(database)

        self.assertTrue(report.ready)
        self.assertEqual(report.integrity_check, "ok")
        self.assertEqual(report.foreign_key_violation_count, 0)
        self.assertEqual(report.missing_tables, [])
        self.assertEqual(report.missing_columns, {})

    def test_verify_is_read_only_and_reports_legacy_gaps(self) -> None:
        database = self.root / "legacy.db"
        connection = sqlite3.connect(database)
        try:
            connection.execute(
                "CREATE TABLE etf_master (code TEXT PRIMARY KEY, name TEXT);"
            )
            connection.execute(
                "INSERT INTO etf_master (code, name) VALUES ('0056', 'sample');"
            )
            connection.commit()
        finally:
            connection.close()

        report = verify_database_schema(database)

        self.assertFalse(report.ready)
        self.assertIn("etf_daily_close", report.missing_tables)
        self.assertEqual(report.row_counts["etf_master"], 1)
        connection = sqlite3.connect(database)
        try:
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM sqlite_master WHERE type='table';"
                ).fetchone()[0],
                1,
            )
        finally:
            connection.close()

    def test_rehearsal_uses_copy_and_preserves_existing_rows(self) -> None:
        source = self.root / "source.db"
        rehearsal = self.root / "rehearsal.db"
        initialize_deployment_database(source)
        connection = sqlite3.connect(source)
        try:
            connection.execute(
                """
                INSERT INTO etf_master (code, name, is_active, is_bond)
                VALUES ('0056', '元大高股息', 0, 0);
                """
            )
            connection.commit()
        finally:
            connection.close()

        report = rehearse_database_migration(source, rehearsal)

        self.assertTrue(report.readiness.ready)
        self.assertEqual(report.source_row_counts["etf_master"], 1)
        self.assertEqual(report.upgraded_row_counts["etf_master"], 1)
        source_connection = sqlite3.connect(source)
        try:
            self.assertEqual(
                source_connection.execute(
                    "SELECT COUNT(*) FROM etf_master;"
                ).fetchone()[0],
                1,
            )
        finally:
            source_connection.close()

    def test_rehearsal_refuses_source_as_destination_or_overwrite(self) -> None:
        source = self.root / "source.db"
        initialize_deployment_database(source)
        with self.assertRaises(ValueError):
            rehearse_database_migration(source, source)
        destination = self.root / "existing.db"
        destination.touch()
        with self.assertRaises(FileExistsError):
            rehearse_database_migration(source, destination)


if __name__ == "__main__":
    unittest.main()
