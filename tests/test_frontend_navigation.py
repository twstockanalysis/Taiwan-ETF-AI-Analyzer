"""Streamlit 導覽與返回狀態測試。"""

import unittest

from frontend.navigation import (
    ADMIN_OVERVIEW_ROUTE,
    ALL_ROUTES,
    DECISION_PROFILE_ROUTE,
    DIVIDEND_DATA_QUALITY_ROUTE,
    ETF_DETAIL_ROUTE,
    ETF_SEARCH_ROUTE,
    PERFORMANCE_RANKING_ROUTE,
    PUBLIC_PLANNER_ROUTE,
    build_detail_query_params,
    normalize_detail_source,
    resolve_detail_return,
    navigation_groups,
    navigation_routes,
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

    def test_public_navigation_places_ranking_before_search(
        self,
    ) -> None:
        """確認股利試算後依序顯示績效排行榜與搜尋。"""

        routes = navigation_routes(False)

        self.assertEqual(
            routes[1:4],
            (
                PUBLIC_PLANNER_ROUTE,
                PERFORMANCE_RANKING_ROUTE,
                ETF_SEARCH_ROUTE,
            ),
        )

    def test_public_navigation_is_not_collapsible_group(self) -> None:
        """確認公開導覽不顯示可收合的群組標題。"""

        groups = navigation_groups(False)
        self.assertEqual(list(groups), [""])

    def test_detail_route_is_hidden(
        self,
    ) -> None:
        """確認詳細頁維持隱藏。"""

        self.assertTrue(
            ETF_DETAIL_ROUTE.hidden
        )

    def test_decision_profile_is_owner_only_route(self) -> None:
        self.assertIn(DECISION_PROFILE_ROUTE, ALL_ROUTES)
        self.assertFalse(DECISION_PROFILE_ROUTE.hidden)
        self.assertEqual(
            DECISION_PROFILE_ROUTE.url_path,
            "decision-profile",
        )
        self.assertNotIn(DECISION_PROFILE_ROUTE, navigation_routes(False))
        self.assertIn(DECISION_PROFILE_ROUTE, navigation_routes(True))

    def test_admin_overview_is_owner_only_route(self) -> None:
        self.assertIn(ADMIN_OVERVIEW_ROUTE, ALL_ROUTES)
        self.assertEqual(ADMIN_OVERVIEW_ROUTE.url_path, "admin-overview")
        self.assertNotIn(ADMIN_OVERVIEW_ROUTE, navigation_routes(False))
        self.assertIn(ADMIN_OVERVIEW_ROUTE, navigation_routes(True))

    def test_dividend_quality_is_grouped_under_admin(self) -> None:
        """確認配息資料品質只出現在管理者功能。"""

        self.assertNotIn(
            DIVIDEND_DATA_QUALITY_ROUTE,
            navigation_routes(False),
        )
        self.assertIn(
            DIVIDEND_DATA_QUALITY_ROUTE,
            navigation_routes(True),
        )
        self.assertNotIn(
            "管理者功能",
            navigation_groups(False),
        )
        self.assertIn(
            DIVIDEND_DATA_QUALITY_ROUTE,
            navigation_groups(True)["管理者功能"],
        )

    def test_public_planner_is_always_available(self) -> None:
        self.assertIn(PUBLIC_PLANNER_ROUTE, navigation_routes(False))
        self.assertIn(PUBLIC_PLANNER_ROUTE, navigation_routes(True))
        self.assertEqual(PUBLIC_PLANNER_ROUTE.url_path, "cash-flow-planner")

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
