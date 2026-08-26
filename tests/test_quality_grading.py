"""V4-1 固定字母評等、缺值與公開安全契約測試。"""

import json
import unittest
from decimal import Decimal

from backend.app.models.decision_profile import (
    ExplainableAssessmentScoreComponent,
)
from backend.app.services.quality_grading import (
    build_historical_quality_grade,
    evaluate_quality_grade_publication_readiness,
    grade_quality_score,
)


def component(code: str, score: str) -> ExplainableAssessmentScoreComponent:
    return ExplainableAssessmentScoreComponent(
        code=code,
        label=code,
        score=Decimal(score),
        weight_pct=Decimal("10"),
        observed_value=Decimal("1"),
        explanation="測試證據",
    )


class TestQualityGrading(unittest.TestCase):
    def test_fixed_grade_boundaries(self) -> None:
        cases = {
            "100": "A+",
            "90": "A+",
            "89.99": "A",
            "80": "A",
            "70": "B",
            "60": "C",
            "50": "D",
            "40": "E",
            "0": "F",
        }
        for score, expected in cases.items():
            with self.subTest(score=score):
                self.assertEqual(
                    grade_quality_score(Decimal(score)),
                    expected,
                )

    def test_missing_core_evidence_is_unrated_not_f(self) -> None:
        result = build_historical_quality_grade(
            score=None,
            components=[],
            missing_metrics=["AFTER_TAX_TOTAL_RETURN", "DOWNSIDE_RETURN"],
            history_years=3,
        )

        self.assertEqual(result.status, "UNRATED")
        self.assertIsNone(result.grade)
        self.assertIn("稅後總報酬資料不足", result.unavailable_evidence)

    def test_optional_actual_76w_gap_does_not_remove_grade(self) -> None:
        result = build_historical_quality_grade(
            score=Decimal("82"),
            components=[
                component("AFTER_TAX_TOTAL_RETURN", "85"),
                component("DOWNSIDE_RETURN", "75"),
            ],
            missing_metrics=["ACTUAL_76W_RATIO"],
            history_years=3,
        )

        self.assertEqual(result.status, "RATED")
        self.assertEqual(result.grade, "A")
        self.assertIn(
            "正式 ACTUAL 76W 組成資料不足",
            result.unavailable_evidence,
        )

    def test_stale_data_blocks_grade_even_when_score_exists(self) -> None:
        result = build_historical_quality_grade(
            score=Decimal("95"),
            components=[component("AFTER_TAX_TOTAL_RETURN", "95")],
            missing_metrics=[],
            history_years=3,
            blocking_reason_codes=["STALE_DATA"],
        )

        self.assertEqual(result.status, "UNRATED")
        self.assertIsNone(result.grade)

    def test_public_payload_never_contains_raw_score_or_confidence(self) -> None:
        result = build_historical_quality_grade(
            score=Decimal("72"),
            components=[component("AFTER_TAX_TOTAL_RETURN", "75")],
            missing_metrics=[],
            history_years=3,
        )
        payload = json.dumps(result.model_dump(mode="json"), ensure_ascii=False)

        self.assertNotIn("quality_score", payload)
        self.assertNotIn("raw_score", payload)
        self.assertNotIn("confidence", payload)

    def test_publication_requires_sample_coverage_and_score_separation(self) -> None:
        blocked = evaluate_quality_grade_publication_readiness(
            scores=[Decimal("95")] * 6,
            supported_product_count=200,
            total_return_component_scores=[Decimal("100")] * 6,
        )
        ready = evaluate_quality_grade_publication_readiness(
            scores=[Decimal("75")] * 30,
            supported_product_count=100,
            total_return_component_scores=(
                [Decimal("100")] * 10 + [Decimal("80")] * 20
            ),
        )

        self.assertFalse(blocked.ready)
        self.assertTrue(any("樣本" in reason for reason in blocked.reasons))
        self.assertTrue(any("覆蓋率" in reason for reason in blocked.reasons))
        self.assertTrue(any("分數上限" in reason for reason in blocked.reasons))
        self.assertTrue(ready.ready)


if __name__ == "__main__":
    unittest.main()
