"""V3-8 首頁資訊架構測試。"""

import unittest
from inspect import getsource

from frontend.pages.home import (
    PLANNER_INTRO,
    PLANNER_NOTICE,
    SITE_NAME,
    SITE_SLOGAN,
    render_exploration_links,
    render_planning_steps,
    render_primary_action,
)
from frontend.ui.theme import GLOBAL_STYLES


class TestFrontendHomeInformationArchitecture(unittest.TestCase):
    def test_home_uses_approved_brand_and_beginner_copy(self) -> None:
        self.assertEqual(SITE_NAME, "GoodCat 股利喵")
        self.assertEqual(
            SITE_SLOGAN,
            "股利喵幫你算，ETF規劃不踩雷！\n\n"
            "Your GoodCat, Easy ETF planning!",
        )
        self.assertIn("或直接空白", PLANNER_INTRO)
        self.assertIn("咪想知道主人", PLANNER_INTRO)
        self.assertIn("喵~", PLANNER_INTRO)
        self.assertIn("不需登入", PLANNER_NOTICE)
        self.assertIn("是否購買皆由用戶決定", PLANNER_NOTICE)

    def test_primary_action_has_scoped_larger_font(self) -> None:
        self.assertIn(".st-key-home-primary-action", GLOBAL_STYLES)
        self.assertIn("font-weight: 700", GLOBAL_STYLES)

    def test_primary_action_does_not_repeat_section_heading(self) -> None:
        """確認首頁配置卡不再顯示重複標題。"""

        source = getsource(render_primary_action)
        self.assertNotIn("先算出適合你的 ETF 配置", source)
        self.assertIn("主人不用先挑 ETF", source)
        self.assertIn("開始讓股利喵規劃", source)

    def test_home_explains_the_three_beginner_steps(self) -> None:
        source = getsource(render_planning_steps)
        self.assertIn("選領息月份", source)
        self.assertIn("告訴咪目標", source)
        self.assertIn("庫存可留空", source)
        self.assertIn("render_beginner_card", source)

    def test_admin_data_quality_is_not_linked_from_home(self) -> None:
        """確認首頁不會繞過管理者限定導覽。"""

        source = getsource(render_exploration_links)
        self.assertNotIn("DIVIDEND_DATA_QUALITY_ROUTE", source)
        self.assertNotIn("了解資料完整度", source)


if __name__ == "__main__":
    unittest.main()
