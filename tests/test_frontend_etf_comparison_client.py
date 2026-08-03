"""ETF 比較前端 Client 測試。"""

import unittest
from unittest.mock import Mock, patch

from frontend.api_client import (
    APIResponseError,
    fetch_etf_comparison,
)


class TestFrontendETFComparisonClient(
    unittest.TestCase
):
    """驗證 ETF 比較回應契約。"""

    def build_item(
        self,
        code: str,
        name: str,
    ) -> dict:
        """建立合法比較項目。"""

        return {
            "etf": {
                "code": code,
                "name": name,
                "is_active": False,
                "is_bond": False,
                "listing_date": "2003-06-30",
                "fund_size": 5000.0,
                "expense_ratio": 0.43,
            },
            "performance_items": [
                {
                    "as_of_date": "2026-07-30",
                    "period_code": "1M",
                    "metric_code": "PRICE_RETURN",
                    "return_pct": 5.0,
                    "source_id": "twse_stock_day",
                },
            ],
            "dividend": {
                "event_count": 1,
                "latest_event_date": "2026-07-15",
                "latest_amount_per_unit": 0.7,
                "currency": "TWD",
            },
            "actual_76w": {
                "record_count": 1,
                "full_76w_count": 0,
                "latest_ratio_pct": 0.0,
                "average_ratio_pct": 0.0,
            },
            "data_profile": {
                "etf_code": code,
                "master": {
                    "sources": [
                        {
                            "source_id": "twse_openapi",
                            "display_name": (
                                "臺灣證券交易所 OpenAPI"
                            ),
                        },
                    ],
                    "latest_import_at": None,
                },
                "performance": {
                    "metric_code": "PRICE_RETURN",
                    "sources": [
                        {
                            "source_id": "twse_stock_day",
                            "display_name": (
                                "TWSE 個股日成交資訊"
                            ),
                        },
                    ],
                    "record_count": 1,
                    "available_periods": [
                        "1M",
                    ],
                    "latest_as_of_date": "2026-07-30",
                    "latest_import_at": None,
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
                        },
                    ],
                    "event_count": 1,
                    "latest_event_date": "2026-07-15",
                    "latest_import_at": None,
                },
                "actual_dividend": {
                    "sources": [
                        {
                            "source_id": (
                                "manual_actual_dividend_notice"
                            ),
                            "display_name": (
                                "人工核對正式通知書"
                            ),
                        },
                    ],
                    "actual_component_event_count": 1,
                    "actual_76w_event_count": 1,
                    "source_document_event_count": 0,
                    "latest_source_document_date": None,
                    "latest_import_at": None,
                },
            },
            "completeness": {
                "available_section_count": 4,
                "total_section_count": 5,
                "score_pct": 80.0,
                "available_sections": [
                    "ETF 主資料",
                    "市價績效",
                    "配息歷史",
                    "正式 76W",
                ],
                "missing_sections": [
                    "正式來源文件",
                ],
            },
        }

    def build_payload(self) -> dict:
        """建立合法完整回應。"""

        return {
            "codes": [
                "0050",
                "0056",
            ],
            "metric_code": "PRICE_RETURN",
            "periods": [
                "1M",
                "3M",
                "6M",
                "1Y",
            ],
            "items": [
                self.build_item(
                    "0050",
                    "元大台灣50",
                ),
                self.build_item(
                    "0056",
                    "元大高股息",
                ),
            ],
        }

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_comparison_is_returned(
        self,
        mock_get: Mock,
    ) -> None:
        """確認合法比較資料可解析。"""

        response = Mock()
        response.json.return_value = (
            self.build_payload()
        )
        response.raise_for_status.return_value = (
            None
        )
        mock_get.return_value = response

        result = fetch_etf_comparison(
            api_base_url=(
                "http://127.0.0.1:8000"
            ),
            codes=[
                "0050",
                "0056",
            ],
        )

        self.assertEqual(
            result["codes"],
            [
                "0050",
                "0056",
            ],
        )
        self.assertEqual(
            result["items"][0][
                "actual_76w"
            ]["latest_ratio_pct"],
            0.0,
        )
        self.assertEqual(
            mock_get.call_args.kwargs[
                "params"
            ]["codes"],
            "0050,0056",
        )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_mismatched_order_is_rejected(
        self,
        mock_get: Mock,
    ) -> None:
        """確認回傳順序不一致時拒絕。"""

        payload = self.build_payload()
        payload["items"].reverse()

        response = Mock()
        response.json.return_value = payload
        response.raise_for_status.return_value = (
            None
        )
        mock_get.return_value = response

        with self.assertRaises(
            APIResponseError
        ):
            fetch_etf_comparison(
                api_base_url=(
                    "http://127.0.0.1:8000"
                ),
                codes=[
                    "0050",
                    "0056",
                ],
            )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_invalid_completeness_is_rejected(
        self,
        mock_get: Mock,
    ) -> None:
        """確認完整度百分比必須符合計數。"""

        payload = self.build_payload()
        payload["items"][0][
            "completeness"
        ]["score_pct"] = 60.0

        response = Mock()
        response.json.return_value = payload
        response.raise_for_status.return_value = (
            None
        )
        mock_get.return_value = response

        with self.assertRaises(
            APIResponseError
        ):
            fetch_etf_comparison(
                api_base_url=(
                    "http://127.0.0.1:8000"
                ),
                codes=[
                    "0050",
                    "0056",
                ],
            )


if __name__ == "__main__":
    unittest.main()
