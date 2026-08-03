"""Streamlit 績效排行榜介面測試。"""

import unittest
from unittest.mock import patch

from frontend.pages.performance_ranking import (
    build_performance_ranking_segments,
    format_performance_ranking_row,
    format_performance_return,
    render_clickable_performance_rows,
)
from frontend.query_state import (
    PerformanceQueryState,
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
            "sort_period": "6M",
            "sort_as_of_date": "2026-07-29",
            "sort_return_pct": 20.0,
            "source_id": "twse_stock_day",
            "performance_items": [
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
                    "return_pct": 10.0,
                    "source_id": (
                        "twse_stock_day"
                    ),
                },
                {
                    "as_of_date": "2026-07-29",
                    "period_code": "6M",
                    "metric_code": (
                        "PRICE_RETURN"
                    ),
                    "return_pct": 20.0,
                    "source_id": (
                        "twse_stock_day"
                    ),
                },
                {
                    "as_of_date": "2026-07-29",
                    "period_code": "1Y",
                    "metric_code": (
                        "PRICE_RETURN"
                    ),
                    "return_pct": 30.0,
                    "source_id": (
                        "twse_stock_day"
                    ),
                },
            ],
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

    def test_zero_and_negative_returns(
        self,
    ) -> None:
        """確認零與負報酬格式一致。"""

        self.assertEqual(
            format_performance_return(0),
            "+0.00%",
        )

        self.assertEqual(
            format_performance_return(-3.2),
            "-3.20%",
        )

    def test_invalid_return_has_error_label(
        self,
    ) -> None:
        """確認格式異常時不偽造數值。"""

        self.assertEqual(
            format_performance_return(
                "not-a-number"
            ),
            "格式異常",
        )

    def test_segments_show_only_sort_period(
        self,
    ) -> None:
        """確認排行榜只顯示目前排序期間。"""

        self.assertEqual(
            build_performance_ranking_segments(
                self.build_item()
            ),
            (
                "**#1　0050**",
                "元大台灣50",
                "**6M +20.00%**",
                "截至 2026-07-29",
                "被動式",
                "非債券",
            ),
        )

    def test_former_name_suffix_is_hidden(
        self,
    ) -> None:
        """確認排行榜名稱不顯示原名註記。"""

        item = self.build_item()
        item["name"] = (
            "期元大S&P黃金反1"
            "(原名：元大S&P黃金反1)"
        )

        segments = (
            build_performance_ranking_segments(
                item
            )
        )

        self.assertEqual(
            segments[1],
            "期元大S&P黃金反1",
        )

        self.assertNotIn(
            "原名",
            "｜".join(segments),
        )

    def test_active_bond_labels(
        self,
    ) -> None:
        """確認主動式債券分類位於右側欄位。"""

        item = self.build_item()
        item["is_active"] = True
        item["is_bond"] = True

        segments = (
            build_performance_ranking_segments(
                item
            )
        )

        self.assertEqual(
            segments[-2:],
            (
                "主動式",
                "債券",
            ),
        )

    def test_row_field_order(
        self,
    ) -> None:
        """確認排序期間位於名稱後、分類位於右側。"""

        label = (
            format_performance_ranking_row(
                self.build_item()
            )
        )

        expected_values = (
            "#1",
            "0050",
            "元大台灣50",
            "6M +20.00%",
            "截至 2026-07-29",
            "被動式",
            "非債券",
        )

        positions = [
            label.index(value)
            for value in expected_values
        ]

        self.assertEqual(
            positions,
            sorted(positions),
        )

        for hidden_period in (
            "1M +5.00%",
            "3M +10.00%",
            "1Y +30.00%",
        ):
            self.assertNotIn(
                hidden_period,
                label,
            )

    def test_missing_sort_period_is_not_zero(
        self,
    ) -> None:
        """確認缺少排序期間時不會偽造零值。"""

        item = self.build_item()
        item["performance_items"] = [
            performance_item
            for performance_item in (
                item["performance_items"]
            )
            if performance_item[
                "period_code"
            ] != "6M"
        ]

        label = (
            format_performance_ranking_row(
                item
            )
        )

        self.assertIn(
            "6M 歷史資料不足",
            label,
        )

        self.assertNotIn(
            "6M +0.00%",
            label,
        )

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
            ],
            query_state=(
                PerformanceQueryState(
                    period="6M",
                    active_label="被動式",
                    bond_label="非債券",
                    page=3,
                    page_size=50,
                )
            ),
        )

        mock_caption.assert_called_once_with(
            "排名與代號｜ETF 名稱｜"
            "6M 報酬率｜"
            "排序基準日｜管理方式｜資產類型"
        )

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
                "from": "performance-ranking",
                "period": "6M",
                "active": "passive",
                "bond": "non-bond",
                "page": "3",
                "page_size": "50",
            },
        )


if __name__ == "__main__":
    unittest.main()
