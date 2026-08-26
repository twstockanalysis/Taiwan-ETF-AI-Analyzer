"""Streamlit 網站 AppTest 自動化測試。"""

import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

STREAMLIT_APP_PATH = (
    PROJECT_ROOT
    / "frontend"
    / "app.py"
)


def build_system_overview_payload() -> dict:
    """建立首頁 AppTest 使用的合法系統總覽。"""

    return {
        "api_status": "healthy",
        "database_type": "SQLite",
        "etfs": {
            "total_count": 4,
            "active_count": 1,
            "passive_count": 3,
            "bond_count": 1,
            "non_bond_count": 3,
            "latest_master_import_at": (
                "2026-07-30T00:05:00+00:00"
            ),
        },
        "performance": {
            "metric_code": "PRICE_RETURN",
            "source_id": "twse_stock_day",
            "etf_count": 2,
            "total_etf_count": 4,
            "coverage_pct": 50.0,
            "latest_as_of_date": "2026-07-30",
            "periods": [
                {
                    "period_code": "1M",
                    "etf_count": 2,
                    "coverage_pct": 50.0,
                    "latest_as_of_date": (
                        "2026-07-30"
                    ),
                },
                {
                    "period_code": "3M",
                    "etf_count": 1,
                    "coverage_pct": 25.0,
                    "latest_as_of_date": (
                        "2026-07-29"
                    ),
                },
                {
                    "period_code": "6M",
                    "etf_count": 2,
                    "coverage_pct": 50.0,
                    "latest_as_of_date": (
                        "2026-07-30"
                    ),
                },
                {
                    "period_code": "1Y",
                    "etf_count": 1,
                    "coverage_pct": 25.0,
                    "latest_as_of_date": (
                        "2026-07-29"
                    ),
                },
            ],
        },
        "dividends": {
            "event_count": 2,
            "etf_count": 2,
            "latest_event_date": "2026-08-10",
            "actual_component_event_count": 1,
            "actual_76w_event_count": 1,
            "source_document_event_count": 1,
            "actual_component_coverage_pct": (
                50.0
            ),
            "actual_76w_coverage_pct": 50.0,
            "source_document_coverage_pct": (
                50.0
            ),
            (
                "latest_actual_"
                "source_document_date"
            ): "2026-07-31",
        },
        "recent_import_batches": [
            {
                "batch_id": 1,
                "pipeline_name": (
                    "etf_master_pipeline"
                ),
                "source_id": "twse_openapi",
                "endpoint_id": (
                    "twse_fund_master"
                ),
                "started_at": (
                    "2026-07-30T00:00:00+00:00"
                ),
                "completed_at": (
                    "2026-07-30T00:05:00+00:00"
                ),
                "status": "success",
                "raw_record_count": 4,
                "accepted_record_count": 4,
                "rejected_record_count": 0,
                "inserted_record_count": 4,
                "updated_record_count": 0,
                "error_message": None,
            },
        ],
    }


SEARCH_PAGE_SCRIPT = """
from unittest.mock import patch

import frontend.pages.etf_search as page


def fake_fetch_etfs(**kwargs):
    return {
        "items": [
            {
                "code": "0050",
                "name": "元大台灣50",
                "is_active": False,
                "is_bond": False,
                "listing_date": "2003-06-30",
                "fund_size": None,
                "expense_ratio": None,
            },
            {
                "code": "00980A",
                "name": "主動式測試ETF",
                "is_active": True,
                "is_bond": False,
                "listing_date": "2025-05-05",
                "fund_size": 50.0,
                "expense_ratio": 0.80,
            },
        ],
        "total": 2,
        "limit": 20,
        "offset": 0,
    }


page.fetch_etfs = fake_fetch_etfs
page.load_etf_page.clear()

# AppTest.from_string 沒有建立完整的多頁導航註冊表。
# 整列 page_link 參數由獨立單元測試負責驗證；
# 此處只測試 ETF 搜尋頁其他畫面元件是否正常呈現。
with patch(
    "frontend.pages.etf_search.st.page_link"
):
    page.render_etf_search()
"""


