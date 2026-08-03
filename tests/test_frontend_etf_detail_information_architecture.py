"""M9-4 ETF 詳細頁資訊架構測試。"""

import inspect
import unittest

from frontend.pages.etf_detail import (
    build_data_profile_rows,
    format_source_references,
    render_etf_detail,
)


class TestFrontendETFDetailInformationArchitecture(
    unittest.TestCase
):
    """驗證詳細頁區塊順序與資料概況顯示。"""

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
            "render_dividend_history(",
            "render_data_profile(",
            "render_comparison_entry_point(",
        ]

        positions = [
            source.index(marker)
            for marker in markers
        ]

        self.assertEqual(
            positions,
            sorted(positions),
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

        self.assertIn(
            'st.subheader("ETF 比較")',
            module_source,
        )

        self.assertIn(
            "build_comparison_query_params(",
            module_source,
        )

        self.assertIn(
            'label="加入 ETF 比較"',
            module_source,
        )

        self.assertNotIn(
            "disabled=True",
            module_source,
        )


if __name__ == "__main__":
    unittest.main()
