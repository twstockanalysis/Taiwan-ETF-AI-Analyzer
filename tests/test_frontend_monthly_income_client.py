"""前端每月領息 API Client 測試。"""

import unittest
from unittest.mock import Mock, patch

from frontend.api_client import (
    APIResponseError,
    fetch_etf_monthly_income,
)


class TestFrontendMonthlyIncomeClient(
    unittest.TestCase
):
    """驗證每月領息回應與查詢契約。"""

    def build_payload(self) -> dict:
        """建立合法的 12 個月份回應。"""

        months = [
            {
                "month": month,
                "event_count": 0,
                "observed_year_count": 0,
                "total_amount_per_unit": None,
                "average_amount_per_event": None,
                "latest_payment_date": None,
            }
            for month in range(1, 13)
        ]

        months[0].update(
            {
                "event_count": 2,
                "observed_year_count": 2,
                "total_amount_per_unit": 1.1,
                "average_amount_per_event": 0.55,
                "latest_payment_date": "2026-01-15",
            }
        )

        months[3].update(
            {
                "event_count": 1,
                "observed_year_count": 1,
                "total_amount_per_unit": 0.7,
                "average_amount_per_event": 0.7,
                "latest_payment_date": "2026-04-15",
            }
        )

        return {
            "etf_code": "00918",
            "name": "大華優利高填息30",
            "date_basis": "PAYMENT_DATE",
            "lookback_years": 3,
            "as_of_date": "2026-04-15",
            "window_start_date": "2023-04-16",
            "total_dividend_event_count": 4,
            "dated_dividend_event_count": 3,
            "missing_payment_date_count": 1,
            "analysis_event_count": 3,
            "covered_month_count": 2,
            "covered_month_occurrence_count": 3,
            "analysis_currency": "TWD",
            "has_mixed_currencies": False,
            "total_amount_per_unit": 1.8,
            "months": months,
        }

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_request_uses_code_and_lookback(
        self,
        mock_get: Mock,
    ) -> None:
        """確認網址、代號與回看年數正確。"""

        response = Mock()
        response.json.return_value = (
            self.build_payload()
        )
        response.raise_for_status.return_value = (
            None
        )
        mock_get.return_value = response

        result = fetch_etf_monthly_income(
            "http://127.0.0.1:8000",
            " 00918 ",
            lookback_years=3,
        )

        self.assertEqual(
            result["etf_code"],
            "00918",
        )

        self.assertTrue(
            mock_get.call_args.args[0].endswith(
                "/api/v1/etfs/00918/"
                "monthly-income"
            )
        )

        self.assertEqual(
            mock_get.call_args.kwargs["params"],
            {
                "lookback_years": 3,
            },
        )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_twelve_months_preserve_zero_semantics(
        self,
        mock_get: Mock,
    ) -> None:
        """確認無事件月份保留零筆與空金額。"""

        response = Mock()
        response.json.return_value = (
            self.build_payload()
        )
        response.raise_for_status.return_value = (
            None
        )
        mock_get.return_value = response

        result = fetch_etf_monthly_income(
            "http://127.0.0.1:8000",
            "00918",
        )

        self.assertEqual(
            len(result["months"]),
            12,
        )

        march = result["months"][2]

        self.assertEqual(
            march["event_count"],
            0,
        )

        self.assertIsNone(
            march["total_amount_per_unit"]
        )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_missing_month_is_rejected(
        self,
        mock_get: Mock,
    ) -> None:
        """確認少於 12 個月份時拒絕回應。"""

        payload = self.build_payload()
        payload["months"].pop()

        response = Mock()
        response.json.return_value = payload
        response.raise_for_status.return_value = (
            None
        )
        mock_get.return_value = response

        with self.assertRaises(
            APIResponseError
        ):
            fetch_etf_monthly_income(
                "http://127.0.0.1:8000",
                "00918",
            )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_inconsistent_event_total_is_rejected(
        self,
        mock_get: Mock,
    ) -> None:
        """確認摘要與月份事件數不可矛盾。"""

        payload = self.build_payload()
        payload["analysis_event_count"] = 99

        response = Mock()
        response.json.return_value = payload
        response.raise_for_status.return_value = (
            None
        )
        mock_get.return_value = response

        with self.assertRaises(
            APIResponseError
        ):
            fetch_etf_monthly_income(
                "http://127.0.0.1:8000",
                "00918",
            )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_mixed_currency_amounts_are_not_summed(
        self,
        mock_get: Mock,
    ) -> None:
        """確認混合幣別只能保留事件分布。"""

        payload = self.build_payload()
        payload["has_mixed_currencies"] = True
        payload["analysis_currency"] = None
        payload["total_amount_per_unit"] = None

        for month in payload["months"]:
            month["total_amount_per_unit"] = None
            month[
                "average_amount_per_event"
            ] = None

        response = Mock()
        response.json.return_value = payload
        response.raise_for_status.return_value = (
            None
        )
        mock_get.return_value = response

        result = fetch_etf_monthly_income(
            "http://127.0.0.1:8000",
            "00918",
        )

        self.assertTrue(
            result["has_mixed_currencies"]
        )

        self.assertIsNone(
            result["total_amount_per_unit"]
        )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_invalid_lookback_is_rejected_before_request(
        self,
        mock_get: Mock,
    ) -> None:
        """確認 Client 先保護 1–10 年範圍。"""

        with self.assertRaises(ValueError):
            fetch_etf_monthly_income(
                "http://127.0.0.1:8000",
                "00918",
                lookback_years=11,
            )

        mock_get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
