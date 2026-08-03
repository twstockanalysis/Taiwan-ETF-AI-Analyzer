"""ETF 市價報酬率計算測試。"""

import unittest
from datetime import date
from decimal import Decimal

from backend.app.models.etf_price import (
    ETFDailyCloseRecord,
)
from backend.app.services.performance_calculator import (
    InsufficientPriceHistoryError,
    calculate_six_month_price_return,
)


class TestPerformanceCalculator(
    unittest.TestCase
):
    """測試 ETF 六個月市價報酬率。"""

    def build_record(
        self,
        trade_date: str,
        close_price: str,
        code: str = "0050",
    ) -> ETFDailyCloseRecord:
        """建立價格測試資料。"""

        return ETFDailyCloseRecord.model_validate(
            {
                "etf_code": code,
                "trade_date": trade_date,
                "close_price": close_price,
                "source_id": "twse_stock_day",
            }
        )

    def test_positive_six_month_return(
        self,
    ) -> None:
        """確認正報酬計算。"""

        result = (
            calculate_six_month_price_return(
                [
                    self.build_record(
                        "2026-01-29",
                        "100",
                    ),
                    self.build_record(
                        "2026-07-29",
                        "120",
                    ),
                ]
            )
        )

        self.assertEqual(
            result.return_pct,
            Decimal("20.000000"),
        )

    def test_negative_six_month_return(
        self,
    ) -> None:
        """確認負報酬計算。"""

        result = (
            calculate_six_month_price_return(
                [
                    self.build_record(
                        "2026-01-29",
                        "100",
                    ),
                    self.build_record(
                        "2026-07-29",
                        "80",
                    ),
                ]
            )
        )

        self.assertEqual(
            result.return_pct,
            Decimal("-20.000000"),
        )

    def test_next_trading_day_is_used(
        self,
    ) -> None:
        """確認目標日無交易時使用下一交易日。"""

        result = (
            calculate_six_month_price_return(
                [
                    self.build_record(
                        "2026-01-30",
                        "100",
                    ),
                    self.build_record(
                        "2026-07-29",
                        "110",
                    ),
                ]
            )
        )

        self.assertEqual(
            result.actual_start_date,
            date(2026, 1, 30),
        )

    def test_short_history_is_rejected(
        self,
    ) -> None:
        """確認上市未滿六個月時不回傳 0%。"""

        with self.assertRaises(
            InsufficientPriceHistoryError
        ):
            calculate_six_month_price_return(
                [
                    self.build_record(
                        "2026-05-01",
                        "100",
                    ),
                    self.build_record(
                        "2026-07-29",
                        "110",
                    ),
                ]
            )

    def test_multiple_codes_are_rejected(
        self,
    ) -> None:
        """確認不可混用多檔 ETF。"""

        with self.assertRaises(
            ValueError
        ):
            calculate_six_month_price_return(
                [
                    self.build_record(
                        "2026-01-29",
                        "100",
                        code="0050",
                    ),
                    self.build_record(
                        "2026-07-29",
                        "110",
                        code="0056",
                    ),
                ]
            )


if __name__ == "__main__":
    unittest.main()