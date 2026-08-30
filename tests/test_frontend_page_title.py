"""個別頁面共用標題與首頁入口測試。"""

from pathlib import Path
import unittest
from unittest.mock import patch

from frontend.ui.components import render_page_title


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestFrontendPageTitle(unittest.TestCase):
    """驗證非首頁頁面的統一標題入口。"""

    @patch(
        "frontend.ui.components."
        "create_streamlit_page",
        return_value="home-page",
    )
    @patch(
        "frontend.ui.components.get_api_base_url",
        return_value="http://127.0.0.1:8000",
    )
    @patch(
        "frontend.ui.components."
        "render_owner_access_trigger"
    )
    @patch(
        "frontend.ui.components."
        "render_theme_toggle"
    )
    @patch("frontend.ui.components.st.title")
    @patch("frontend.ui.components.st.page_link")
    @patch("frontend.ui.components.st.container")
    def test_home_link_precedes_page_title(
        self,
        mock_container,
        mock_page_link,
        mock_title,
        mock_theme_toggle,
        mock_owner_access,
        mock_api_base_url,
        mock_create_page,
    ) -> None:
        """確認共用元件建立返回首頁及頁面標題。"""

        render_page_title("ETF 比較")

        mock_create_page.assert_called_once()
        mock_page_link.assert_called_once_with(
            "home-page",
            label="返回首頁",
            icon=":material/arrow_back:",
            width="content",
        )
        mock_owner_access.assert_called_once_with(
            "http://127.0.0.1:8000"
        )
        mock_title.assert_called_once_with(
            "ETF 比較",
            width="content",
        )
        mock_theme_toggle.assert_called_once_with()
        self.assertEqual(mock_container.call_count, 2)
        mock_container.assert_any_call(
            key="page-top-actions",
            horizontal=True,
            horizontal_alignment="distribute",
            vertical_alignment="center",
            gap="small",
        )
        mock_container.assert_any_call(
            key="page-title-actions",
            horizontal=True,
            horizontal_alignment="distribute",
            vertical_alignment="center",
            gap="small",
        )

    def test_all_non_home_pages_use_shared_title(
        self,
    ) -> None:
        """確認所有個別頁面使用一致的首頁入口。"""

        expected_titles = {
            "admin_overview.py": "網站管理",
            "decision_profile.py": (
                "我的條件與持有部位"
            ),
            "dividend_data_quality.py": (
                "配息資料品質"
            ),
            "etf_comparison.py": "比較",
            "etf_detail.py": "詳細資料",
            "etf_search.py": "搜尋",
            "performance_ranking.py": (
                "績效排行榜"
            ),
            "public_planner.py": "股利試算",
        }

        for file_name, title in (
            expected_titles.items()
        ):
            source = (
                PROJECT_ROOT
                / "frontend"
                / "pages"
                / file_name
            ).read_text(encoding="utf-8")

            self.assertIn(
                f'render_page_title("{title}")',
                source,
            )

    def test_comparison_removes_redundant_copy(
        self,
    ) -> None:
        """確認比較頁移除技術說明與可見代號標籤。"""

        source = (
            PROJECT_ROOT
            / "frontend"
            / "pages"
            / "etf_comparison.py"
        ).read_text(encoding="utf-8")

        self.assertNotIn(
            "並列比較 2 至 4 檔 ETF",
            source,
        )
        self.assertNotIn(
            "目前績效為 PRICE_RETURN",
            source,
        )
        self.assertNotIn(
            "返回 ETF 查詢",
            source,
        )
        self.assertIn(
            'label_visibility="collapsed"',
            source,
        )

    def test_detail_actions_are_compact_and_remove_query_caption(
        self,
    ) -> None:
        """確認詳細頁並列返回與更新，且不重複顯示查詢代號。"""

        source = (
            PROJECT_ROOT
            / "frontend"
            / "pages"
            / "etf_detail.py"
        ).read_text(encoding="utf-8")

        self.assertIn('render_page_title("詳細資料")', source)
        self.assertIn('"更新"', source)
        self.assertIn("horizontal=True", source)
        self.assertIn('gap="small"', source)
        self.assertNotIn("查詢代號：", source)
        self.assertNotIn('"重新載入資料"', source)


if __name__ == "__main__":
    unittest.main()
