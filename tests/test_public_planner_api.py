"""V3-1 公開且不持久化的現金流試算 API 測試。"""

from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from backend.app.api.dependencies import get_database_path
from backend.app.database.connection import get_connection
from backend.app.database.init_db import initialize_database
from backend.app.main import create_app


class TestPublicPlannerAPI(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_directory.name) / "public-planner-api.db"
        initialize_database(self.database_path)
        connection = get_connection(self.database_path)
        connection.execute(
            """
            INSERT INTO etf_master (code, name, is_active, is_bond)
            VALUES ('0056', '元大高股息', 0, 0);
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
    def request_payload() -> dict:
        return {
            "target_after_tax_cash_twd": 3000,
            "target_months": [2, 1],
            "existing_holdings": [],
            "history_years": 3,
            "cash_deduction_rate_pct": 0,
            "currency": "TWD",
        }

    def test_openapi_contains_public_baseline_path(self) -> None:
        path = "/api/v1/allocation-plans/baseline"
        self.assertIn(path, self.application.openapi()["paths"])
        self.assertIn("post", self.application.openapi()["paths"][path])

    def test_public_zero_holding_request_needs_no_owner_token(self) -> None:
        response = self.client.post(
            "/api/v1/allocation-plans/baseline",
            json=self.request_payload(),
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["profile_scope"], "PUBLIC_STATELESS")
        self.assertFalse(body["request_persisted"])
        self.assertEqual(body["target_months"], [1, 2])
        self.assertEqual(body["holdings"], [])
        self.assertEqual(len(body["monthly_cash_flow"]), 12)

    def test_request_does_not_write_private_profile_tables(self) -> None:
        self.client.post(
            "/api/v1/allocation-plans/baseline",
            json=self.request_payload(),
        )
        connection = get_connection(self.database_path)
        try:
            condition_count = connection.execute(
                "SELECT COUNT(*) FROM decision_profile;"
            ).fetchone()[0]
            holding_count = connection.execute(
                "SELECT COUNT(*) FROM manual_holding;"
            ).fetchone()[0]
        finally:
            connection.close()

        self.assertEqual(condition_count, 0)
        self.assertEqual(holding_count, 0)

    def test_unknown_etf_returns_404(self) -> None:
        payload = self.request_payload()
        payload["existing_holdings"] = [{"etf_code": "9999", "held_units": 1}]
        response = self.client.post(
            "/api/v1/allocation-plans/baseline",
            json=payload,
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "找不到 ETF：9999")

    def test_duplicate_holdings_are_rejected(self) -> None:
        payload = self.request_payload()
        payload["existing_holdings"] = [
            {"etf_code": "0056", "held_units": 1},
            {"etf_code": " 0056 ", "held_units": 2},
        ]
        response = self.client.post(
            "/api/v1/allocation-plans/baseline",
            json=payload,
        )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
