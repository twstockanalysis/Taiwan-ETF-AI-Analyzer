"""Streamlit URL Query State 測試。"""

import unittest

from frontend.query_state import (
    ETFSearchQueryState,
    PerformanceQueryState,
    parse_etf_search_query_state,
    parse_performance_query_state,
    sync_query_params,
)


class QueryParamsStub(dict):
    """模擬 Streamlit Query Parameters。"""

    def from_dict(
        self,
        values: dict[str, str],
    ) -> None:
        """以新值取代目前參數。"""

        self.clear()
        self.update(values)

    def to_dict(
        self,
    ) -> dict[str, str]:
        """回傳一般字典。"""

        return dict(self)


class TestFrontendQueryState(
    unittest.TestCase
):
    """驗證搜尋與排行榜網址狀態。"""

    def test_search_query_is_normalized(
        self,
    ) -> None:
        """確認 ETF 查詢參數可還原。"""

        state = parse_etf_search_query_state(
            {
                "keyword": " 00918 ",
                "active": "active",
                "bond": "non-bond",
                "page": "3",
                "page_size": "50",
            }
        )

        self.assertEqual(
            state,
            ETFSearchQueryState(
                keyword="00918",
                active_label="主動式",
                bond_label="非債券",
                page=3,
                page_size=50,
            ),
        )

    def test_invalid_search_query_uses_defaults(
        self,
    ) -> None:
        """確認不合法搜尋參數回到安全預設值。"""

        state = parse_etf_search_query_state(
            {
                "active": "unknown",
                "bond": "unknown",
                "page": "-2",
                "page_size": "999",
            }
        )

        self.assertEqual(
            state,
            ETFSearchQueryState(),
        )

    def test_repeated_query_uses_last_value(
        self,
    ) -> None:
        """確認重複 Query Key 採最後一值。"""

        state = parse_etf_search_query_state(
            {
                "page": [
                    "2",
                    "4",
                ],
            }
        )

        self.assertEqual(
            state.page,
            4,
        )

    def test_performance_query_is_normalized(
        self,
    ) -> None:
        """確認排行榜參數可還原。"""

        state = (
            parse_performance_query_state(
                {
                    "period": "1y",
                    "active": "passive",
                    "bond": "bond",
                    "page": "2",
                    "page_size": "10",
                }
            )
        )

        self.assertEqual(
            state,
            PerformanceQueryState(
                period="1Y",
                active_label="被動式",
                bond_label="債券",
                page=2,
                page_size=10,
            ),
        )

    def test_invalid_performance_query_uses_defaults(
        self,
    ) -> None:
        """確認不合法排行榜參數回預設值。"""

        state = (
            parse_performance_query_state(
                {
                    "period": "2Y",
                    "active": "other",
                    "bond": "other",
                    "page": "0",
                    "page_size": "0",
                }
            )
        )

        self.assertEqual(
            state,
            PerformanceQueryState(),
        )

    def test_search_state_serializes_stably(
        self,
    ) -> None:
        """確認搜尋狀態輸出穩定網址參數。"""

        state = ETFSearchQueryState(
            keyword="元大",
            active_label="全部",
            bond_label="債券",
            page=2,
            page_size=20,
        )

        self.assertEqual(
            state.to_query_params(),
            {
                "active": "all",
                "bond": "bond",
                "page": "2",
                "page_size": "20",
                "keyword": "元大",
            },
        )

    def test_sync_query_params_is_idempotent(
        self,
    ) -> None:
        """確認相同狀態不重寫網址。"""

        params = QueryParamsStub(
            {
                "page": "1",
            }
        )

        self.assertFalse(
            sync_query_params(
                params,
                {
                    "page": "1",
                },
            )
        )

        self.assertTrue(
            sync_query_params(
                params,
                {
                    "page": "2",
                },
            )
        )

        self.assertEqual(
            params,
            {
                "page": "2",
            },
        )


if __name__ == "__main__":
    unittest.main()
