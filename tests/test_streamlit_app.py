"""Streamlit 網站 AppTest 自動化測試。"""

import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from frontend.pages.home import (
    load_api_health,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

STREAMLIT_APP_PATH = (
    PROJECT_ROOT
    / "frontend"
    / "app.py"
)


SEARCH_PAGE_SCRIPT = """
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


page.fetch_etf_by_code = fake_fetch_etf_by_code
page.load_etf_detail.clear()
page.render_etf_detail()
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

    @patch(
        "frontend.pages.home.fetch_api_health"
    )
    def test_application_renders_home_page(
        self,
        mock_fetch_api_health,
    ) -> None:
        """確認網站入口可顯示首頁。"""

        mock_fetch_api_health.return_value = {
            "status": "healthy",
        }

        load_api_health.clear()

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
            "TW ETF AI Analyzer",
        )

        success_messages = [
            item.value
            for item in app.success
        ]

        self.assertTrue(
            any(
                "FastAPI 連線成功"
                in message
                for message in success_messages
            )
        )

    def test_search_page_renders_etf_table(
        self,
    ) -> None:
        """確認 ETF 查詢頁顯示正式表格。"""

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
            "ETF 查詢",
        )

        self.assertEqual(
            len(app.dataframe),
            1,
        )

        dataframe = app.dataframe[0].value

        self.assertEqual(
            len(dataframe),
            2,
        )

        self.assertEqual(
            str(
                dataframe.iloc[0]["代號"]
            ),
            "0050",
        )

        self.assertEqual(
            dataframe.iloc[0]["上市日期"],
            "2003-06-30",
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

        self.assertIn(
            "被動式",
            metric_values,
        )

        self.assertIn(
            "非債券",
            metric_values,
        )

        self.assertIn(
            "2003-06-30",
            metric_values,
        )

        self.assertNotIn(
            "0920-06-30",
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