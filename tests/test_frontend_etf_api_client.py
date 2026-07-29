"""Streamlit ETF API Client 測試。"""

import unittest
from unittest.mock import Mock, patch

import httpx

from frontend.api_client import (
    APIResponseError,
    fetch_etfs,
)


class TestFrontendETFAPIClient(
    unittest.TestCase
):
    """測試前端 ETF 列表 API Client。"""

    def build_valid_payload(
        self,
    ) -> dict:
        """建立合法 ETF 列表回應。"""

        return {
            "items": [
                {
                    "code": "00918",
                    "name": (
                        "大華優利高填息30"
                    ),
                    "is_active": False,
                    "is_bond": False,
                    "listing_date": (
                        "2022-11-24"
                    ),
                    "fund_size": None,
                    "expense_ratio": None,
                }
            ],
            "total": 1,
            "limit": 20,
            "offset": 0,
        }

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_fetch_etfs_returns_data(
        self,
        mock_get: Mock,
    ) -> None:
        """確認合法 ETF 回應可解析。"""

        response = Mock()
        response.json.return_value = (
            self.build_valid_payload()
        )
        response.raise_for_status.return_value = (
            None
        )

        mock_get.return_value = response

        result = fetch_etfs(
            api_base_url=(
                "http://127.0.0.1:8000"
            ),
        )

        self.assertEqual(
            result["total"],
            1,
        )

        self.assertEqual(
            result["items"][0]["code"],
            "00918",
        )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_query_parameters_are_sent(
        self,
        mock_get: Mock,
    ) -> None:
        """確認篩選及分頁參數正確送出。"""

        response = Mock()

        payload = self.build_valid_payload()
        payload["limit"] = 10
        payload["offset"] = 20

        response.json.return_value = payload
        response.raise_for_status.return_value = (
            None
        )

        mock_get.return_value = response

        fetch_etfs(
            api_base_url=(
                "http://127.0.0.1:8000"
            ),
            keyword=" 00918 ",
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
                "keyword": "00918",
                "is_active": "true",
                "is_bond": "false",
                "limit": 10,
                "offset": 20,
            },
        )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_empty_filters_are_omitted(
        self,
        mock_get: Mock,
    ) -> None:
        """確認未使用的篩選條件不會傳送。"""

        response = Mock()
        response.json.return_value = (
            self.build_valid_payload()
        )
        response.raise_for_status.return_value = (
            None
        )

        mock_get.return_value = response

        fetch_etfs(
            api_base_url=(
                "http://127.0.0.1:8000"
            ),
            keyword=" ",
            is_active=None,
            is_bond=None,
        )

        params = mock_get.call_args.kwargs[
            "params"
        ]

        self.assertEqual(
            params,
            {
                "limit": 20,
                "offset": 0,
            },
        )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_invalid_payload_is_rejected(
        self,
        mock_get: Mock,
    ) -> None:
        """確認錯誤 ETF 格式被拒絕。"""

        response = Mock()
        response.json.return_value = {
            "items": "invalid",
            "total": 1,
            "limit": 20,
            "offset": 0,
        }
        response.raise_for_status.return_value = (
            None
        )

        mock_get.return_value = response

        with self.assertRaises(
            APIResponseError
        ):
            fetch_etfs(
                "http://127.0.0.1:8000"
            )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_http_error_is_converted(
        self,
        mock_get: Mock,
    ) -> None:
        """確認 HTTP 錯誤轉成前端錯誤。"""

        request = httpx.Request(
            "GET",
            (
                "http://127.0.0.1:8000/"
                "api/v1/etfs"
            ),
        )

        response = httpx.Response(
            status_code=500,
            request=request,
            json={
                "detail": "伺服器錯誤",
            },
        )

        mock_get.return_value = response

        with self.assertRaises(
            APIResponseError
        ) as context:
            fetch_etfs(
                "http://127.0.0.1:8000"
            )

        self.assertIn(
            "伺服器錯誤",
            str(context.exception),
        )

    def test_invalid_page_size_is_rejected(
        self,
    ) -> None:
        """確認錯誤分頁筆數被拒絕。"""

        with self.assertRaises(
            ValueError
        ):
            fetch_etfs(
                api_base_url=(
                    "http://127.0.0.1:8000"
                ),
                limit=0,
            )


if __name__ == "__main__":
    unittest.main()