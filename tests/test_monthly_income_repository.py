"""每月領息分布 Repository 測試。"""

import tempfile
import unittest
from pathlib import Path

from backend.app.database.connection import (
    get_connection,
)
from backend.app.database.init_db import (
    initialize_database,
)
from backend.app.repositories.monthly_income_repository import (
    build_monthly_income_distribution,
)


class TestMonthlyIncomeRepository(
    unittest.TestCase
):
    """測試依實際入帳日建立月份分布。"""

    def setUp(self) -> None:
        """建立臨時資料庫。"""

        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )
        self.database_path = (
            Path(self.temp_directory.name)
            / "monthly_income.db"
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
                        "outside-window",
                        "2023-01-05",
                        "2023-01-20",
                        0.4,
                        "TWD",
                        "official",
                    ),
                    (
                        "00918",
                        "2024-january",
                        "2023-12-20",
                        "2024-01-15",
                        0.5,
                        "TWD",
                        "official",
                    ),
                    (
                        "00918",
                        "2025-january",
                        "2024-12-20",
                        "2025-01-15",
                        0.6,
                        "TWD",
                        "official",
                    ),
                    (
                        "00918",
                        "2025-april",
                        "2025-03-20",
                        "2025-04-15",
                        0.7,
                        "TWD",
                        "official",
                    ),
                    (
                        "00918",
                        "2026-january",
                        "2025-12-20",
                        "2026-01-15",
                        0.8,
                        "TWD",
                        "official",
                    ),
                    (
                        "00918",
                        "2026-april",
                        "2026-03-20",
                        "2026-04-15",
                        0.9,
                        "TWD",
                        "official",
                    ),
                    (
                        "00918",
                        "2026-july",
                        "2026-06-20",
                        "2026-07-15",
                        1.0,
                        "TWD",
                        "official",
                    ),
                    (
                        "00918",
                        "missing-payment-date",
                        "2026-08-20",
                        None,
                        1.1,
                        "TWD",
                        "official",
                    ),
                ],
            )
            connection.commit()

        finally:
            connection.close()

    def tearDown(self) -> None:
        """清除臨時資料。"""

        self.temp_directory.cleanup()

    def test_distribution_uses_payment_date(
        self,
    ) -> None:
        """確認月份一律以實際入帳日計算。"""

        result = (
            build_monthly_income_distribution(
                etf_code=" 00918 ",
                database_path=(
                    self.database_path
                ),
            )
        )

        self.assertIsNotNone(result)
        assert result is not None

        self.assertEqual(
            result["date_basis"],
            "PAYMENT_DATE",
        )
        self.assertEqual(
            result["as_of_date"].isoformat(),
            "2026-07-15",
        )
        self.assertEqual(
            result["window_start_date"].isoformat(),
            "2023-07-16",
        )
        self.assertEqual(
            result["total_dividend_event_count"],
            8,
        )
        self.assertEqual(
            result["dated_dividend_event_count"],
            7,
        )
        self.assertEqual(
            result["missing_payment_date_count"],
            1,
        )
        self.assertEqual(
            result["analysis_event_count"],
            6,
        )
        self.assertEqual(
            result["covered_month_count"],
            3,
        )
        self.assertEqual(
            result[
                "covered_month_occurrence_count"
            ],
            6,
        )

        january = result["months"][0]

        self.assertEqual(
            january["event_count"],
            3,
        )
        self.assertEqual(
            january["observed_year_count"],
            3,
        )
        self.assertAlmostEqual(
            january["total_amount_per_unit"],
            1.9,
        )

        self.assertEqual(
            result["months"][2]["event_count"],
            0,
        )
        self.assertIsNone(
            result["months"][2][
                "total_amount_per_unit"
            ]
        )

    def test_shorter_lookback_excludes_old_events(
        self,
    ) -> None:
        """確認可縮短回看期間且不改基準日。"""

        result = (
            build_monthly_income_distribution(
                etf_code="00918",
                database_path=(
                    self.database_path
                ),
                lookback_years=1,
            )
        )

        assert result is not None

        self.assertEqual(
            result["window_start_date"].isoformat(),
            "2025-07-16",
        )
        self.assertEqual(
            result["analysis_event_count"],
            3,
        )

    def test_existing_etf_without_dividends_is_empty(
        self,
    ) -> None:
        """確認沒有配息資料時保留空值語意。"""

        result = (
            build_monthly_income_distribution(
                etf_code="0050",
                database_path=(
                    self.database_path
                ),
            )
        )

        assert result is not None

        self.assertIsNone(
            result["as_of_date"]
        )
        self.assertIsNone(
            result["total_amount_per_unit"]
        )
        self.assertEqual(
            len(result["months"]),
            12,
        )
        self.assertTrue(
            all(
                item["event_count"] == 0
                for item in result["months"]
            )
        )

    def test_mixed_currencies_do_not_sum_amounts(
        self,
    ) -> None:
        """確認不同幣別不會被加總成同一金額。"""

        connection = get_connection(
            self.database_path
        )

        try:
            connection.execute(
                """
                INSERT INTO etf_dividend (
                    etf_code,
                    source_event_id,
                    payment_date,
                    amount_per_unit,
                    currency,
                    source_id
                )
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    "00918",
                    "2026-usd",
                    "2026-06-15",
                    0.1,
                    "USD",
                    "official",
                ),
            )
            connection.commit()

        finally:
            connection.close()

        result = (
            build_monthly_income_distribution(
                etf_code="00918",
                database_path=(
                    self.database_path
                ),
            )
        )

        assert result is not None

        self.assertTrue(
            result["has_mixed_currencies"]
        )
        self.assertIsNone(
            result["analysis_currency"]
        )
        self.assertIsNone(
            result["total_amount_per_unit"]
        )
        self.assertIsNone(
            result["months"][5][
                "total_amount_per_unit"
            ]
        )

    def test_missing_etf_returns_none(
        self,
    ) -> None:
        """確認找不到 ETF 時回傳 None。"""

        self.assertIsNone(
            build_monthly_income_distribution(
                etf_code="UNKNOWN",
                database_path=(
                    self.database_path
                ),
            )
        )

    def test_invalid_lookback_is_rejected(
        self,
    ) -> None:
        """確認 Repository 也保護回看年數。"""

        with self.assertRaises(ValueError):
            build_monthly_income_distribution(
                etf_code="00918",
                database_path=(
                    self.database_path
                ),
                lookback_years=0,
            )


if __name__ == "__main__":
    unittest.main()
