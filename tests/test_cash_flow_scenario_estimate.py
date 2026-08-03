"""現金流與總報酬情境估算測試。"""

import unittest
from decimal import Decimal

from pydantic import ValidationError

from backend.app.models.cash_flow_analysis import (
    CalculationUnavailableReason,
    DistributionReinvestmentPolicy,
    ScenarioEstimateCalculationInput,
)
from backend.app.services.cash_flow_calculator import (
    calculate_scenario_estimate,
)


def build_context() -> dict[str, str]:
    """建立固定情境估算期間。"""

    return {
        "mode": "SCENARIO_ESTIMATE",
        "currency": "TWD",
        "period_start": "2026-01-01",
        "period_end": "2028-12-31",
    }


class TestScenarioEstimateCalculator(unittest.TestCase):
    """測試不再投入配息的情境估算。"""

    def build_input(
        self,
        **overrides: object,
    ) -> ScenarioEstimateCalculationInput:
        """建立完整情境輸入。"""

        payload: dict[str, object] = {
            "context": build_context(),
            "initial_capital": "1000000",
            "annual_gross_cash_rate_pct": "6",
            "cash_deduction_rate_pct": "10",
            "annual_price_return_pct": "5",
            "projection_years": 3,
        }
        payload.update(overrides)
        return ScenarioEstimateCalculationInput.model_validate(
            payload
        )

    def test_complete_no_reinvestment_scenario(self) -> None:
        """確認價格複利與固定本金現金率分開計算。"""

        result = calculate_scenario_estimate(
            self.build_input()
        )

        self.assertEqual(
            result.ending_holding_value,
            Decimal("1157625.00"),
        )
        self.assertEqual(
            result.cumulative_gross_cash,
            Decimal("180000.00"),
        )
        self.assertEqual(
            result.cumulative_cash_deductions,
            Decimal("18000.00"),
        )
        self.assertEqual(
            result.cumulative_after_tax_cash,
            Decimal("162000.00"),
        )
        self.assertEqual(
            result.after_tax_total_gain_loss,
            Decimal("319625.00"),
        )
        self.assertEqual(
            result.after_tax_total_return_pct,
            Decimal("31.962500"),
        )
        self.assertEqual(result.issues, [])
        self.assertEqual(
            result.reinvestment_policy,
            DistributionReinvestmentPolicy.NO_REINVESTMENT,
        )

    def test_negative_price_return_is_supported(self) -> None:
        """確認價格下跌可由稅後現金部分抵銷。"""

        result = calculate_scenario_estimate(
            self.build_input(
                annual_gross_cash_rate_pct="4",
                cash_deduction_rate_pct="0",
                annual_price_return_pct="-10",
                projection_years=2,
            )
        )

        self.assertEqual(
            result.ending_holding_value,
            Decimal("810000.00"),
        )
        self.assertEqual(
            result.after_tax_total_gain_loss,
            Decimal("-110000.00"),
        )
        self.assertEqual(
            result.after_tax_total_return_pct,
            Decimal("-11.000000"),
        )

    def test_zero_assumptions_are_formal_values(self) -> None:
        """確認零現金率與零價格報酬不是缺值。"""

        result = calculate_scenario_estimate(
            self.build_input(
                annual_gross_cash_rate_pct="0",
                cash_deduction_rate_pct="0",
                annual_price_return_pct="0",
            )
        )

        self.assertEqual(
            result.cumulative_after_tax_cash,
            Decimal("0.00"),
        )
        self.assertEqual(
            result.after_tax_total_return_pct,
            Decimal("0.000000"),
        )
        self.assertEqual(result.issues, [])

    def test_full_cash_deduction_is_supported(self) -> None:
        """確認 100% 現金扣除率仍可正式計算。"""

        result = calculate_scenario_estimate(
            self.build_input(
                cash_deduction_rate_pct="100",
            )
        )

        self.assertEqual(
            result.cumulative_after_tax_cash,
            Decimal("0.00"),
        )
        self.assertEqual(
            result.after_tax_total_return_pct,
            Decimal("15.762500"),
        )

    def test_total_price_loss_stays_at_zero_value(self) -> None:
        """確認 -100% 價格報酬不產生負持有價值。"""

        result = calculate_scenario_estimate(
            self.build_input(
                annual_price_return_pct="-100",
            )
        )

        self.assertEqual(
            result.ending_holding_value,
            Decimal("0.00"),
        )

    def test_missing_assumption_keeps_results_unavailable(
        self,
    ) -> None:
        """確認缺少假設時不自動補零。"""

        result = calculate_scenario_estimate(
            self.build_input(
                annual_price_return_pct=None,
            )
        )

        self.assertIsNone(result.ending_holding_value)
        self.assertIsNone(
            result.cumulative_after_tax_cash
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

    def test_zero_initial_capital_has_no_rate(self) -> None:
        """確認零本金保留零金額但沒有報酬率。"""

        result = calculate_scenario_estimate(
            self.build_input(initial_capital="0")
        )

        self.assertEqual(
            result.after_tax_total_gain_loss,
            Decimal("0.00"),
        )
        self.assertIsNone(
            result.after_tax_total_return_pct
        )
        self.assertEqual(
            result.issues[0].reason,
            CalculationUnavailableReason
            .NON_POSITIVE_INITIAL_CAPITAL,
        )

    def test_historical_mode_is_rejected(self) -> None:
        """確認情境假設不可標示成歷史回放。"""

        with self.assertRaises(ValidationError):
            self.build_input(
                context={
                    **build_context(),
                    "mode": "HISTORICAL_REPLAY",
                }
            )

    def test_invalid_deduction_rate_is_rejected(self) -> None:
        """確認現金扣除率不可超過 100%。"""

        with self.assertRaises(ValidationError):
            self.build_input(
                cash_deduction_rate_pct="100.000001"
            )

    def test_price_return_below_total_loss_is_rejected(
        self,
    ) -> None:
        """確認價格報酬不可低於 -100%。"""

        with self.assertRaises(ValidationError):
            self.build_input(
                annual_price_return_pct="-100.000001"
            )

    def test_projection_year_range_is_enforced(self) -> None:
        """確認推估期間限制為 1 至 50 年。"""

        for years in (0, 51):
            with self.subTest(years=years):
                with self.assertRaises(ValidationError):
                    self.build_input(
                        projection_years=years
                    )

    def test_public_results_round_half_up(self) -> None:
        """確認情境公開結果沿用契約四捨五入。"""

        result = calculate_scenario_estimate(
            self.build_input(
                initial_capital="1",
                annual_gross_cash_rate_pct="0.5",
                cash_deduction_rate_pct="0",
                annual_price_return_pct="0.5",
                projection_years=1,
            )
        )

        self.assertEqual(
            result.ending_holding_value,
            Decimal("1.01"),
        )
        self.assertEqual(
            result.cumulative_gross_cash,
            Decimal("0.01"),
        )
