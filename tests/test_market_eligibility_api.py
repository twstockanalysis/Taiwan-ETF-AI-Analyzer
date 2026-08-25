"""V3-2 公開安全投影 API 測試。"""

from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from backend.app.api.dependencies import get_database_path
from backend.app.database.connection import get_connection
from backend.app.database.init_db import initialize_database
from backend.app.main import create_app


class TestMarketEligibilityAPI(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_directory.name) / "market-api.db"
        initialize_database(self.database_path)
        connection = get_connection(self.database_path)
        connection.execute(
            """
            INSERT INTO etf_master (code, name, is_active, is_bond)
            VALUES ('0050', '元大台灣50', 0, 0);
            """
        )
        connection.commit()
        connection.close()
        self.application = create_app()
        self.application.dependency_overrides[get_database_path] = (
            lambda: self.database_path
        )
        self.client = TestClient(self.application)

    def tearDown(self) -> None:
        self.client.close()
        self.application.dependency_overrides.clear()
        self.temp_directory.cleanup()

    @staticmethod
    def payload() -> dict:
        return {
            "target_after_tax_cash_twd": 3000,
            "target_months": [1, 2],
            "existing_holdings": [],
            "history_years": 3,
            "cash_deduction_rate_pct": 0,
            "currency": "TWD",
        }

    def test_public_projection_needs_no_owner_token_and_exposes_no_score(self) -> None:
        response = self.client.post(
            "/api/v1/allocation-plans/eligibility-index",
            json=self.payload(),
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["methodology"], "DETERMINISTIC_MARKET_ELIGIBILITY_V3_2")
        self.assertEqual(body["universe_count"], 1)
        self.assertNotIn("quality_score", response.text)
        self.assertNotIn("confidence", response.text)

    def test_unknown_existing_holding_returns_404(self) -> None:
        payload = self.payload()
        payload["existing_holdings"] = [{"etf_code": "9999", "held_units": 1}]
        response = self.client.post(
            "/api/v1/allocation-plans/eligibility-index",
            json=payload,
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "找不到 ETF：9999")

    def test_public_request_cannot_override_server_eligibility_rules(self) -> None:
        payload = self.payload()
        payload["rules"] = {"min_completeness_pct": 0}
        response = self.client.post(
            "/api/v1/allocation-plans/eligibility-index",
            json=payload,
        )
        self.assertEqual(response.status_code, 422)

    def test_index_request_does_not_persist_profile_or_holdings(self) -> None:
        self.client.post(
            "/api/v1/allocation-plans/eligibility-index",
            json=self.payload(),
        )
        connection = get_connection(self.database_path)
        try:
            profile_count = connection.execute(
                "SELECT COUNT(*) FROM decision_profile;"
            ).fetchone()[0]
            holding_count = connection.execute(
                "SELECT COUNT(*) FROM manual_holding;"
            ).fetchone()[0]
        finally:
            connection.close()
        self.assertEqual(profile_count, 0)
        self.assertEqual(holding_count, 0)

    def test_openapi_contains_eligibility_index(self) -> None:
        path = "/api/v1/allocation-plans/eligibility-index"
        self.assertIn(path, self.application.openapi()["paths"])
        self.assertIn("post", self.application.openapi()["paths"][path])


if __name__ == "__main__":
    unittest.main()
