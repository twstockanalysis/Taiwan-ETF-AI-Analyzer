"""第二版可解釋雙分數的交互規則測試。"""

import unittest
from decimal import Decimal

from backend.app.models.monthly_combination import (
    CandidateReason,
    CandidateReasonCode,
    CandidateReasonKind,
    MonthlyCombinationCalculationResult,
    MonthlyCombinationCandidateResult,
    MonthlyCombinationEligibilityRules,
    MonthlyCombinationStatus,
)
from backend.app.services.explainable_assessment import (
    build_explainable_assessment,
)


def candidate(**updates) -> MonthlyCombinationCandidateResult:
    values = {
        "etf_code": "00999",
        "name": "測試 ETF",
        "is_active": True,
        "is_bond": False,
        "selected": False,
        "supported_gap_months": [3],
        "stable_payment_months": [3, 6, 9, 12],
        "completeness_pct": Decimal("100"),
        "data_is_fresh": True,
        "distribution_stability_pct": Decimal("100"),
        "annual_after_tax_cash_rate_pct": Decimal("8"),
        "estimated_after_tax_total_return_pct": Decimal("-20"),
        "downside_return_pct": Decimal("-40"),
        "holding_overlap_pct": Decimal("0"),
        "proposed_allocation_pct": Decimal("10"),
        "reasons": [
            CandidateReason(
                kind=CandidateReasonKind.EXCLUDE,
                code=CandidateReasonCode.WEAK_TOTAL_RETURN,
                message="總報酬未達門檻。",
            )
        ],
    }
    values.update(updates)
    return MonthlyCombinationCandidateResult(**values)


def calculation(item: MonthlyCombinationCandidateResult):
    return MonthlyCombinationCalculationResult(
        status=MonthlyCombinationStatus.AVAILABLE,
        base_etf_code="CURRENT",
        base_etf_name="目前持倉",
        base_payment_months=[1],
        target_payment_months=list(range(1, 13)),
        initial_gap_months=list(range(2, 13)),
        selected_candidates=[] if not item.selected else [item],
        rejected_candidates=[item] if not item.selected else [],
        combined_payment_months=[1],
        remaining_gap_months=list(range(2, 13)),
    )


class TestExplainableAssessment(unittest.TestCase):
    def test_high_cash_and_76w_cannot_offset_weak_performance(self):
        result = build_explainable_assessment(
            calculation(candidate()),
            MonthlyCombinationEligibilityRules(),
            actual_76w_summary={
                "actual_76w_record_count": 4,
                "average_76w_ratio_pct": 100,
            },
        )

        self.assertEqual(result.outcome.value, "BLOCKED_BY_GATE")
        self.assertLess(result.etf_quality_score, Decimal("50"))

    def test_low_manual_overlap_is_not_scored_as_automatic_overlap(self):
        result = build_explainable_assessment(
            calculation(candidate(holding_overlap_pct=Decimal("0"))),
            MonthlyCombinationEligibilityRules(),
        )

        scored_codes = {
            item.code
            for item in [*result.quality_components, *result.fit_components]
        }
        self.assertNotIn("CONSTITUENT_OVERLAP", scored_codes)
        self.assertIn(
            "AUTOMATED_CONSTITUENT_OVERLAP",
            result.unscored_metrics,
        )


if __name__ == "__main__":
    unittest.main()
