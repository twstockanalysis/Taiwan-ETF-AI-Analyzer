"""ETF 比較 URL State 與返回行為測試。"""

import unittest

from frontend.navigation import (
    ETF_COMPARISON_ROUTE,
    ETF_DETAIL_ROUTE,
    PERFORMANCE_RANKING_ROUTE,
    build_comparison_query_params,
    resolve_comparison_return,
)
from frontend.query_state import (
    ETFComparisonQueryState,
    normalize_comparison_codes,
    parse_etf_comparison_query_state,
)


class TestFrontendETFComparisonState(
    unittest.TestCase
):
    """驗證比較清單與來源頁狀態。"""

    def test_comparison_route_is_public(
        self,
    ) -> None:
        """確認 ETF 比較頁不是隱藏頁。"""

        self.assertFalse(
            ETF_COMPARISON_ROUTE.hidden
        )
        self.assertEqual(
            ETF_COMPARISON_ROUTE.url_path,
            "etf-comparison",
        )

    def test_codes_are_normalized_and_capped(
        self,
    ) -> None:
        """確認代號去重、轉大寫且最多四檔。"""

        self.assertEqual(
            normalize_comparison_codes(
                [
                    " 0050 ",
                    "0056",
                    "0050",
                    "00878",
                    "00919",
                    "00940",
                ]
            ),
            (
                "0050",
                "0056",
                "00878",
                "00919",
            ),
        )

    def test_query_state_round_trip(
        self,
    ) -> None:
        """確認比較清單可穩定寫回網址。"""

        state = (
            parse_etf_comparison_query_state(
                {
                    "codes": (
                        "0050,0056,0050"
                    ),
                }
            )
        )

        self.assertEqual(
            state,
            ETFComparisonQueryState(
                codes=(
                    "0050",
                    "0056",
                )
            ),
        )
        self.assertEqual(
            state.to_query_params(),
            {
                "codes": "0050,0056",
            },
        )

    def test_detail_source_is_preserved(
        self,
    ) -> None:
        """確認從詳細頁進入比較後可以返回原狀態。"""

        params = build_comparison_query_params(
            codes=("0050",),
            source="etf-detail",
            source_query_params={
                "code": "0050",
                "from": "performance-ranking",
                "period": "1Y",
                "page": "2",
            },
        )

        route, return_params = (
            resolve_comparison_return(
                params
            )
        )

        self.assertEqual(
            route,
            ETF_DETAIL_ROUTE,
        )
        self.assertEqual(
            return_params["code"],
            "0050",
        )
        self.assertEqual(
            return_params["from"],
            "performance-ranking",
        )

    def test_ranking_source_is_canonicalized(
        self,
    ) -> None:
        """確認排行榜條件可通過比較頁還原。"""

        params = build_comparison_query_params(
            codes=("0050", "0056"),
            source="performance-ranking",
            source_query_params={
                "period": "1Y",
                "active": "passive",
                "bond": "bond",
                "page": "3",
                "page_size": "50",
            },
        )

        route, return_params = (
            resolve_comparison_return(
                params
            )
        )

        self.assertEqual(
            route,
            PERFORMANCE_RANKING_ROUTE,
        )
        self.assertEqual(
            return_params["period"],
            "1Y",
        )
        self.assertEqual(
            return_params["page"],
            "3",
        )


if __name__ == "__main__":
    unittest.main()
