"""SQLite 資料庫自動化測試。"""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from backend.app.database.connection import get_connection
from backend.app.database.init_db import initialize_database


class TestDatabase(unittest.TestCase):
    """測試資料庫連線、Schema 與資料約束。"""

    def setUp(self) -> None:
        """每個測試執行前建立獨立的臨時資料庫。"""

        self.temp_directory = tempfile.TemporaryDirectory()

        self.database_path = (
            Path(self.temp_directory.name)
            / "test_tw_etf.db"
        )

        initialize_database(self.database_path)

        self.connection = get_connection(
            self.database_path
        )

    def tearDown(self) -> None:
        """每個測試結束後關閉並刪除臨時資料庫。"""

        self.connection.close()
        self.temp_directory.cleanup()

    def insert_etf(
        self,
        code: str = "00918",
        name: str = "大華優利高填息30",
        is_active: int = 0,
        is_bond: int = 0,
        listing_date: str = "2022-11-24",
        fund_size: float = 100.0,
        expense_ratio: float = 0.50,
    ) -> None:
        """寫入一筆測試 ETF 資料。"""

        self.connection.execute(
            """
            INSERT INTO etf_master (
                code,
                name,
                is_active,
                is_bond,
                listing_date,
                fund_size,
                expense_ratio
            )
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                code,
                name,
                is_active,
                is_bond,
                listing_date,
                fund_size,
                expense_ratio,
            ),
        )

        self.connection.commit()

    def test_etf_master_table_exists(self) -> None:
        """確認 etf_master 資料表存在。"""

        result = self.connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'etf_master';
            """
        ).fetchone()

        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "etf_master")

    def test_etf_master_has_expected_columns(self) -> None:
        """確認 etf_master 包含預定欄位。"""

        results = self.connection.execute(
            "PRAGMA table_info(etf_master);"
        ).fetchall()

        actual_columns = {
            result["name"]
            for result in results
        }

        expected_columns = {
            "code",
            "name",
            "is_active",
            "is_bond",
            "listing_date",
            "fund_size",
            "expense_ratio",
        }

        self.assertEqual(
            actual_columns,
            expected_columns,
        )

    def test_foreign_keys_are_enabled(self) -> None:
        """確認 SQLite 外鍵約束已啟用。"""

        result = self.connection.execute(
            "PRAGMA foreign_keys;"
        ).fetchone()

        self.assertEqual(result[0], 1)

    def test_valid_etf_can_be_inserted(self) -> None:
        """確認合法 ETF 資料可以正常寫入。"""

        self.insert_etf()

        result = self.connection.execute(
            """
            SELECT *
            FROM etf_master
            WHERE code = ?;
            """,
            ("00918",),
        ).fetchone()

        self.assertIsNotNone(result)
        self.assertEqual(result["code"], "00918")
        self.assertEqual(result["is_active"], 0)
        self.assertEqual(result["is_bond"], 0)

    def test_duplicate_code_is_rejected(self) -> None:
        """確認 ETF 代號不可重複。"""

        self.insert_etf()

        with self.assertRaises(
            sqlite3.IntegrityError
        ):
            self.insert_etf()

        self.connection.rollback()

    def test_invalid_boolean_is_rejected(self) -> None:
        """確認布林欄位只能使用 0 或 1。"""

        with self.assertRaises(
            sqlite3.IntegrityError
        ):
            self.insert_etf(
                code="00980A",
                name="主動野村臺灣優選",
                is_active=2,
            )

        self.connection.rollback()

    def test_negative_fund_size_is_rejected(self) -> None:
        """確認基金規模不可為負數。"""

        with self.assertRaises(
            sqlite3.IntegrityError
        ):
            self.insert_etf(
                code="00919",
                name="群益台灣精選高息",
                fund_size=-1.0,
            )

        self.connection.rollback()


if __name__ == "__main__":
    unittest.main()