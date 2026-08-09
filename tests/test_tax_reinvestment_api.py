"""M10-4 稅務與再投資 API 測試。"""

from datetime import date
from pathlib import Path
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.api.dependencies import get_database_path
from backend.app.main import create_app
from backend.app.services.target_analysis_data import TargetAnalysisData


class TestTaxReinvestmentAPI(unittest.TestCase):
    def setUp(self) -> None:
        self.database_path = Path("tax-reinvestment-test.db")
        self.application = create_app()
        self.application.dependency_overrides[get_database_path] = (
            lambda: self.database_path
        )
        self.client = TestClient(self.application)

    def tearDown(self) -> None:
        self.client.close()
        self.application.dependency_overrides.clear()

    @staticmethod
    def request_payload() -> dict:
        return {
            "held_units": 1000,
            "unit_price": 20,
            "monthly_cash_target": 1000,
            "analysis_years": 5,
            "history_years": 3,
            "payments_per_year": 4,
            "custom_reinvestment_pct": 50,
            "tax_rule": {
                "rule_version": "TW-INDIVIDUAL-2026.1",
                "effective_date": "2021-01-01",
                "component_assumptions": [
                    {
                        "component_code": "54C",
                        "income_tax_rate_pct": 12,
                        "tax_credit_rate_pct": 8.5,
                        "supplementary_premium_applicable": True,
                    },
                    {
                        "component_code": "76W",
                        "income_tax_rate_pct": 0,
                    },
                ],
            },
        }

    def test_openapi_contains_tax_reinvestment_path(self) -> None:
        path = "/api/v1/etfs/{code}/tax-reinvestment-scenarios"
        self.assertIn(path, self.application.openapi()["paths"])
        self.assertIn("post", self.application.openapi()["paths"][path])

    @patch(
        "backend.app.api.routers.target_analysis."
        "list_etf_actual_component_history"
    )
    @patch(
        "backend.app.api.routers.target_analysis.load_target_analysis_data"
    )
    @patch("backend.app.api.routers.target_analysis.get_etf_by_code")
    def test_returns_traceable_four_scenario_result(
        self,
        mock_get_etf,
        mock_load_data,
        mock_list_components,
    ) -> None:
        mock_get_etf.return_value = {"code": "0056"}
        mock_load_data.return_value = TargetAnalysisData(
            monthly_income={
                "analysis_currency": "TWD",
                "window_start_date": date(2023, 1, 1),
                "as_of_date": date(2025, 12, 31),
                "total_amount_per_unit": 6,
            },
            dividends=[],
            selected_performance={
                "period_code": "3Y",
                "return_pct": 3,
            },
            warnings=[],
            unavailable_fields=[],
        )
        common = {
            "dividend_id": 7,
            "source_event_id": "official-7",
            "payment_date": "2025-12-20",
        }
        mock_list_components.return_value = [
            {
                **common,
                "component_code": "54C",
                "component_name": "境內股利",
                "ratio_pct": 40,
            },
            {
                **common,
                "component_code": "76W",
                "component_name": "國內財產交易",
                "ratio_pct": 60,
            },
        ]

        response = self.client.post(
            "/api/v1/etfs/0056/tax-reinvestment-scenarios",
            json=self.request_payload(),
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "AVAILABLE")
        self.assertEqual(
            body["historical_facts"]["component_source_event_id"],
            "official-7",
        )
        self.assertEqual(len(body["calculation"]["scenarios"]), 4)
        self.assertEqual(
            body["historical_facts"]["price_return_period_code"],
            "3Y",
        )
        self.assertAlmostEqual(
            float(body["historical_facts"]["annual_price_return_pct"]),
            0.990163,
            places=6,
        )
        self.assertEqual(
            body["calculation"]["estimate_label"],
            "情境估算，非稅務建議",
        )


if __name__ == "__main__":
    unittest.main()
