"""Streamlit ETF 績效詳細區塊測試。"""

import unittest
from unittest.mock import patch

from frontend.pages.etf_detail import (
    build_performance_lookup,
    format_performance_return,
    get_performance_data_date,
    render_price_history_chart,
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

    def test_performance_data_date_prefers_metric_date(self) -> None:
        """卡片共用日期優先採績效資料日期。"""

        self.assertEqual(
            get_performance_data_date(
                [{"as_of_date": "2026-08-25"}],
                {
                    "items": [
                        {
                            "trade_date": "2026-08-24",
                            "close_price": 104.0,
                        }
                    ]
                },
            ),
            "2026-08-25",
        )

    def test_performance_data_date_falls_back_to_latest_price(self) -> None:
        """尚無績效時仍可顯示走勢資料的最新日期。"""

        self.assertEqual(
            get_performance_data_date(
                [],
                {
                    "items": [
                        {
                            "trade_date": "2026-08-24",
                            "close_price": 103.8,
                        },
                        {
                            "trade_date": "2026-08-25",
                            "close_price": 104.4,
                        },
                    ]
                },
            ),
            "2026-08-25",
        )

    @patch("frontend.pages.etf_detail.st.vega_lite_chart")
    @patch("frontend.pages.etf_detail.st.info")
    def test_price_history_renders_area_chart_when_available(
        self,
        mock_info,
        mock_chart,
    ) -> None:
        """兩筆以上官方收盤價應渲染折線面積圖。"""

        render_price_history_chart(
            {
                "items": [
                    {
                        "trade_date": "2026-08-24",
                        "close_price": 103.8,
                        "source_id": "twse_stock_day",
                    },
                    {
                        "trade_date": "2026-08-25",
                        "close_price": 104.4,
                        "source_id": "twse_stock_day",
                    },
                ]
            }
        )

        mock_info.assert_not_called()
        mock_chart.assert_called_once()
        rows, specification = mock_chart.call_args.args
        self.assertEqual(rows[1]["收盤價"], 104.4)
        self.assertEqual(specification["mark"]["type"], "area")
        self.assertFalse(specification["encoding"]["y"]["scale"]["zero"])
        self.assertEqual(mock_chart.call_args.kwargs["width"], "stretch")

    @patch("frontend.pages.etf_detail.st.vega_lite_chart")
    @patch("frontend.pages.etf_detail.st.info")
    def test_price_history_stays_pending_when_insufficient(
        self,
        mock_info,
        mock_chart,
    ) -> None:
        """不足兩筆資料時不繪製誤導圖表。"""

        render_price_history_chart({"items": []})

        mock_chart.assert_not_called()
        mock_info.assert_called_once_with("股價走勢資料抓取中")


if __name__ == "__main__":
    unittest.main()
