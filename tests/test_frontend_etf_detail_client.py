"""Streamlit ETF 詳細資料 Client 測試。"""

import unittest
from unittest.mock import Mock, patch

import httpx

from frontend.api_client import (
    APIResourceNotFoundError,
    APIResponseError,
    fetch_etf_by_code,
)


class TestFrontendETFDetailClient(
    unittest.TestCase
):
    """測試前端單筆 ETF API Client。"""

    def build_valid_payload(
        self,
        code: str = "00918",
    ) -> dict:
        """建立合法單筆 ETF 回應。"""

        return {
            "code": code,
            "name": "大華優利高填息30",
            "is_active": False,
            "is_bond": False,
            "listing_date": "2022-11-24",
            "fund_size": None,
            "expense_ratio": None,
        }

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_etf_detail_is_returned(
        self,
        mock_get: Mock,
    ) -> None:
        """確認合法詳細資料可解析。"""

        response = Mock()
        response.json.return_value = (
            self.build_valid_payload()
        )
        response.raise_for_status.return_value = (
            None
        )

        mock_get.return_value = response

        result = fetch_etf_by_code(
            api_base_url=(
                "http://127.0.0.1:8000"
            ),
            code="00918",
        )

        self.assertEqual(
            result["code"],
            "00918",
        )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_code_is_normalized(
        self,
        mock_get: Mock,
    ) -> None:
        """確認代號會去空白並轉大寫。"""

        response = Mock()
        response.json.return_value = (
            self.build_valid_payload(
                code="00980A"
            )
        )
        response.raise_for_status.return_value = (
            None
        )

        mock_get.return_value = response

        result = fetch_etf_by_code(
            api_base_url=(
                "http://127.0.0.1:8000"
            ),
            code=" 00980a ",
        )

        self.assertEqual(
            result["code"],
            "00980A",
        )

        requested_url = (
            mock_get.call_args.args[0]
        )

        self.assertTrue(
            requested_url.endswith(
                "/api/v1/etfs/00980A"
            )
        )

    def test_empty_code_is_rejected(
        self,
    ) -> None:
        """確認空白 ETF 代號被拒絕。"""

        with self.assertRaises(
            ValueError
        ):
            fetch_etf_by_code(
                api_base_url=(
                    "http://127.0.0.1:8000"
                ),
                code=" ",
            )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_missing_etf_returns_not_found(
        self,
        mock_get: Mock,
    ) -> None:
        """確認 HTTP 404 轉成找不到錯誤。"""

        request = httpx.Request(
            "GET",
            (
                "http://127.0.0.1:8000/"
                "api/v1/etfs/UNKNOWN"
            ),
        )

        response = httpx.Response(
            status_code=404,
            request=request,
            json={
                "detail": (
                    "找不到 ETF：UNKNOWN"
                ),
            },
        )

        mock_get.return_value = response

        with self.assertRaises(
            APIResourceNotFoundError
        ):
            fetch_etf_by_code(
                api_base_url=(
                    "http://127.0.0.1:8000"
                ),
                code="UNKNOWN",
            )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_mismatched_code_is_rejected(
        self,
        mock_get: Mock,
    ) -> None:
        """確認回傳代號不一致時被拒絕。"""

        response = Mock()
        response.json.return_value = (
            self.build_valid_payload(
                code="0050"
            )
        )
        response.raise_for_status.return_value = (
            None
        )

        mock_get.return_value = response

        with self.assertRaises(
            APIResponseError
        ):
            fetch_etf_by_code(
                api_base_url=(
                    "http://127.0.0.1:8000"
                ),
                code="00918",
            )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_missing_field_is_rejected(
        self,
        mock_get: Mock,
    ) -> None:
        """確認缺少必要欄位時被拒絕。"""

        payload = (
            self.build_valid_payload()
        )

        del payload["name"]

        response = Mock()
        response.json.return_value = payload
        response.raise_for_status.return_value = (
            None
        )

        mock_get.return_value = response

        with self.assertRaises(
            APIResponseError
        ):
            fetch_etf_by_code(
                api_base_url=(
                    "http://127.0.0.1:8000"
                ),
                code="00918",
            )


if __name__ == "__main__":
    unittest.main()