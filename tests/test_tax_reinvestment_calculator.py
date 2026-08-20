"""M10-4 稅務與再投資純計算測試。"""

from datetime import date
from decimal import Decimal
import unittest

from backend.app.models.tax_reinvestment import (
    ComponentCalculationBasis,
    ComponentTaxAssumption,
    OfficialComponentAllocation,
    ReinvestmentPolicy,
    TaiwanIndividualTaxRule,
    TaxReinvestmentCalculationInput,
    TaxScenarioUnavailableReason,
)
from backend.app.services.tax_reinvestment_calculator import (
    calculate_tax_reinvestment_scenarios,
)


class TestTaxReinvestmentCalculator(unittest.TestCase):
    """鎖定稅、補充保費與再投入帳本邊界。"""

    @staticmethod
    def build_input(**updates) -> TaxReinvestmentCalculationInput:
        values = {
            "initial_units": "10000",
            "initial_unit_price": "20",
            "annual_gross_distribution_rate_pct": "10",
            "annual_price_return_pct": "0",
            "projection_years": 1,
            "annual_cash_target": "12000",
            "payments_per_year": 1,
            "actual_component_mix": [
                OfficialComponentAllocation(
                    component_code="54C",
                    component_name="境內股利所得",
                    ratio_pct="50",
                ),
                OfficialComponentAllocation(
                    component_code="76W",
                    component_name="國內財產交易所得",
                    ratio_pct="50",
                ),
            ],
            "tax_rule": TaiwanIndividualTaxRule(
                rule_version="TW-INDIVIDUAL-2026.1",
                effective_date=date(2021, 1, 1),
                supplementary_premium_rate_pct="2.11",
                supplementary_premium_payment_threshold="20000",
                supplementary_premium_payment_cap="10000000",
                annual_tax_credit_cap="80000",
                component_assumptions=[
                    ComponentTaxAssumption(
                        component_code="54C",
                        income_tax_rate_pct="12",
                        tax_credit_rate_pct="8.5",
                        supplementary_premium_applicable=True,
                    ),
                    ComponentTaxAssumption(
                        component_code="76W",
                        income_tax_rate_pct="0",
                        supplementary_premium_applicable=False,
                    ),
                ],
            ),
            "custom_reinvestment_pct": "25",
        }
        values.update(updates)
        return TaxReinvestmentCalculationInput(**values)

    def test_compares_all_four_policies(self) -> None:
        result = calculate_tax_reinvestment_scenarios(self.build_input())

        self.assertEqual(
            [item.policy for item in result.scenarios],
            list(ReinvestmentPolicy),
        )
        self.assertEqual(result.estimate_label, "情境估算，非稅務建議")
        self.assertEqual(result.projection_years, 1)
        self.assertEqual(result.historical_component_basis, "ACTUAL")

    def test_reinvested_cash_is_not_double_counted(self) -> None:
        result = calculate_tax_reinvestment_scenarios(self.build_input())
        no_reinvestment = result.scenarios[0]
        full_reinvestment = result.scenarios[-1]

        self.assertEqual(no_reinvestment.modeled_income_tax, Decimal("350.00"))
        self.assertEqual(no_reinvestment.usable_cash, Decimal("19650.00"))
        self.assertEqual(full_reinvestment.usable_cash, Decimal("0.00"))
        self.assertEqual(full_reinvestment.reinvested_cash, Decimal("19650.00"))
        self.assertEqual(
            no_reinvestment.after_tax_total_gain_loss,
            full_reinvestment.after_tax_total_gain_loss,
        )

    def test_excess_only_preserves_fixed_cash_target(self) -> None:
        result = calculate_tax_reinvestment_scenarios(self.build_input())
        excess = result.scenarios[1]

        self.assertEqual(excess.usable_cash, Decimal("12000.00"))
        self.assertEqual(excess.reinvested_cash, Decimal("7650.00"))

    def test_supplementary_premium_uses_per_payment_threshold(self) -> None:
        two_payments = calculate_tax_reinvestment_scenarios(
            self.build_input(payments_per_year=2)
        )
        one_payment = calculate_tax_reinvestment_scenarios(
            self.build_input(
                actual_component_mix=[
                    OfficialComponentAllocation(
                        component_code="54C",
                        ratio_pct="100",
                    )
                ],
                tax_rule=TaiwanIndividualTaxRule(
                    rule_version="test",
                    effective_date=date(2021, 1, 1),
                    component_assumptions=[
                        ComponentTaxAssumption(
                            component_code="54C",
                            income_tax_rate_pct="0",
                            supplementary_premium_applicable=True,
                        )
                    ],
                ),
            )
        )

        self.assertEqual(
            two_payments.scenarios[0].modeled_supplementary_premium,
            Decimal("0.00"),
        )
        self.assertEqual(
            one_payment.scenarios[0].modeled_supplementary_premium,
            Decimal("422.00"),
        )

    def test_missing_actual_components_never_becomes_zero(self) -> None:
        result = calculate_tax_reinvestment_scenarios(
            self.build_input(actual_component_mix=None)
        )

        self.assertEqual(
            result.issues[0].reason,
            TaxScenarioUnavailableReason.MISSING_ACTUAL_COMPONENTS,
        )
        self.assertIsNone(result.scenarios[0].modeled_tax_cost)
        self.assertIsNone(result.scenarios[0].usable_cash)

    def test_formal_zero_component_is_available(self) -> None:
        result = calculate_tax_reinvestment_scenarios(
            self.build_input(
                actual_component_mix=[
                    OfficialComponentAllocation(
                        component_code="54C",
                        ratio_pct="100",
                    ),
                    OfficialComponentAllocation(
                        component_code="76W",
                        ratio_pct="0",
                    ),
                ]
            )
        )

        self.assertEqual(result.issues, [])
        self.assertIsNotNone(result.scenarios[0].modeled_tax_cost)

    def test_estimated_fallback_is_calculable_and_labeled(self) -> None:
        rule = self.build_input().tax_rule.model_copy(
            update={
                "component_assumptions": [
                    ComponentTaxAssumption(
                        component_code="EST_DIVIDEND",
                        income_tax_rate_pct="12",
                        tax_credit_rate_pct="8.5",
                        supplementary_premium_applicable=True,
                    ),
                    ComponentTaxAssumption(
                        component_code="EST_REALIZED_CAPITAL_GAIN",
                        income_tax_rate_pct="0",
                    ),
                ]
            }
        )
        result = calculate_tax_reinvestment_scenarios(
            self.build_input(
                actual_component_mix=None,
                calculation_component_mix=[
                    OfficialComponentAllocation(
                        component_code="EST_DIVIDEND",
                        ratio_pct="26",
                    ),
                    OfficialComponentAllocation(
                        component_code="EST_REALIZED_CAPITAL_GAIN",
                        ratio_pct="74",
                    ),
                ],
                component_calculation_basis=(
                    ComponentCalculationBasis.ESTIMATED_FALLBACK
                ),
                tax_rule=rule,
            )
        )

        self.assertEqual(result.issues, [])
        self.assertEqual(
            result.historical_component_basis,
            "ESTIMATED_FALLBACK",
        )
        self.assertIsNotNone(result.scenarios[0].usable_cash)

    def test_positive_component_requires_explicit_tax_assumption(self) -> None:
        rule = self.build_input().tax_rule.model_copy(
            update={
                "component_assumptions": [
                    ComponentTaxAssumption(
                        component_code="54C",
                        income_tax_rate_pct="12",
                    )
                ]
            }
        )
        result = calculate_tax_reinvestment_scenarios(
            self.build_input(tax_rule=rule)
        )

        issue = result.issues[0]
        self.assertEqual(
            issue.reason,
            TaxScenarioUnavailableReason.MISSING_COMPONENT_TAX_ASSUMPTION,
        )
        self.assertEqual(issue.component_code, "76W")

    def test_negative_total_return_fails_gate(self) -> None:
        result = calculate_tax_reinvestment_scenarios(
            self.build_input(
                annual_gross_distribution_rate_pct="0",
                annual_price_return_pct="-10",
            )
        )

        self.assertFalse(result.scenarios[0].total_return_check_passed)

    def test_different_user_tax_assumptions_change_usable_cash(self) -> None:
        low_tax = calculate_tax_reinvestment_scenarios(self.build_input())
        high_tax_rule = self.build_input().tax_rule.model_copy(
            update={
                "component_assumptions": [
                    ComponentTaxAssumption(
                        component_code="54C",
                        income_tax_rate_pct="30",
                        tax_credit_rate_pct="8.5",
                        supplementary_premium_applicable=True,
                    ),
                    ComponentTaxAssumption(
                        component_code="76W",
                        income_tax_rate_pct="0",
                    ),
                ]
            }
        )
        high_tax = calculate_tax_reinvestment_scenarios(
            self.build_input(tax_rule=high_tax_rule)
        )

        self.assertGreater(
            low_tax.scenarios[0].usable_cash,
            high_tax.scenarios[0].usable_cash,
        )


if __name__ == "__main__":
    unittest.main()
