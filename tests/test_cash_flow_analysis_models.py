"""現金流與總報酬計算契約模型測試。"""

import unittest
from decimal import Decimal

from pydantic import ValidationError

from backend.app.models.cash_flow_analysis import (
    AnalysisMode,
    CalculationContext,
    CalculationDateBasis,
    CalculationIssue,
    CalculationUnavailableReason,
    CashFlowCalculationInput,
    TotalReturnCalculationInput,
)


class TestCalculationContext(unittest.TestCase):
    """測試共用計算範圍。"""

    def build_context(self) -> CalculationContext:
        """建立有效的歷史回放範圍。"""

        return CalculationContext.model_validate(
            {
                "mode": "HISTORICAL_REPLAY",
                "currency": " twd ",
                "period_start": "2025-01-02",
                "period_end": "2026-01-02",
            }
        )

    def test_context_normalizes_currency(self) -> None:
        """確認單次計算幣別會被正規化。"""

        context = self.build_context()

        self.assertEqual(
            context.currency,
            "TWD",
        )
        self.assertEqual(
            context.mode,
            AnalysisMode.HISTORICAL_REPLAY,
        )

    def test_context_uses_explicit_date_bases(
        self,
    ) -> None:
        """確認現金與估值日期基準不混用。"""

        context = self.build_context()

        self.assertEqual(
            context.cash_date_basis,
            CalculationDateBasis.PAYMENT_DATE,
        )
        self.assertEqual(
            context.valuation_date_basis,
            CalculationDateBasis.TRADE_DATE,
        )

    def test_reversed_period_is_rejected(self) -> None:
        """確認起日不可晚於迄日。"""

        with self.assertRaises(ValidationError):
            CalculationContext.model_validate(
                {
                    "mode": "SCENARIO_ESTIMATE",
                    "currency": "TWD",
                    "period_start": "2026-01-03",
                    "period_end": "2026-01-02",
                }
            )

    def test_cash_date_basis_cannot_be_trade_date(
        self,
    ) -> None:
        """確認配息現金不得改用交易日歸期。"""

        with self.assertRaises(ValidationError):
            CalculationContext.model_validate(
                {
                    "mode": "HISTORICAL_REPLAY",
                    "currency": "TWD",
                    "period_start": "2025-01-02",
                    "period_end": "2026-01-02",
                    "cash_date_basis": "TRADE_DATE",
                }
            )

    def test_extra_context_field_is_rejected(self) -> None:
        """確認契約不接受未定義欄位。"""

        with self.assertRaises(ValidationError):
            CalculationContext.model_validate(
                {
                    "mode": "HISTORICAL_REPLAY",
                    "currency": "TWD",
                    "period_start": "2025-01-02",
                    "period_end": "2026-01-02",
                    "score": 100,
                }
            )


class TestCalculationInputs(unittest.TestCase):
    """測試輸入模型的缺值與數值語意。"""

    def build_context(self) -> dict[str, str]:
        """建立有效的情境估算範圍。"""

        return {
            "mode": "SCENARIO_ESTIMATE",
            "currency": "TWD",
            "period_start": "2026-01-03",
            "period_end": "2027-01-02",
        }

    def test_cash_flow_missing_values_remain_none(
        self,
    ) -> None:
        """確認缺少稅費或配息時不自動補零。"""

        value = CashFlowCalculationInput.model_validate(
            {
                "context": self.build_context(),
                "available_capital": "1000000",
                "monthly_after_tax_target": "10000",
            }
        )

        self.assertIsNone(value.reference_capital)
        self.assertIsNone(
            value.gross_distribution_cash
        )
        self.assertIsNone(value.distribution_tax)
        self.assertIsNone(
            value.supplementary_premium
        )
        self.assertIsNone(
            value.other_distribution_costs
        )

    def test_formal_zero_is_preserved(self) -> None:
        """確認正式零值與缺值不同。"""

        value = CashFlowCalculationInput.model_validate(
            {
                "context": self.build_context(),
                "available_capital": "1000000",
                "monthly_after_tax_target": "10000",
                "reference_capital": "1000000",
                "gross_distribution_cash": "60000",
                "distribution_tax": "0",
                "supplementary_premium": "0",
                "other_distribution_costs": "0",
            }
        )

        self.assertEqual(
            value.distribution_tax,
            Decimal("0"),
        )
        self.assertEqual(
            value.supplementary_premium,
            Decimal("0"),
        )

    def test_negative_money_input_is_rejected(self) -> None:
        """確認現金流輸入不得為負數。"""

        with self.assertRaises(ValidationError):
            CashFlowCalculationInput.model_validate(
                {
                    "context": self.build_context(),
                    "available_capital": "-1",
                    "monthly_after_tax_target": "10000",
                }
            )

    def test_zero_denominator_is_preserved_for_reason(
        self,
    ) -> None:
        """確認零本金留給計算器產生原因代碼。"""

        value = TotalReturnCalculationInput.model_validate(
            {
                "context": self.build_context(),
                "initial_capital": "0",
            }
        )

        self.assertEqual(
            value.initial_capital,
            Decimal("0"),
        )

    def test_total_return_uses_ledger_inputs(
        self,
    ) -> None:
        """確認帳本輸入明確分開外部金流。"""

        value = TotalReturnCalculationInput.model_validate(
            {
                "context": self.build_context(),
                "initial_capital": "1000000",
                "ending_holding_value": "950000",
                "net_withdrawn_cash": "80000",
                "later_external_contributions": "20000",
                "externally_paid_costs": "1000",
            }
        )

        self.assertEqual(
            value.initial_capital,
            Decimal("1000000"),
        )
        self.assertEqual(
            value.net_withdrawn_cash,
            Decimal("80000"),
        )

    def test_total_return_missing_values_remain_none(
        self,
    ) -> None:
        """確認總報酬缺值不會變成中性結果。"""

        value = TotalReturnCalculationInput.model_validate(
            {
                "context": self.build_context(),
            }
        )

        self.assertIsNone(value.initial_capital)
        self.assertIsNone(
            value.ending_holding_value
        )
        self.assertIsNone(value.net_withdrawn_cash)


class TestCalculationIssues(unittest.TestCase):
    """測試機器可讀的不可計算原因。"""

    def test_issue_uses_stable_reason_code(self) -> None:
        """確認缺值原因不是自由文字。"""

        issue = CalculationIssue.model_validate(
            {
                "field": "required_capital",
                "reason": (
                    "NON_POSITIVE_AFTER_TAX_CASH_RATE"
                ),
            }
        )

        self.assertEqual(
            issue.reason,
            CalculationUnavailableReason
            .NON_POSITIVE_AFTER_TAX_CASH_RATE,
        )


if __name__ == "__main__":
    unittest.main()
