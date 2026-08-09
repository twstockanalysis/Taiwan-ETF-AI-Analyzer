"""M10-5 月配缺口組合 API 契約測試。"""

from datetime import date
from pathlib import Path
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.api.dependencies import get_database_path
from backend.app.main import create_app
from backend.app.models.monthly_combination import (
    MonthlyCombinationCandidateInput,
)
from backend.app.services.monthly_combination_data import (
    MonthlyCombinationLoadedData,
)


class TestMonthlyCombinationAPI(unittest.TestCase):
    def setUp(self):
        self.database_path = Path("monthly-combination-test.db")
        self.application = create_app()
        self.application.dependency_overrides[get_database_path] = (
            lambda: self.database_path
        )
        self.client = TestClient(self.application)

    def tearDown(self):
        self.client.close()
        self.application.dependency_overrides.clear()

    @staticmethod
    def request_payload():
        return {
            "candidates": [
                {
                    "etf_code": "00878",
                    "unit_price": "40",
                    "proposed_allocation_pct": "10",
                }
            ],
            "lookback_years": 3,
            "cash_deduction_rate_pct": "5",
            "max_complementary_etfs": 1,
        }

    def test_openapi_contains_monthly_combination_path(self):
        path = "/api/v1/etfs/{code}/monthly-payment-combination"
        self.assertIn(path, self.application.openapi()["paths"])
        self.assertIn("post", self.application.openapi()["paths"][path])

    def test_candidate_cannot_equal_base(self):
        payload = self.request_payload()
        payload["candidates"][0]["etf_code"] = "0056"
        response = self.client.post(
            "/api/v1/etfs/0056/monthly-payment-combination", json=payload
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"], "候選清單不可包含基準 ETF")

    @patch(
        "backend.app.api.routers.monthly_combination."
        "load_monthly_combination_data"
    )
    def test_returns_explainable_calculation(self, mock_load):
        mock_load.return_value = MonthlyCombinationLoadedData(
            base_etf={"code": "0056", "name": "元大高股息"},
            base_payment_months=[1, 4, 7, 10],
            candidate_etfs={
                "00878": {"code": "00878", "name": "國泰永續高股息"}
            },
            candidates=[
                MonthlyCombinationCandidateInput(
                    etf_code="00878",
                    name="國泰永續高股息",
                    is_active=False,
                    is_bond=False,
                    stable_payment_months=[2, 5, 8, 11],
                    completeness_pct="100",
                    data_is_fresh=True,
                    distribution_stability_pct="80",
                    annual_after_tax_cash_rate_pct="4.75",
                    estimated_after_tax_total_return_pct="8.75",
                    downside_return_pct="-2",
                    holding_overlap_pct=None,
                    proposed_allocation_pct="10",
                )
            ],
        )
        with patch(
            "backend.app.api.routers.monthly_combination.date"
        ) as mock_date:
            mock_date.today.return_value = date(2026, 8, 9)
            response = self.client.post(
                "/api/v1/etfs/0056/monthly-payment-combination",
                json=self.request_payload(),
            )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["historical_facts"]["as_of_date"], "2026-08-09")
        self.assertEqual(body["calculation"]["base_etf_code"], "0056")
        self.assertEqual(
            body["calculation"]["selected_candidates"][0]["etf_code"],
            "00878",
        )
        self.assertEqual(body["calculation"]["status"], "PARTIAL")

    def test_unknown_fields_are_rejected(self):
        response = self.client.post(
            "/api/v1/etfs/0056/monthly-payment-combination",
            json={**self.request_payload(), "unexpected": True},
        )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
