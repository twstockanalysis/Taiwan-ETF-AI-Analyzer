"""Streamlit 導覽與返回狀態測試。"""

import unittest

from frontend.navigation import (
    ALL_ROUTES,
    DECISION_PROFILE_ROUTE,
    ETF_DETAIL_ROUTE,
    ETF_SEARCH_ROUTE,
    PERFORMANCE_RANKING_ROUTE,
    build_detail_query_params,
    normalize_detail_source,
    resolve_detail_return,
)


class TestFrontendNavigation(
    unittest.TestCase
):
    """驗證集中路由與 ETF 詳細頁返回行為。"""

    def test_all_routes_have_unique_keys(
        self,
    ) -> None:
        """確認頁面 Key 與 URL Path 不重複。"""

        keys = [
            route.key
            for route in ALL_ROUTES
        ]

        url_paths = [
            route.url_path
            for route in ALL_ROUTES
            if route.url_path is not None
        ]

        self.assertEqual(
            len(keys),
            len(set(keys)),
        )

        self.assertEqual(
            len(url_paths),
            len(set(url_paths)),
        )

    def test_detail_route_is_hidden(
        self,
    ) -> None:
        """確認詳細頁維持隱藏。"""

        self.assertTrue(
            ETF_DETAIL_ROUTE.hidden
        )

    def test_decision_profile_is_public_single_user_route(self) -> None:
        self.assertIn(DECISION_PROFILE_ROUTE, ALL_ROUTES)
        self.assertFalse(DECISION_PROFILE_ROUTE.hidden)
        self.assertEqual(
            DECISION_PROFILE_ROUTE.url_path,
            "decision-profile",
        )

    def test_detail_query_preserves_search_state(
        self,
    ) -> None:
        """確認搜尋條件會帶入詳細頁網址。"""

        params = build_detail_query_params(
            code=" 0050 ",
            source="etf-search",
            source_query_params={
                "keyword": "元大",
                "active": "all",
                "bond": "all",
                "page": "2",
                "page_size": "20",
            },
        )

        self.assertEqual(
            params["code"],
            "0050",
        )

        self.assertEqual(
            params["from"],
            "etf-search",
        )

        self.assertEqual(
            params["page"],
            "2",
        )

    def test_return_to_performance_ranking(
        self,
    ) -> None:
        """確認排行榜來源可正確返回。"""

        route, params = resolve_detail_return(
            {
                "from": "performance-ranking",
                "period": "1Y",
                "active": "passive",
                "bond": "bond",
                "page": "3",
                "page_size": "50",
            }
        )

        self.assertEqual(
            route,
            PERFORMANCE_RANKING_ROUTE,
        )

        self.assertEqual(
            params,
            {
                "period": "1Y",
                "active": "passive",
                "bond": "bond",
                "page": "3",
                "page_size": "50",
            },
        )

    def test_unknown_source_returns_to_search(
        self,
    ) -> None:
        """確認未知來源安全回到 ETF 查詢。"""

        self.assertEqual(
            normalize_detail_source(
                "unknown"
            ),
            "etf-search",
        )

        route, params = resolve_detail_return(
            {
                "from": "unknown",
                "page": "-1",
            }
        )

        self.assertEqual(
            route,
            ETF_SEARCH_ROUTE,
        )

        self.assertEqual(
            params["page"],
            "1",
        )


if __name__ == "__main__":
    unittest.main()
