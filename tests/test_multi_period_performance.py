"""ETF 多期間市價報酬率測試。"""

import unittest
from decimal import Decimal

from backend.app.models.etf_analysis import (
    PerformanceMetric,
    PerformancePeriod,
)
from backend.app.models.etf_price import (
    ETFDailyCloseRecord,
)
from backend.app.services.performance_calculator import (
    UnsupportedPerformancePeriodError,
    calculate_price_return,
    calculate_six_month_price_return,
)


class TestMultiPeriodPerformance(
    unittest.TestCase
):
    """測試 1M、3M、6M、1Y 市價報酬率。"""

    def build_record(
        self,
        trade_date: str,
        close_price: str,
    ) -> ETFDailyCloseRecord:
        """建立測試價格。"""

        return ETFDailyCloseRecord.model_validate(
            {
                "etf_code": "0050",
                "trade_date": trade_date,
                "close_price": close_price,
                "source_id": "twse_stock_day",
            }
        )

    def build_history(
        self,
    ) -> list[ETFDailyCloseRecord]:
        """建立一年測試價格歷史。"""

        return [
            self.build_record(
                "2025-07-29",
                "80",
            ),
            self.build_record(
                "2026-01-29",
                "100",
            ),
            self.build_record(
                "2026-04-29",
                "110",
            ),
            self.build_record(
                "2026-06-29",
                "120",
            ),
            self.build_record(
                "2026-07-29",
                "132",
            ),
        ]

    def test_one_month_return(
        self,
    ) -> None:
        """確認一個月報酬率。"""

        result = calculate_price_return(
            self.build_history(),
            "1M",
        )

        self.assertEqual(
            result.return_pct,
            Decimal("10.000000"),
        )

    def test_three_month_return(
        self,
    ) -> None:
        """確認三個月報酬率。"""

        result = calculate_price_return(
            self.build_history(),
            "3M",
        )

        self.assertEqual(
            result.return_pct,
            Decimal("20.000000"),
        )

    def test_six_month_wrapper(
        self,
    ) -> None:
        """確認原六個月函式仍可使用。"""

        result = (
            calculate_six_month_price_return(
                self.build_history()
            )
        )

        self.assertEqual(
            result.period_code,
            PerformancePeriod.SIX_MONTHS,
        )

        self.assertEqual(
            result.metric_code,
            PerformanceMetric.PRICE_RETURN,
        )

        self.assertEqual(
            result.return_pct,
            Decimal("32.000000"),
        )

    def test_one_year_return(
        self,
    ) -> None:
        """確認一年報酬率。"""

        result = calculate_price_return(
            self.build_history(),
            "1Y",
        )

        self.assertEqual(
            result.return_pct,
            Decimal("65.000000"),
        )

    def test_one_week_is_not_supported(
        self,
    ) -> None:
        """確認目前不接受 1W。"""

        with self.assertRaises(
            UnsupportedPerformancePeriodError
        ):
            calculate_price_return(
                self.build_history(),
                "1W",
            )


if __name__ == "__main__":
    unittest.main()