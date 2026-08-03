"""單一 ETF 多期間績效 Repository 測試。"""

import tempfile
import unittest
from pathlib import Path

from backend.app.database.connection import (
    get_connection,
)
from backend.app.database.init_db import (
    initialize_database,
)
from backend.app.models.etf_analysis import (
    PerformanceMetric,
)
from backend.app.repositories.performance_repository import (
    list_latest_etf_performance,
)


class TestETFPerformanceRepository(
    unittest.TestCase
):
    """測試單一 ETF 多期間最新績效查詢。"""

    def setUp(self) -> None:
        """建立臨時資料庫。"""

        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.database_path = (
            Path(self.temp_directory.name)
            / "etf_performance_detail.db"
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
                        3.0,
                        "twse_stock_day",
                    ),
                    (
                        "0050",
                        "2026-06-30",
                        "6M",
                        "PRICE_RETURN",
                        50.0,
                        "twse_stock_day",
                    ),
                    (
                        "0050",
                        "2026-07-29",
                        "6M",
                        "PRICE_RETURN",
                        10.0,
                        "twse_stock_day",
                    ),
                    (
                        "0050",
                        "2026-07-29",
                        "6M",
                        "TOTAL_RETURN",
                        20.0,
                        "twse_stock_day",
                    ),
                ],
            )

            connection.commit()

        finally:
            connection.close()

    def tearDown(self) -> None:
        """清除臨時資料。"""

        self.temp_directory.cleanup()

    def test_latest_record_is_returned_per_period(
        self,
    ) -> None:
        """確認每個期間只取最新一筆。"""

        rows = list_latest_etf_performance(
            etf_code="0050",
            database_path=self.database_path,
        )

        self.assertEqual(
            [
                row["period_code"]
                for row in rows
            ],
            [
                "1M",
                "6M",
            ],
        )

        self.assertEqual(
            rows[1]["return_pct"],
            10.0,
        )

    def test_metric_is_isolated(
        self,
    ) -> None:
        """確認不同績效類型不會互相混合。"""

        rows = list_latest_etf_performance(
            etf_code="0050",
            database_path=self.database_path,
            metric_code=(
                PerformanceMetric.TOTAL_RETURN
            ),
        )

        self.assertEqual(
            len(rows),
            1,
        )

        self.assertEqual(
            rows[0]["metric_code"],
            "TOTAL_RETURN",
        )

        self.assertEqual(
            rows[0]["return_pct"],
            20.0,
        )


if __name__ == "__main__":
    unittest.main()
