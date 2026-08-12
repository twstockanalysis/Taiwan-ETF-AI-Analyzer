"""M11-1 前端決策條件 API client 測試。"""

import unittest
from unittest.mock import Mock, patch

from frontend.api.decision_profile import (
    delete_manual_holding,
    fetch_candidate_holding_analysis,
    fetch_current_holding_analysis,
    fetch_decision_profile,
    fetch_decision_record_export,
    fetch_decision_records,
    save_candidate_decision_record,
    save_manual_holding,
    save_manual_holdings,
    save_user_conditions,
)
from frontend.api.errors import APIResponseError


class TestFrontendDecisionProfileClient(unittest.TestCase):
    OWNER_TOKEN = "test-owner-token"
    @staticmethod
    def candidate_analysis():
        return {
            "profile_scope": "SINGLE_USER",
            "broker_connected": False,
            "status": "AVAILABLE",
            "analysis_date": "2026-08-10",
            "candidate_etf_code": "00878",
            "candidate_name": "國泰永續高股息",
            "current_portfolio": {},
            "proposed_portfolio": {},
            "comparison": {},
            "eligibility": {
                "selected_candidates": [{"reasons": []}],
                "rejected_candidates": [],
            },
            "decision_priority": ["TOTAL_RETURN_AND_PRINCIPAL_RISK"],
            "unavailable_fields": [],
        }

    @classmethod
    def decision_record(cls):
        return {
            "id": 1,
            "record_type": "CANDIDATE_HOLDING_ANALYSIS",
            "candidate_etf_code": "00878",
            "candidate_name": "國泰永續高股息",
            "analysis_status": "AVAILABLE",
            "outcome": "ELIGIBLE",
            "created_at": "2026-08-10T12:00:00",
            "profile_scope": "SINGLE_USER",
            "broker_connected": False,
            "immutable": True,
            "request": {"proposed_units": 100, "unit_price": "20"},
            "analysis": cls.candidate_analysis(),
            "rationale": [],
            "exclusions": [],
            "alternatives": [],
            "risk_notes": [],
        }

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
            "price_source_id": "twse_stock_day",
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
        result = fetch_decision_profile("http://127.0.0.1:8000", self.OWNER_TOKEN)
        self.assertFalse(result["broker_connected"])
        self.assertEqual(result["holdings"][0]["etf_code"], "0056")

    @patch("frontend.api.transport.httpx.get")
    def test_fetches_current_holding_analysis(self, mock_get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "profile_scope": "SINGLE_USER",
            "broker_connected": False,
            "status": "UNAVAILABLE",
            "analysis_date": "2026-08-09",
            "currency": "TWD",
            "conditions": None,
            "total_current_value": None,
            "holdings": [],
            "portfolio_analysis": None,
            "unavailable_fields": [
                {"field": "conditions", "reason": "尚未儲存固定分析條件"}
            ],
        }
        mock_get.return_value = response

        result = fetch_current_holding_analysis("http://127.0.0.1:8000", self.OWNER_TOKEN)

        self.assertEqual(result["status"], "UNAVAILABLE")
        self.assertTrue(
            mock_get.call_args.args[0].endswith(
                "/api/v1/decision-profile/current-holding-analysis"
            )
        )

    @patch("frontend.api.transport.httpx.post")
    def test_posts_candidate_holding_analysis(self, mock_post):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = self.candidate_analysis()
        mock_post.return_value = response
        payload = {"proposed_units": 100, "unit_price": 20}

        result = fetch_candidate_holding_analysis(
            "http://127.0.0.1:8000",
            "00878",
            payload,
            self.OWNER_TOKEN,
        )

        self.assertEqual(result["candidate_etf_code"], "00878")
        self.assertEqual(mock_post.call_args.kwargs["json"], payload)
        self.assertTrue(
            mock_post.call_args.args[0].endswith(
                "/api/v1/decision-profile/candidate-analysis/00878"
            )
        )

    @patch("frontend.api.transport.httpx.post")
    def test_saves_server_recomputed_decision_record(self, mock_post):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = self.decision_record()
        mock_post.return_value = response
        payload = {"proposed_units": 100, "unit_price": 20}

        result = save_candidate_decision_record(
            "http://127.0.0.1:8000", "00878", payload, self.OWNER_TOKEN
        )

        self.assertTrue(result["immutable"])
        self.assertTrue(
            mock_post.call_args.args[0].endswith(
                "/candidate-analysis/00878/decision-records"
            )
        )

    @patch("frontend.api.transport.httpx.get")
    def test_lists_records_and_fetches_binary_export(self, mock_get):
        summary = {
            key: value
            for key, value in self.decision_record().items()
            if key in {
                "id",
                "record_type",
                "candidate_etf_code",
                "candidate_name",
                "analysis_status",
                "outcome",
                "created_at",
            }
        }
        list_response = Mock()
        list_response.raise_for_status.return_value = None
        list_response.json.return_value = [summary]
        binary_response = Mock()
        binary_response.raise_for_status.return_value = None
        binary_response.content = b"PK\x03\x04xlsx"
        mock_get.side_effect = [list_response, binary_response]

        records = fetch_decision_records("http://127.0.0.1:8000", self.OWNER_TOKEN)
        exported = fetch_decision_record_export("http://127.0.0.1:8000", 1, self.OWNER_TOKEN)

        self.assertEqual(records[0]["id"], 1)
        self.assertEqual(exported, b"PK\x03\x04xlsx")
        self.assertIn("export.xlsx", mock_get.call_args.args[0])

    @patch("frontend.api.transport.httpx.put")
    def test_saves_conditions_and_holding_with_put(self, mock_put):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.side_effect = [self.conditions(), self.holding()]
        mock_put.return_value = response
        save_user_conditions(
            "http://127.0.0.1:8000",
            {"monthly_after_tax_target": 3000},
            self.OWNER_TOKEN,
        )
        save_manual_holding(
            "http://127.0.0.1:8000",
            "0056",
            {"held_units": 1000, "unit_price": 35.5},
            self.OWNER_TOKEN,
        )
        self.assertEqual(mock_put.call_count, 2)
        self.assertTrue(
            mock_put.call_args.args[0].endswith(
                "/api/v1/decision-profile/holdings/0056"
            )
        )

    @patch("frontend.api.transport.httpx.put")
    def test_saves_two_field_holding_batch(self, mock_put):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = [self.holding()]
        mock_put.return_value = response

        result = save_manual_holdings(
            "http://127.0.0.1:8000",
            [{"etf_code": "0056", "held_units": 1000}],
            self.OWNER_TOKEN,
        )

        self.assertEqual(result[0]["price_source_id"], "twse_stock_day")
        self.assertEqual(
            mock_put.call_args.kwargs["json"],
            {"holdings": [{"etf_code": "0056", "held_units": 1000}]},
        )
        self.assertTrue(
            mock_put.call_args.args[0].endswith(
                "/api/v1/decision-profile/holdings"
            )
        )

    @patch("frontend.api.transport.httpx.delete")
    def test_delete_accepts_empty_204_response(self, mock_delete):
        response = Mock(status_code=204)
        response.raise_for_status.return_value = None
        mock_delete.return_value = response
        result = delete_manual_holding(
            "http://127.0.0.1:8000", "0056", self.OWNER_TOKEN
        )
        self.assertIsNone(result)

    @patch("frontend.api.transport.httpx.get")
    def test_owner_token_is_sent_in_header(self, mock_get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "profile_scope": "SINGLE_USER",
            "broker_connected": False,
            "conditions": None,
            "holdings": [],
        }
        mock_get.return_value = response
        fetch_decision_profile("http://127.0.0.1:8000", self.OWNER_TOKEN)
        self.assertEqual(
            mock_get.call_args.kwargs["headers"]["X-Owner-Token"],
            self.OWNER_TOKEN,
        )

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
