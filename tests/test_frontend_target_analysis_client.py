"""測試目標現金流前端 API client。"""

import unittest
from unittest.mock import patch

from frontend.api.errors import APIResponseError
from frontend.api.target_analysis import (
    fetch_etf_latest_close,
    fetch_etf_price_history,
    fetch_etf_target_analysis,
    validate_latest_close,
    validate_price_history,
)


class TestFrontendTargetAnalysisClient(unittest.TestCase):
    @patch("frontend.api.transport.httpx.get")
    def test_fetches_latest_close_path(self, mock_get) -> None:
        mock_get.return_value.json.return_value = {
            "etf_code": "0056",
            "name": "元大高股息",
            "close_price": 35.25,
            "trade_date": "2026-08-07",
            "source_id": "TWSE_STOCK_DAY",
        }
        result = fetch_etf_latest_close("http://api", "0056")
        self.assertEqual(result["close_price"], 35.25)
        self.assertIn("/api/v1/etfs/0056/latest-close", mock_get.call_args.args[0])

    def test_rejects_partial_price_provenance(self) -> None:
        with self.assertRaises(APIResponseError):
            validate_latest_close(
                {
                    "etf_code": "0056",
                    "name": "元大高股息",
                    "close_price": 35.25,
                    "trade_date": None,
                    "source_id": None,
                }
            )

    @patch("frontend.api.transport.httpx.get")
    def test_fetches_validated_price_history(self, mock_get) -> None:
        """確認歷史收盤價 client 傳遞筆數並保留交易日排序。"""

        mock_get.return_value.json.return_value = {
            "etf_code": "0056",
            "name": "元大高股息",
            "items": [
                {
                    "trade_date": "2026-08-01",
                    "close_price": 35.1,
                    "source_id": "twse_stock_day",
                },
                {
                    "trade_date": "2026-08-04",
                    "close_price": 35.25,
                    "source_id": "twse_stock_day",
                },
            ],
        }

        result = fetch_etf_price_history(
            "http://api",
            "0056",
            limit=260,
        )

        self.assertEqual(len(result["items"]), 2)
        self.assertIn(
            "/api/v1/etfs/0056/price-history",
            mock_get.call_args.args[0],
        )
        self.assertEqual(
            mock_get.call_args.kwargs["params"],
            {"limit": 260},
        )

    def test_rejects_unsorted_price_history(self) -> None:
        """確認前端拒絕日期倒序或重複的走勢資料。"""

        with self.assertRaises(APIResponseError):
            validate_price_history(
                {
                    "etf_code": "0056",
                    "name": "元大高股息",
                    "items": [
                        {
                            "trade_date": "2026-08-04",
                            "close_price": 35.25,
                            "source_id": "twse_stock_day",
                        },
                        {
                            "trade_date": "2026-08-01",
                            "close_price": 35.1,
                            "source_id": "twse_stock_day",
                        },
                    ],
                }
            )

    @patch("frontend.api.transport.httpx.post")
    def test_posts_target_analysis_and_requires_twelve_months(
        self, mock_post
    ) -> None:
        mock_post.return_value.json.return_value = {
            "status": "AVAILABLE",
            "cash_flow": {},
            "scenario_estimate": {},
            "warnings": [
                {
                    "code": "PERSISTENT_PRICE_DECLINE",
                    "message": "最近三個月末收盤價連續下跌。",
                    "affected_fields": ["ending_holding_value"],
                    "as_of_date": "2026-08-07",
                    "source_id": "twse_stock_day",
                    "evidence": {"decline_pct": -12},
                }
            ],
            "unavailable_fields": [],
            "monthly_cash_flow": [
                {
                    "month": month,
                    "event_count": 0,
                    "observed_year_count": 0,
                    "annualized_gross_cash": None,
                    "annualized_after_tax_cash": None,
                    "latest_payment_date": None,
                }
                for month in range(1, 13)
            ],
        }
        result = fetch_etf_target_analysis(
            "http://api", "0056", {"held_units": 0}
        )
        self.assertEqual(len(result["monthly_cash_flow"]), 12)
        self.assertEqual(
            result["warnings"][0]["as_of_date"], "2026-08-07"
        )
        self.assertIn("/api/v1/etfs/0056/target-analysis", mock_post.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
