"""配息摘要補充資料測試。"""

import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
import sqlite3

from pydantic import ValidationError

from backend.app.database.connection import (
    get_connection,
)
from backend.app.database.init_db import (
    initialize_database,
)
from backend.app.models.etf_analysis import (
    DividendYieldBasis,
    ETFDividendSummaryMetricRecord,
)
from backend.app.repositories.dividend_repository import (
    list_etf_dividends,
    upsert_dividend_summary_metrics,
)


class TestDividendSummaryMetric(
    unittest.TestCase
):
    """驗證年季、殖利率來源與官方優先權。"""

    def setUp(self) -> None:
        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.database_path = (
            Path(self.temp_directory.name)
            / "summary.db"
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
                VALUES ('00918', '測試 ETF', 0, 0);
                """
            )

            connection.execute(
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
                VALUES (
                    1,
                    '00918',
                    'event-1',
                    '2026-03-20',
                    '2026-04-15',
                    0.5,
                    'TWD',
                    'official'
                );
                """
            )

            connection.commit()

        finally:
            connection.close()

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_calculated_yield_requires_reference_price(
        self,
    ) -> None:
        """確認回退值必須保存交易日與收盤價。"""

        with self.assertRaises(
            ValidationError
        ):
            ETFDividendSummaryMetricRecord(
                dividend_id=1,
                yield_pct=Decimal("2"),
                yield_basis=(
                    DividendYieldBasis.CALCULATED
                ),
                yield_source_id="twse_stock_day",
            )

    def test_database_rejects_untraceable_yield(
        self,
    ) -> None:
        """確認直接 SQL 也不能寫入無來源殖利率。"""

        connection = get_connection(
            self.database_path
        )

        try:
            with self.assertRaises(
                sqlite3.IntegrityError
            ):
                connection.execute(
                    """
                    INSERT INTO etf_dividend_summary_metric (
                        dividend_id,
                        yield_pct,
                        yield_basis
                    )
                    VALUES (1, 2.0, 'OFFICIAL');
                    """
                )

        finally:
            connection.rollback()
            connection.close()

    def test_official_yield_replaces_and_blocks_fallback(
        self,
    ) -> None:
        """確認官方值可取代回退值且不會被反向覆蓋。"""

        calculated = (
            ETFDividendSummaryMetricRecord(
                dividend_id=1,
                yield_pct=Decimal("2.0"),
                yield_basis=(
                    DividendYieldBasis.CALCULATED
                ),
                yield_source_id="twse_stock_day",
                reference_trade_date=(
                    "2026-03-19"
                ),
                reference_close_price=(
                    Decimal("25")
                ),
            )
        )

        upsert_dividend_summary_metrics(
            [calculated],
            self.database_path,
        )

        official = (
            ETFDividendSummaryMetricRecord(
                dividend_id=1,
                distribution_period="2026q1",
                distribution_period_source_id=(
                    "Official_Notice"
                ),
                yield_pct=Decimal("2.15"),
                yield_basis=(
                    DividendYieldBasis.OFFICIAL
                ),
                yield_source_id=(
                    "Official_Notice"
                ),
            )
        )

        upsert_dividend_summary_metrics(
            [official],
            self.database_path,
        )

        upsert_dividend_summary_metrics(
            [calculated],
            self.database_path,
        )

        item = list_etf_dividends(
            etf_code="00918",
            database_path=self.database_path,
        )[0]

        self.assertEqual(
            item["distribution_period"],
            "2026Q1",
        )
        self.assertEqual(
            item["yield_pct"],
            2.15,
        )
        self.assertEqual(
            item["yield_basis"],
            "OFFICIAL",
        )
        self.assertIsNone(
            item["reference_trade_date"]
        )
        self.assertIsNone(
            item["reference_close_price"]
        )


if __name__ == "__main__":
    unittest.main()
