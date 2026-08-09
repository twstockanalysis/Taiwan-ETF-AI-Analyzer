"""M11-1 前端決策條件 API client 測試。"""

import unittest
from unittest.mock import Mock, patch

from frontend.api.decision_profile import (
    delete_manual_holding,
    fetch_decision_profile,
    save_manual_holding,
    save_user_conditions,
)
from frontend.api.errors import APIResponseError


class TestFrontendDecisionProfileClient(unittest.TestCase):
    @staticmethod
    def conditions():
        return {
            "monthly_after_tax_target": "3000.0",
            "analysis_years": 10,
            "history_years": 3,
            "cash_deduction_rate_pct": None,
            "currency": "TWD",
            "updated_at": "2026-08-09T12:00:00",
        }

    @staticmethod
    def holding():
        return {
            "etf_code": "0056",
            "name": "元大高股息",
            "is_active": False,
            "is_bond": False,
            "held_units": 1000,
            "unit_price": "35.5",
            "price_as_of_date": "2026-08-09",
            "currency": "TWD",
            "updated_at": "2026-08-09T12:00:00",
        }

    @patch("frontend.api.transport.httpx.get")
    def test_fetches_single_user_profile(self, mock_get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "profile_scope": "SINGLE_USER",
            "broker_connected": False,
            "conditions": self.conditions(),
            "holdings": [self.holding()],
        }
        mock_get.return_value = response
        result = fetch_decision_profile("http://127.0.0.1:8000")
        self.assertFalse(result["broker_connected"])
        self.assertEqual(result["holdings"][0]["etf_code"], "0056")

    @patch("frontend.api.transport.httpx.put")
    def test_saves_conditions_and_holding_with_put(self, mock_put):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.side_effect = [self.conditions(), self.holding()]
        mock_put.return_value = response
        save_user_conditions(
            "http://127.0.0.1:8000",
            {"monthly_after_tax_target": 3000},
        )
        save_manual_holding(
            "http://127.0.0.1:8000",
            "0056",
            {"held_units": 1000, "unit_price": 35.5},
        )
        self.assertEqual(mock_put.call_count, 2)
        self.assertTrue(
            mock_put.call_args.args[0].endswith(
                "/api/v1/decision-profile/holdings/0056"
            )
        )

    @patch("frontend.api.transport.httpx.delete")
    def test_delete_accepts_empty_204_response(self, mock_delete):
        response = Mock(status_code=204)
        response.raise_for_status.return_value = None
        mock_delete.return_value = response
        result = delete_manual_holding(
            "http://127.0.0.1:8000", "0056"
        )
        self.assertIsNone(result)

    def test_rejects_broker_connected_claim(self):
        with self.assertRaises(APIResponseError):
            from frontend.api.decision_profile import validate_decision_profile

            validate_decision_profile(
                {
                    "profile_scope": "SINGLE_USER",
                    "broker_connected": True,
                    "conditions": None,
                    "holdings": [],
                }
            )


if __name__ == "__main__":
    unittest.main()
