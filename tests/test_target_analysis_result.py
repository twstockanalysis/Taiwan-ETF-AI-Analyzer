import unittest
from pydantic import ValidationError

from backend.app.models.cash_flow_analysis import (
    CashFlowCalculationResult,
    ScenarioEstimateCalculationResult,
)
from backend.app.models.target_analysis import (
    TargetAnalysisResult,
    TargetAnalysisStatus,
    TargetAnalysisUnavailableField,
    TargetAnalysisWarning,
    TargetAnalysisWarningCode,
)


class TestTargetAnalysisResult(unittest.TestCase):
    def test_available_result_preserves_calculator_results(self):
        cash_flow = CashFlowCalculationResult.model_construct()
        scenario = (
            ScenarioEstimateCalculationResult.model_construct()
        )

        result = TargetAnalysisResult(
            status=TargetAnalysisStatus.AVAILABLE,
            cash_flow=cash_flow,
            scenario_estimate=scenario,
        )

        self.assertIs(result.cash_flow, cash_flow)
        self.assertIs(result.scenario_estimate, scenario)
        self.assertEqual(result.warnings, [])
        self.assertEqual(result.unavailable_fields, [])

    def test_partial_result_preserves_qualification_details(self):
        warning = TargetAnalysisWarning(
            code=(
                TargetAnalysisWarningCode
                .INSUFFICIENT_DIVIDEND_HISTORY
            ),
            message="Dividend history is incomplete.",
            affected_fields=["required_capital"],
        )
        unavailable = TargetAnalysisUnavailableField(
            field="required_capital",
            reason="Dividend yield history is incomplete.",
        )

        result = TargetAnalysisResult(
            status=TargetAnalysisStatus.PARTIAL,
            cash_flow=(
                CashFlowCalculationResult.model_construct()
            ),
            scenario_estimate=(
                ScenarioEstimateCalculationResult.model_construct()
            ),
            warnings=[warning],
            unavailable_fields=[unavailable],
        )

        self.assertEqual(result.warnings, [warning])
        self.assertEqual(
            result.unavailable_fields,
            [unavailable],
        )


    def test_unknown_result_fields_are_rejected(self):
        """確認公開結果契約拒絕未定義欄位。"""

        with self.assertRaises(ValidationError):
            TargetAnalysisResult(
                status=TargetAnalysisStatus.AVAILABLE,
                cash_flow=(
                    CashFlowCalculationResult.model_construct()
                ),
                scenario_estimate=(
                    ScenarioEstimateCalculationResult
                    .model_construct()
                ),
                unsupported_option=True,
            )

if __name__ == "__main__":
    unittest.main()
