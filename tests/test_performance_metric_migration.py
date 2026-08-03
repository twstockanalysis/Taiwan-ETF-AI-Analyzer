"""ETF 績效 metric_code Migration 測試。"""

import tempfile
import unittest
from pathlib import Path

from backend.app.database.connection import (
    get_connection,
)
from backend.app.database.init_db import (
    initialize_database,
)
from backend.app.database.migrate_performance_metric import (
    migrate_performance_metric,
)


class TestPerformanceMetricMigration(
    unittest.TestCase
):
    """測試舊績效資料庫升級。"""

    def setUp(self) -> None:
        """建立模擬舊版資料庫。"""

        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.database_path = (
            Path(self.temp_directory.name)
            / "migration.db"
        )

        initialize_database(
            self.database_path
        )

        connection = get_connection(
            self.database_path
        )

        try:
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
                    "0050",
                    "元大台灣50",
                    0,
                    0,
                ),
            )

            connection.execute(
                """
                DROP TABLE etf_performance;
                """
            )

            connection.execute(
                """
                CREATE TABLE etf_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    etf_code TEXT NOT NULL,
                    as_of_date TEXT NOT NULL,
                    period_code TEXT NOT NULL,
                    return_pct REAL NOT NULL,
                    source_id TEXT NOT NULL,
                    import_batch_id INTEGER,
                    source_updated_at TEXT,
                    created_at TEXT NOT NULL
                        DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL
                        DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (
                        etf_code,
                        as_of_date,
                        period_code,
                        source_id
                    )
                );
                """
            )

            connection.execute(
                """
                INSERT INTO etf_performance (
                    etf_code,
                    as_of_date,
                    period_code,
                    return_pct,
                    source_id
                )
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    "0050",
                    "2026-07-29",
                    "6M",
                    20.0,
                    "twse_stock_day",
                ),
            )

            connection.commit()

        finally:
            connection.close()

    def tearDown(self) -> None:
        """刪除臨時資料庫。"""

        self.temp_directory.cleanup()

    def test_old_record_becomes_price_return(
        self,
    ) -> None:
        """確認舊資料轉為 PRICE_RETURN。"""

        changed = migrate_performance_metric(
            self.database_path
        )

        self.assertTrue(changed)

        connection = get_connection(
            self.database_path
        )

        try:
            row = connection.execute(
                """
                SELECT
                    metric_code,
                    return_pct
                FROM etf_performance;
                """
            ).fetchone()

            self.assertEqual(
                row["metric_code"],
                "PRICE_RETURN",
            )

            self.assertEqual(
                row["return_pct"],
                20.0,
            )

        finally:
            connection.close()

    def test_migration_is_idempotent(
        self,
    ) -> None:
        """確認 Migration 可重複執行。"""

        first_result = (
            migrate_performance_metric(
                self.database_path
            )
        )

        second_result = (
            migrate_performance_metric(
                self.database_path
            )
        )

        self.assertTrue(first_result)
        self.assertFalse(second_result)

    def test_initialize_database_upgrades_old_schema(
        self,
    ) -> None:
        """一般初始化也必須自動升級舊績效表。"""

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
                    etf_performance
                );
                """
            ).fetchall()

            column_names = {
                row["name"]
                for row in columns
            }

            self.assertIn(
                "metric_code",
                column_names,
            )

            row = connection.execute(
                """
                SELECT
                    metric_code,
                    return_pct
                FROM etf_performance;
                """
            ).fetchone()

            self.assertEqual(
                row["metric_code"],
                "PRICE_RETURN",
            )

            self.assertEqual(
                row["return_pct"],
                20.0,
            )

        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
