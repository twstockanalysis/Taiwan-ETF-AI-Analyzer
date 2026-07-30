"""ETF 績效查詢 API 自動化測試。"""

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


class TestPerformanceAPI(
    unittest.TestCase
):
    """測試績效排行榜與單一 ETF 績效 API。"""

    def setUp(self) -> None:
        """建立臨時資料庫及測試應用程式。"""

        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.database_path = (
            Path(self.temp_directory.name)
            / "test_performance_api.db"
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
        """關閉測試資源。"""

        self.client.close()

        self.application.dependency_overrides = {}

        self.temp_directory.cleanup()

    def insert_test_data(self) -> None:
        """寫入 ETF 及績效測試資料。"""

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
                    listing_date
                )
                VALUES (?, ?, ?, ?, ?);
                """,
                [
                    (
                        "TEST001",
                        "被動式股票測試ETF",
                        0,
                        0,
                        "2022-01-01",
                    ),
                    (
                        "TEST002A",
                        "主動式股票測試ETF",
                        1,
                        0,
                        "2025-01-01",
                    ),
                    (
                        "TEST003B",
                        "被動式債券測試ETF",
                        0,
                        1,
                        "2023-01-01",
                    ),
                    (
                        "TEST004",
                        "尚無績效測試ETF",
                        0,
                        0,
                        "2024-01-01",
                    ),
                ],
            )

            connection.executemany(
                """
                INSERT INTO etf_performance (
                    etf_code,
                    as_of_date,
                    period_code,
                    metric_code,
                    return_pct,
                    source_id
                )
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                [
                    (
                        "TEST001",
                        "2026-07-29",
                        "1M",
                        "PRICE_RETURN",
                        3.0,
                        "twse_stock_day",
                    ),
                    (
                        "TEST001",
                        "2026-07-29",
                        "3M",
                        "PRICE_RETURN",
                        5.0,
                        "twse_stock_day",
                    ),
                    (
                        "TEST001",
                        "2026-06-30",
                        "6M",
                        "PRICE_RETURN",
                        99.0,
                        "twse_stock_day",
                    ),
                    (
                        "TEST001",
                        "2026-07-29",
                        "6M",
                        "PRICE_RETURN",
                        10.0,
                        "twse_stock_day",
                    ),
                    (
                        "TEST001",
                        "2026-07-29",
                        "1Y",
                        "PRICE_RETURN",
                        20.0,
                        "twse_stock_day",
                    ),
                    (
                        "TEST001",
                        "2026-07-29",
                        "6M",
                        "TOTAL_RETURN",
                        30.0,
                        "twse_stock_day",
                    ),
                    (
                        "TEST002A",
                        "2026-07-29",
                        "1M",
                        "PRICE_RETURN",
                        8.0,
                        "twse_stock_day",
                    ),
                    (
                        "TEST002A",
                        "2026-07-29",
                        "3M",
                        "PRICE_RETURN",
                        12.0,
                        "twse_stock_day",
                    ),
                    (
                        "TEST002A",
                        "2026-07-29",
                        "6M",
                        "PRICE_RETURN",
                        15.0,
                        "twse_stock_day",
                    ),
                    (
                        "TEST002A",
                        "2026-07-29",
                        "1Y",
                        "PRICE_RETURN",
                        25.0,
                        "twse_stock_day",
                    ),
                    (
                        "TEST003B",
                        "2026-07-29",
                        "6M",
                        "PRICE_RETURN",
                        100.0,
                        "twse_stock_day",
                    ),
                ],
            )

            connection.commit()

        finally:
            connection.close()

    def test_ranking_defaults_to_six_months(
        self,
    ) -> None:
        """確認排行榜預設為六個月且排除債券。"""

        response = self.client.get(
            "/api/v1/performance/ranking"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            data["period_code"],
            "6M",
        )

        self.assertEqual(
            data["metric_code"],
            "PRICE_RETURN",
        )

        self.assertEqual(
            data["total"],
            2,
        )

        self.assertEqual(
            [
                item["etf_code"]
                for item in data["items"]
            ],
            [
                "TEST002A",
                "TEST001",
            ],
        )

        self.assertEqual(
            [
                item["rank"]
                for item in data["items"]
            ],
            [
                1,
                2,
            ],
        )

    def test_ranking_supports_period_filter(
        self,
    ) -> None:
        """確認排行榜可指定三個月期間。"""

        response = self.client.get(
            "/api/v1/performance/ranking",
            params={
                "period": "3M",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            data["period_code"],
            "3M",
        )

        self.assertTrue(
            all(
                item["period_code"]
                == "3M"
                for item in data["items"]
            )
        )

    def test_ranking_supports_active_filter(
        self,
    ) -> None:
        """確認排行榜可只顯示主動式 ETF。"""

        response = self.client.get(
            "/api/v1/performance/ranking",
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
            data["items"][0]["etf_code"],
            "TEST002A",
        )

    def test_ranking_supports_pagination(
        self,
    ) -> None:
        """確認排行榜分頁名次延續 offset。"""

        response = self.client.get(
            "/api/v1/performance/ranking",
            params={
                "limit": 1,
                "offset": 1,
            },
        )

        data = response.json()

        self.assertEqual(
            data["total"],
            2,
        )

        self.assertEqual(
            len(data["items"]),
            1,
        )

        self.assertEqual(
            data["items"][0]["rank"],
            2,
        )

        self.assertEqual(
            data["items"][0]["etf_code"],
            "TEST001",
        )

    def test_ranking_supports_metric_filter(
        self,
    ) -> None:
        """確認排行榜可指定總報酬類型。"""

        response = self.client.get(
            "/api/v1/performance/ranking",
            params={
                "metric": "TOTAL_RETURN",
            },
        )

        data = response.json()

        self.assertEqual(
            data["total"],
            1,
        )

        self.assertEqual(
            data["items"][0]["etf_code"],
            "TEST001",
        )

        self.assertEqual(
            data["items"][0]["return_pct"],
            30.0,
        )

    def test_unsupported_period_returns_422(
        self,
    ) -> None:
        """確認目前不支援的期間被拒絕。"""

        response = self.client.get(
            "/api/v1/performance/ranking",
            params={
                "period": "1W",
            },
        )

        self.assertEqual(
            response.status_code,
            422,
        )

    def test_etf_performance_returns_latest_periods(
        self,
    ) -> None:
        """確認單一 ETF 回傳各期間最新績效。"""

        response = self.client.get(
            "/api/v1/etfs/test001/performance"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            data["etf_code"],
            "TEST001",
        )

        self.assertEqual(
            [
                item["period_code"]
                for item in data["items"]
            ],
            [
                "1M",
                "3M",
                "6M",
                "1Y",
            ],
        )

        six_month_item = next(
            item
            for item in data["items"]
            if item["period_code"] == "6M"
        )

        self.assertEqual(
            six_month_item["return_pct"],
            10.0,
        )

    def test_existing_etf_without_performance_is_empty(
        self,
    ) -> None:
        """確認 ETF 存在但無績效時回傳空清單。"""

        response = self.client.get(
            "/api/v1/etfs/TEST004/performance"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.json()["items"],
            [],
        )

    def test_missing_etf_returns_404(
        self,
    ) -> None:
        """確認不存在的 ETF 回傳 404。"""

        response = self.client.get(
            "/api/v1/etfs/UNKNOWN/performance"
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

    def test_openapi_contains_performance_paths(
        self,
    ) -> None:
        """確認 OpenAPI 已登錄績效端點。"""

        paths = self.application.openapi()[
            "paths"
        ]

        self.assertIn(
            "/api/v1/performance/ranking",
            paths,
        )

        self.assertIn(
            "/api/v1/etfs/{code}/performance",
            paths,
        )


if __name__ == "__main__":
    unittest.main()
