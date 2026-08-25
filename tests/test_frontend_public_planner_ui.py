"""V3-8 公開股利試算頁資訊架構測試。"""

import unittest
from inspect import getsource

from streamlit.testing.v1 import AppTest

from frontend.pages.public_planner import MONTH_OPTIONS, render_public_planner


PLANNER_PAGE_SCRIPT = """
from frontend.pages.public_planner import render_public_planner

render_public_planner()
"""


class TestFrontendPublicPlannerUI(unittest.TestCase):
    def test_primary_inputs_follow_beginner_order(self) -> None:
        app = AppTest.from_string(PLANNER_PAGE_SCRIPT, default_timeout=10)
        app.run()

        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.title[0].value, "股利試算")
        self.assertEqual(app.caption[0].value, "請依序選擇輸入")

        number_labels = [item.label for item in app.number_input]
        self.assertEqual(
            number_labels[:2],
            [
                "1. 每個目標月想領多少股利（TWD）",
                "3. 想持有年限",
            ],
        )
        self.assertEqual(app.number_input[0].value, 3000)
        self.assertEqual(app.number_input[1].value, 10)

        source = getsource(render_public_planner)
        self.assertEqual(MONTH_OPTIONS, list(range(1, 13)))
        self.assertIn('st.pills(', source)
        self.assertIn('"2. 領息月份"', source)
        self.assertIn('selection_mode="multi"', source)

    def test_technical_allocation_inputs_are_not_exposed(self) -> None:
        app = AppTest.from_string(PLANNER_PAGE_SCRIPT, default_timeout=10)
        app.run()

        labels = [item.label for item in app.number_input]
        self.assertNotIn("歷史配息年數", labels)
        self.assertNotIn("配置階段現金扣除率（%）", labels)
        self.assertEqual(len(app.multiselect), 0)

        page_text = "\n".join(
            [item.value for item in app.caption]
            + [item.value for item in app.markdown]
        )
        self.assertIn("直接算出可能的所得稅與二代健保金額", page_text)


if __name__ == "__main__":
    unittest.main()
