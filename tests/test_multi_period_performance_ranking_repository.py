"""多期間績效排行榜 Repository 測試。"""

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
    PerformancePeriod,
)
from backend.app.repositories.performance_repository import (
    list_latest_multi_period_performance_ranking,
)


class TestMultiPeriodPerformanceRankingRepository(
    unittest.TestCase
):
    """測試主要期間排序與四期間明細。"""

    def setUp(self) -> None:
        """建立臨時資料庫。"""

        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )
        self.database_path = (
            Path(self.temp_directory.name)
            / "multi_period_ranking.db"
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
                        "0050",
                        "元大台灣50",
                        0,
                        0,
                    ),
                    (
                        "0056",
                        "元大高股息",
                        0,
                        0,
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
                    (
                        "0056",
                        "2026-07-29",
                        "1M",
                        "PRICE_RETURN",
                        8.0,
                        "twse_stock_day",
                    ),
                    (
                        "0056",
                        "2026-07-29",
                        "3M",
                        "PRICE_RETURN",
                        9.0,
                        "twse_stock_day",
                    ),
                    (
                        "0056",
                        "2026-07-29",
                        "6M",
                        "PRICE_RETURN",
                        10.0,
                        "twse_stock_day",
                    ),
                    (
                        "0056",
                        "2026-07-29",
                        "1Y",
                        "PRICE_RETURN",
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

    def test_six_month_sort_keeps_all_available_periods(
        self,
    ) -> None:
        """確認 6M 排序但仍回傳其他可用期間。"""

        rows = (
            list_latest_multi_period_performance_ranking(
                database_path=self.database_path,
            )
        )

        self.assertEqual(
            [
                row["etf_code"]
                for row in rows
            ],
            [
                "0050",
                "0056",
            ],
        )

        self.assertEqual(
            [
                item["period_code"]
                for item in rows[0][
                    "performance_items"
                ]
            ],
            [
                "1M",
                "6M",
                "1Y",
            ],
        )

        self.assertNotIn(
            "3M",
            {
                item["period_code"]
                for item in rows[0][
                    "performance_items"
                ]
            },
        )

    def test_sort_period_can_change_without_hiding_periods(
        self,
    ) -> None:
        """確認改用 1M 排序後仍保留四期間明細。"""

        rows = (
            list_latest_multi_period_performance_ranking(
                database_path=self.database_path,
                sort_period=(
                    PerformancePeriod.ONE_MONTH
                ),
            )
        )

        self.assertEqual(
            rows[0]["etf_code"],
            "0056",
        )

        self.assertEqual(
            rows[0]["sort_period"],
            "1M",
        )

        self.assertIn(
            "1Y",
            {
                item["period_code"]
                for item in rows[0][
                    "performance_items"
                ]
            },
        )


if __name__ == "__main__":
    unittest.main()
