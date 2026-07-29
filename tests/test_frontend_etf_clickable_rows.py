"""ETF 整列點擊介面測試。"""

import unittest
from unittest.mock import patch

from frontend.pages.etf_search import (
    format_clickable_etf_row,
    render_clickable_etf_rows,
)


class TestFrontendETFClickableRows(
    unittest.TestCase
):
    """測試 ETF 搜尋結果整列導航。"""

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

    def test_row_label_contains_etf_data(
        self,
    ) -> None:
        """確認資料列包含主要 ETF 資訊。"""

        label = format_clickable_etf_row(
            self.build_item()
        )

        self.assertIn(
            "0050",
            label,
        )

        self.assertIn(
            "元大台灣50",
            label,
        )

        self.assertIn(
            "被動式",
            label,
        )

        self.assertIn(
            "2003-06-30",
            label,
        )

@patch(
    "frontend.pages.etf_search."
    "st.page_link"
)
def test_whole_row_uses_stretched_page_link(
    self,
    mock_page_link,
) -> None:
    """確認整列使用全寬頁面連結。"""

    render_clickable_etf_rows(
        [
            self.build_item(),
        ]
    )

    mock_page_link.assert_called_once()

    call_arguments = (
        mock_page_link.call_args
    )

    self.assertEqual(
        call_arguments.args[0],
        "page_scripts/etf_detail_page.py",
    )

    self.assertEqual(
        call_arguments.kwargs["width"],
        "stretch",
    )

    self.assertEqual(
        call_arguments.kwargs[
            "query_params"
        ],
        {
            "code": "0050",
        },
    )

    self.assertEqual(
        call_arguments.kwargs[
            "icon_position"
        ],
        "right",
    )

    self.assertIn(
        "0050",
        call_arguments.kwargs["label"],
    )

    self.assertIn(
        "元大台灣50",
        call_arguments.kwargs["label"],
    )


if __name__ == "__main__":
    unittest.main()