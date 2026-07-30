"""ETF 配息查詢 Repository 測試。"""

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
    DividendComponentBasis,
)
from backend.app.repositories.dividend_repository import (
    build_actual_76w_summary,
    count_etf_dividends,
    get_dividend_by_id,
    list_actual_76w_history,
    list_filtered_dividend_components,
)


class TestDividendQueryRepository(
    unittest.TestCase
):
    """測試配息 API 所需 Repository 查詢。"""

    def setUp(self) -> None:
        """建立臨時資料庫。"""

        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.database_path = (
            Path(self.temp_directory.name)
            / "dividend_query.db"
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
                    "00918",
                    "大華優利高填息30",
                    0,
                    0,
                ),
            )

            connection.executemany(
                """
                INSERT INTO etf_dividend (
                    id,
                    etf_code,
                    source_event_id,
                    ex_dividend_date,
                    payment_date,
                    amount_per_unit,
                    currency,
                    source_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                [
                    (
                        1,
                        "00918",
                        "event-1",
                        "2026-03-20",
                        "2026-04-15",
                        0.5,
                        "TWD",
                        "official",
                    ),
                    (
                        2,
                        "00918",
                        "event-2",
                        "2026-06-18",
                        "2026-07-10",
                        0.7,
                        "TWD",
                        "official",
                    ),
                ],
            )

            connection.executemany(
                """
                INSERT INTO etf_dividend_component (
                    dividend_id,
                    component_code,
                    component_basis,
                    ratio_pct,
                    source_id
                )
                VALUES (?, ?, ?, ?, ?);
                """,
                [
                    (
                        1,
                        "EST_REALIZED_CAPITAL_GAIN",
                        "ESTIMATED",
                        100.0,
                        "twse_etfortune_dividend",
                    ),
                    (
                        1,
                        "76W",
                        "ACTUAL",
                        80.0,
                        "notice",
                    ),
                    (
                        2,
                        "76W",
                        "ACTUAL",
                        100.0,
                        "notice",
                    ),
                ],
            )

            connection.commit()

        finally:
            connection.close()

    def tearDown(self) -> None:
        """刪除臨時資料庫。"""

        self.temp_directory.cleanup()

    def test_count_and_get_dividend(
        self,
    ) -> None:
        """確認事件計數與 ID 查詢。"""

        self.assertEqual(
            count_etf_dividends(
                "00918",
                self.database_path,
            ),
            2,
        )

        row = get_dividend_by_id(
            2,
            self.database_path,
        )

        self.assertEqual(
            row["source_event_id"],
            "event-2",
        )

        self.assertIsNone(
            get_dividend_by_id(
                999,
                self.database_path,
            )
        )

    def test_component_filters_normalize_values(
        self,
    ) -> None:
        """確認組成篩選會正規化代碼與來源。"""

        rows = (
            list_filtered_dividend_components(
                dividend_id=1,
                database_path=(
                    self.database_path
                ),
                component_basis=(
                    DividendComponentBasis.ACTUAL
                ),
                component_code="76w",
                source_id="NOTICE",
            )
        )

        self.assertEqual(
            len(rows),
            1,
        )

        self.assertEqual(
            rows[0]["component_code"],
            "76W",
        )

    def test_actual_76w_history_excludes_estimated(
        self,
    ) -> None:
        """確認實際 76W 不混入預估資本利得。"""

        rows = list_actual_76w_history(
            "00918",
            self.database_path,
        )

        self.assertEqual(
            [
                row["ratio_pct"]
                for row in rows
            ],
            [
                100.0,
                80.0,
            ],
        )

        self.assertTrue(
            all(
                row["source_id"] == "notice"
                for row in rows
            )
        )

    def test_actual_76w_summary(
        self,
    ) -> None:
        """確認實際 76W 摘要統計。"""

        summary = build_actual_76w_summary(
            "00918",
            self.database_path,
        )

        self.assertEqual(
            summary["total_dividend_count"],
            2,
        )

        self.assertEqual(
            summary["actual_76w_record_count"],
            2,
        )

        self.assertEqual(
            summary["full_76w_count"],
            1,
        )

        self.assertEqual(
            summary["latest_76w_ratio_pct"],
            100.0,
        )

        self.assertEqual(
            summary["average_76w_ratio_pct"],
            90.0,
        )


if __name__ == "__main__":
    unittest.main()