DETAIL_PAGE_SCRIPT = """
import frontend.pages.etf_detail as page


def fake_fetch_etf_by_code(**kwargs):
    return {
        "code": "0050",
        "name": "元大台灣50",
        "is_active": False,
        "is_bond": False,
        "listing_date": "2003-06-30",
        "fund_size": 5000.0,
        "expense_ratio": 0.43,
    }


def fake_fetch_etf_performance(**kwargs):
    return {
        "etf_code": "0050",
        "metric_code": "PRICE_RETURN",
        "items": [
            {
                "as_of_date": "2026-07-29",
                "period_code": "1M",
                "metric_code": "PRICE_RETURN",
                "return_pct": 5.0,
                "source_id": "twse_stock_day",
            },
            {
                "as_of_date": "2026-07-29",
                "period_code": "6M",
                "metric_code": "PRICE_RETURN",
                "return_pct": 20.0,
                "source_id": "twse_stock_day",
            },
        ],
    }


def fake_fetch_etf_latest_close(**kwargs):
    return {
        "etf_code": "0050",
        "name": "元大台灣50",
        "close_price": 60.0,
        "trade_date": "2026-07-29",
        "source_id": "TWSE_STOCK_DAY",
    }


page.fetch_etf_by_code = fake_fetch_etf_by_code
page.fetch_etf_performance = fake_fetch_etf_performance
page.fetch_etf_latest_close = fake_fetch_etf_latest_close
page.load_etf_detail.clear()
page.load_etf_performance.clear()
page.load_etf_latest_close.clear()
page.render_etf_detail()
"""


PERFORMANCE_PAGE_SCRIPT = """
from unittest.mock import patch

import frontend.pages.performance_ranking as page


def fake_fetch_multi_period_performance_ranking(
    **kwargs,
):
    return {
        "sort_period": "6M",
        "metric_code": "PRICE_RETURN",
        "periods": [
            "1M",
            "3M",
            "6M",
            "1Y",
        ],
        "items": [
            {
                "rank": 1,
                "etf_code": "0050",
                "name": "元大台灣50",
                "is_active": False,
                "is_bond": False,
                "sort_period": "6M",
                "sort_as_of_date": "2026-07-29",
                "sort_return_pct": 20.0,
                "performance_items": [
                    {
                        "as_of_date": "2026-07-29",
                        "period_code": "1M",
                        "metric_code": "PRICE_RETURN",
                        "return_pct": 5.0,
                        "source_id": "twse_stock_day",
                    },
                    {
                        "as_of_date": "2026-07-29",
                        "period_code": "3M",
                        "metric_code": "PRICE_RETURN",
                        "return_pct": 10.0,
                        "source_id": "twse_stock_day",
                    },
                    {
                        "as_of_date": "2026-07-29",
                        "period_code": "6M",
                        "metric_code": "PRICE_RETURN",
                        "return_pct": 20.0,
                        "source_id": "twse_stock_day",
                    },
                    {
                        "as_of_date": "2026-07-29",
                        "period_code": "1Y",
                        "metric_code": "PRICE_RETURN",
                        "return_pct": 30.0,
                        "source_id": "twse_stock_day",
                    },
                ],
            },
        ],
        "total": 1,
        "limit": 20,
        "offset": 0,
    }


page.fetch_multi_period_performance_ranking = (
    fake_fetch_multi_period_performance_ranking
)
page.load_performance_ranking.clear()

with patch(
    "frontend.pages.performance_ranking."
    "st.page_link"
):
    page.render_performance_ranking()
"""


NOT_FOUND_PAGE_SCRIPT = """
import frontend.pages.etf_detail as page

from frontend.api_client import (
    APIResourceNotFoundError,
)


def raise_not_found(**kwargs):
    raise APIResourceNotFoundError(
        "ETF UNKNOWN 查詢找不到資料："
        "找不到 ETF：UNKNOWN"
    )


page.fetch_etf_by_code = raise_not_found
page.load_etf_detail.clear()
page.render_etf_detail()
"""


