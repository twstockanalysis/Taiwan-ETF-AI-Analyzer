"""Streamlit 績效排行榜介面測試。"""

import unittest
from unittest.mock import patch

from frontend.pages.performance_ranking import (
    format_performance_ranking_row,
    format_performance_return,
    render_clickable_performance_rows,
)


class TestFrontendPerformanceRanking(
    unittest.TestCase
):
    """測試績效排行榜顯示與導覽。"""

    def build_item(self) -> dict:
        """建立排行榜測試資料。"""

        return {
            "rank": 1,
            "etf_code": "0050",
            "name": "元大台灣50",
            "is_active": False,
            "is_bond": False,
            "as_of_date": "2026-07-29",
            "period_code": "6M",
            "metric_code": "PRICE_RETURN",
            "return_pct": 20.0,
            "source_id": "twse_stock_day",
        }

    def test_positive_return_has_plus_sign(
        self,
    ) -> None:
        """確認正報酬顯示正號。"""

        self.assertEqual(
            format_performance_return(
                5.125
            ),
            "+5.12%",
        )

    def test_row_contains_ranking_data(
        self,
    ) -> None:
        """確認排行榜列包含主要資訊。"""

        label = (
            format_performance_ranking_row(
                self.build_item()
            )
        )

        self.assertIn("#1", label)
        self.assertIn("0050", label)
        self.assertIn("元大台灣50", label)
        self.assertIn("6M +20.00%", label)
        self.assertIn("2026-07-29", label)

    @patch(
        "frontend.pages.performance_ranking."
        "st.caption"
    )
    @patch(
        "frontend.pages.performance_ranking."
        "st.page_link"
    )
    def test_row_links_to_etf_detail(
        self,
        mock_page_link,
        mock_caption,
    ) -> None:
        """確認整列連到 ETF 詳細頁。"""

        render_clickable_performance_rows(
            [
                self.build_item(),
            ]
        )

        mock_caption.assert_called_once()
        mock_page_link.assert_called_once()

        call_arguments = (
            mock_page_link.call_args
        )

        self.assertEqual(
            call_arguments.args[0],
            "page_scripts/etf_detail_page.py",
        )

        self.assertEqual(
            call_arguments.kwargs["width"],
            "stretch",
        )

        self.assertEqual(
            call_arguments.kwargs[
                "query_params"
            ],
            {
                "code": "0050",
            },
        )


if __name__ == "__main__":
    unittest.main()
