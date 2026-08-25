"""V3-5 公開長期情境 API 邊界測試。"""

from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from backend.app.api.dependencies import get_database_path
from backend.app.database.init_db import initialize_database
from backend.app.main import app


class TestLongTermScenarioApi(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_directory.name) / "scenario-api.db"
        initialize_database(self.database_path)
        app.dependency_overrides[get_database_path] = lambda: self.database_path
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        self.temp_directory.cleanup()

    def test_zero_target_returns_unavailable_evidence_without_fabricated_values(self) -> None:
        response = self.client.post(
            "/api/v1/allocation-plans/long-term-scenarios",
            json={
                "target_after_tax_cash_twd": "0",
                "target_months": [1],
                "existing_holdings": [],
                "history_years": 3,
                "cash_deduction_rate_pct": "0",
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["profile_scope"], "PUBLIC_STATELESS")
        evidence = body["plan_evidence"][0]
        self.assertEqual(evidence["historical_periods"][0]["status"], "UNAVAILABLE")
        self.assertEqual(evidence["scenarios"], [])
        self.assertNotIn("quality_score", response.text)


if __name__ == "__main__":
    unittest.main()