class TestStreamlitApp(unittest.TestCase):
    """測試 Streamlit 網站主要頁面。"""

    def test_application_renders_home_page(
        self,
    ) -> None:
        """確認網站入口以初學者配置任務為主。"""

        app = AppTest.from_file(
            STREAMLIT_APP_PATH,
            default_timeout=10,
        )

        app.run()

        self.assertEqual(
            len(app.exception),
            0,
        )

        self.assertGreaterEqual(
            len(app.title),
            1,
        )

        self.assertEqual(
            app.title[0].value,
            "GoodCat 股利喵",
        )

        self.assertEqual(len(app.success), 0)

        self.assertEqual(len(app.metric), 0)

        page_text = "\n".join(
            [item.value for item in app.subheader]
            + [item.value for item in app.caption]
        )
        self.assertIn("先算出適合你的 ETF 配置", page_text)
        self.assertIn("運用AI評分系統", page_text)
        self.assertIn("所有資料皆來源自證交所及投信", page_text)
        self.assertNotIn("本站不下單", page_text)
        self.assertNotIn("目前可用資料", page_text)
        self.assertNotIn("FastAPI", page_text)
        self.assertNotIn("SQLite", page_text)
        self.assertNotIn("最近匯入批次", page_text)

    def test_search_page_renders_aligned_detail_rows(
        self,
    ) -> None:
        """確認搜尋頁顯示固定欄位與詳細資料入口。"""

        app = AppTest.from_string(
            SEARCH_PAGE_SCRIPT,
            default_timeout=10,
        )

        app.run()

        self.assertEqual(
            len(app.exception),
            0,
        )

        self.assertEqual(
            app.title[0].value,
            "搜尋&詳細資料",
        )

        selectbox_labels = [
            item.label
            for item in app.selectbox
        ]

        self.assertNotIn(
            "資產類型",
            selectbox_labels,
        )

        self.assertEqual(len(app.dataframe), 1)

        result_table = app.dataframe[0].value

        self.assertEqual(
            list(result_table.columns),
            [
                "code",
                "name",
                "management_type",
                "listing_date",
                "fund_size",
                "expense_ratio",
            ],
        )

        caption_text = "\n".join(
            str(item.value)
            for item in app.caption
        )

        self.assertNotIn(
            "搜尋及篩選臺灣 ETF 官方主資料",
            caption_text,
        )

    def test_performance_page_renders_ranking(
        self,
    ) -> None:
        """確認績效排行榜頁可正常顯示。"""

        app = AppTest.from_string(
            PERFORMANCE_PAGE_SCRIPT,
            default_timeout=10,
        )

        app.run()

        self.assertEqual(
            len(app.exception),
            0,
        )

        self.assertEqual(
            app.title[0].value,
            "績效排行榜",
        )

        metric_values = [
            str(item.value)
            for item in app.metric
        ]

        self.assertIn(
            "6M",
            metric_values,
        )

        selectbox_labels = [
            item.label
            for item in app.selectbox
        ]

        self.assertNotIn("資產類型", selectbox_labels)
        self.assertNotIn("每頁筆數", selectbox_labels)

        button_labels = [
            item.label
            for item in app.button
        ]

        self.assertNotIn("上一頁", button_labels)
        self.assertNotIn("下一頁", button_labels)

        caption_text = "\n".join(
            str(item.value)
            for item in app.caption
        )

        self.assertIn(
            "預設為6M",
            caption_text,
        )

        self.assertNotIn("市價報酬率", caption_text)

        self.assertEqual(len(app.dataframe), 1)
        self.assertEqual(
            list(app.dataframe[0].value.columns),
            [
                "rank",
                "detail",
                "period_return",
                "as_of_date",
                "management_type",
            ],
        )


    def test_detail_page_uses_gregorian_date(
        self,
    ) -> None:
        """確認 ETF 詳細頁顯示西元日期。"""

        app = AppTest.from_string(
            DETAIL_PAGE_SCRIPT,
            default_timeout=10,
        )

        app.query_params["code"] = "0050"

        app.run()

        self.assertEqual(
            len(app.exception),
            0,
        )

        headers = [
            item.value
            for item in app.header
        ]

        self.assertTrue(
            any(
                "0050" in header
                and "元大台灣50" in header
                for header in headers
            )
        )

        metric_values = [
            str(item.value)
            for item in app.metric
        ]

        caption_values = [
            str(item.value)
            for item in app.caption
        ]

        classification_text = "\n".join(
            caption_values
        )

        self.assertIn(
            "被動式",
            classification_text,
        )

        self.assertIn(
            "非債券",
            classification_text,
        )

        self.assertIn(
            "2003-06-30",
            metric_values,
        )

        self.assertNotIn(
            "0920-06-30",
            metric_values,
        )

        self.assertIn(
            "+5.00%",
            metric_values,
        )

        self.assertIn(
            "+20.00%",
            metric_values,
        )

        self.assertIn(
            "歷史資料不足",
            metric_values,
        )

    def test_missing_etf_shows_warning(
        self,
    ) -> None:
        """確認查無 ETF 時顯示警告。"""

        app = AppTest.from_string(
            NOT_FOUND_PAGE_SCRIPT,
            default_timeout=10,
        )

        app.query_params["code"] = "UNKNOWN"

        app.run()

        self.assertEqual(
            len(app.exception),
            0,
        )

        warning_messages = [
            item.value
            for item in app.warning
        ]

        self.assertTrue(
            any(
                "找不到 ETF：UNKNOWN"
                in message
                for message in warning_messages
            )
        )


if __name__ == "__main__":
    unittest.main()
