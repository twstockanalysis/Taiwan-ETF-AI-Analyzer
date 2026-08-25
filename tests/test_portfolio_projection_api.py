"""V3-6 公開組合情境 API 邊界測試。"""

from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from backend.app.api.dependencies import get_database_path
from backend.app.database.init_db import initialize_database
from backend.app.main import app


class TestPortfolioProjectionApi(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_directory.name) / "portfolio-api.db"
        initialize_database(self.database_path)
        app.dependency_overrides[get_database_path] = lambda: self.database_path
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        self.temp_directory.cleanup()

    def test_zero_target_fails_closed_without_fabricated_projection(self) -> None:
        response = self.client.post(
            "/api/v1/allocation-plans/portfolio-projections",
            json={
                "target_after_tax_cash_twd": "0",
                "target_months": [1],
                "existing_holdings": [],
                "history_years": 3,
                "cash_deduction_rate_pct": "0",
                "projection_years": 20,
                "custom_reinvestment_pct": "50",
                "dividend_tax_method": "COMBINED_WITH_CREDIT",
                "marginal_income_tax_rate_pct": "5",
                "other_income_tax_rate_pct": "0",
                "remaining_annual_dividend_credit_cap_twd": "80000",
                "supplementary_premium_exempt": False,
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["profile_scope"], "PUBLIC_STATELESS")
        self.assertEqual(body["projection_years"], 20)
        self.assertEqual(body["plan_projections"][0]["status"], "UNAVAILABLE")
        self.assertEqual(body["plan_projections"][0]["market_projections"], [])
        self.assertNotIn("quality_score", response.text)
        self.assertNotIn("confidence", response.text.lower())

    def test_projection_years_above_20_is_rejected(self) -> None:
        response = self.client.post(
            "/api/v1/allocation-plans/portfolio-projections",
            json={
                "target_after_tax_cash_twd": "0",
                "target_months": [1],
                "existing_holdings": [],
                "projection_years": 21,
            },
        )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
