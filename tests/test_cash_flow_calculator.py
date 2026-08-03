"""現金流與稅後總報酬計算服務測試。"""

import unittest
from decimal import Decimal

from backend.app.models.cash_flow_analysis import (
    CalculationUnavailableReason,
    CashFlowCalculationInput,
    NoReinvestmentTotalReturnCalculationInput,
    TotalReturnCalculationInput,
)
from backend.app.services.cash_flow_calculator import (
    calculate_cash_flow_target,
    calculate_no_reinvestment_total_return,
    calculate_total_return,
)


def build_context() -> dict[str, str]:
    """建立固定歷史回放期間。"""

    return {
        "mode": "HISTORICAL_REPLAY",
        "currency": "TWD",
        "period_start": "2025-01-02",
        "period_end": "2026-01-02",
    }


class TestCashFlowCalculator(unittest.TestCase):
    """測試固定稅後現金流目標。"""

    def build_input(
        self,
        **overrides: object,
    ) -> CashFlowCalculationInput:
        """建立完整現金流輸入。"""

        payload: dict[str, object] = {
            "context": build_context(),
            "available_capital": "1000000",
            "monthly_after_tax_target": "10000",
            "reference_capital": "1000000",
            "gross_distribution_cash": "60000",
            "distribution_tax": "6000",
            "supplementary_premium": "1000",
            "other_distribution_costs": "3000",
        }
        payload.update(overrides)
        return CashFlowCalculationInput.model_validate(
            payload
        )

    def test_complete_cash_flow_target(self) -> None:
        """確認稅後現金率、覆蓋率與所需本金。"""

        result = calculate_cash_flow_target(
            self.build_input()
        )

        self.assertEqual(
            result.annual_after_tax_target,
            Decimal("120000.00"),
        )
        self.assertEqual(
            result.after_tax_usable_cash,
            Decimal("50000.00"),
        )
        self.assertEqual(
            result.target_coverage_pct,
            Decimal("41.666667"),
        )
        self.assertEqual(
            result.required_capital,
            Decimal("2400000.00"),
        )
        self.assertEqual(
            result.funding_shortfall,
            Decimal("1400000.00"),
        )
        self.assertEqual(result.issues, [])

    def test_sufficient_capital_has_zero_shortfall(
        self,
    ) -> None:
        """確認本金足夠時缺口為正式零值。"""

        result = calculate_cash_flow_target(
            self.build_input(
                available_capital="3000000"
            )
        )

        self.assertEqual(
            result.target_coverage_pct,
            Decimal("125.000000"),
        )
        self.assertEqual(
            result.funding_shortfall,
            Decimal("0.00"),
        )

    def test_zero_target_needs_no_reference_rate(
        self,
    ) -> None:
        """確認零目標不被誤判成缺少目標。"""

        value = CashFlowCalculationInput.model_validate(
            {
                "context": build_context(),
                "available_capital": "0",
                "monthly_after_tax_target": "0",
            }
        )

        result = calculate_cash_flow_target(value)

        self.assertEqual(
            result.annual_after_tax_target,
            Decimal("0.00"),
        )
        self.assertEqual(
            result.target_coverage_pct,
            Decimal("100.000000"),
        )
        self.assertEqual(
            result.required_capital,
            Decimal("0.00"),
        )
        self.assertEqual(
            result.funding_shortfall,
            Decimal("0.00"),
        )

    def test_missing_deduction_keeps_results_unavailable(
        self,
    ) -> None:
        """確認缺少稅費時不自動補零。"""

        result = calculate_cash_flow_target(
            self.build_input(
                distribution_tax=None,
            )
        )

        self.assertIsNone(
            result.after_tax_usable_cash
        )
        self.assertIsNone(
            result.target_coverage_pct
        )
        self.assertIsNone(result.required_capital)
        self.assertIsNone(result.funding_shortfall)
        self.assertTrue(
            all(
                issue.reason
                == CalculationUnavailableReason.MISSING_INPUT
                for issue in result.issues
            )
        )

    def test_missing_reference_capital_is_reported(
        self,
    ) -> None:
        """確認缺少參考本金時仍保留已算稅後現金。"""

        result = calculate_cash_flow_target(
            self.build_input(
                reference_capital=None,
            )
        )

        self.assertEqual(
            result.after_tax_usable_cash,
            Decimal("50000.00"),
        )
        self.assertIsNone(result.required_capital)
        self.assertEqual(
            result.issues[0].reason,
            CalculationUnavailableReason.MISSING_INPUT,
        )

    def test_zero_cash_rate_is_reported(self) -> None:
        """確認零稅後現金率不執行除法。"""

        result = calculate_cash_flow_target(
            self.build_input(
                gross_distribution_cash="10000",
                distribution_tax="6000",
                supplementary_premium="1000",
                other_distribution_costs="3000",
            )
        )

        self.assertEqual(
            result.after_tax_usable_cash,
            Decimal("0.00"),
        )
        self.assertIsNone(result.required_capital)
        self.assertEqual(
            result.issues[0].reason,
            CalculationUnavailableReason
            .NON_POSITIVE_AFTER_TAX_CASH_RATE,
        )

    def test_negative_usable_cash_is_reported(
        self,
    ) -> None:
        """確認扣除額高於配息時不推算本金。"""

        result = calculate_cash_flow_target(
            self.build_input(
                gross_distribution_cash="5000",
            )
        )

        self.assertEqual(
            result.after_tax_usable_cash,
            Decimal("-5000.00"),
        )
        self.assertIsNone(result.required_capital)
        self.assertEqual(
            result.issues[0].reason,
            CalculationUnavailableReason
            .NEGATIVE_AFTER_TAX_USABLE_CASH,
        )

    def test_public_results_round_half_up(self) -> None:
        """確認公開結果採契約指定四捨五入。"""

        result = calculate_cash_flow_target(
            self.build_input(
                monthly_after_tax_target="0.00125"
            )
        )

        self.assertEqual(
            result.annual_after_tax_target,
            Decimal("0.02"),
        )


