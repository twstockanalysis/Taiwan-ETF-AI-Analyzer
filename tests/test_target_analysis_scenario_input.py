from datetime import date
from decimal import Decimal
import unittest

from backend.app.models.cash_flow_analysis import (
    AnalysisMode,
    CalculationContext,
    DistributionReinvestmentPolicy,
    ScenarioEstimateCalculationInput,
)
from backend.app.models.target_analysis import (
    TargetAnalysisRequest,
)
from backend.app.services.target_analysis_calculator import (
    build_scenario_estimate_input,
)


class TestTargetAnalysisScenarioInput(unittest.TestCase):
    @staticmethod
    def _build_context() -> CalculationContext:
        return CalculationContext(
            mode=AnalysisMode.SCENARIO_ESTIMATE,
            currency="TWD",
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
        )

    def test_request_and_assumptions_are_mapped(self):
        context = self._build_context()
        request = TargetAnalysisRequest(
            held_units=1000,
            unit_price="35.50",
            monthly_after_tax_target="10000",
            analysis_years=10,
            cash_deduction_rate_pct="2.11",
        )

        result = build_scenario_estimate_input(
            request,
            context=context,
            annual_gross_cash_rate_pct="6.50",
            annual_price_return_pct="-1.25",
        )

        self.assertIsInstance(
            result,
            ScenarioEstimateCalculationInput,
        )
        self.assertIs(result.context, context)
        self.assertEqual(
            result.initial_capital,
            Decimal("35500.00"),
        )
        self.assertEqual(
            result.annual_gross_cash_rate_pct,
            Decimal("6.50"),
        )
        self.assertEqual(
            result.cash_deduction_rate_pct,
            Decimal("2.11"),
        )
        self.assertEqual(
            result.annual_price_return_pct,
            Decimal("-1.25"),
        )
        self.assertEqual(result.projection_years, 10)
        self.assertEqual(
            result.reinvestment_policy,
            DistributionReinvestmentPolicy.NO_REINVESTMENT,
        )

    def test_missing_optional_assumptions_remain_missing(self):
        context = self._build_context()
        request = TargetAnalysisRequest(
            held_units=0,
            unit_price="35.50",
            monthly_after_tax_target="10000",
            analysis_years=5,
        )

        result = build_scenario_estimate_input(
            request,
            context=context,
            annual_gross_cash_rate_pct=None,
            annual_price_return_pct=None,
        )

        self.assertEqual(
            result.initial_capital,
            Decimal("0.00"),
        )
        self.assertIsNone(
            result.annual_gross_cash_rate_pct
        )
        self.assertIsNone(
            result.cash_deduction_rate_pct
        )
        self.assertIsNone(
            result.annual_price_return_pct
        )


if __name__ == "__main__":
    unittest.main()