"""喵喵評等公開與喵窩顯示邊界測試。"""

import unittest
from unittest.mock import patch

from frontend.ui.quality_grade import (
    render_historical_quality_evidence,
)


class TestFrontendQualityGradeUI(unittest.TestCase):
    """確認缺漏原因只在喵窩狀態顯示。"""

    def build_unrated_payload(self) -> dict:
        return {
            "status": "UNRATED",
            "grade": None,
            "explanation": "舊版公開說明。",
            "strengths": [],
            "risks": [],
            "unavailable_evidence": [
                "稅後總報酬資料不足",
                "資料閘門未通過：STALE_DATA",
            ],
        }

    @patch("frontend.ui.quality_grade.st.markdown")
    @patch("frontend.ui.quality_grade.st.caption")
    @patch("frontend.ui.quality_grade.st.badge")
    def test_public_view_hides_missing_evidence(
        self,
        mock_badge,
        mock_caption,
        mock_markdown,
    ) -> None:
        render_historical_quality_evidence(
            self.build_unrated_payload()
        )

        mock_badge.assert_called_once_with(
            "喵喵評等：暫無",
            color="gray",
        )
        mock_caption.assert_not_called()
        mock_markdown.assert_not_called()

    @patch("frontend.ui.quality_grade.st.markdown")
    @patch("frontend.ui.quality_grade.st.caption")
    @patch("frontend.ui.quality_grade.st.badge")
    def test_owner_view_lists_missing_evidence_by_line(
        self,
        _mock_badge,
        _mock_caption,
        mock_markdown,
    ) -> None:
        render_historical_quality_evidence(
            self.build_unrated_payload(),
            show_owner_details=True,
        )

        _mock_caption.assert_called_once_with(
            "核心資料不足或未通過資料閘門"
        )
        markup = mock_markdown.call_args.args[0]
        self.assertIn("**原因：**", markup)
        self.assertIn("稅後總報酬資料不足；", markup)
        self.assertIn(
            "資料閘門未通過：STALE_DATA；",
            markup,
        )
        self.assertIn("  \n", markup)


if __name__ == "__main__":
    unittest.main()
