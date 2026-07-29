"""Streamlit 前端 API Client 測試。"""

import os
import unittest
from unittest.mock import Mock, patch

import httpx

from frontend.api_client import (
    APIConnectionError,
    APIResponseError,
    fetch_api_health,
)
from frontend.config import (
    DEFAULT_API_BASE_URL,
    get_api_base_url,
)


class TestFrontendAPIClient(unittest.TestCase):
    """測試前端設定及 FastAPI Client。"""

    def test_default_api_url(
        self,
    ) -> None:
        """確認未設定環境變數時使用預設網址。"""

        with patch.dict(
            os.environ,
            {},
            clear=True,
        ):
            self.assertEqual(
                get_api_base_url(),
                DEFAULT_API_BASE_URL,
            )

    def test_environment_api_url(
        self,
    ) -> None:
        """確認可從環境變數設定 API 網址。"""

        with patch.dict(
            os.environ,
            {
                "TW_ETF_API_URL": (
                    "https://api.example.test/"
                ),
            },
            clear=True,
        ):
            self.assertEqual(
                get_api_base_url(),
                "https://api.example.test",
            )

    def test_invalid_api_url(
        self,
    ) -> None:
        """確認不合法 API URL 被拒絕。"""

        with patch.dict(
            os.environ,
            {
                "TW_ETF_API_URL": (
                    "api.example.test"
                ),
            },
            clear=True,
        ):
            with self.assertRaises(
                ValueError
            ):
                get_api_base_url()

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_healthy_api_response(
        self,
        mock_get: Mock,
    ) -> None:
        """確認 healthy 回應可正常解析。"""

        response = Mock()
        response.json.return_value = {
            "status": "healthy",
        }
        response.raise_for_status.return_value = (
            None
        )

        mock_get.return_value = response

        result = fetch_api_health(
            "http://127.0.0.1:8000"
        )

        self.assertEqual(
            result,
            {
                "status": "healthy",
            },
        )

        mock_get.assert_called_once()

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_connection_error(
        self,
        mock_get: Mock,
    ) -> None:
        """確認連線失敗會轉成前端錯誤。"""

        request = httpx.Request(
            "GET",
            "http://127.0.0.1:8000/health",
        )

        mock_get.side_effect = (
            httpx.ConnectError(
                "connection failed",
                request=request,
            )
        )

        with self.assertRaises(
            APIConnectionError
        ):
            fetch_api_health(
                "http://127.0.0.1:8000"
            )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_invalid_health_payload(
        self,
        mock_get: Mock,
    ) -> None:
        """確認不正確的狀態被拒絕。"""

        response = Mock()
        response.json.return_value = {
            "status": "unhealthy",
        }
        response.raise_for_status.return_value = (
            None
        )

        mock_get.return_value = response

        with self.assertRaises(
            APIResponseError
        ):
            fetch_api_health(
                "http://127.0.0.1:8000"
            )


if __name__ == "__main__":
    unittest.main()