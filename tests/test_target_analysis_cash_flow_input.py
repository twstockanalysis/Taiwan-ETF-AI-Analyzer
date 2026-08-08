from datetime import date
import unittest

from backend.app.models.cash_flow_analysis import (
    AnalysisMode,
    CalculationContext,
)
from backend.app.models.target_analysis import (
    TargetAnalysisRequest,
)
from backend.app.services.target_analysis_calculator import (
    build_cash_flow_calculation_input,
)


class TestTargetAnalysisCashFlowInput(unittest.TestCase):
    def setUp(self):
        self.context = CalculationContext(
            mode=AnalysisMode.SCENARIO_ESTIMATE,
            currency="TWD",
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
        )
        self.request = TargetAnalysisRequest(
            held_units=2000,
            unit_price="50.25",
            monthly_after_tax_target="10000",
            analysis_years=10,
            cash_deduction_rate_pct="2.11",
        )

    def test_request_and_cash_breakdown_are_mapped(self):
        result = build_cash_flow_calculation_input(
            self.request,
            context=self.context,
            gross_distribution_cash="6500",
            distribution_tax="100",
            supplementary_premium="50",
            other_distribution_costs="25",
        )

        self.assertIs(result.context, self.context)
        self.assertEqual(
            result.available_capital,
            self.request.unit_price * self.request.held_units,
        )
        self.assertEqual(
            result.reference_capital,
            self.request.unit_price * self.request.held_units,
        )
        self.assertEqual(
            result.monthly_after_tax_target,
            self.request.monthly_after_tax_target,
        )
        self.assertEqual(
            result.gross_distribution_cash,
            6500,
        )
        self.assertEqual(result.distribution_tax, 100)
        self.assertEqual(result.supplementary_premium, 50)
        self.assertEqual(result.other_distribution_costs, 25)

    def test_missing_cash_breakdown_remains_missing(self):
        result = build_cash_flow_calculation_input(
            self.request,
            context=self.context,
            gross_distribution_cash=None,
            distribution_tax=None,
            supplementary_premium=None,
            other_distribution_costs=None,
        )

        self.assertIsNone(result.gross_distribution_cash)
        self.assertIsNone(result.distribution_tax)
        self.assertIsNone(result.supplementary_premium)
        self.assertIsNone(result.other_distribution_costs)

    def test_explicit_zero_costs_are_preserved(self):
        result = build_cash_flow_calculation_input(
            self.request,
            context=self.context,
            gross_distribution_cash="6500",
            distribution_tax="0",
            supplementary_premium="0",
            other_distribution_costs="0",
        )

        self.assertEqual(result.distribution_tax, 0)
        self.assertEqual(result.supplementary_premium, 0)
        self.assertEqual(result.other_distribution_costs, 0)


if __name__ == "__main__":
    unittest.main()
