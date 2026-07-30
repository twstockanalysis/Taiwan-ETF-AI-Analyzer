"""Streamlit ETF 績效詳細區塊測試。"""

import unittest

from frontend.pages.etf_detail import (
    build_performance_lookup,
    format_performance_return,
)


class TestFrontendETFPerformanceDetail(
    unittest.TestCase
):
    """測試 ETF 詳細頁績效輔助函式。"""

    def test_return_is_formatted(
        self,
    ) -> None:
        """確認報酬率顯示正負號。"""

        self.assertEqual(
            format_performance_return(
                12.345
            ),
            "+12.35%",
        )

        self.assertEqual(
            format_performance_return(
                -3.2
            ),
            "-3.20%",
        )

    def test_lookup_keeps_available_periods(
        self,
    ) -> None:
        """確認只建立實際存在的期間。"""

        lookup = build_performance_lookup(
            [
                {
                    "as_of_date": "2026-07-29",
                    "period_code": "1M",
                    "metric_code": (
                        "PRICE_RETURN"
                    ),
                    "return_pct": 5.0,
                    "source_id": (
                        "twse_stock_day"
                    ),
                },
                {
                    "as_of_date": "2026-07-29",
                    "period_code": "3M",
                    "metric_code": (
                        "PRICE_RETURN"
                    ),
                    "return_pct": 8.0,
                    "source_id": (
                        "twse_stock_day"
                    ),
                },
            ]
        )

        self.assertEqual(
            set(lookup),
            {
                "1M",
                "3M",
            },
        )

        self.assertNotIn(
            "6M",
            lookup,
        )

        self.assertNotIn(
            "1Y",
            lookup,
        )

    def test_unknown_period_is_ignored(
        self,
    ) -> None:
        """確認未支援期間不進入畫面。"""

        lookup = build_performance_lookup(
            [
                {
                    "period_code": "1W",
                    "return_pct": 1.0,
                }
            ]
        )

        self.assertEqual(
            lookup,
            {},
        )


if __name__ == "__main__":
    unittest.main()
