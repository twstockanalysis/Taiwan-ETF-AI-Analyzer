"""每月領息分布 API 測試。"""

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


class TestMonthlyIncomeAPI(
    unittest.TestCase
):
    """測試每月領息 Read Model。"""

    def setUp(self) -> None:
        """建立臨時資料庫與測試應用程式。"""

        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )
        self.database_path = (
            Path(self.temp_directory.name)
            / "monthly_income_api.db"
        )

        initialize_database(
            self.database_path
        )

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
                [
                    (
                        "00918",
                        "2025-event",
                        "2025-12-20",
                        "2026-01-15",
                        0.8,
                        "TWD",
                        "official",
                    ),
                    (
                        "00918",
                        "2026-event",
                        "2026-06-20",
                        "2026-07-15",
                        1.0,
                        "TWD",
                        "official",
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

    def test_defaults_to_three_year_payment_distribution(
        self,
    ) -> None:
        """確認預設回看三年且固定回傳十二個月。"""

        response = self.client.get(
            "/api/v1/etfs/00918/monthly-income"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            data["etf_code"],
            "00918",
        )
        self.assertEqual(
            data["date_basis"],
            "PAYMENT_DATE",
        )
        self.assertEqual(
            data["lookback_years"],
            3,
        )
        self.assertEqual(
            data["as_of_date"],
            "2026-07-15",
        )
        self.assertEqual(
            len(data["months"]),
            12,
        )
        self.assertEqual(
            [
                item["month"]
                for item in data["months"]
            ],
            list(range(1, 13)),
        )
        self.assertEqual(
            data["months"][0]["event_count"],
            1,
        )
        self.assertEqual(
            data["months"][6]["event_count"],
            1,
        )

    def test_lookback_years_can_be_changed(
        self,
    ) -> None:
        """確認 API 接受合法回看年數。"""

        response = self.client.get(
            "/api/v1/etfs/00918/monthly-income",
            params={
                "lookback_years": 1,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            response.json()["lookback_years"],
            1,
        )

    def test_existing_etf_without_data_is_not_zero(
        self,
    ) -> None:
        """確認缺資料時金額維持 null。"""

        response = self.client.get(
            "/api/v1/etfs/0050/monthly-income"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertIsNone(
            data["as_of_date"]
        )
        self.assertIsNone(
            data["total_amount_per_unit"]
        )
        self.assertEqual(
            data["analysis_event_count"],
            0,
        )

    def test_missing_etf_returns_404(
        self,
    ) -> None:
        """確認不存在的 ETF 回傳 404。"""

        response = self.client.get(
            "/api/v1/etfs/UNKNOWN/monthly-income"
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

    def test_invalid_lookback_returns_422(
        self,
    ) -> None:
        """確認不合法回看年數由 API 拒絕。"""

        too_short = self.client.get(
            "/api/v1/etfs/00918/monthly-income",
            params={
                "lookback_years": 0,
            },
        )
        too_long = self.client.get(
            "/api/v1/etfs/00918/monthly-income",
            params={
                "lookback_years": 11,
            },
        )

        self.assertEqual(
            too_short.status_code,
            422,
        )
        self.assertEqual(
            too_long.status_code,
            422,
        )

    def test_openapi_contains_monthly_income_path(
        self,
    ) -> None:
        """確認 OpenAPI 登錄每月領息端點。"""

        self.assertIn(
            "/api/v1/etfs/{code}/monthly-income",
            self.application.openapi()["paths"],
        )


if __name__ == "__main__":
    unittest.main()
