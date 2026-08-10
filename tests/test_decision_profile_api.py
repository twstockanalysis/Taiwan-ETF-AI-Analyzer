"""M11-1 決策條件與手動持有部位 API 測試。"""

from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from backend.app.api.dependencies import get_database_path
from backend.app.database.connection import get_connection
from backend.app.database.init_db import initialize_database
from backend.app.main import create_app


class TestDecisionProfileAPI(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_directory.name) / "profile-api.db"
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

    def tearDown(self):
        self.client.close()
        self.application.dependency_overrides.clear()
        self.temp_directory.cleanup()

    def test_openapi_contains_profile_crud_paths(self):
        paths = self.application.openapi()["paths"]
        self.assertIn("/api/v1/decision-profile", paths)
        self.assertIn("/api/v1/decision-profile/conditions", paths)
        self.assertIn("/api/v1/decision-profile/holdings/{etf_code}", paths)
        self.assertIn(
            "/api/v1/decision-profile/current-holding-analysis",
            paths,
        )

    def test_current_holding_analysis_requires_saved_conditions(self):
        response = self.client.get(
            "/api/v1/decision-profile/current-holding-analysis"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "UNAVAILABLE")
        self.assertEqual(
            response.json()["unavailable_fields"],
            [{"field": "conditions", "reason": "尚未儲存固定分析條件"}],
        )

    def test_current_holding_analysis_preserves_missing_market_data(self):
        self.client.put(
            "/api/v1/decision-profile/conditions",
            json={
                "monthly_after_tax_target": 3000,
                "analysis_years": 10,
                "history_years": 3,
                "cash_deduction_rate_pct": None,
            },
        )
        self.client.put(
            "/api/v1/decision-profile/holdings/0056",
            json={"held_units": 1000, "unit_price": 35.5},
        )

        response = self.client.get(
            "/api/v1/decision-profile/current-holding-analysis"
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "PARTIAL")
        self.assertEqual(body["total_current_value"], "35500.0")
        self.assertIsNone(
            body["portfolio_analysis"]["scenario_estimate"][
                "ending_holding_value"
            ]
        )

    def test_empty_profile_is_explicit_single_user_without_broker(self):
        response = self.client.get("/api/v1/decision-profile")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "profile_scope": "SINGLE_USER",
                "broker_connected": False,
                "conditions": None,
                "holdings": [],
            },
        )

    def test_conditions_can_be_created_and_updated(self):
        response = self.client.put(
            "/api/v1/decision-profile/conditions",
            json={
                "monthly_after_tax_target": "3000",
                "analysis_years": 10,
                "history_years": 3,
                "cash_deduction_rate_pct": None,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["monthly_after_tax_target"], "3000.0")
        self.assertIsNone(response.json()["cash_deduction_rate_pct"])

    def test_unknown_condition_field_is_rejected(self):
        response = self.client.put(
            "/api/v1/decision-profile/conditions",
            json={
                "monthly_after_tax_target": 3000,
                "analysis_years": 10,
                "unexpected": True,
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_holding_can_be_saved_and_read_from_profile(self):
        response = self.client.put(
            "/api/v1/decision-profile/holdings/0056",
            json={
                "held_units": 1000,
                "unit_price": "35.5",
                "price_as_of_date": "2026-08-09",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["etf_code"], "0056")
        profile = self.client.get("/api/v1/decision-profile").json()
        self.assertEqual(profile["holdings"][0]["held_units"], 1000)

    def test_holding_batch_uses_latest_stored_official_close(self):
        connection = get_connection(self.database_path)
        connection.executemany(
            """
            INSERT INTO etf_daily_close (
                etf_code, trade_date, close_price, source_id
            ) VALUES ('0056', ?, ?, 'twse_stock_day');
            """,
            [("2026-08-07", 35), ("2026-08-08", 36.5)],
        )
        connection.commit()
        connection.close()

        response = self.client.put(
            "/api/v1/decision-profile/holdings",
            json={"holdings": [{"etf_code": "0056", "held_units": 1200}]},
        )

        self.assertEqual(response.status_code, 200)
        holding = response.json()[0]
        self.assertEqual(holding["held_units"], 1200)
        self.assertEqual(holding["unit_price"], "36.5")
        self.assertEqual(holding["price_as_of_date"], "2026-08-08")
        self.assertEqual(holding["price_source_id"], "twse_stock_day")

    def test_holding_batch_preserves_missing_price_and_can_clear_all(self):
        saved = self.client.put(
            "/api/v1/decision-profile/holdings",
            json={"holdings": [{"etf_code": "0056", "held_units": 1000}]},
        )
        self.assertEqual(saved.status_code, 200)
        self.assertIsNone(saved.json()[0]["unit_price"])
        self.assertIsNone(saved.json()[0]["price_as_of_date"])
        self.assertIsNone(saved.json()[0]["price_source_id"])

        analysis = self.client.get(
            "/api/v1/decision-profile/current-holding-analysis"
        ).json()
        self.assertEqual(analysis["status"], "UNAVAILABLE")

        cleared = self.client.put(
            "/api/v1/decision-profile/holdings",
            json={"holdings": []},
        )
        self.assertEqual(cleared.status_code, 200)
        self.assertEqual(cleared.json(), [])
        self.assertEqual(
            self.client.get("/api/v1/decision-profile").json()["holdings"],
            [],
        )

    def test_holding_batch_rejects_duplicates_without_replacing(self):
        self.client.put(
            "/api/v1/decision-profile/holdings/0056",
            json={"held_units": 1, "unit_price": 30},
        )
        response = self.client.put(
            "/api/v1/decision-profile/holdings",
            json={
                "holdings": [
                    {"etf_code": "0056", "held_units": 1},
                    {"etf_code": "0056", "held_units": 2},
                ]
            },
        )
        self.assertEqual(response.status_code, 422)
        profile = self.client.get("/api/v1/decision-profile").json()
        self.assertEqual(profile["holdings"][0]["held_units"], 1)

    def test_unknown_etf_returns_404(self):
        response = self.client.put(
            "/api/v1/decision-profile/holdings/9999",
            json={"held_units": 1, "unit_price": 30},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "找不到 ETF：9999")

    def test_zero_units_are_rejected(self):
        response = self.client.put(
            "/api/v1/decision-profile/holdings/0056",
            json={"held_units": 0, "unit_price": 30},
        )
        self.assertEqual(response.status_code, 422)

    def test_future_price_date_is_rejected(self):
        response = self.client.put(
            "/api/v1/decision-profile/holdings/0056",
            json={
                "held_units": 1,
                "unit_price": 30,
                "price_as_of_date": "2999-01-01",
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_holding_delete_is_idempotently_explainable(self):
        self.client.put(
            "/api/v1/decision-profile/holdings/0056",
            json={"held_units": 1, "unit_price": 30},
        )
        deleted = self.client.delete(
            "/api/v1/decision-profile/holdings/0056"
        )
        self.assertEqual(deleted.status_code, 204)
        missing = self.client.delete(
            "/api/v1/decision-profile/holdings/0056"
        )
        self.assertEqual(missing.status_code, 404)


if __name__ == "__main__":
    unittest.main()