class TestTotalReturnCalculator(unittest.TestCase):
    """測試帳本式稅後總報酬。"""

    def build_input(
        self,
        **overrides: object,
    ) -> TotalReturnCalculationInput:
        """建立完整帳本輸入。"""

        payload: dict[str, object] = {
            "context": build_context(),
            "initial_capital": "1000000",
            "ending_holding_value": "950000",
            "net_withdrawn_cash": "80000",
            "later_external_contributions": "20000",
            "externally_paid_costs": "1000",
        }
        payload.update(overrides)
        return TotalReturnCalculationInput.model_validate(
            payload
        )

    def test_positive_ledger_total_return(self) -> None:
        """確認市場損益與稅後總損益分開。"""

        result = calculate_total_return(
            self.build_input()
        )

        self.assertEqual(
            result.market_value_gain_loss,
            Decimal("-50000.00"),
        )
        self.assertEqual(
            result.after_tax_total_gain_loss,
            Decimal("9000.00"),
        )
        self.assertEqual(
            result.after_tax_total_return_pct,
            Decimal("0.900000"),
        )
        self.assertEqual(result.issues, [])

    def test_negative_total_return(self) -> None:
        """確認負總報酬不會截斷為零。"""

        result = calculate_total_return(
            self.build_input(
                ending_holding_value="850000"
            )
        )

        self.assertEqual(
            result.after_tax_total_gain_loss,
            Decimal("-91000.00"),
        )
        self.assertEqual(
            result.after_tax_total_return_pct,
            Decimal("-9.100000"),
        )

    def test_missing_ledger_values_remain_none(
        self,
    ) -> None:
        """確認缺值不會產生中性總報酬。"""

        value = TotalReturnCalculationInput.model_validate(
            {"context": build_context()}
        )

        result = calculate_total_return(value)

        self.assertIsNone(
            result.market_value_gain_loss
        )
        self.assertIsNone(
            result.after_tax_total_gain_loss
        )
        self.assertIsNone(
            result.after_tax_total_return_pct
        )
        self.assertTrue(
            all(
                issue.reason
                == CalculationUnavailableReason.MISSING_INPUT
                for issue in result.issues
            )
        )

    def test_zero_initial_capital_only_blocks_rate(
        self,
    ) -> None:
        """確認零期初本金只使報酬率不可計算。"""

        result = calculate_total_return(
            self.build_input(
                initial_capital="0",
            )
        )

        self.assertEqual(
            result.market_value_gain_loss,
            Decimal("950000.00"),
        )
        self.assertEqual(
            result.after_tax_total_gain_loss,
            Decimal("1009000.00"),
        )
        self.assertIsNone(
            result.after_tax_total_return_pct
        )
        self.assertEqual(
            result.issues[0].reason,
            CalculationUnavailableReason
            .NON_POSITIVE_INITIAL_CAPITAL,
        )

    def test_total_return_percentage_rounds_half_up(
        self,
    ) -> None:
        """確認總報酬百分比保留六位。"""

        result = calculate_total_return(
            self.build_input(
                initial_capital="3",
                ending_holding_value="4",
                net_withdrawn_cash="0",
                later_external_contributions="0",
                externally_paid_costs="0",
            )
        )

        self.assertEqual(
            result.after_tax_total_return_pct,
            Decimal("33.333333"),
        )

    def test_formal_zero_cash_is_calculable(self) -> None:
        """確認正式零提領現金不是缺值。"""

        result = calculate_total_return(
            self.build_input(
                ending_holding_value="1000000",
                net_withdrawn_cash="0",
                later_external_contributions="0",
                externally_paid_costs="0",
            )
        )

        self.assertEqual(
            result.after_tax_total_return_pct,
            Decimal("0.000000"),
        )
        self.assertEqual(result.issues, [])


