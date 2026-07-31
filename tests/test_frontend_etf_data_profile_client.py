"""ETF 資料來源與新鮮度前端 Client 測試。"""

import unittest
from unittest.mock import Mock, patch

from frontend.api_client import (
    APIResponseError,
    fetch_etf_data_profile,
)


class TestFrontendETFDataProfileClient(
    unittest.TestCase
):
    """測試 ETF 資料概況前端驗證。"""

    def build_valid_payload(
        self,
        code: str = "0050",
    ) -> dict:
        """建立合法資料概況回應。"""

        return {
            "etf_code": code,
            "master": {
                "sources": [
                    {
                        "source_id": "twse_openapi",
                        "display_name": (
                            "臺灣證券交易所 OpenAPI"
                        ),
                    }
                ],
                "latest_import_at": (
                    "2026-07-30T00:05:00+00:00"
                ),
            },
            "performance": {
                "metric_code": "PRICE_RETURN",
                "sources": [
                    {
                        "source_id": "twse_stock_day",
                        "display_name": (
                            "TWSE 個股日成交資訊"
                        ),
                    }
                ],
                "record_count": 4,
                "available_periods": [
                    "1M",
                    "3M",
                    "6M",
                    "1Y",
                ],
                "latest_as_of_date": "2026-07-30",
                "latest_import_at": (
                    "2026-07-30T01:05:00+00:00"
                ),
            },
            "dividends": {
                "sources": [
                    {
                        "source_id": (
                            "twse_etfortune_dividend"
                        ),
                        "display_name": (
                            "TWSE ETF e添富配息清單"
                        ),
                    }
                ],
                "event_count": 2,
                "latest_event_date": "2026-07-15",
                "latest_import_at": (
                    "2026-07-30T02:05:00+00:00"
                ),
            },
            "actual_dividend": {
                "sources": [
                    {
                        "source_id": (
                            "cathay_actual_dividend_announcement"
                        ),
                        "display_name": (
                            "國泰證券投資信託股份有限公司"
                        ),
                    }
                ],
                "actual_component_event_count": 1,
                "actual_76w_event_count": 1,
                "source_document_event_count": 1,
                "latest_source_document_date": (
                    "2026-07-20"
                ),
                "latest_import_at": (
                    "2026-07-30T03:05:00+00:00"
                ),
            },
        }

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_profile_is_returned(
        self,
        mock_get: Mock,
    ) -> None:
        """確認合法資料概況可解析。"""

        response = Mock()
        response.json.return_value = (
            self.build_valid_payload()
        )
        response.raise_for_status.return_value = (
            None
        )

        mock_get.return_value = response

        result = fetch_etf_data_profile(
            api_base_url=(
                "http://127.0.0.1:8000"
            ),
            code=" 0050 ",
        )

        self.assertEqual(
            result["etf_code"],
            "0050",
        )

        self.assertEqual(
            result["performance"][
                "available_periods"
            ],
            [
                "1M",
                "3M",
                "6M",
                "1Y",
            ],
        )

        requested_url = (
            mock_get.call_args.args[0]
        )

        self.assertTrue(
            requested_url.endswith(
                "/api/v1/etfs/0050/data-profile"
            )
        )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_mismatched_code_is_rejected(
        self,
        mock_get: Mock,
    ) -> None:
        """確認回傳代號不一致時拒絕。"""

        response = Mock()
        response.json.return_value = (
            self.build_valid_payload(
                code="00918"
            )
        )
        response.raise_for_status.return_value = (
            None
        )

        mock_get.return_value = response

        with self.assertRaises(
            APIResponseError
        ):
            fetch_etf_data_profile(
                api_base_url=(
                    "http://127.0.0.1:8000"
                ),
                code="0050",
            )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_invalid_actual_counts_are_rejected(
        self,
        mock_get: Mock,
    ) -> None:
        """確認 76W 事件數不可大於 ACTUAL。"""

        payload = (
            self.build_valid_payload()
        )

        payload["actual_dividend"][
            "actual_76w_event_count"
        ] = 2

        response = Mock()
        response.json.return_value = payload
        response.raise_for_status.return_value = (
            None
        )

        mock_get.return_value = response

        with self.assertRaises(
            APIResponseError
        ):
            fetch_etf_data_profile(
                api_base_url=(
                    "http://127.0.0.1:8000"
                ),
                code="0050",
            )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_zero_performance_keeps_missing_date(
        self,
        mock_get: Mock,
    ) -> None:
        """確認零筆績效不得附帶偽造日期。"""

        payload = (
            self.build_valid_payload()
        )

        payload["performance"][
            "record_count"
        ] = 0

        payload["performance"][
            "available_periods"
        ] = []

        payload["performance"][
            "latest_as_of_date"
        ] = "2026-07-30"

        response = Mock()
        response.json.return_value = payload
        response.raise_for_status.return_value = (
            None
        )

        mock_get.return_value = response

        with self.assertRaises(
            APIResponseError
        ):
            fetch_etf_data_profile(
                api_base_url=(
                    "http://127.0.0.1:8000"
                ),
                code="0050",
            )


if __name__ == "__main__":
    unittest.main()
