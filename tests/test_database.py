"""Automated tests for the M5-2 SQLite schema."""

import sqlite3
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from collections.abc import Iterator
from unittest.mock import patch

from backend.app.database import connection, init_db


EXPECTED_COLUMNS = {
    "code": ("TEXT", 0, None, 1),
    "name": ("TEXT", 1, None, 0),
    "is_active": ("INTEGER", 1, "0", 0),
    "is_bond": ("INTEGER", 1, "0", 0),
    "listing_date": ("TEXT", 0, None, 0),
    "fund_size": ("REAL", 0, None, 0),
    "expense_ratio": ("REAL", 0, None, 0),
}


class DatabaseSchemaTests(unittest.TestCase):
    """Verify initialization, columns, indexes, and data constraints."""

    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_dir = Path(self.temp_directory.name) / "database"
        self.database_path = self.database_dir / "test_tw_etf.db"

        self.patches = (
            patch.object(connection, "DATABASE_DIR", self.database_dir),
            patch.object(connection, "DATABASE_PATH", self.database_path),
            patch.object(init_db, "DATABASE_PATH", self.database_path),
        )
        for current_patch in self.patches:
            current_patch.start()

        init_db.initialize_database()

    def tearDown(self) -> None:
        for current_patch in reversed(self.patches):
            current_patch.stop()
        self.temp_directory.cleanup()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        """Yield and then close a connection to the isolated database."""

        database = connection.get_connection()
        try:
            with database:
                yield database
        finally:
            database.close()

    def test_initialization_is_idempotent(self) -> None:
        """Repeated initialization preserves existing records."""

        with self.connect() as database:
            database.execute(
                "INSERT INTO etf_master (code, name) VALUES (?, ?)",
                ("0050", "Test ETF"),
            )

        init_db.initialize_database()

        with self.connect() as database:
            count = database.execute(
                "SELECT COUNT(*) FROM etf_master WHERE code = ?",
                ("0050",),
            ).fetchone()[0]

        self.assertEqual(count, 1)

    def test_etf_master_columns_match_schema(self) -> None:
        """The ETF master table exposes the documented seven columns."""

        with self.connect() as database:
            rows = database.execute("PRAGMA table_info(etf_master)").fetchall()

        actual_columns = {
            row["name"]: (row["type"], row["notnull"], row["dflt_value"], row["pk"])
            for row in rows
        }
        self.assertEqual(actual_columns, EXPECTED_COLUMNS)

    def test_name_lookup_index_exists(self) -> None:
        """The explicit ETF name index is created."""

        with self.connect() as database:
            indexes = database.execute("PRAGMA index_list(etf_master)").fetchall()

        self.assertIn("idx_etf_master_name", {row["name"] for row in indexes})

    def test_defaults_are_applied(self) -> None:
        """Boolean flags default to false."""

        with self.connect() as database:
            database.execute(
                "INSERT INTO etf_master (code, name) VALUES (?, ?)",
                ("0050", "Test ETF"),
            )
            row = database.execute(
                "SELECT is_active, is_bond FROM etf_master WHERE code = ?",
                ("0050",),
            ).fetchone()

        self.assertEqual((row["is_active"], row["is_bond"]), (0, 0))

    def test_primary_key_rejects_duplicate_codes(self) -> None:
        """ETF codes must be unique."""

        with self.connect() as database:
            database.execute(
                "INSERT INTO etf_master (code, name) VALUES (?, ?)",
                ("0050", "First ETF"),
            )
            with self.assertRaises(sqlite3.IntegrityError):
                database.execute(
                    "INSERT INTO etf_master (code, name) VALUES (?, ?)",
                    ("0050", "Duplicate ETF"),
                )

    def test_required_and_check_constraints_reject_invalid_data(self) -> None:
        """NOT NULL and CHECK constraints reject invalid values."""

        invalid_rows = (
            ("INSERT INTO etf_master (code, name) VALUES (?, NULL)", ("A",)),
            ("INSERT INTO etf_master (code, name, is_active) VALUES (?, ?, ?)", ("B", "ETF", 2)),
            ("INSERT INTO etf_master (code, name, is_bond) VALUES (?, ?, ?)", ("C", "ETF", -1)),
            ("INSERT INTO etf_master (code, name, fund_size) VALUES (?, ?, ?)", ("D", "ETF", -0.1)),
            ("INSERT INTO etf_master (code, name, expense_ratio) VALUES (?, ?, ?)", ("E", "ETF", 100.1)),
        )

        with self.connect() as database:
            for statement, parameters in invalid_rows:
                with self.subTest(statement=statement):
                    with self.assertRaises(sqlite3.IntegrityError):
                        database.execute(statement, parameters)

    def test_foreign_keys_are_enabled_per_connection(self) -> None:
        """Application connections enable SQLite foreign-key enforcement."""

        with self.connect() as database:
            enabled = database.execute("PRAGMA foreign_keys").fetchone()[0]

        self.assertEqual(enabled, 1)


if __name__ == "__main__":
    unittest.main()
