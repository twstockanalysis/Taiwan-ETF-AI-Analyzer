"""ETF dividend component-basis Migration tests."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from backend.app.database.connection import (
    get_connection,
)
from backend.app.database.init_db import (
    initialize_database,
)
from backend.app.database.migrate_dividend_component_basis import (
    migrate_dividend_component_basis,
)


OLD_SCHEMA_SQL = """
CREATE TABLE etf_master (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 0,
    is_bond INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE import_batch (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_name TEXT NOT NULL,
    source_id TEXT NOT NULL,
    endpoint_id TEXT NOT NULL,
    started_at TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE etf_dividend (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    etf_code TEXT NOT NULL,
    source_event_id TEXT NOT NULL,
    announcement_date TEXT,
    ex_dividend_date TEXT,
    record_date TEXT,
    payment_date TEXT,
    amount_per_unit REAL NOT NULL,
    currency TEXT NOT NULL DEFAULT 'TWD',
    source_id TEXT NOT NULL,
    import_batch_id INTEGER,
    source_updated_at TEXT,
    created_at TEXT NOT NULL
        DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL
        DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (etf_code)
        REFERENCES etf_master (code),
    UNIQUE (
        source_id,
        source_event_id
    )
);

CREATE TABLE etf_dividend_component (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dividend_id INTEGER NOT NULL,
    component_code TEXT NOT NULL,
    component_name TEXT,
    amount_per_unit REAL,
    ratio_pct REAL,
    source_id TEXT NOT NULL,
    import_batch_id INTEGER,
    source_updated_at TEXT,
    created_at TEXT NOT NULL
        DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL
        DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dividend_id)
        REFERENCES etf_dividend (id)
        ON DELETE CASCADE,
    UNIQUE (
        dividend_id,
        component_code
    )
);
"""


class TestDividendComponentMigration(
    unittest.TestCase
):
    """Test legacy dividend-component migration."""

    def setUp(self) -> None:
        """Create one legacy database."""

        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.database_path = (
            Path(self.temp_directory.name)
            / "dividend_migration.db"
        )

        connection = sqlite3.connect(
            self.database_path
        )

        try:
            connection.executescript(
                OLD_SCHEMA_SQL
            )

            connection.execute(
                """
                INSERT INTO etf_master (
                    code,
                    name,
                    is_active,
                    is_bond
                )
                VALUES (?, ?, ?, ?);
                """,
                (
                    "00918",
                    "大華優利高填息30",
                    0,
                    0,
                ),
            )

            cursor = connection.execute(
                """
                INSERT INTO etf_dividend (
                    etf_code,
                    source_event_id,
                    ex_dividend_date,
                    payment_date,
                    amount_per_unit,
                    currency,
                    source_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    "00918",
                    "official:00918:2026-Q3",
                    "2026-09-15",
                    "2026-10-15",
                    0.70,
                    "TWD",
                    "official",
                ),
            )

            connection.execute(
                """
                INSERT INTO etf_dividend_component (
                    dividend_id,
                    component_code,
                    component_name,
                    ratio_pct,
                    source_id
                )
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    int(cursor.lastrowid),
                    "76W",
                    "舊版實際所得",
                    100.0,
                    "official",
                ),
            )

            connection.commit()

        finally:
            connection.close()

    def tearDown(self) -> None:
        """Remove the temporary database."""

        self.temp_directory.cleanup()

    def test_old_component_becomes_actual(
        self,
    ) -> None:
        """Legacy component rows become ACTUAL."""

        changed = (
            migrate_dividend_component_basis(
                self.database_path
            )
        )

        self.assertTrue(changed)

        connection = get_connection(
            self.database_path
        )

        try:
            row = connection.execute(
                """
                SELECT
                    component_code,
                    component_basis,
                    ratio_pct
                FROM etf_dividend_component;
                """
            ).fetchone()

            self.assertEqual(
                row["component_code"],
                "76W",
            )

            self.assertEqual(
                row["component_basis"],
                "ACTUAL",
            )

            self.assertEqual(
                row["ratio_pct"],
                100.0,
            )

        finally:
            connection.close()

    def test_new_unique_key_allows_basis_and_source(
        self,
    ) -> None:
        """Basis and source are part of uniqueness."""

        migrate_dividend_component_basis(
            self.database_path
        )

        connection = get_connection(
            self.database_path
        )

        try:
            dividend_id = connection.execute(
                """
                SELECT id
                FROM etf_dividend;
                """
            ).fetchone()["id"]

            connection.execute(
                """
                INSERT INTO etf_dividend_component (
                    dividend_id,
                    component_code,
                    component_basis,
                    ratio_pct,
                    source_id
                )
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    dividend_id,
                    "76W",
                    "ESTIMATED",
                    50.0,
                    "official",
                ),
            )

            connection.execute(
                """
                INSERT INTO etf_dividend_component (
                    dividend_id,
                    component_code,
                    component_basis,
                    ratio_pct,
                    source_id
                )
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    dividend_id,
                    "76W",
                    "ACTUAL",
                    99.0,
                    "second_notice",
                ),
            )

            connection.commit()

            count = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM etf_dividend_component;
                """
            ).fetchone()["total"]

            self.assertEqual(
                count,
                3,
            )

            with self.assertRaises(
                sqlite3.IntegrityError
            ):
                connection.execute(
                    """
                    INSERT INTO etf_dividend_component (
                        dividend_id,
                        component_code,
                        component_basis,
                        ratio_pct,
                        source_id
                    )
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (
                        dividend_id,
                        "76W",
                        "ACTUAL",
                        100.0,
                        "official",
                    ),
                )

            connection.rollback()

        finally:
            connection.close()

    def test_migration_is_idempotent(
        self,
    ) -> None:
        """Migration can be run repeatedly."""

        first_result = (
            migrate_dividend_component_basis(
                self.database_path
            )
        )

        second_result = (
            migrate_dividend_component_basis(
                self.database_path
            )
        )

        self.assertTrue(first_result)
        self.assertFalse(second_result)

    def test_initialize_database_upgrades_old_schema(
        self,
    ) -> None:
        """Normal initialization automatically migrates."""

        initialize_database(
            self.database_path
        )

        connection = get_connection(
            self.database_path
        )

        try:
            columns = connection.execute(
                """
                PRAGMA table_info(
                    etf_dividend_component
                );
                """
            ).fetchall()

            column_names = {
                row["name"]
                for row in columns
            }

            self.assertIn(
                "component_basis",
                column_names,
            )

            row = connection.execute(
                """
                SELECT component_basis
                FROM etf_dividend_component;
                """
            ).fetchone()

            self.assertEqual(
                row["component_basis"],
                "ACTUAL",
            )

        finally:
            connection.close()

    def test_new_database_has_current_schema(
        self,
    ) -> None:
        """Fresh databases include component_basis."""

        fresh_path = (
            Path(self.temp_directory.name)
            / "fresh.db"
        )

        initialize_database(
            fresh_path
        )

        connection = get_connection(
            fresh_path
        )

        try:
            columns = connection.execute(
                """
                PRAGMA table_info(
                    etf_dividend_component
                );
                """
            ).fetchall()

            column_names = {
                row["name"]
                for row in columns
            }

            self.assertIn(
                "component_basis",
                column_names,
            )

        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
