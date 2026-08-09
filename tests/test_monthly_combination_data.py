"""M10-5 歷史資料轉換測試。"""

from datetime import date
from decimal import Decimal
import unittest

from backend.app.models.monthly_combination import (
    MonthlyCombinationCandidateAssumption,
    MonthlyCombinationEligibilityRules,
)
from backend.app.services.monthly_combination_data import (
    build_candidate_input,
    stable_payment_months,
)


class TestMonthlyCombinationData(unittest.TestCase):
    @staticmethod
    def monthly_income():
        return {
            "as_of_date": date(2026, 8, 1),
            "has_mixed_currencies": False,
            "total_amount_per_unit": 6,
            "covered_month_count": 4,
            "covered_month_occurrence_count": 10,
            "months": [
                {
                    "month": month,
                    "observed_year_count": (3 if month in {2, 5} else 0),
                }
                for month in range(1, 13)
            ],
        }

    @staticmethod
    def performance_rows():
        return [
            {
                "period_code": period,
                "metric_code": "PRICE_RETURN",
                "return_pct": value,
                "as_of_date": date(2026, 8, 8),
            }
            for period, value in (
                ("1M", "-2"),
                ("3M", "1"),
                ("6M", "3"),
                ("1Y", "4"),
            )
        ]

    def test_builds_explicit_after_tax_and_total_return_estimates(self):
        result = build_candidate_input(
            etf={
                "code": "00878",
                "name": "國泰永續高股息",
                "is_active": False,
                "is_bond": False,
            },
            assumption=MonthlyCombinationCandidateAssumption(
                etf_code="00878",
                unit_price="40",
                proposed_allocation_pct="10",
            ),
            monthly_income=self.monthly_income(),
            performance_rows=self.performance_rows(),
            lookback_years=3,
            cash_deduction_rate_pct=Decimal("5"),
            rules=MonthlyCombinationEligibilityRules(),
            as_of_date=date(2026, 8, 9),
        )
        self.assertEqual(result.stable_payment_months, [2, 5])
        self.assertEqual(result.completeness_pct, Decimal("100.000000"))
        self.assertEqual(
            result.annual_after_tax_cash_rate_pct, Decimal("4.750000")
        )
        self.assertEqual(
            result.estimated_after_tax_total_return_pct,
            Decimal("8.750000"),
        )
        self.assertEqual(result.downside_return_pct, Decimal("-2"))
        self.assertIsNone(result.holding_overlap_pct)

    def test_missing_monthly_data_stays_missing(self):
        self.assertIsNone(
            stable_payment_months(
                None,
                lookback_years=3,
                minimum_stability_pct=Decimal("50"),
            )
        )

    def test_formal_zero_monthly_total_is_not_missing(self):
        monthly = self.monthly_income()
        monthly["total_amount_per_unit"] = 0
        result = build_candidate_input(
            etf={
                "code": "00878",
                "name": "國泰永續高股息",
                "is_active": False,
                "is_bond": False,
            },
            assumption=MonthlyCombinationCandidateAssumption(
                etf_code="00878",
                unit_price="40",
                proposed_allocation_pct="10",
                holding_overlap_pct="0",
            ),
            monthly_income=monthly,
            performance_rows=self.performance_rows(),
            lookback_years=3,
            cash_deduction_rate_pct=Decimal("0"),
            rules=MonthlyCombinationEligibilityRules(),
            as_of_date=date(2026, 8, 9),
        )
        self.assertEqual(result.annual_after_tax_cash_rate_pct, Decimal("0"))
        self.assertEqual(result.holding_overlap_pct, Decimal("0"))


if __name__ == "__main__":
    unittest.main()
