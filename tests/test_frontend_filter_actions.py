"""搜尋與排行榜篩選操作版面測試。"""

import inspect
import unittest

from frontend.pages.etf_search import render_search_form
from frontend.pages.performance_ranking import (
    render_performance_filter_form,
)


class TestFrontendFilterActions(unittest.TestCase):
    """確認兩頁使用一致且緊湊的篩選操作列。"""

    def test_search_actions_stay_inside_filter_form(self) -> None:
        """確認搜尋、清除與重新載入位於同一表單。"""

        source = inspect.getsource(render_search_form)

        self.assertIn('"搜尋"', source)
        self.assertNotIn('"套用篩選"', source)
        self.assertIn('key="etf-search-secondary-actions"', source)
        self.assertIn("horizontal=True", source)
        self.assertIn('gap="small"', source)
        self.assertEqual(source.count("st.form_submit_button("), 3)

    def test_ranking_actions_stay_inside_filter_form(self) -> None:
        """確認排行榜篩選、清除與重新載入位於同一表單。"""

        source = inspect.getsource(render_performance_filter_form)

        self.assertIn('"篩選"', source)
        self.assertNotIn('"套用篩選"', source)
        self.assertIn(
            'key="performance-ranking-secondary-actions"',
            source,
        )
        self.assertIn("horizontal=True", source)
        self.assertIn('gap="small"', source)
        self.assertEqual(source.count("st.form_submit_button("), 3)


if __name__ == "__main__":
    unittest.main()
