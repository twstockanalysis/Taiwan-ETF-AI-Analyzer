"""M10-5 月配組合純計算測試。"""

from decimal import Decimal
import unittest

from backend.app.models.monthly_combination import (
    CandidateReasonCode,
    MonthlyCombinationCalculationInput,
    MonthlyCombinationCandidateInput,
    MonthlyCombinationEligibilityRules,
    MonthlyCombinationStatus,
)
from backend.app.services.monthly_combination_calculator import (
    calculate_monthly_payment_combination,
)


class TestMonthlyCombinationCalculator(unittest.TestCase):
    @staticmethod
    def candidate(code: str, months: list[int], **updates):
        values = {
            "etf_code": code,
            "name": f"ETF {code}",
            "is_active": False,
            "is_bond": False,
            "stable_payment_months": months,
            "completeness_pct": "100",
            "data_is_fresh": True,
            "distribution_stability_pct": "80",
            "annual_after_tax_cash_rate_pct": "5",
            "estimated_after_tax_total_return_pct": "6",
            "downside_return_pct": "-10",
            "holding_overlap_pct": "20",
            "proposed_allocation_pct": "10",
        }
        values.update(updates)
        return MonthlyCombinationCandidateInput(**values)

    def build_input(self, candidates, **updates):
        values = {
            "base_etf_code": "0056",
            "base_etf_name": "元大高股息",
            "base_payment_months": [1, 4, 7, 10],
            "candidates": candidates,
            "max_complementary_etfs": 2,
        }
        values.update(updates)
        return MonthlyCombinationCalculationInput(**values)

    def test_selects_only_candidates_that_pass_all_gates(self) -> None:
        good = self.candidate("00878", [2, 5, 8, 11])
        high_cash_weak_return = self.candidate(
            "00919",
            [3, 6, 9, 12],
            annual_after_tax_cash_rate_pct="12",
            estimated_after_tax_total_return_pct="-1",
        )
        result = calculate_monthly_payment_combination(
            self.build_input([good, high_cash_weak_return])
        )

        self.assertEqual(
            [item.etf_code for item in result.selected_candidates],
            ["00878"],
        )
        rejected = result.rejected_candidates[0]
        self.assertIn(
            CandidateReasonCode.WEAK_TOTAL_RETURN,
            [reason.code for reason in rejected.reasons],
        )

    def test_greedy_selection_explains_supported_and_remaining_months(self):
        first = self.candidate("00878", [2, 3, 5, 6])
        second = self.candidate("00900", [8, 9, 11, 12])
        result = calculate_monthly_payment_combination(
            self.build_input([second, first])
        )

        self.assertEqual(
            [item.etf_code for item in result.selected_candidates],
            ["00878", "00900"],
        )
        self.assertEqual(result.remaining_gap_months, [])
        self.assertEqual(result.base_etf_code, "0056")

    def test_missing_overlap_is_partial_not_zero(self) -> None:
        candidate = self.candidate(
            "00878", [2, 5, 8, 11], holding_overlap_pct=None
        )
        result = calculate_monthly_payment_combination(
            self.build_input([candidate])
        )

        self.assertEqual(result.status, MonthlyCombinationStatus.PARTIAL)
        self.assertIsNone(
            result.selected_candidates[0].holding_overlap_pct
        )
        self.assertIn(
            CandidateReasonCode.HOLDING_OVERLAP_UNAVAILABLE,
            [reason.code for reason in result.tradeoffs],
        )

    def test_required_missing_overlap_excludes_candidate(self) -> None:
        candidate = self.candidate(
            "00878", [2, 5, 8, 11], holding_overlap_pct=None
        )
        result = calculate_monthly_payment_combination(
            self.build_input(
                [candidate],
                rules=MonthlyCombinationEligibilityRules(
                    require_holding_overlap=True
                ),
            )
        )
        self.assertEqual(result.selected_candidates, [])

    def test_base_missing_months_blocks_combination(self) -> None:
        result = calculate_monthly_payment_combination(
            self.build_input(
                [self.candidate("00878", [2])],
                base_payment_months=None,
            )
        )
        self.assertEqual(result.status, MonthlyCombinationStatus.UNAVAILABLE)
        self.assertIsNone(result.remaining_gap_months)

    def test_monthly_coverage_can_be_disabled_explicitly(self) -> None:
        result = calculate_monthly_payment_combination(
            self.build_input(
                [self.candidate("00878", [2])],
                monthly_coverage_enabled=False,
            )
        )
        self.assertEqual(result.selected_candidates, [])
        self.assertEqual(
            result.rejected_candidates[0].reasons[0].code,
            CandidateReasonCode.MONTHLY_COVERAGE_DISABLED,
        )

    def test_formal_zero_overlap_is_available(self) -> None:
        candidate = self.candidate(
            "00878", [2], holding_overlap_pct=Decimal("0")
        )
        result = calculate_monthly_payment_combination(
            self.build_input([candidate])
        )
        self.assertEqual(result.status, MonthlyCombinationStatus.AVAILABLE)
        self.assertEqual(
            result.selected_candidates[0].holding_overlap_pct,
            Decimal("0"),
        )

    def test_formal_zero_total_return_sorts_ahead_of_negative(self) -> None:
        zero = self.candidate(
            "00878", [2], estimated_after_tax_total_return_pct="0"
        )
        negative = self.candidate(
            "00900", [3], estimated_after_tax_total_return_pct="-1"
        )
        result = calculate_monthly_payment_combination(
            self.build_input(
                [negative, zero],
                max_complementary_etfs=1,
                rules=MonthlyCombinationEligibilityRules(
                    min_after_tax_total_return_pct="-100"
                ),
            )
        )
        self.assertEqual(result.selected_candidates[0].etf_code, "00878")

    def test_recalculates_gap_contribution_after_each_selection(self) -> None:
        first = self.candidate("00878", [2, 3, 5, 6])
        overlapping = self.candidate("00900", [2, 3, 8, 9])
        complementary = self.candidate("00919", [8, 9, 11])
        result = calculate_monthly_payment_combination(
            self.build_input(
                [first, overlapping, complementary],
                max_complementary_etfs=2,
            )
        )
        self.assertEqual(
            [item.etf_code for item in result.selected_candidates],
            ["00878", "00919"],
        )

    def test_custom_target_months_only_fill_requested_gaps(self) -> None:
        requested = self.candidate("00878", [2, 5, 8, 11])
        outside = self.candidate("00900", [3, 6, 9, 12])
        result = calculate_monthly_payment_combination(
            self.build_input(
                [outside, requested],
                target_payment_months=[1, 2, 4, 5],
            )
        )
        self.assertEqual(result.target_payment_months, [1, 2, 4, 5])
        self.assertEqual(result.initial_gap_months, [2, 5])
        self.assertEqual(
            [item.etf_code for item in result.selected_candidates], ["00878"]
        )
        self.assertEqual(result.combined_payment_months, [1, 2, 4, 5])
        self.assertEqual(result.remaining_gap_months, [])

    def test_target_months_are_normalized_and_cannot_be_empty(self) -> None:
        value = self.build_input(
            [self.candidate("00878", [2])], target_payment_months=[5, 2, 5]
        )
        self.assertEqual(value.target_payment_months, [2, 5])
        with self.assertRaisesRegex(ValueError, "至少選擇一個月份"):
            self.build_input(
                [self.candidate("00878", [2])], target_payment_months=[]
            )


if __name__ == "__main__":
    unittest.main()
