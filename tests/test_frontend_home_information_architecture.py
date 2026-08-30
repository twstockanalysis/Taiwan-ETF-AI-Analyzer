"""V3-8 首頁資訊架構測試。"""

import unittest
from inspect import getsource

from frontend.pages.home import (
    PLANNER_INTRO,
    SITE_NAME,
    SITE_SLOGAN,
    render_exploration_links,
    render_home,
    render_primary_action,
)
from frontend.ui.theme import GLOBAL_STYLES


class TestFrontendHomeInformationArchitecture(unittest.TestCase):
    def test_home_uses_approved_brand_and_beginner_copy(self) -> None:
        self.assertEqual(SITE_NAME, "GoodCat 股利喵")
        self.assertEqual(
            SITE_SLOGAN,
            "股利喵幫你算，規劃不踩雷！\n\n"
            "Your GoodCat, Easy planning!",
        )
        self.assertIn("固定賺到罐頭錢", PLANNER_INTRO)
        self.assertIn("買很多好吃的罐頭", PLANNER_INTRO)
        self.assertIn("規劃&計算所需資金吧", PLANNER_INTRO)
        self.assertIn("喵嗚~", PLANNER_INTRO)
        self.assertNotIn("\n\n", PLANNER_INTRO)

    def test_primary_action_has_scoped_larger_font(self) -> None:
        self.assertIn(".st-key-home-primary-action", GLOBAL_STYLES)
        self.assertIn("min-height: 3.75rem", GLOBAL_STYLES)
        self.assertIn("clamp(1.35rem, 2.4vw, 1.7rem)", GLOBAL_STYLES)
        self.assertIn("font-weight: 700", GLOBAL_STYLES)

    def test_primary_action_does_not_repeat_section_heading(self) -> None:
        """確認首頁配置卡不再顯示重複標題。"""

        source = getsource(render_primary_action)
        self.assertNotIn("先算出適合你的 ETF 配置", source)
        self.assertNotIn("主人不用先挑 ETF", source)
        self.assertIn('label="開始!"', source)
        self.assertIn("st.image", source)
        self.assertIn("st.columns", source)
        self.assertIn("[2, 3]", source)
        self.assertIn("HOME_GOODCAT_HERO_PATH", source)
        self.assertIn("width=260", source)
        self.assertLess(source.index("st.image"), source.index("st.write"))
        self.assertLess(source.index("st.write"), source.index("st.page_link"))
        self.assertNotIn("不需登入", source)
        self.assertNotIn("是否購買皆由用戶決定", source)

    def test_home_does_not_render_a_separate_goodcat_card(self) -> None:
        source = getsource(render_home)
        self.assertNotIn("render_goodcat_companion", source)
        self.assertNotIn("陪主人慢慢想", source)
        self.assertNotIn("主人先想想在哪幾個月領股利", source)

    def test_home_title_and_owner_access_share_one_header_row(self) -> None:
        """確認品牌標題與喵窩入口同高並分置左右。"""

        source = getsource(render_home)
        self.assertIn('key="home-top-actions"', source)
        self.assertIn("horizontal=True", source)
        self.assertIn(
            'horizontal_alignment="distribute"',
            source,
        )
        self.assertIn(
            'vertical_alignment="center"',
            source,
        )
        self.assertIn(
            "render_owner_access_trigger",
            source,
        )

    def test_home_slogan_uses_a_compact_smaller_heading(self) -> None:
        """確認中英文標語緊密排列，且中文不使用較大的副標題。"""

        source = getsource(render_home)
        self.assertIn('key="home-slogan"', source)
        self.assertIn('key="home-slogan-actions"', source)
        self.assertIn("gap=None", source)
        self.assertIn('st.markdown(f"#### {slogan_zh}")', source)
        self.assertNotIn("st.subheader(slogan_zh)", source)
        self.assertIn(".st-key-home-slogan h4", GLOBAL_STYLES)
        self.assertIn(
            "clamp(1rem, 1.5vw, 1.15rem)",
            GLOBAL_STYLES,
        )
        self.assertIn(
            "margin-bottom: 0 !important",
            GLOBAL_STYLES,
        )
        self.assertLess(
            source.index("render_owner_access_trigger"),
            source.index('key="home-slogan-actions"'),
        )
        self.assertLess(
            source.index('key="home-slogan-actions"'),
            source.index("render_theme_toggle"),
        )

    def test_home_keeps_planning_instructions_on_planner_page(self) -> None:
        source = getsource(render_home)
        self.assertNotIn("三步就能開始", source)
        self.assertNotIn("render_planning_steps", source)
        self.assertIn("render_primary_action", source)
        self.assertIn("render_exploration_links", source)

    def test_admin_data_quality_is_not_linked_from_home(self) -> None:
        """確認首頁不會繞過管理者限定導覽。"""

        source = getsource(render_exploration_links)
        self.assertNotIn("DIVIDEND_DATA_QUALITY_ROUTE", source)
        self.assertNotIn("了解資料完整度", source)

    def test_exploration_copy_is_short_and_playful(self) -> None:
        source = getsource(render_exploration_links)
        self.assertIn('st.subheader("也可以")', source)
        self.assertIn("查查基本資料", source)
        self.assertIn("看看績效", source)
        self.assertIn("比較比較", source)


if __name__ == "__main__":
    unittest.main()
