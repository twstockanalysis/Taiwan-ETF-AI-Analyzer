"""多期間績效排行榜 API 測試。"""

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


class TestMultiPeriodPerformanceRankingAPI(
    unittest.TestCase
):
    """測試多期間排行榜 Read Model。"""

    def setUp(self) -> None:
        """建立臨時資料庫與測試應用程式。"""

        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )
        self.database_path = (
            Path(self.temp_directory.name)
            / "multi_period_api.db"
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
                        "0050",
                        "2026-07-29",
                        "1M",
                        "PRICE_RETURN",
                        4.0,
                        "twse_stock_day",
                    ),
                    (
                        "0050",
                        "2026-07-29",
                        "6M",
                        "PRICE_RETURN",
                        12.0,
                        "twse_stock_day",
                    ),
                    (
                        "0050",
                        "2026-07-29",
                        "1Y",
                        "PRICE_RETURN",
                        18.0,
                        "twse_stock_day",
                    ),
                ],
            )
            connection.commit()

        finally:
            connection.close()

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

    def test_defaults_to_six_month_sort(
        self,
    ) -> None:
        """確認預設以 6M 排名且回傳四期間契約。"""

        response = self.client.get(
            "/api/v1/performance/"
            "multi-period-ranking"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            data["sort_period"],
            "6M",
        )

        self.assertEqual(
            data["periods"],
            [
                "1M",
                "3M",
                "6M",
                "1Y",
            ],
        )

        self.assertEqual(
            [
                item["period_code"]
                for item in data["items"][0][
                    "performance_items"
                ]
            ],
            [
                "1M",
                "6M",
                "1Y",
            ],
        )

    def test_openapi_contains_multi_period_path(
        self,
    ) -> None:
        """確認 OpenAPI 登錄新端點。"""

        self.assertIn(
            (
                "/api/v1/performance/"
                "multi-period-ranking"
            ),
            self.application.openapi()[
                "paths"
            ],
        )


if __name__ == "__main__":
    unittest.main()
