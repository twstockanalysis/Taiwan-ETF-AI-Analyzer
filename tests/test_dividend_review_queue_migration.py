"""正式配息審核佇列 Migration 測試。"""

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
from backend.app.database.migrate_dividend_review_queue import (
    migrate_dividend_review_queue,
    review_queue_table_exists,
)


class TestDividendReviewQueueMigration(
    unittest.TestCase
):
    """驗證審核佇列表與唯一性。"""

    def setUp(self) -> None:
        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.database_path = (
            Path(self.temp_directory.name)
            / "review_queue.db"
        )

        initialize_database(
            self.database_path
        )

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_table_exists_and_migration_is_idempotent(
        self,
    ) -> None:
        """初始化後資料表存在且可重複 Migration。"""

        self.assertTrue(
            review_queue_table_exists(
                self.database_path
            )
        )

        self.assertFalse(
            migrate_dividend_review_queue(
                self.database_path
            )
        )

    def test_unique_event_and_issue_type(
        self,
    ) -> None:
        """同一事件不允許重複相同缺失類型。"""

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
                    "00878",
                    "國泰永續高股息",
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
                    amount_per_unit,
                    currency,
                    source_id
                )
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    "00878",
                    "event-1",
                    "2026-08-18",
                    0.4,
                    "TWD",
                    "official",
                ),
            )

            dividend_id = int(
                cursor.lastrowid
            )

            connection.execute(
                """
                INSERT INTO
                dividend_source_review_queue (
                    dividend_id,
                    issue_type,
                    last_evaluated_at
                )
                VALUES (?, ?, ?);
                """,
                (
                    dividend_id,
                    "MISSING_ACTUAL_COMPONENTS",
                    "2026-07-31T00:00:00+00:00",
                ),
            )

            with self.assertRaises(
                sqlite3.IntegrityError
            ):
                connection.execute(
                    """
                    INSERT INTO
                    dividend_source_review_queue (
                        dividend_id,
                        issue_type,
                        last_evaluated_at
                    )
                    VALUES (?, ?, ?);
                    """,
                    (
                        dividend_id,
                        "MISSING_ACTUAL_COMPONENTS",
                        "2026-07-31T00:00:00+00:00",
                    ),
                )

        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
