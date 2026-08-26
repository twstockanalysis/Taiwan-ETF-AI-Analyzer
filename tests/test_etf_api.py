"""ETF 查詢 API 自動化測試。"""

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.api.dependencies import (
    get_database_path,
)
from backend.app.database.connection import (
    get_connection,
)
from backend.app.database.init_db import (
    initialize_database,
)
from backend.app.main import create_app


class TestETFAPI(unittest.TestCase):
    """測試 ETF 列表及單筆查詢 API。"""

    def setUp(self) -> None:
        """建立獨立臨時資料庫及測試應用程式。"""

        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.database_path = (
            Path(self.temp_directory.name)
            / "test_etf_api.db"
        )

        initialize_database(
            self.database_path
        )

        self.insert_test_data()

        self.application = create_app()

        self.application.dependency_overrides[
            get_database_path
        ] = lambda: self.database_path

        self.client = TestClient(
            self.application
        )

    def tearDown(self) -> None:
        """關閉測試用戶端並刪除臨時資料庫。"""

        self.client.close()

        self.application.dependency_overrides = {}

        self.temp_directory.cleanup()

    def insert_test_data(self) -> None:
        """寫入 ETF 測試資料。"""

        connection = get_connection(
            self.database_path
        )

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
                        "被動式股票測試ETF",
                        0,
                        0,
                        "2022-01-01",
                        100.0,
                        0.50,
                    ),
                    (
                        "TEST002A",
                        "主動式股票測試ETF",
                        1,
                        0,
                        "2025-01-01",
                        50.0,
                        0.80,
                    ),
                    (
                        "TEST003B",
                        "被動式債券測試ETF",
                        0,
                        1,
                        "2023-01-01",
                        80.0,
                        0.40,
                    ),
                ],
            )

            connection.commit()

        finally:
            connection.close()

    def test_list_etfs_returns_paginated_response(
        self,
    ) -> None:
        """確認列表 API 回傳分頁格式。"""

        response = self.client.get(
            "/api/v1/etfs"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            data["total"],
            3,
        )
        self.assertEqual(
            data["limit"],
            20,
        )
        self.assertEqual(
            data["offset"],
            0,
        )
        self.assertEqual(
            len(data["items"]),
            3,
        )

    def test_historical_quality_grades_are_public_safe_and_ordered(self) -> None:
        response = self.client.get(
            "/api/v1/etfs/historical-quality-grades",
            params={"codes": "TEST002A,TEST001"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(
            [item["etf_code"] for item in payload["items"]],
            ["TEST002A", "TEST001"],
        )
        self.assertTrue(
            all(
                item["historical_quality_grade"]["status"] == "UNRATED"
                for item in payload["items"]
            )
        )
        serialized = response.text.lower()
        self.assertNotIn("quality_score", serialized)
        self.assertNotIn("confidence", serialized)

    def test_historical_quality_grades_reject_unknown_code(self) -> None:
        response = self.client.get(
            "/api/v1/etfs/historical-quality-grades",
            params={"codes": "UNKNOWN"},
        )

        self.assertEqual(response.status_code, 404)

    def test_list_etfs_converts_boolean_values(
        self,
    ) -> None:
        """確認整數正確轉換為 JSON 布林值。"""

        response = self.client.get(
            "/api/v1/etfs"
        )

        items = response.json()["items"]

        self.assertFalse(
            items[0]["is_active"]
        )
        self.assertTrue(
            items[1]["is_active"]
        )
        self.assertTrue(
            items[2]["is_bond"]
        )

    def test_list_etfs_supports_pagination(
        self,
    ) -> None:
        """確認 limit 與 offset 分頁功能。"""

        response = self.client.get(
            "/api/v1/etfs",
            params={
                "limit": 1,
                "offset": 1,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            data["total"],
            3,
        )
        self.assertEqual(
            len(data["items"]),
            1,
        )
        self.assertEqual(
            data["items"][0]["code"],
            "TEST002A",
        )

    def test_list_etfs_supports_keyword_filter(
        self,
    ) -> None:
        """確認可以搜尋 ETF 代號或名稱。"""

        response = self.client.get(
            "/api/v1/etfs",
            params={
                "keyword": "主動式",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            data["total"],
            1,
        )
        self.assertEqual(
            data["items"][0]["code"],
            "TEST002A",
        )

    def test_list_etfs_supports_active_filter(
        self,
    ) -> None:
        """確認可以篩選主動式 ETF。"""

        response = self.client.get(
            "/api/v1/etfs",
            params={
                "is_active": "true",
            },
        )

        data = response.json()

        self.assertEqual(
            data["total"],
            1,
        )
        self.assertEqual(
            data["items"][0]["code"],
            "TEST002A",
        )

    def test_list_etfs_supports_bond_filter(
        self,
    ) -> None:
        """確認可以篩選債券 ETF。"""

        response = self.client.get(
            "/api/v1/etfs",
            params={
                "is_bond": "true",
            },
        )

        data = response.json()

        self.assertEqual(
            data["total"],
            1,
        )
        self.assertEqual(
            data["items"][0]["code"],
            "TEST003B",
        )

    def test_invalid_limit_returns_422(
        self,
    ) -> None:
        """確認不合法 limit 會被拒絕。"""

        response = self.client.get(
            "/api/v1/etfs",
            params={
                "limit": 0,
            },
        )

        self.assertEqual(
            response.status_code,
            422,
        )

    def test_get_etf_by_code(self) -> None:
        """確認可以依代號取得單筆 ETF。"""

        response = self.client.get(
            "/api/v1/etfs/TEST001"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            data["code"],
            "TEST001",
        )
        self.assertEqual(
            data["name"],
            "被動式股票測試ETF",
        )
        self.assertEqual(
            data["listing_date"],
            "2022-01-01",
        )

    def test_etf_code_is_case_insensitive(
        self,
    ) -> None:
        """確認小寫 ETF 代號也能查詢。"""

        response = self.client.get(
            "/api/v1/etfs/test002a"
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            response.json()["code"],
            "TEST002A",
        )

    def test_missing_etf_returns_404(
        self,
    ) -> None:
        """確認找不到 ETF 時回傳 404。"""

        response = self.client.get(
            "/api/v1/etfs/UNKNOWN"
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertEqual(
            response.json(),
            {
                "detail": "找不到 ETF：UNKNOWN",
            },
        )


if __name__ == "__main__":
    unittest.main()
