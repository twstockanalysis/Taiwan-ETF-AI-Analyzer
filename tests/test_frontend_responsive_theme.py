"""Streamlit 響應式字體設定測試。"""

import unittest
from unittest.mock import patch

from frontend.ui.theme import (
    GLOBAL_STYLE_MARKER,
    GLOBAL_STYLES,
    apply_global_styles,
)


class TestFrontendResponsiveTheme(
    unittest.TestCase
):
    """測試全站可讀性 CSS 契約。"""

    def test_styles_prevent_metric_ellipsis(
        self,
    ) -> None:
        """確認 Metric 數值不使用省略號截斷。"""

        self.assertIn(
            GLOBAL_STYLE_MARKER,
            GLOBAL_STYLES,
        )
        self.assertIn(
            '[data-testid="stMetricValue"]',
            GLOBAL_STYLES,
        )
        self.assertIn(
            "text-overflow: clip",
            GLOBAL_STYLES,
        )
        self.assertIn(
            "font-size: 0.9rem",
            GLOBAL_STYLES,
        )

    def test_search_results_hide_table_toolbar(
        self,
    ) -> None:
        """確認 ETF 搜尋結果不顯示表格控制列。"""

        self.assertIn(
            ".st-key-etf_search_detail_action "
            '[data-testid="stElementToolbar"]',
            GLOBAL_STYLES,
        )

    def test_search_summary_divider_has_no_top_gap(self) -> None:
        """確認搜尋摘要後直接銜接既有分隔線。"""

        self.assertIn(
            ".st-key-etf-search-summary hr",
            GLOBAL_STYLES,
        )
        self.assertIn(
            "margin-top: 0 !important",
            GLOBAL_STYLES,
        )

    def test_titled_cards_share_compact_top_inset(self) -> None:
        """確認有標題的卡片沿用詳細資料卡片的上方間距。"""

        self.assertIn(
            '[data-testid="stVerticalBlock"][class*="-card"]',
            GLOBAL_STYLES,
        )
        self.assertIn(
            ".st-key-etf-detail-performance",
            GLOBAL_STYLES,
        )
        self.assertIn(
            ".st-key-etf-detail-dividend-summary",
            GLOBAL_STYLES,
        )
        self.assertIn(
            "padding-top: 10px !important",
            GLOBAL_STYLES,
        )

    def test_dividend_source_caption_is_compact(self) -> None:
        """確認配息摘要來源文字使用較小字級。"""

        self.assertIn(
            ".st-key-etf-detail-dividend-summary",
            GLOBAL_STYLES,
        )
        self.assertIn(
            "font-size: 0.75rem !important",
            GLOBAL_STYLES,
        )

    def test_dividend_expandable_rows_use_fixed_width_columns(self) -> None:
        """確認配息表頭與資料列使用相同等寬排版。"""

        self.assertIn(
            ".st-key-dividend-event-header",
            GLOBAL_STYLES,
        )
        self.assertIn(
            "details summary p",
            GLOBAL_STYLES,
        )
        self.assertIn(
            "white-space: pre !important",
            GLOBAL_STYLES,
        )
        self.assertIn(
            "min-width: 0",
            GLOBAL_STYLES,
        )
        self.assertIn(
            "clamp(0.72rem, 1.35vw, 0.875rem)",
            GLOBAL_STYLES,
        )
        self.assertNotIn("tab-size:", GLOBAL_STYLES)
        self.assertIn(
            "background: var(--secondary-background-color)",
            GLOBAL_STYLES,
        )
        self.assertIn("overflow: hidden", GLOBAL_STYLES)

    def test_dividend_charts_hide_toolbar(self) -> None:
        """確認配息圖表不顯示下載、搜尋等控制區。"""

        self.assertIn(
            ".st-key-etf-detail-dividend-summary",
            GLOBAL_STYLES,
        )
        self.assertIn(
            '[data-testid="stElementToolbar"]',
            GLOBAL_STYLES,
        )

    def test_performance_chart_hides_toolbar(self) -> None:
        """確認績效走勢圖不顯示右上角控制列。"""

        self.assertIn(
            ".st-key-etf-detail-performance",
            GLOBAL_STYLES,
        )
        self.assertIn(
            '[data-testid="stElementToolbar"]',
            GLOBAL_STYLES,
        )

    def test_detail_comparison_link_uses_native_unframed_style(self) -> None:
        """確認資訊卡比較連結未套用自訂按鈕外框。"""

        self.assertNotIn(
            '.st-key-etf-detail-actions [data-testid="stPageLink"]',
            GLOBAL_STYLES,
        )

    def test_desktop_sidebar_aligns_with_home_return_action(
        self,
    ) -> None:
        """確認桌面側欄整組下移且不改變項目相對位置。"""

        self.assertIn(
            "@media (min-width: 769px)",
            GLOBAL_STYLES,
        )
        self.assertIn(
            '[data-testid="stSidebarNav"]',
            GLOBAL_STYLES,
        )
        self.assertIn(
            "margin-top: 3.75rem",
            GLOBAL_STYLES,
        )

    def test_reviewed_tables_hide_toolbar_and_lock_headers(
        self,
    ) -> None:
        """確認持股與排行榜不顯示控制列且表頭不可互動。"""

        self.assertIn(
            ".st-key-performance_ranking_detail_action",
            GLOBAL_STYLES,
        )
        self.assertIn(
            '[data-testid="stDataFrameResizable"]::after',
            GLOBAL_STYLES,
        )
        self.assertIn("height: 36px", GLOBAL_STYLES)
        self.assertIn(
            "--gdg-bg-cell: var(--secondary-background-color)",
            GLOBAL_STYLES,
        )
        self.assertIn(
            "--gdg-bg-icon-header: transparent",
            GLOBAL_STYLES,
        )

    def test_month_buttons_keep_three_columns_on_narrow_screens(
        self,
    ) -> None:
        """確認窄版月份按鈕不會各自佔滿一整列。"""

        self.assertIn("@media (max-width: 768px)", GLOBAL_STYLES)
        self.assertIn(
            '[class*="st-key-public-planner-month-row-"]',
            GLOBAL_STYLES,
        )
        self.assertIn(
            "grid-template-columns: repeat(3, minmax(0, 1fr))",
            GLOBAL_STYLES,
        )
        self.assertIn("width: auto !important", GLOBAL_STYLES)

    @patch(
        "frontend.ui.theme.st.markdown"
    )
    def test_styles_use_safe_streamlit_injection(
        self,
        mock_markdown,
    ) -> None:
        """確認 CSS 由單一函式注入。"""

        apply_global_styles()

        mock_markdown.assert_called_once_with(
            GLOBAL_STYLES,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    unittest.main()
