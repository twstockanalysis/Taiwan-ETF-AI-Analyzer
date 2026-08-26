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
    @patch("frontend.ui.components.st.title")
    @patch("frontend.ui.components.st.page_link")
    def test_home_link_precedes_page_title(
        self,
        mock_page_link,
        mock_title,
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
        mock_title.assert_called_once_with(
            "ETF 比較"
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
            "etf_comparison.py": "ETF 比較",
            "etf_detail.py": "ETF 詳細資料",
            "etf_search.py": "搜尋&詳細資料",
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


if __name__ == "__main__":
    unittest.main()
