"""V3-8 首頁資訊架構測試。"""

import unittest

from frontend.pages.home import (
    PLANNER_INTRO,
    PLANNER_NOTICE,
    SITE_NAME,
    SITE_SLOGAN,
)
from frontend.ui.theme import GLOBAL_STYLES


class TestFrontendHomeInformationArchitecture(unittest.TestCase):
    def test_home_uses_approved_brand_and_beginner_copy(self) -> None:
        self.assertEqual(SITE_NAME, "ETF nano cat")
        self.assertEqual(
            SITE_SLOGAN,
            "運用AI評分系統，讓奈米戶自己也能月月領錢",
        )
        self.assertIn("或直接空白", PLANNER_INTRO)
        self.assertIn("推薦 ETF＋股數", PLANNER_INTRO)
        self.assertIn("不需登入", PLANNER_NOTICE)
        self.assertIn("是否購買皆由用戶決定", PLANNER_NOTICE)

    def test_primary_action_has_scoped_larger_font(self) -> None:
        self.assertIn(".st-key-home-primary-action", GLOBAL_STYLES)
        self.assertIn("font-weight: 700", GLOBAL_STYLES)


if __name__ == "__main__":
    unittest.main()
