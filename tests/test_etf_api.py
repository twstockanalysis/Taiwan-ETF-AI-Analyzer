"""ETF 查詢 API 自動化測試。"""

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.api.dependencies import get_database_path
from backend.app.database.connection import get_connection
from backend.app.database.init_db import initialize_database
from backend.app.main import create_app


class TestETFAPI(unittest.TestCase):
    """測試 ETF 列表及單筆查詢 API。"""

    def setUp(self) -> None:
        """每個測試建立獨立的臨時資料庫與應用程式。"""

        self.temp_directory = tempfile.TemporaryDirectory()

        self.database_path = (
            Path(self.temp_directory.name)
            / "test_etf_api.db"
        )

        initialize_database(self.database_path)
        self.insert_test_data()

        self.application = create_app()

        self.application.dependency_overrides[
            get_database_path
        ] = lambda: self.database_path

        self.client = TestClient(self.application)

    def tearDown(self) -> None:
        """關閉測試用戶端並刪除臨時資料庫。"""

        self.client.close()
        self.application.dependency_overrides = {}
        self.temp_directory.cleanup()

    def insert_test_data(self) -> None:
        """在臨時資料庫寫入 ETF 測試資料。"""

        connection = get_connection(self.database_path)

        try:
            connection.executemany(
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
                [
                    (
                        "TEST001",
                        "被動式測試ETF",
                        0,
                        0,
                        "2022-01-01",
                        100.0,
                        0.50,
                    ),
                    (
                        "TEST002A",
                        "主動式測試ETF",
                        1,
                        0,
                        "2025-01-01",
                        50.0,
                        0.80,
                    ),
                ],
            )

            connection.commit()

        finally:
            connection.close()

    def test_list_etfs_returns_all_records(self) -> None:
        """確認 ETF 列表 API 回傳所有資料。"""

        response = self.client.get(
            "/api/v1/etfs"
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(len(data), 2)

        self.assertEqual(
            [item["code"] for item in data],
            ["TEST001", "TEST002A"],
        )

    def test_list_etfs_converts_boolean_values(self) -> None:
        """確認 SQLite 整數轉換成 JSON 布林值。"""

        response = self.client.get(
            "/api/v1/etfs"
        )

        data = response.json()

        self.assertFalse(data[0]["is_active"])
        self.assertTrue(data[1]["is_active"])

    def test_get_etf_by_code(self) -> None:
        """確認可以依 ETF 代號查詢單筆資料。"""

        response = self.client.get(
            "/api/v1/etfs/TEST001"
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data["code"], "TEST001")
        self.assertEqual(
            data["name"],
            "被動式測試ETF",
        )
        self.assertEqual(
            data["listing_date"],
            "2022-01-01",
        )

    def test_etf_code_is_case_insensitive(self) -> None:
        """確認小寫 ETF 代號也可以查詢。"""

        response = self.client.get(
            "/api/v1/etfs/test002a"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["code"],
            "TEST002A",
        )

    def test_missing_etf_returns_404(self) -> None:
        """確認找不到 ETF 時回傳 HTTP 404。"""

        response = self.client.get(
            "/api/v1/etfs/UNKNOWN"
        )

        self.assertEqual(response.status_code, 404)

        self.assertEqual(
            response.json(),
            {
                "detail": "找不到 ETF：UNKNOWN",
            },
        )


if __name__ == "__main__":
    unittest.main()