class TestNoReinvestmentReconciliation(
    unittest.TestCase
):
    """測試未再投入配息拆解與帳本恆等式。"""

    def build_breakdown(
        self,
        **overrides: object,
    ) -> NoReinvestmentTotalReturnCalculationInput:
        """建立完整未再投入配息拆解。"""

        payload: dict[str, object] = {
            "context": build_context(),
            "initial_capital": "1000000",
            "ending_holding_value": "950000",
            "gross_distributions": "90000",
            "distribution_tax": "6000",
            "supplementary_premium": "1000",
            "transaction_costs": "3000",
            "other_externally_paid_costs": "1000",
        }
        payload.update(overrides)
        return (
            NoReinvestmentTotalReturnCalculationInput
            .model_validate(payload)
        )

    def test_breakdown_reconciles_with_ledger(
        self,
    ) -> None:
        """確認兩種等價輸入產生相同總報酬。"""

        breakdown_result = (
            calculate_no_reinvestment_total_return(
                self.build_breakdown()
            )
        )
        ledger_result = calculate_total_return(
            TotalReturnCalculationInput.model_validate(
                {
                    "context": build_context(),
                    "initial_capital": "1000000",
                    "ending_holding_value": "950000",
                    "net_withdrawn_cash": "80000",
                    "externally_paid_costs": "1000",
                }
            )
        )

        self.assertEqual(
            breakdown_result.after_tax_total_gain_loss,
            Decimal("29000.00"),
        )
        self.assertEqual(
            breakdown_result,
            ledger_result,
        )

    def test_breakdown_missing_tax_is_unavailable(
        self,
    ) -> None:
        """確認拆解缺少稅額時不自動補零。"""

        result = (
            calculate_no_reinvestment_total_return(
                self.build_breakdown(
                    distribution_tax=None,
                )
            )
        )

        self.assertEqual(
            result.market_value_gain_loss,
            Decimal("-50000.00"),
        )
        self.assertIsNone(
            result.after_tax_total_gain_loss
        )
        self.assertIsNone(
            result.after_tax_total_return_pct
        )

    def test_breakdown_zero_costs_are_valid(self) -> None:
        """確認正式零成本可進入總報酬公式。"""

        result = (
            calculate_no_reinvestment_total_return(
                self.build_breakdown(
                    distribution_tax="0",
                    supplementary_premium="0",
                    transaction_costs="0",
                    other_externally_paid_costs="0",
                )
            )
        )

        self.assertEqual(
            result.after_tax_total_gain_loss,
            Decimal("40000.00"),
        )
        self.assertEqual(
            result.after_tax_total_return_pct,
            Decimal("4.000000"),
        )


if __name__ == "__main__":
    unittest.main()
