"""首頁系統資料總覽 API 測試。"""

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


class TestSystemOverviewAPI(
    unittest.TestCase
):
    """測試首頁總覽 Endpoint 與缺資料語意。"""

    def setUp(self) -> None:
        """建立獨立測試應用程式與資料庫。"""

        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.database_path = (
            Path(self.temp_directory.name)
            / "system_overview_api.db"
        )

        initialize_database(
            self.database_path
        )

        self.application = create_app()

        self.application.dependency_overrides[
            get_database_path
        ] = lambda: self.database_path

        self.client = TestClient(
            self.application
        )

    def tearDown(self) -> None:
        """關閉測試用戶端並移除資料庫。"""

        self.client.close()

        self.application.dependency_overrides = {}

        self.temp_directory.cleanup()

    def test_empty_overview_returns_null_rates(
        self,
    ) -> None:
        """確認空資料庫不回傳偽造的 0% 或日期。"""

        response = self.client.get(
            "/api/v1/system/overview"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            data["api_status"],
            "healthy",
        )

        self.assertEqual(
            data["database_type"],
            "SQLite",
        )

        self.assertEqual(
            data["etfs"]["total_count"],
            0,
        )

        self.assertIsNone(
            data["performance"][
                "coverage_pct"
            ]
        )

        self.assertIsNone(
            data["dividends"][
                "actual_76w_coverage_pct"
            ]
        )

        self.assertEqual(
            data["recent_import_batches"],
            [],
        )

    def test_overview_response_uses_database_data(
        self,
    ) -> None:
        """確認 Endpoint 回傳實際 ETF 與績效統計。"""

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
                    is_bond,
                    listing_date
                )
                VALUES (
                    '0050',
                    '元大台灣50',
                    0,
                    0,
                    '2003-06-30'
                );
                """
            )

            connection.execute(
                """
                INSERT INTO etf_performance (
                    etf_code,
                    as_of_date,
                    period_code,
                    metric_code,
                    return_pct,
                    source_id
                )
                VALUES (
                    '0050',
                    '2026-07-30',
                    '6M',
                    'PRICE_RETURN',
                    20,
                    'twse_stock_day'
                );
                """
            )

            connection.commit()

        finally:
            connection.close()

        response = self.client.get(
            "/api/v1/system/overview"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            data["etfs"]["total_count"],
            1,
        )

        self.assertEqual(
            data["etfs"][
                "non_bond_count"
            ],
            1,
        )

        self.assertEqual(
            data["performance"][
                "etf_count"
            ],
            1,
        )

        self.assertEqual(
            data["performance"][
                "coverage_pct"
            ],
            100.0,
        )

        period_lookup = {
            item["period_code"]: item
            for item in data[
                "performance"
            ]["periods"]
        }

        self.assertEqual(
            period_lookup["6M"][
                "latest_as_of_date"
            ],
            "2026-07-30",
        )

    def test_openapi_registers_overview_path(
        self,
    ) -> None:
        """確認 OpenAPI 登錄首頁總覽 Endpoint。"""

        paths = set(
            self.application
            .openapi()["paths"]
        )

        self.assertIn(
            "/api/v1/system/overview",
            paths,
        )


if __name__ == "__main__":
    unittest.main()
