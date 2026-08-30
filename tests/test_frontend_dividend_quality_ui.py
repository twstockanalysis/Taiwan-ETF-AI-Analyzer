"""Streamlit 正式配息資料品質頁測試。"""

import unittest
from pathlib import Path

from streamlit.testing.v1 import (
    AppTest,
)

from frontend.pages.dividend_data_quality import (
    build_review_queue_rows,
    format_coverage_percentage,
    get_review_issue_label,
)


QUALITY_PAGE_SCRIPT = """
import frontend.pages.dividend_data_quality as page

page.render_page_title = lambda title: page.st.title(title)


def fake_fetch_actual_dividend_coverage(
    etf_code=None,
    **kwargs,
):
    return {
        "etf_code": etf_code,
        "total_dividend_count": 4,
        "estimated_component_event_count": 3,
        "actual_component_event_count": 2,
        "actual_76w_event_count": 1,
        "source_document_event_count": 1,
        "missing_actual_component_event_count": 2,
        "missing_source_document_event_count": 3,
        "actual_component_coverage_pct": 50.0,
        "actual_76w_coverage_pct": 25.0,
        "source_document_coverage_pct": 25.0,
    }


def build_item(queue_id=472):
    return {
        "queue_id": queue_id,
        "dividend_id": 233,
        "etf_code": "00900",
        "source_event_id": (
            "twse_etfortune_dividend:"
            "00900:2026-02-25"
        ),
        "ex_dividend_date": "2026-02-25",
        "amount_per_unit": 0.075,
        "currency": "TWD",
        "issue_type": (
            "MISSING_SOURCE_DOCUMENT"
        ),
        "suggested_source_id": (
            "manual_actual_dividend_notice"
        ),
        "priority": 20,
        "status": "PENDING",
        "notes": None,
        "resolution_document_id": None,
        "last_evaluated_at": (
            "2026-07-31T07:55:28+00:00"
        ),
        "resolved_at": None,
        "created_at": (
            "2026-07-31T07:55:28+00:00"
        ),
        "updated_at": (
            "2026-07-31T07:55:28+00:00"
        ),
    }


def fake_fetch_dividend_review_queue(**kwargs):
    return {
        "total": 1,
        "limit": kwargs["limit"],
        "offset": kwargs["offset"],
        "items": [
            build_item(),
        ],
    }


def fake_fetch_dividend_review_queue_item(
    queue_id,
    **kwargs,
):
    return build_item(queue_id)


page.fetch_actual_dividend_coverage = (
    fake_fetch_actual_dividend_coverage
)
page.fetch_dividend_review_queue = (
    fake_fetch_dividend_review_queue
)
page.fetch_dividend_review_queue_item = (
    fake_fetch_dividend_review_queue_item
)

page.load_actual_dividend_coverage.clear()
page.load_dividend_review_queue.clear()
page.load_dividend_review_queue_item.clear()

page.render_dividend_data_quality()
"""


EMPTY_QUALITY_PAGE_SCRIPT = """
import frontend.pages.dividend_data_quality as page

page.render_page_title = lambda title: page.st.title(title)


def fake_fetch_actual_dividend_coverage(
    etf_code=None,
    **kwargs,
):
    return {
        "etf_code": etf_code,
        "total_dividend_count": 0,
        "estimated_component_event_count": 0,
        "actual_component_event_count": 0,
        "actual_76w_event_count": 0,
        "source_document_event_count": 0,
        "missing_actual_component_event_count": 0,
        "missing_source_document_event_count": 0,
        "actual_component_coverage_pct": None,
        "actual_76w_coverage_pct": None,
        "source_document_coverage_pct": None,
    }


def fake_fetch_dividend_review_queue(**kwargs):
    return {
        "total": 0,
        "limit": kwargs["limit"],
        "offset": kwargs["offset"],
        "items": [],
    }


page.fetch_actual_dividend_coverage = (
    fake_fetch_actual_dividend_coverage
)
page.fetch_dividend_review_queue = (
    fake_fetch_dividend_review_queue
)

page.load_actual_dividend_coverage.clear()
page.load_dividend_review_queue.clear()
page.load_dividend_review_queue_item.clear()

page.render_dividend_data_quality()
"""


