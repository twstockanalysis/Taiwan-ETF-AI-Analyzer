"""前端多期間績效排行榜 Client 測試。"""

import unittest
from unittest.mock import Mock, patch

from frontend.api_client import (
    APIResponseError,
    fetch_multi_period_performance_ranking,
)


class TestFrontendMultiPeriodPerformanceClient(
    unittest.TestCase
):
    """測試多期間排行榜回應驗證。"""

    def build_payload(self) -> dict:
        """建立合法 API 回應。"""

        return {
            "sort_period": "6M",
            "metric_code": "PRICE_RETURN",
            "periods": [
                "1M",
                "3M",
                "6M",
                "1Y",
            ],
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
                    "sort_period": "6M",
                    "sort_as_of_date": (
                        "2026-07-29"
                    ),
                    "sort_return_pct": 12.0,
                    "source_id": (
                        "twse_stock_day"
                    ),
                    "performance_items": [
                        {
                            "as_of_date": (
                                "2026-07-29"
                            ),
                            "period_code": "1M",
                            "metric_code": (
                                "PRICE_RETURN"
                            ),
                            "return_pct": 4.0,
                            "source_id": (
                                "twse_stock_day"
                            ),
                        },
                        {
                            "as_of_date": (
                                "2026-07-29"
                            ),
                            "period_code": "6M",
                            "metric_code": (
                                "PRICE_RETURN"
                            ),
                            "return_pct": 12.0,
                            "source_id": (
                                "twse_stock_day"
                            ),
                        },
                    ],
                }
            ],
        }

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_all_available_periods_are_returned(
        self,
        mock_get: Mock,
    ) -> None:
        """確認缺少 3M 不會被補成零。"""

        response = Mock()
        response.json.return_value = (
            self.build_payload()
        )
        response.raise_for_status.return_value = (
            None
        )
        mock_get.return_value = response

        result = (
            fetch_multi_period_performance_ranking(
                "http://127.0.0.1:8000"
            )
        )

        self.assertEqual(
            [
                item["period_code"]
                for item in result["items"][0][
                    "performance_items"
                ]
            ],
            [
                "1M",
                "6M",
            ],
        )

        self.assertEqual(
            mock_get.call_args.kwargs[
                "params"
            ]["sort_period"],
            "6M",
        )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_inconsistent_sort_summary_is_rejected(
        self,
        mock_get: Mock,
    ) -> None:
        """確認排序摘要不得與 6M 明細矛盾。"""

        payload = self.build_payload()
        payload["items"][0][
            "sort_return_pct"
        ] = 99.0

        response = Mock()
        response.json.return_value = payload
        response.raise_for_status.return_value = (
            None
        )
        mock_get.return_value = response

        with self.assertRaises(
            APIResponseError
        ):
            fetch_multi_period_performance_ranking(
                "http://127.0.0.1:8000"
            )


if __name__ == "__main__":
    unittest.main()
