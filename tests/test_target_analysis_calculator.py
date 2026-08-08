from datetime import date
import unittest
from unittest.mock import patch

from backend.app.models.cash_flow_analysis import (
    AnalysisMode,
    CalculationContext,
    CashFlowCalculationInput,
    CashFlowCalculationResult,
    ScenarioEstimateCalculationInput,
    ScenarioEstimateCalculationResult,
)
from backend.app.models.target_analysis import (
    TargetAnalysisRequest,
    TargetAnalysisStatus,
    TargetAnalysisWarningCode,
)
from backend.app.services.target_analysis_calculator import (
    calculate_target_analysis,
)


class TestTargetAnalysisCalculator(unittest.TestCase):
    @patch(
        "backend.app.services.target_analysis_calculator."
        "calculate_scenario_estimate"
    )
    @patch(
        "backend.app.services.target_analysis_calculator."
        "calculate_cash_flow_target"
    )
    @patch(
        "backend.app.services.target_analysis_calculator."
        "build_scenario_estimate_input"
    )
    @patch(
        "backend.app.services.target_analysis_calculator."
        "build_cash_flow_calculation_input"
    )
    def test_complete_inputs_delegate_to_existing_calculators(
        self,
        mock_build_cash_flow,
        mock_build_scenario,
        mock_calculate_cash_flow,
        mock_calculate_scenario,
    ):
        context = CalculationContext(
            mode=AnalysisMode.SCENARIO_ESTIMATE,
            currency="TWD",
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
        )
        request = TargetAnalysisRequest(
            held_units=2000,
            unit_price="50.25",
            monthly_after_tax_target="10000",
            analysis_years=10,
            cash_deduction_rate_pct="2.11",
        )

        cash_flow_input = (
            CashFlowCalculationInput.model_construct()
        )
        scenario_input = (
            ScenarioEstimateCalculationInput.model_construct()
        )
        cash_flow_result = (
            CashFlowCalculationResult.model_construct()
        )
        scenario_result = (
            ScenarioEstimateCalculationResult.model_construct()
        )

        mock_build_cash_flow.return_value = cash_flow_input
        mock_build_scenario.return_value = scenario_input
        mock_calculate_cash_flow.return_value = (
            cash_flow_result
        )
        mock_calculate_scenario.return_value = scenario_result

        result = calculate_target_analysis(
            request,
            context=context,
            gross_distribution_cash="6500",
            distribution_tax="100",
            supplementary_premium="50",
            other_distribution_costs="25",
            annual_gross_cash_rate_pct="6.50",
            annual_price_return_pct="-1.25",
        )

        mock_build_cash_flow.assert_called_once_with(
            request,
            context=context,
            gross_distribution_cash="6500",
            distribution_tax="100",
            supplementary_premium="50",
            other_distribution_costs="25",
        )
        mock_build_scenario.assert_called_once_with(
            request,
            context=context,
            annual_gross_cash_rate_pct="6.50",
            annual_price_return_pct="-1.25",
        )
        mock_calculate_cash_flow.assert_called_once_with(
            cash_flow_input
        )
        mock_calculate_scenario.assert_called_once_with(
            scenario_input
        )

        self.assertEqual(
            result.status,
            TargetAnalysisStatus.AVAILABLE,
        )
        self.assertIs(result.cash_flow, cash_flow_result)
        self.assertIs(
            result.scenario_estimate,
            scenario_result,
        )
        self.assertEqual(result.warnings, [])
        self.assertEqual(result.unavailable_fields, [])

    def test_missing_history_returns_partial_result(self):
        context = CalculationContext(
            mode=AnalysisMode.SCENARIO_ESTIMATE,
            currency="TWD",
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
        )
        request = TargetAnalysisRequest(
            held_units=2000,
            unit_price="50.25",
            monthly_after_tax_target="10000",
            analysis_years=10,
            cash_deduction_rate_pct="2.11",
        )

        result = calculate_target_analysis(
            request,
            context=context,
            gross_distribution_cash=None,
            distribution_tax=None,
            supplementary_premium=None,
            other_distribution_costs=None,
            annual_gross_cash_rate_pct=None,
            annual_price_return_pct=None,
        )

        self.assertEqual(
            result.status,
            TargetAnalysisStatus.PARTIAL,
        )
        self.assertEqual(
            str(result.cash_flow.annual_after_tax_target),
            "120000.00",
        )
        self.assertEqual(
            result.scenario_estimate.projection_years,
            10,
        )

        warning_codes = {
            warning.code
            for warning in result.warnings
        }
        self.assertEqual(
            warning_codes,
            {
                TargetAnalysisWarningCode
                .INSUFFICIENT_DIVIDEND_HISTORY,
                TargetAnalysisWarningCode
                .INSUFFICIENT_PERFORMANCE_HISTORY,
            },
        )
        self.assertTrue(
            all(
                warning.message
                for warning in result.warnings
            )
        )

        unavailable_by_field = {
            unavailable.field: unavailable.reason
            for unavailable in result.unavailable_fields
        }
        self.assertEqual(
            unavailable_by_field,
            {
                "after_tax_usable_cash": "MISSING_INPUT",
                "target_coverage_pct": "MISSING_INPUT",
                "required_capital": "MISSING_INPUT",
                "funding_shortfall": "MISSING_INPUT",
                "ending_holding_value": "MISSING_INPUT",
                "cumulative_gross_cash": "MISSING_INPUT",
                "cumulative_cash_deductions": "MISSING_INPUT",
                "cumulative_after_tax_cash": "MISSING_INPUT",
                "after_tax_total_gain_loss": "MISSING_INPUT",
                "after_tax_total_return_pct": "MISSING_INPUT",
            },
        )
    def test_only_missing_dividend_history_warns_dividend(self):
        context = CalculationContext(
            mode=AnalysisMode.SCENARIO_ESTIMATE,
            currency="TWD",
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
        )
        request = TargetAnalysisRequest(
            held_units=2000,
            unit_price="50.25",
            monthly_after_tax_target="10000",
            analysis_years=10,
            cash_deduction_rate_pct="2.11",
        )

        result = calculate_target_analysis(
            request,
            context=context,
            gross_distribution_cash=None,
            distribution_tax=None,
            supplementary_premium=None,
            other_distribution_costs=None,
            annual_gross_cash_rate_pct=None,
            annual_price_return_pct="4.00",
        )

        self.assertEqual(
            result.status,
            TargetAnalysisStatus.PARTIAL,
        )
        self.assertEqual(
            [warning.code for warning in result.warnings],
            [
                TargetAnalysisWarningCode
                .INSUFFICIENT_DIVIDEND_HISTORY
            ],
        )

        unavailable_names = {
            unavailable.field
            for unavailable in result.unavailable_fields
        }
        self.assertIn(
            "required_capital",
            unavailable_names,
        )
        self.assertNotIn(
            "ending_holding_value",
            unavailable_names,
        )

        for warning in result.warnings:
            self.assertTrue(warning.affected_fields)
            self.assertTrue(
                set(warning.affected_fields)
                <= unavailable_names
            )

    def test_only_missing_performance_history_warns_performance(
        self,
    ):
        context = CalculationContext(
            mode=AnalysisMode.SCENARIO_ESTIMATE,
            currency="TWD",
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
        )
        request = TargetAnalysisRequest(
            held_units=2000,
            unit_price="50.25",
            monthly_after_tax_target="10000",
            analysis_years=10,
            cash_deduction_rate_pct="2.11",
        )

        result = calculate_target_analysis(
            request,
            context=context,
            gross_distribution_cash="6500",
            distribution_tax="100",
            supplementary_premium="50",
            other_distribution_costs="25",
            annual_gross_cash_rate_pct="6.50",
            annual_price_return_pct=None,
        )

        self.assertEqual(
            result.status,
            TargetAnalysisStatus.PARTIAL,
        )
        self.assertEqual(
            [warning.code for warning in result.warnings],
            [
                TargetAnalysisWarningCode
                .INSUFFICIENT_PERFORMANCE_HISTORY
            ],
        )

        unavailable_names = {
            unavailable.field
            for unavailable in result.unavailable_fields
        }
        self.assertIn(
            "ending_holding_value",
            unavailable_names,
        )
        self.assertNotIn(
            "required_capital",
            unavailable_names,
        )

        for warning in result.warnings:
            self.assertTrue(warning.affected_fields)
            self.assertTrue(
                set(warning.affected_fields)
                <= unavailable_names
            )

    def test_missing_cash_breakdown_warns_incomplete_data(
        self,
    ):
        """確認配息稅費明細缺漏時產生資料不完整警告。"""

        context = CalculationContext(
            mode=AnalysisMode.SCENARIO_ESTIMATE,
            currency="TWD",
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
        )
        request = TargetAnalysisRequest(
            held_units=2000,
            unit_price="50.25",
            monthly_after_tax_target="10000",
            analysis_years=10,
            cash_deduction_rate_pct="2.11",
        )

        result = calculate_target_analysis(
            request,
            context=context,
            gross_distribution_cash="6500",
            distribution_tax=None,
            supplementary_premium="50",
            other_distribution_costs="25",
            annual_gross_cash_rate_pct="6.50",
            annual_price_return_pct="4.00",
        )

        self.assertEqual(
            result.status,
            TargetAnalysisStatus.PARTIAL,
        )
        self.assertEqual(
            [
                warning.code
                for warning in result.warnings
            ],
            [
                TargetAnalysisWarningCode
                .INCOMPLETE_DIVIDEND_DATA
            ],
        )
        self.assertEqual(
            set(result.warnings[0].affected_fields),
            {
                "after_tax_usable_cash",
                "target_coverage_pct",
                "required_capital",
                "funding_shortfall",
            },
        )

if __name__ == "__main__":
    unittest.main()
