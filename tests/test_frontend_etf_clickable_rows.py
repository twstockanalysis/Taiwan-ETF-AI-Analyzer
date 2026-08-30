"""ETF 搜尋結果欄位測試。"""

import unittest
from unittest.mock import patch

from frontend.pages.etf_search import (
    RESULT_ACTION_KEY,
    build_etf_search_column_layout,
    build_etf_search_table_html,
    estimate_text_width_rem,
    format_etf_result_row,
    open_etf_detail,
)
from frontend.query_state import (
    ETFSearchQueryState,
)


class TestFrontendETFClickableRows(
    unittest.TestCase
):
    """測試 ETF 搜尋結果的固定欄位內容。"""

    def build_item(self) -> dict:
        """建立 ETF 測試資料。"""

        return {
            "code": "0050",
            "name": "元大台灣50",
            "is_active": False,
            "is_bond": False,
            "listing_date": "2003-06-30",
            "fund_size": None,
            "expense_ratio": None,
        }

    def test_row_contains_aligned_etf_data(
        self,
    ) -> None:
        """確認資料列保留主要官方欄位。"""

        row = format_etf_result_row(
            self.build_item()
        )

        self.assertEqual(
            row,
            {
                "code": "0050",
                "name": "元大台灣50",
                "historical_quality": "暫無",
                "management_type": "被動式",
                "listing_date": "2003-06-30",
                "fund_size": "—",
                "expense_ratio": "—",
            },
        )

    def test_row_does_not_expose_asset_type(
        self,
    ) -> None:
        """確認結果資料不再產生資產類型欄位。"""

        row = format_etf_result_row(
            self.build_item()
        )

        self.assertNotIn("asset_type", row)

    def test_row_shows_public_letter_grade(self) -> None:
        """確認搜尋結果顯示公開字母評等。"""

        row = format_etf_result_row(
            self.build_item(),
            {
                "status": "RATED",
                "grade": "A+",
                "explanation": "歷史證據完整。",
            },
        )
        self.assertEqual(row["historical_quality"], "A+")

    def test_table_html_has_clickable_rows_without_selection_column(
        self,
    ) -> None:
        """確認搜尋結果整列皆可開啟詳細資料。"""

        markup = build_etf_search_table_html(
            [self.build_item()],
            ETFSearchQueryState(
                keyword="元大",
                bond_label="非債券",
                page=2,
            ),
        )

        self.assertIn('role="table"', markup)
        self.assertIn('class="performance-ranking-row"', markup)
        self.assertIn('/etf-detail?code=0050&amp;', markup)
        self.assertLess(markup.index("代號"), markup.index("名稱"))
        self.assertNotIn("checkbox", markup.lower())
        self.assertNotIn("selection", markup.lower())
        self.assertIn("--etf-search-columns:", markup)
        layout_style = (
            markup.split('style="', 1)[1]
            .split('"', 1)[0]
        )
        self.assertNotIn("minmax", layout_style)
        self.assertNotIn("fr", layout_style)

    def test_each_column_width_uses_its_longest_visible_text(self) -> None:
        """確認所有欄寬都由該欄最長文字決定。"""

        short_rows = [format_etf_result_row(self.build_item())]
        wide_rows = [dict(short_rows[0], fund_size="12,345.67 億元")]

        short_template, short_total = build_etf_search_column_layout(
            short_rows
        )
        wide_template, wide_total = build_etf_search_column_layout(
            wide_rows
        )

        self.assertGreater(
            estimate_text_width_rem("喵喵評等"),
            estimate_text_width_rem("A+"),
        )
        self.assertNotEqual(short_template, wide_template)
        self.assertGreater(wide_total, short_total)

    @patch(
        "frontend.pages.etf_search."
        "st.switch_page"
    )
    @patch(
        "frontend.pages.etf_search."
        "st.session_state",
        {
            RESULT_ACTION_KEY: {
                "selection": {
                    "rows": [0],
                },
            }
        },
    )
    def test_table_action_opens_detail(
        self,
        mock_switch_page,
    ) -> None:
        """確認選取整列會保留搜尋狀態並導向詳細頁。"""

        open_etf_detail(
            [self.build_item()],
            ETFSearchQueryState(
                keyword="元大",
                bond_label="非債券",
                page=2,
            ),
        )

        mock_switch_page.assert_called_once_with(
            "page_scripts/etf_detail_page.py",
            query_params={
                "code": "0050",
                "from": "etf-search",
                "active": "all",
                "bond": "non-bond",
                "page": "2",
                "page_size": "20",
                "keyword": "元大",
            },
        )


if __name__ == "__main__":
    unittest.main()
