"""M11-3 候選 ETF 持倉情境整合測試。"""

from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from backend.app.api.dependencies import get_database_path
from backend.app.database.connection import get_connection
from backend.app.database.init_db import initialize_database
from backend.app.main import create_app


class TestCandidateHoldingAnalysis(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = (
            Path(self.temp_directory.name) / "candidate-analysis.db"
        )
        initialize_database(self.database_path)
        connection = get_connection(self.database_path)
        connection.executemany(
            """
            INSERT INTO etf_master (code, name, is_active, is_bond)
            VALUES (?, ?, 0, 0);
            """,
            [
                ("0056", "元大高股息"),
                ("00878", "國泰永續高股息"),
            ],
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

    @staticmethod
    def request_payload():
        return {
            "proposed_units": 100,
            "unit_price": "20",
            "holding_overlap_pct": None,
            "monthly_coverage_enabled": True,
        }

    def _save_profile(self, *, deduction="10"):
        self.client.put(
            "/api/v1/decision-profile/conditions",
            json={
                "monthly_after_tax_target": 3000,
                "analysis_years": 10,
                "history_years": 3,
                "cash_deduction_rate_pct": deduction,
            },
        )
        self.client.put(
            "/api/v1/decision-profile/holdings/0056",
            json={"held_units": 1000, "unit_price": "30"},
        )

    def _insert_market_history(self):
        connection = get_connection(self.database_path)
        dividend_rows = []
        event_index = 0
        schedules = {
            "0056": [
                (1, (2024, 2025, 2026)),
                (4, (2024, 2025, 2026)),
                (7, (2024, 2025, 2026)),
                (10, (2023, 2024, 2025)),
            ],
            "00878": [
                (2, (2024, 2025, 2026)),
                (5, (2024, 2025, 2026)),
                (8, (2024, 2025, 2026)),
                (11, (2023, 2024, 2025)),
            ],
        }
        for code, month_groups in schedules.items():
            for month, years in month_groups:
                for year in years:
                    event_index += 1
                    dividend_rows.append(
                        (
                            code,
                            f"event-{event_index}",
                            f"{year}-{month:02d}-01",
                            1.0,
                            "TWD",
                            "TEST",
                        )
                    )
        connection.executemany(
            """
            INSERT INTO etf_dividend (
                etf_code, source_event_id, payment_date,
                amount_per_unit, currency, source_id
            ) VALUES (?, ?, ?, ?, ?, ?);
            """,
            dividend_rows,
        )
        performance_rows = []
        for code, values in {
            "0056": {"1M": 1, "3M": 2, "6M": 3, "1Y": 4, "3Y": 12},
            "00878": {"1M": 1, "3M": 2, "6M": 3, "1Y": 5, "3Y": 15},
        }.items():
            for period, return_pct in values.items():
                performance_rows.append(
                    (
                        code,
                        "2026-08-01",
                        period,
                        "PRICE_RETURN",
                        return_pct,
                        "twse_stock_day",
                    )
                )
        connection.executemany(
            """
            INSERT INTO etf_performance (
                etf_code, as_of_date, period_code,
                metric_code, return_pct, source_id
            ) VALUES (?, ?, ?, ?, ?, ?);
            """,
            performance_rows,
        )
        connection.commit()
        connection.close()

    def test_openapi_contains_candidate_analysis_path(self):
        path = "/api/v1/decision-profile/candidate-analysis/{etf_code}"
        self.assertIn(path, self.application.openapi()["paths"])
        self.assertIn("post", self.application.openapi()["paths"][path])

    def test_unknown_candidate_returns_404(self):
        response = self.client.post(
            "/api/v1/decision-profile/candidate-analysis/9999",
            json=self.request_payload(),
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "找不到 ETF：9999")

    def test_missing_conditions_returns_explicit_unavailable(self):
        response = self.client.post(
            "/api/v1/decision-profile/candidate-analysis/00878",
            json=self.request_payload(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "UNAVAILABLE")
        self.assertEqual(
            response.json()["unavailable_fields"][0]["field"],
            "conditions",
        )

    def test_candidate_compares_before_after_without_persisting(self):
        self._save_profile()
        self._insert_market_history()

        response = self.client.post(
            "/api/v1/decision-profile/candidate-analysis/00878",
            json=self.request_payload(),
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "PARTIAL")
        self.assertEqual(body["candidate_etf_code"], "00878")
        self.assertEqual(body["comparison"]["additional_capital"], "2000")
        self.assertEqual(body["comparison"]["total_value_before"], "30000.0")
        self.assertEqual(body["comparison"]["total_value_after"], "32000.0")
        self.assertGreater(
            float(body["comparison"]["target_coverage_pct_delta"]),
            0,
        )
        self.assertEqual(
            body["eligibility"]["selected_candidates"][0]["etf_code"],
            "00878",
        )
        profile = self.client.get("/api/v1/decision-profile").json()
        self.assertEqual(
            [item["etf_code"] for item in profile["holdings"]],
            ["0056"],
        )

    def test_missing_deduction_does_not_become_zero(self):
        self._save_profile(deduction=None)
        self._insert_market_history()

        response = self.client.post(
            "/api/v1/decision-profile/candidate-analysis/00878",
            json=self.request_payload(),
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "PARTIAL")
        rejected = body["eligibility"]["rejected_candidates"][0]
        self.assertEqual(rejected["completeness_pct"], "100.000000")
        self.assertIn(
            "MISSING_AFTER_TAX_CASH",
            {item["code"] for item in rejected["reasons"]},
        )
        self.assertIsNone(
            body["comparison"]["annual_after_tax_cash_delta"]
        )

    def test_invalid_proposed_units_are_rejected(self):
        response = self.client.post(
            "/api/v1/decision-profile/candidate-analysis/00878",
            json={**self.request_payload(), "proposed_units": 0},
        )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
