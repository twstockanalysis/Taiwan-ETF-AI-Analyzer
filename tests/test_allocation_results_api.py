"""V3-4 公開配置結果 API 邊界測試。"""

from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from backend.app.api.dependencies import get_database_path
from backend.app.database.init_db import initialize_database
from backend.app.main import app


class TestAllocationResultsApi(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_directory.name) / "results.db"
        initialize_database(self.database_path)
        app.dependency_overrides[get_database_path] = lambda: self.database_path
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        self.temp_directory.cleanup()

    def test_zero_target_returns_public_stateless_recommended_plan(self) -> None:
        response = self.client.post(
            "/api/v1/allocation-plans/allocation-results",
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
        self.assertFalse(body["request_persisted"])
        self.assertEqual(body["plans"][0]["label"], "推薦配置")
        self.assertNotIn("quality_score", response.text)


if __name__ == "__main__":
    unittest.main()
