"""配息殖利率回退 Pipeline 測試。"""

import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from backend.app.database.connection import (
    get_connection,
)
from backend.app.database.init_db import (
    initialize_database,
)
from backend.app.data_sources.dividend_yield_pipeline import (
    calculate_dividend_yield_pct,
    run_dividend_yield_pipeline,
    select_previous_trading_close,
)
from backend.app.models.etf_price import (
    ETFDailyCloseRecord,
)
from backend.app.repositories.dividend_repository import (
    list_etf_dividends,
)


class TestDividendYieldPipeline(
    unittest.TestCase
):
    """驗證公式、交易日選擇與資料保存。"""

    def setUp(self) -> None:
        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.database_path = (
            Path(self.temp_directory.name)
            / "yield.db"
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
                VALUES (?, '00918', ?, ?, ?, ?, 'TWD', 'official');
                """,
                [
                    (
                        1,
                        "event-1",
                        "2026-03-20",
                        "2026-04-15",
                        0.5,
                    ),
                    (
                        2,
                        "event-future",
                        "2026-09-20",
                        "2026-10-15",
                        0.6,
                    ),
                ],
            )

            connection.commit()

        finally:
            connection.close()

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def build_price(
        self,
        trade_date: date,
        close_price: str,
    ) -> ETFDailyCloseRecord:
        """建立測試價格。"""

        return ETFDailyCloseRecord(
            etf_code="00918",
            trade_date=trade_date,
            close_price=Decimal(
                close_price
            ),
            source_id="twse_stock_day",
        )

    def test_formula_and_previous_trade_selection(
        self,
    ) -> None:
        """確認採嚴格早於除息日的最近交易日。"""

        records = [
            self.build_price(
                date(2026, 3, 18),
                "24.5",
            ),
            self.build_price(
                date(2026, 3, 19),
                "25",
            ),
            self.build_price(
                date(2026, 3, 20),
                "24",
            ),
        ]

        selected = select_previous_trading_close(
            records,
            date(2026, 3, 20),
        )

        self.assertEqual(
            selected.trade_date,
            date(2026, 3, 19),
        )
        self.assertEqual(
            calculate_dividend_yield_pct(
                Decimal("0.5"),
                selected.close_price,
            ),
            Decimal("2.000000"),
        )

    def test_pipeline_saves_reference_and_skips_future_event(
        self,
    ) -> None:
        """確認回退值寫入，未到除息日事件維持缺值。"""

        calls: list[tuple] = []

        def fake_price_fetcher(
            etf_code,
            end_date,
            month_count,
            request_interval_seconds,
        ):
            calls.append(
                (
                    etf_code,
                    end_date,
                    month_count,
                    request_interval_seconds,
                )
            )

            return [
                self.build_price(
                    date(2026, 3, 19),
                    "25",
                )
            ]

        result = run_dividend_yield_pipeline(
            database_path=self.database_path,
            etf_code="00918",
            request_interval_seconds=0,
            today=date(2026, 8, 1),
            price_fetcher=fake_price_fetcher,
        )

        self.assertEqual(
            result.candidate_count,
            2,
        )
        self.assertEqual(
            result.calculated_count,
            1,
        )
        self.assertEqual(
            result.failed_count,
            1,
        )
        self.assertEqual(
            len(calls),
            1,
        )

        items = list_etf_dividends(
            etf_code="00918",
            database_path=self.database_path,
        )

        historical = next(
            item
            for item in items
            if item["id"] == 1
        )
        future = next(
            item
            for item in items
            if item["id"] == 2
        )

        self.assertEqual(
            historical["yield_pct"],
            2.0,
        )
        self.assertEqual(
            historical["yield_basis"],
            "CALCULATED",
        )
        self.assertEqual(
            historical[
                "reference_trade_date"
            ],
            "2026-03-19",
        )
        self.assertEqual(
            historical[
                "reference_close_price"
            ],
            25.0,
        )
        self.assertIsNone(
            future["yield_pct"]
        )


if __name__ == "__main__":
    unittest.main()
