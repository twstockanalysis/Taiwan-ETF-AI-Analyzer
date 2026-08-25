"""公開現金流試算 API client 測試。"""

import unittest
from unittest.mock import patch

from frontend.api.errors import APIResponseError
from frontend.api.public_planner import (
    fetch_allocation_results,
    fetch_public_planner_baseline,
    validate_allocation_results,
    validate_public_planner_result,
)


def valid_result() -> dict:
    return {
        "profile_scope": "PUBLIC_STATELESS",
        "request_persisted": False,
        "status": "AVAILABLE",
        "holdings": [],
        "monthly_cash_flow": [
            {"month": month} for month in range(1, 13)
        ],
    }


class TestFrontendPublicPlannerClient(unittest.TestCase):
    def test_fetch_uses_public_baseline_endpoint(self) -> None:
        with patch(
            "frontend.api.public_planner.post_json",
            return_value=valid_result(),
        ) as post_json:
            result = fetch_public_planner_baseline(
                "http://127.0.0.1:8000",
                {"target_months": [1]},
            )
        self.assertEqual(result["status"], "AVAILABLE")
        self.assertEqual(
            post_json.call_args.kwargs["endpoint_path"],
            "/api/v1/allocation-plans/baseline",
        )

    def test_validator_rejects_internal_score_fields(self) -> None:
        payload = valid_result()
        payload["etf_quality_score"] = 99
        with self.assertRaises(APIResponseError):
            validate_public_planner_result(payload)

    def test_validator_requires_all_twelve_months_in_order(self) -> None:
        payload = valid_result()
        payload["monthly_cash_flow"] = [{"month": 1}]
        with self.assertRaises(APIResponseError):
            validate_public_planner_result(payload)

    def test_fetch_allocation_results_uses_v3_4_endpoint(self) -> None:
        payload = {
            "profile_scope": "PUBLIC_STATELESS",
            "request_persisted": False,
            "plans": [
                {
                    "strategy": "RECOMMENDED",
                    "result": {
                        "status": "TARGET_MET",
                        "additions": [],
                        "monthly_results": [],
                    },
                }
            ],
        }
        with patch(
            "frontend.api.public_planner.post_json",
            return_value=payload,
        ) as post_json:
            result = fetch_allocation_results(
                "http://127.0.0.1:8000",
                {"target_months": [1]},
            )
        self.assertEqual(result, payload)
        self.assertEqual(
            post_json.call_args.kwargs["endpoint_path"],
            "/api/v1/allocation-plans/allocation-results",
        )

    def test_allocation_validator_rejects_nested_internal_score(self) -> None:
        payload = {
            "profile_scope": "PUBLIC_STATELESS",
            "request_persisted": False,
            "plans": [
                {
                    "strategy": "RECOMMENDED",
                    "result": {
                        "status": "TARGET_MET",
                        "additions": [],
                        "monthly_results": [],
                        "quality_score": 99,
                    },
                }
            ],
        }
        with self.assertRaises(APIResponseError):
            validate_allocation_results(payload)


if __name__ == "__main__":
    unittest.main()