class TestFrontendDividendQualityUI(
    unittest.TestCase
):
    """測試品質格式、佇列資料及 Streamlit 畫面。"""

    def test_missing_and_zero_coverage_are_distinct(
        self,
    ) -> None:
        """確認缺資料與正式 0% 顯示不同。"""

        self.assertEqual(
            format_coverage_percentage(
                None
            ),
            "尚無事件",
        )

        self.assertEqual(
            format_coverage_percentage(
                0
            ),
            "0.00%",
        )

    def test_issue_label_is_readable(
        self,
    ) -> None:
        """確認缺失代碼轉成清楚中文。"""

        self.assertEqual(
            get_review_issue_label(
                "MISSING_SOURCE_DOCUMENT"
            ),
            "缺少正式來源文件",
        )

    def test_queue_rows_use_consistent_order(
        self,
    ) -> None:
        """確認待處理資料列欄位順序固定。"""

        rows = build_review_queue_rows(
            [
                {
                    "priority": 20,
                    "etf_code": "00900",
                    "ex_dividend_date": (
                        "2026-02-25"
                    ),
                    "issue_type": (
                        "MISSING_SOURCE_DOCUMENT"
                    ),
                    "status": "PENDING",
                    "amount_per_unit": 0.075,
                    "currency": "TWD",
                    "suggested_source_id": (
                        "manual_actual_dividend_notice"
                    ),
                    "last_evaluated_at": (
                        "2026-07-31T07:55:28+00:00"
                    ),
                }
            ]
        )

        self.assertEqual(
            list(rows[0]),
            [
                "優先級",
                "ETF",
                "除息日",
                "問題",
                "狀態",
                "每單位配息",
                "建議來源",
                "最後檢查",
            ],
        )

        self.assertEqual(
            rows[0]["問題"],
            "缺少正式來源文件",
        )


    def test_app_registers_quality_navigation(
        self,
    ) -> None:
        """確認網站導覽將配息資料品質登錄為管理者頁面。"""

        project_root = Path(
            __file__
        ).resolve().parents[1]

        navigation_source = (
            project_root
            / "frontend"
            / "navigation.py"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            'title="配息資料品質"',
            navigation_source,
        )

        self.assertIn(
            'url_path="dividend-data-quality"',
            navigation_source,
        )

        public_routes = navigation_source.split(
            "PUBLIC_ROUTES = (",
            maxsplit=1,
        )[1].split(")", maxsplit=1)[0]
        owner_routes = navigation_source.split(
            "OWNER_ROUTES = (",
            maxsplit=1,
        )[1].split(")", maxsplit=1)[0]

        self.assertNotIn(
            "DIVIDEND_DATA_QUALITY_ROUTE",
            public_routes,
        )
        self.assertIn(
            "DIVIDEND_DATA_QUALITY_ROUTE",
            owner_routes,
        )

    def test_quality_page_renders_summary_and_detail(
        self,
    ) -> None:
        """確認品質頁顯示摘要、佇列及單筆明細。"""

        app = AppTest.from_string(
            QUALITY_PAGE_SCRIPT,
            default_timeout=10,
        )

        app.run()

        self.assertEqual(
            len(app.exception),
            0,
        )

        subheaders = [
            item.value
            for item in app.subheader
        ]

        self.assertIn(
            "全站覆蓋率摘要",
            subheaders,
        )

        self.assertIn(
            "待處理來源佇列",
            subheaders,
        )

        self.assertIn(
            "佇列項目明細",
            subheaders,
        )

        metric_values = [
            str(item.value)
            for item in app.metric
        ]

        self.assertIn(
            "50.00%",
            metric_values,
        )

        self.assertIn(
            "25.00%",
            metric_values,
        )

        self.assertIn(
            "1 項",
            metric_values,
        )

    def test_empty_page_does_not_show_zero_rate(
        self,
    ) -> None:
        """確認零事件時不把缺資料顯示為 0%。"""

        app = AppTest.from_string(
            EMPTY_QUALITY_PAGE_SCRIPT,
            default_timeout=10,
        )

        app.run()

        self.assertEqual(
            len(app.exception),
            0,
        )

        info_messages = [
            item.value
            for item in app.info
        ]

        self.assertTrue(
            any(
                "尚無配息事件"
                in message
                for message in info_messages
            )
        )

        metric_values = [
            str(item.value)
            for item in app.metric
        ]

        self.assertIn(
            "尚無事件",
            metric_values,
        )

        self.assertNotIn(
            "0.00%",
            metric_values,
        )


if __name__ == "__main__":
    unittest.main()
