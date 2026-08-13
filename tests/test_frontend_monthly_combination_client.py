"""M10-5 前端 API client 測試。"""

import unittest
from unittest.mock import Mock, patch

from frontend.api.errors import APIResponseError
from frontend.api.monthly_combination import (
    fetch_monthly_payment_combination,
    validate_monthly_combination_result,
)


class TestFrontendMonthlyCombinationClient(unittest.TestCase):
    @staticmethod
    def response_payload():
        return {
            "historical_facts": {"as_of_date": "2026-08-09"},
            "calculation": {
                "status": "PARTIAL",
                "base_etf_code": "0056",
                "target_payment_months": [1, 4, 7, 10],
                "selected_candidates": [{"reasons": []}],
                "rejected_candidates": [],
            },
        }

    @patch("frontend.api.transport.httpx.post")
    def test_posts_payload_to_base_etf_path(self, mock_post):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = self.response_payload()
        mock_post.return_value = response
        payload = {"candidates": [{"etf_code": "00878"}]}
        result = fetch_monthly_payment_combination(
            "http://127.0.0.1:8000", "0056", payload
        )
        self.assertEqual(result["calculation"]["status"], "PARTIAL")
        self.assertEqual(mock_post.call_args.kwargs["json"], payload)
        self.assertTrue(
            mock_post.call_args.args[0].endswith(
                "/api/v1/etfs/0056/monthly-payment-combination"
            )
        )

    def test_rejects_candidate_without_reasons(self):
        payload = self.response_payload()
        payload["calculation"]["selected_candidates"] = [{}]
        with self.assertRaises(APIResponseError):
            validate_monthly_combination_result(payload)


if __name__ == "__main__":
    unittest.main()
