"""ETF 搜尋結果欄位測試。"""

import unittest

from frontend.pages.etf_search import (
    format_etf_result_row,
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


if __name__ == "__main__":
    unittest.main()
