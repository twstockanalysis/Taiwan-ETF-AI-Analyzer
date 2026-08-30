"""V4 公開歷史品質與主人目標適配呈現測試。"""

import unittest

from frontend.ui.assessment import (
    allocation_fit_presentation,
    historical_quality_presentation,
)


class TestFrontendAssessment(unittest.TestCase):
    def test_rated_quality_uses_letter_without_internal_score_language(self) -> None:
        presentation = historical_quality_presentation(
            {
                "status": "RATED",
                "grade": "A+",
                "explanation": "歷史資料完整且總報酬表現穩定。",
                "quality_score": 99,
            }
        )

        self.assertEqual(presentation.label, "喵喵評等：A+")
        self.assertEqual(presentation.color, "green")
        self.assertNotIn("99", presentation.explanation)
        self.assertNotIn("分數", presentation.label)

    def test_missing_quality_is_unrated_instead_of_f(self) -> None:
        presentation = historical_quality_presentation(
            {
                "status": "UNRATED",
                "grade": None,
                "explanation": "市場校準尚未達到發布門檻。",
            }
        )

        self.assertEqual(presentation.label, "喵喵評等：暫無")
        self.assertEqual(
            presentation.explanation,
            "核心資料不足或未通過資料閘門",
        )
        self.assertNotIn("F", presentation.label)
        self.assertEqual(presentation.color, "gray")

    def test_allocation_fit_only_describes_submitted_owner_conditions(self) -> None:
        met = allocation_fit_presentation({"status": "TARGET_MET"})
        partial = allocation_fit_presentation({"status": "PARTIAL"})

        self.assertEqual(met.label, "符合主人設定")
        self.assertIn("本次", met.explanation)
        self.assertEqual(partial.label, "部分符合主人設定")
        self.assertNotIn("品質", partial.label)
        self.assertNotIn("推薦", partial.label)


if __name__ == "__main__":
    unittest.main()
