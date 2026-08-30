"""M9-4 ETF 詳細頁資訊架構測試。"""

import inspect
import unittest

from frontend.pages.etf_detail import (
    build_price_history_chart_rows,
    build_data_profile_rows,
    format_source_references,
    render_etf_detail,
    render_etf_information,
    render_etf_performance,
    render_dividend_event_rows,
    render_dividend_summary,
)


class TestFrontendETFDetailInformationArchitecture(
    unittest.TestCase
):
    """驗證詳細頁區塊順序與資料概況顯示。"""

    def test_price_history_rows_preserve_official_values(self) -> None:
        """走勢圖只使用實際收盤價，不以零補齊缺少日期。"""

        rows = build_price_history_chart_rows(
            {
                "items": [
                    {
                        "trade_date": "2026-08-01",
                        "close_price": 14.1,
                        "source_id": "twse_stock_day",
                    },
                    {
                        "trade_date": "2026-08-04",
                        "close_price": 14.25,
                        "source_id": "twse_stock_day",
                    },
                ]
            }
        )

        self.assertEqual(
            rows,
            [
                {"交易日": "2026-08-01", "收盤價": 14.1},
                {"交易日": "2026-08-04", "收盤價": 14.25},
            ],
        )
        self.assertEqual(build_price_history_chart_rows(None), [])

    def test_performance_card_places_chart_and_source_last(self) -> None:
        """績效卡片先顯示四項績效，再以圖表及來源收尾。"""

        source = inspect.getsource(render_etf_performance)
        metrics_position = source.index("columns = st.columns(")
        chart_position = source.index("render_price_history_chart(")
        caption_position = source.index("st.caption(source_caption)")

        self.assertLess(metrics_position, chart_position)
        self.assertLess(chart_position, caption_position)
        self.assertNotIn("截至 ", source)
        self.assertIn('source_caption = "資料來源於證交所"', source)
        self.assertIn('f"　資料日期：{data_date}"', source)
        self.assertNotIn("來源於證交所資料", source)

    def build_profile(
        self,
    ) -> dict:
        """建立資料概況測試資料。"""

        return {
            "etf_code": "0050",
            "master": {
                "sources": [
                    {
                        "source_id": "twse_openapi",
                        "display_name": (
                            "臺灣證券交易所 OpenAPI"
                        ),
                    }
                ],
                "latest_import_at": (
                    "2026-07-30T00:05:00+00:00"
                ),
            },
            "performance": {
                "metric_code": "PRICE_RETURN",
                "sources": [
                    {
                        "source_id": "twse_stock_day",
                        "display_name": (
                            "TWSE 個股日成交資訊"
                        ),
                    }
                ],
                "record_count": 4,
                "available_periods": [
                    "1M",
                    "3M",
                    "6M",
                    "1Y",
                ],
                "latest_as_of_date": "2026-07-30",
                "latest_import_at": (
                    "2026-07-30T01:05:00+00:00"
                ),
            },
            "dividends": {
                "sources": [],
                "event_count": 0,
                "latest_event_date": None,
                "latest_import_at": None,
            },
            "actual_dividend": {
                "sources": [],
                "actual_component_event_count": 0,
                "actual_76w_event_count": 0,
                "source_document_event_count": 0,
                "latest_source_document_date": None,
                "latest_import_at": None,
            },
        }

    def test_sources_include_name_and_id(
        self,
    ) -> None:
        """確認畫面同時保留來源名稱與識別碼。"""

        self.assertEqual(
            format_source_references(
                [
                    {
                        "source_id": "twse_openapi",
                        "display_name": (
                            "臺灣證券交易所 OpenAPI"
                        ),
                    }
                ]
            ),
            (
                "臺灣證券交易所 OpenAPI "
                "(twse_openapi)"
            ),
        )

        self.assertEqual(
            format_source_references(
                []
            ),
            "尚未取得",
        )

    def test_profile_rows_preserve_missing_dates(
        self,
    ) -> None:
        """確認缺資料不以今天日期或 0 代替。"""

        rows = build_data_profile_rows(
            self.build_profile()
        )

        self.assertEqual(
            [
                row["資料區塊"]
                for row in rows
            ],
            [
                "ETF 主資料",
                "市價績效",
                "配息事件",
                "正式配息組成",
            ],
        )

        dividend_row = rows[2]
        actual_row = rows[3]

        self.assertEqual(
            dividend_row[
                "最新資料日期"
            ],
            "尚未取得",
        )

        self.assertEqual(
            actual_row[
                "最近匯入"
            ],
            "尚未取得",
        )

        self.assertIn(
            "76W 0 次",
            actual_row["資料量"],
        )

    def test_detail_sections_have_fixed_order(
        self,
    ) -> None:
        """確認詳細頁依決策流程排列區塊。"""

        source = inspect.getsource(
            render_etf_detail
        )

        markers = [
            "render_etf_information(",
            "render_etf_performance(",
            "render_dividend_summary(",
            "render_actual_76w_summary(",
            "render_tax_reinvestment_analysis(",
        ]

        positions = [
            source.index(marker)
            for marker in markers
        ]

        self.assertEqual(
            positions,
            sorted(positions),
        )
        self.assertNotIn(
            "render_data_profile(",
            source,
        )
        self.assertNotIn(
            "render_base_target_analysis(",
            source,
        )
        self.assertNotIn(
            "render_dividend_history(",
            source,
        )
        self.assertIn(
            "if owner_unlocked:",
            source,
        )
        self.assertIn(
            "show_owner_details=owner_unlocked",
            source,
        )
        self.assertLess(
            source.index("if owner_unlocked:"),
            source.index(
                "render_tax_reinvestment_analysis("
            ),
        )

    def test_performance_uses_public_card_copy(self) -> None:
        """確認績效以卡片呈現並使用核定來源說明。"""

        source = inspect.getsource(
            render_etf_performance
        )

        self.assertIn('key="etf-detail-performance"', source)
        self.assertIn("border=True", source)
        self.assertIn('st.subheader("績效")', source)
        self.assertIn(
            'source_caption = "資料來源於證交所"',
            source,
        )
        self.assertNotIn("目前為市價報酬率", source)
        self.assertNotIn("不包含配息再投資", source)
        self.assertNotIn("st.divider()", source)

    def test_dividend_summary_uses_compact_card_and_bar_chart(self) -> None:
        """確認配息摘要採卡片、條形圖與精簡欄位。"""

        module_source = inspect.getsource(
            __import__(
                "frontend.pages.etf_detail",
                fromlist=["render_dividend_summary"],
            )
        )
        wrapper_source = inspect.getsource(
            render_dividend_summary
        )

        self.assertIn(
            'key="etf-detail-dividend-summary"',
            wrapper_source,
        )
        self.assertIn("border=True", wrapper_source)
        self.assertNotIn("st.divider()", wrapper_source)
        self.assertIn('"type": "bar"', module_source)
        self.assertIn('"type": "line"', module_source)
        self.assertIn('st.columns(2, gap="medium")', module_source)
        self.assertIn('"現金股利"', module_source)
        self.assertIn('"股票股利"', module_source)
        self.assertIn('"**股利**　"', module_source)
        self.assertIn("DIVIDEND_CASH_COLOR", module_source)
        self.assertIn("DIVIDEND_STOCK_COLOR", module_source)
        self.assertIn("unsafe_allow_html=True", module_source)
        self.assertIn('st.markdown("**殖利率(%)**")', module_source)
        self.assertNotIn('"title": "每單位股利"', module_source)
        self.assertNotIn('"title": "殖利率（%）"', module_source)
        self.assertIn('"type": "rule"', module_source)
        self.assertIn('"type": "text"', module_source)
        self.assertIn('"strokeDash": [4, 2]', module_source)
        self.assertIn("datum['顯示分隔線'] === true", module_source)
        self.assertIn("datum['顯示年度合計'] === true", module_source)
        self.assertIn('"field": "年度股利合計"', module_source)
        self.assertIn('"format": ".2f"', module_source)
        self.assertIn('"domain": [0, dividend_y_upper]', module_source)
        self.assertIn('"domain": [0, yield_y_upper]', module_source)
        self.assertIn('st.context.theme.type == "dark"', module_source)
        self.assertIn('"#FFFFFF"', module_source)
        self.assertIn('"#000000"', module_source)
        self.assertEqual(
            module_source.count('"color": chart_value_text_color'),
            2,
        )
        self.assertIn('"title": None', module_source)
        self.assertIn('"domain": chart_years', module_source)
        self.assertIn(
            "股票股利資料尚未匯入",
            module_source,
        )
        self.assertIn(
            "show_owner_details",
            module_source,
        )
        self.assertIn('"現金/股票"', module_source)
        self.assertIn('st.subheader("配息資料")', module_source)
        self.assertIn('key="dividend-cash-stock-chart"', module_source)
        self.assertIn('key="dividend-yield-chart"', module_source)
        self.assertNotIn('"最新每單位配息"', module_source)
        self.assertNotIn(
            '"**歷次現金股利與殖利率趨勢**"',
            module_source,
        )
        self.assertIn(
            "資料皆來源於證交所；若有缺少時才以",
            module_source,
        )

    def test_summary_hides_owner_diagnostics_from_public_view(
        self,
    ) -> None:
        """確認摘要卡只對已進入喵窩者顯示缺漏診斷。"""

        summary_source = inspect.getsource(
            render_etf_information
        )
        page_source = inspect.getsource(
            render_etf_detail
        )

        self.assertNotIn("核心資料概覽", summary_source)
        self.assertIn(
            "if show_owner_details and (",
            summary_source,
        )
        self.assertIn(
            "目前 ETF 主資料來源尚未提供或",
            summary_source,
        )
        self.assertIn('f"{code} {name}"', summary_source)
        self.assertNotIn('f"{code}　{name}"', summary_source)
        self.assertIn(
            "owner_unlocked = get_owner_token() is not None",
            page_source,
        )

    def test_detail_missing_values_use_fetching_copy(self) -> None:
        """確認詳細頁缺值統一顯示資料抓取中。"""

        module_source = inspect.getsource(
            __import__(
                "frontend.pages.etf_detail",
                fromlist=["render_etf_detail"],
            )
        )

        self.assertNotIn('"尚無資料"', module_source)
        self.assertNotIn('"歷史資料不足"', module_source)
        self.assertIn('"資料抓取中"', module_source)

    def test_dividend_expander_skips_repeated_event_table(self) -> None:
        """確認展開列直接顯示組成，不重複列出事件基本資料。"""

        source = inspect.getsource(
            render_dividend_event_rows
        )

        self.assertNotIn("event_rows = [", source)
        self.assertNotIn("st.table", source)
        self.assertIn("load_dividend_detail", source)
        self.assertIn("render_component_group", source)
        self.assertIn('title="現金股利組成"', source)
        self.assertNotIn('title="股利組成"', source)
        self.assertNotIn('title="實際所得組成"', source)
        self.assertIn(
            'detail.get(\n                "selected_components"',
            source,
        )
        self.assertIn(
            'class="dividend-event-grid-header"',
            source,
        )

    def test_comparison_entry_is_enabled(
        self,
    ) -> None:
        """確認詳細頁可將目前 ETF 帶入比較頁。"""

        module_source = inspect.getsource(
            __import__(
                "frontend.pages.etf_detail",
                fromlist=["render_etf_detail"],
            )
        )

        self.assertNotIn(
            'st.subheader("ETF 比較")',
            module_source,
        )

        self.assertIn(
            "build_comparison_query_params(",
            module_source,
        )

        self.assertIn(
            'label="加入比較"',
            module_source,
        )

        information_source = inspect.getsource(
            __import__(
                "frontend.pages.etf_detail",
                fromlist=["render_etf_information"],
            ).render_etf_information
        )
        self.assertIn(
            "render_comparison_action(",
            information_source,
        )
        self.assertIn(
            'horizontal_alignment="distribute"',
            information_source,
        )
        self.assertNotIn("st.divider()", information_source)

        self.assertNotIn(
            "disabled=True",
            module_source,
        )


if __name__ == "__main__":
    unittest.main()
