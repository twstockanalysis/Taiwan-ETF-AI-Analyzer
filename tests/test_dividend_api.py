"""ETF 配息查詢 API 自動化測試。"""

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


class TestDividendAPI(
    unittest.TestCase
):
    """測試配息歷史、組成與實際 76W API。"""

    def setUp(self) -> None:
        """建立臨時資料庫及測試應用程式。"""

        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.database_path = (
            Path(self.temp_directory.name)
            / "test_dividend_api.db"
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
        """寫入 ETF、配息事件及組成資料。"""

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
                    is_bond
                )
                VALUES (?, ?, ?, ?);
                """,
                [
                    (
                        "00918",
                        "大華優利高填息30",
                        0,
                        0,
                    ),
                    (
                        "0050",
                        "元大台灣50",
                        0,
                        0,
                    ),
                ],
            )

            connection.executemany(
                """
                INSERT INTO etf_dividend (
                    id,
                    etf_code,
                    source_event_id,
                    ex_dividend_date,
                    record_date,
                    payment_date,
                    amount_per_unit,
                    currency,
                    source_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                [
                    (
                        1,
                        "00918",
                        "official:00918:2026-03",
                        "2026-03-20",
                        "2026-03-26",
                        "2026-04-15",
                        0.50,
                        "TWD",
                        "official",
                    ),
                    (
                        2,
                        "00918",
                        "official:00918:2026-06",
                        "2026-06-18",
                        "2026-06-24",
                        "2026-07-10",
                        0.70,
                        "TWD",
                        "official",
                    ),
                    (
                        3,
                        "00918",
                        "official:00918:2026-09",
                        "2026-09-15",
                        "2026-09-21",
                        "2026-10-15",
                        0.80,
                        "TWD",
                        "official",
                    ),
                ],
            )

            connection.executemany(
                """
                INSERT INTO etf_dividend_component (
                    id,
                    dividend_id,
                    component_code,
                    component_basis,
                    component_name,
                    ratio_pct,
                    source_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                [
                    (
                        1,
                        1,
                        "EST_REALIZED_CAPITAL_GAIN",
                        "ESTIMATED",
                        "已實現資本利得",
                        100.0,
                        "twse_etfortune_dividend",
                    ),
                    (
                        2,
                        1,
                        "76W",
                        "ACTUAL",
                        "實際所得類別 76W",
                        80.0,
                        "official_distribution_notice",
                    ),
                    (
                        3,
                        2,
                        "EST_REALIZED_CAPITAL_GAIN",
                        "ESTIMATED",
                        "已實現資本利得",
                        90.0,
                        "twse_etfortune_dividend",
                    ),
                    (
                        4,
                        2,
                        "76W",
                        "ACTUAL",
                        "實際所得類別 76W",
                        100.0,
                        "official_distribution_notice",
                    ),
                ],
            )

            connection.commit()

        finally:
            connection.close()

    def test_etf_dividend_history_is_paginated(
        self,
    ) -> None:
        """確認配息歷史排序與分頁。"""

        response = self.client.get(
            "/api/v1/etfs/00918/dividends",
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
            data["limit"],
            1,
        )

        self.assertEqual(
            data["offset"],
            1,
        )

        self.assertEqual(
            len(data["items"]),
            1,
        )

        self.assertEqual(
            data["items"][0]["dividend_id"],
            2,
        )

    def test_existing_etf_without_dividends_is_empty(
        self,
    ) -> None:
        """確認 ETF 存在但沒有配息時回傳空清單。"""

        response = self.client.get(
            "/api/v1/etfs/0050/dividends"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            data["total"],
            0,
        )

        self.assertEqual(
            data["items"],
            [],
        )

    def test_missing_etf_returns_404(
        self,
    ) -> None:
        """確認不存在的 ETF 回傳 404。"""

        response = self.client.get(
            "/api/v1/etfs/UNKNOWN/dividends"
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

    def test_dividend_detail_contains_all_components(
        self,
    ) -> None:
        """確認單次配息回傳預估與實際組成。"""

        response = self.client.get(
            "/api/v1/dividends/2"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            data["dividend_id"],
            2,
        )

        self.assertEqual(
            data["etf_code"],
            "00918",
        )

        keys = {
            (
                item["component_basis"],
                item["component_code"],
            )
            for item in data["components"]
        }

        self.assertEqual(
            keys,
            {
                (
                    "ESTIMATED",
                    "EST_REALIZED_CAPITAL_GAIN",
                ),
                (
                    "ACTUAL",
                    "76W",
                ),
            },
        )

    def test_component_filters_are_applied(
        self,
    ) -> None:
        """確認 basis、code 與 source 篩選。"""

        response = self.client.get(
            "/api/v1/dividends/2/components",
            params={
                "component_basis": "ACTUAL",
                "component_code": "76w",
                "source_id": (
                    "OFFICIAL_DISTRIBUTION_NOTICE"
                ),
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
            data["items"][0][
                "component_code"
            ],
            "76W",
        )

        self.assertEqual(
            data["items"][0][
                "component_basis"
            ],
            "ACTUAL",
        )

    def test_actual_76w_summary_excludes_estimated_gain(
        self,
    ) -> None:
        """確認 76W 統計只採 ACTUAL 76W。"""

        response = self.client.get(
            "/api/v1/etfs/00918/dividends/76w"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            data["total_dividend_count"],
            3,
        )

        self.assertEqual(
            data["actual_76w_record_count"],
            2,
        )

        self.assertEqual(
            data["full_76w_count"],
            1,
        )

        self.assertEqual(
            data["latest_76w_ratio_pct"],
            100.0,
        )

        self.assertEqual(
            data["average_76w_ratio_pct"],
            90.0,
        )

        self.assertEqual(
            [
                item["ratio_pct"]
                for item in data["items"]
            ],
            [
                100.0,
                80.0,
            ],
        )

    def test_no_actual_76w_is_null_not_zero(
        self,
    ) -> None:
        """確認缺少正式 76W 時不顯示為 0%。"""

        response = self.client.get(
            "/api/v1/etfs/0050/dividends/76w"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            data["actual_76w_record_count"],
            0,
        )

        self.assertIsNone(
            data["latest_76w_ratio_pct"]
        )

        self.assertIsNone(
            data["average_76w_ratio_pct"]
        )

        self.assertEqual(
            data["items"],
            [],
        )

    def test_missing_dividend_returns_404(
        self,
    ) -> None:
        """確認不存在的配息事件回傳 404。"""

        response = self.client.get(
            "/api/v1/dividends/999"
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertEqual(
            response.json(),
            {
                "detail": "找不到配息事件：999",
            },
        )

    def test_invalid_parameters_return_422(
        self,
    ) -> None:
        """確認不合法分頁及組成類型被拒絕。"""

        invalid_limit = self.client.get(
            "/api/v1/etfs/00918/dividends",
            params={
                "limit": 0,
            },
        )

        invalid_basis = self.client.get(
            "/api/v1/dividends/2/components",
            params={
                "component_basis": "UNKNOWN",
            },
        )

        invalid_id = self.client.get(
            "/api/v1/dividends/0"
        )

        self.assertEqual(
            invalid_limit.status_code,
            422,
        )

        self.assertEqual(
            invalid_basis.status_code,
            422,
        )

        self.assertEqual(
            invalid_id.status_code,
            422,
        )

    def test_openapi_contains_dividend_paths(
        self,
    ) -> None:
        """確認 OpenAPI 已登錄全部配息端點。"""

        paths = self.application.openapi()[
            "paths"
        ]

        expected_paths = {
            "/api/v1/etfs/{code}/dividends",
            "/api/v1/etfs/{code}/dividends/76w",
            "/api/v1/dividends/{dividend_id}",
            (
                "/api/v1/dividends/"
                "{dividend_id}/components"
            ),
        }

        self.assertTrue(
            expected_paths.issubset(
                paths
            )
        )


if __name__ == "__main__":
    unittest.main()
