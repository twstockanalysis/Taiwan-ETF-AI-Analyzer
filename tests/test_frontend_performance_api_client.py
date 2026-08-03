"""Streamlit 績效 API Client 測試。"""

import unittest
from unittest.mock import Mock, patch

from frontend.api_client import (
    APIResponseError,
    fetch_etf_performance,
    fetch_performance_ranking,
)


class TestFrontendPerformanceAPIClient(
    unittest.TestCase
):
    """測試前端績效 API Client。"""

    def build_ranking_payload(
        self,
    ) -> dict:
        """建立合法排行榜回應。"""

        return {
            "period_code": "6M",
            "metric_code": "PRICE_RETURN",
            "total": 1,
            "limit": 20,
            "offset": 0,
            "items": [
                {
                    "rank": 1,
                    "etf_code": "0050",
                    "name": "元大台灣50",
                    "is_active": False,
                    "is_bond": False,
                    "as_of_date": "2026-07-29",
                    "period_code": "6M",
                    "metric_code": (
                        "PRICE_RETURN"
                    ),
                    "return_pct": 20.0,
                    "source_id": (
                        "twse_stock_day"
                    ),
                }
            ],
        }

    def build_detail_payload(
        self,
    ) -> dict:
        """建立合法 ETF 績效回應。"""

        return {
            "etf_code": "0050",
            "metric_code": "PRICE_RETURN",
            "items": [
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
                    "period_code": "1M",
                    "metric_code": (
                        "PRICE_RETURN"
                    ),
                    "return_pct": 5.0,
                    "source_id": (
                        "twse_stock_day"
                    ),
                },
            ],
        }

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_ranking_is_returned(
        self,
        mock_get: Mock,
    ) -> None:
        """確認合法排行榜可以解析。"""

        response = Mock()
        response.json.return_value = (
            self.build_ranking_payload()
        )
        response.raise_for_status.return_value = (
            None
        )

        mock_get.return_value = response

        result = fetch_performance_ranking(
            api_base_url=(
                "http://127.0.0.1:8000"
            ),
        )

        self.assertEqual(
            result["period_code"],
            "6M",
        )

        self.assertEqual(
            result["items"][0]["rank"],
            1,
        )

        self.assertEqual(
            result["items"][0]["return_pct"],
            20.0,
        )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_ranking_query_parameters(
        self,
        mock_get: Mock,
    ) -> None:
        """確認排行榜查詢參數正確送出。"""

        response = Mock()

        payload = self.build_ranking_payload()
        payload["period_code"] = "3M"
        payload["limit"] = 10
        payload["offset"] = 20
        payload["items"][0][
            "period_code"
        ] = "3M"

        response.json.return_value = payload
        response.raise_for_status.return_value = (
            None
        )

        mock_get.return_value = response

        fetch_performance_ranking(
            api_base_url=(
                "http://127.0.0.1:8000"
            ),
            period="3m",
            is_active=True,
            is_bond=False,
            limit=10,
            offset=20,
        )

        params = mock_get.call_args.kwargs[
            "params"
        ]

        self.assertEqual(
            params,
            {
                "period": "3M",
                "metric": "PRICE_RETURN",
                "is_active": "true",
                "is_bond": "false",
                "limit": 10,
                "offset": 20,
            },
        )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_mixed_ranking_period_is_rejected(
        self,
        mock_get: Mock,
    ) -> None:
        """確認排行榜不可混入其他期間。"""

        response = Mock()

        payload = self.build_ranking_payload()
        payload["items"][0][
            "period_code"
        ] = "3M"

        response.json.return_value = payload
        response.raise_for_status.return_value = (
            None
        )

        mock_get.return_value = response

        with self.assertRaises(
            APIResponseError
        ):
            fetch_performance_ranking(
                "http://127.0.0.1:8000"
            )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_etf_performance_is_sorted(
        self,
        mock_get: Mock,
    ) -> None:
        """確認 ETF 績效依固定期間排序。"""

        response = Mock()
        response.json.return_value = (
            self.build_detail_payload()
        )
        response.raise_for_status.return_value = (
            None
        )

        mock_get.return_value = response

        result = fetch_etf_performance(
            api_base_url=(
                "http://127.0.0.1:8000"
            ),
            code=" 0050 ",
        )

        self.assertEqual(
            [
                item["period_code"]
                for item in result["items"]
            ],
            [
                "1M",
                "6M",
            ],
        )

        requested_url = (
            mock_get.call_args.args[0]
        )

        self.assertTrue(
            requested_url.endswith(
                "/api/v1/etfs/"
                "0050/performance"
            )
        )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_duplicate_period_is_rejected(
        self,
        mock_get: Mock,
    ) -> None:
        """確認 ETF 績效不可重複期間。"""

        response = Mock()

        payload = self.build_detail_payload()
        payload["items"][1][
            "period_code"
        ] = "6M"

        response.json.return_value = payload
        response.raise_for_status.return_value = (
            None
        )

        mock_get.return_value = response

        with self.assertRaises(
            APIResponseError
        ):
            fetch_etf_performance(
                api_base_url=(
                    "http://127.0.0.1:8000"
                ),
                code="0050",
            )

    def test_invalid_period_is_rejected(
        self,
    ) -> None:
        """確認前端拒絕不支援期間。"""

        with self.assertRaises(
            ValueError
        ):
            fetch_performance_ranking(
                api_base_url=(
                    "http://127.0.0.1:8000"
                ),
                period="1W",
            )


if __name__ == "__main__":
    unittest.main()
