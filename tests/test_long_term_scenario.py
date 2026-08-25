"""V3-5 組合歷史含息績效與長期情境測試。"""

from datetime import date
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from backend.app.database.connection import get_connection
from backend.app.database.init_db import initialize_database
from backend.app.models.allocation_results import (
    AllocationResultsResponse,
    AllocationStrategyPlan,
)
from backend.app.models.integer_allocation import (
    IntegerAllocationAssumptions,
    IntegerAllocationHoldingResult,
    IntegerAllocationResponse,
)
from backend.app.models.long_term_scenario import LongTermScenarioRequest
from backend.app.services.long_term_scenario import build_long_term_scenarios


_SNAPSHOT = "sha256:" + "b" * 64


class TestLongTermScenario(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_directory.name) / "long-term.db"
        initialize_database(self.database_path)
        connection = get_connection(self.database_path)
        try:
            connection.execute(
                "INSERT INTO etf_master (code, name, is_active, is_bond) "
                "VALUES ('0050', '元大台灣50', 0, 0);"
            )
            for year, price in (
                (2022, 100),
                (2023, 105),
                (2024, 110),
                (2025, 115),
                (2026, 120),
            ):
                connection.execute(
                    "INSERT INTO etf_daily_close "
                    "(etf_code, trade_date, close_price, source_id) "
                    "VALUES ('0050', ?, ?, 'twse_stock_day');",
                    (f"{year}-01-03", price),
                )
                if year > 2022:
                    connection.execute(
                        "INSERT INTO etf_dividend "
                        "(etf_code, source_event_id, payment_date, "
                        "amount_per_unit, currency, source_id) "
                        "VALUES ('0050', ?, ?, 2, 'TWD', 'TEST');",
                        (f"0050-{year}", f"{year}-01-02"),
                    )
            connection.commit()
        finally:
            connection.close()

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    @staticmethod
    def _allocation_results() -> AllocationResultsResponse:
        result = IntegerAllocationResponse(
            status="TARGET_MET",
            optimality="BOUNDED_BEST_EFFORT",
            analysis_date=date(2026, 1, 3),
            snapshot_id=_SNAPSHOT,
            target_after_tax_cash_twd=100,
            target_months=[1],
            assumptions=IntegerAllocationAssumptions(
                cash_deduction_rate_pct=0,
                max_candidate_allocation_pct=20,
            ),
            universe_count=1,
            eligible_count=1,
            additions=[],
            total_required_additional_capital=0,
            monthly_results=[
                {
                    "month": 1,
                    "current_after_tax_cash": 100,
                    "added_after_tax_cash": 0,
                    "modeled_after_tax_cash": 100,
                    "target_after_tax_cash": 100,
                    "shortfall": 0,
                }
            ],
            resulting_holdings=[
                IntegerAllocationHoldingResult(
                    etf_code="0050",
                    existing_shares=100,
                    additional_shares=0,
                    resulting_shares=100,
                    reference_price=120,
                    reference_price_as_of=date(2026, 1, 3),
                    reference_price_source_id="twse_stock_day",
                    resulting_value=12000,
                    allocation_pct=100,
                )
            ],
        )
        return AllocationResultsResponse(
            snapshot_id=_SNAPSHOT,
            plans=[
                AllocationStrategyPlan(
                    strategy="RECOMMENDED",
                    label="推薦配置",
                    simple_explanation="測試",
                    result=result,
                )
            ],
        )

    @patch("backend.app.services.long_term_scenario.build_allocation_results")
    def test_uses_all_common_history_and_builds_three_scenarios(
        self,
        build_results,
    ) -> None:
        build_results.return_value = self._allocation_results()
        response = build_long_term_scenarios(
            LongTermScenarioRequest(
                target_after_tax_cash_twd=100,
                target_months=[1],
                existing_holdings=[],
                history_years=3,
                cash_deduction_rate_pct=0,
            ),
            self.database_path,
            as_of_date=date(2026, 1, 3),
        )

        evidence = response.plan_evidence[0]
        available = evidence.historical_periods[0]
        self.assertEqual(available.status, "AVAILABLE")
        self.assertEqual(available.period_start, date(2022, 1, 3))
        self.assertEqual(available.period_end, date(2026, 1, 3))
        self.assertEqual(available.start_value, Decimal("10000.00"))
        self.assertEqual(available.end_value, Decimal("12000.00"))
        self.assertEqual(available.gross_distributions, Decimal("800.00"))
        self.assertEqual(available.total_return_pct, Decimal("28.000000"))
        self.assertEqual(
            [item.status for item in evidence.historical_periods],
            ["AVAILABLE", "AVAILABLE", "UNAVAILABLE", "UNAVAILABLE"],
        )
        self.assertEqual(evidence.annual_observation_count, 4)
        self.assertEqual(
            [scenario.label for scenario in evidence.scenarios],
            ["保守情境", "基準情境", "樂觀情境"],
        )
        self.assertTrue(
            all(len(scenario.index_points) == 11 for scenario in evidence.scenarios)
        )
        self.assertTrue(
            evidence.scenarios[0].annual_total_return_assumption_pct
            <= evidence.scenarios[1].annual_total_return_assumption_pct
            <= evidence.scenarios[2].annual_total_return_assumption_pct
        )
        self.assertIn(
            "UNIT_CHANGE_ADJUSTMENT_UNAVAILABLE",
            {issue.code for issue in evidence.issues},
        )

    @patch("backend.app.services.long_term_scenario.build_allocation_results")
    def test_missing_payment_date_fails_closed_for_affected_period(
        self,
        build_results,
    ) -> None:
        connection = get_connection(self.database_path)
        try:
            connection.execute(
                "INSERT INTO etf_dividend "
                "(etf_code, source_event_id, ex_dividend_date, "
                "amount_per_unit, currency, source_id) "
                "VALUES ('0050', 'missing-payment', '2025-06-01', 1, 'TWD', 'TEST');"
            )
            connection.commit()
        finally:
            connection.close()
        build_results.return_value = self._allocation_results()

        response = build_long_term_scenarios(
            LongTermScenarioRequest(
                target_after_tax_cash_twd=100,
                target_months=[1],
                existing_holdings=[],
            ),
            self.database_path,
            as_of_date=date(2026, 1, 3),
        )

        available = response.plan_evidence[0].historical_periods[0]
        self.assertEqual(available.status, "UNAVAILABLE")
        self.assertIn("MISSING_PAYMENT_DATE", {item.code for item in available.issues})


if __name__ == "__main__":
    unittest.main()
