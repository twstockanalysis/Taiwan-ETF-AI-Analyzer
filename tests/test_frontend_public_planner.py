"""公開現金流試算頁的純函式測試。"""

import unittest

import pandas as pd

from frontend.pages.public_planner import (
    build_holding_payload,
    build_monthly_rows,
    empty_holding_editor_rows,
)


class TestFrontendPublicPlanner(unittest.TestCase):
    def test_empty_editor_supports_zero_holdings_with_explicit_dtypes(self) -> None:
        rows = empty_holding_editor_rows()
        self.assertTrue(rows.empty)
        self.assertEqual(str(rows["ETF 代號"].dtype), "string")
        self.assertEqual(str(rows["持有股數"].dtype), "Int64")
        self.assertEqual(build_holding_payload(rows), ([], []))

    def test_holding_payload_normalizes_and_rejects_duplicates(self) -> None:
        rows = pd.DataFrame(
            {
                "ETF 代號": [" 0056 ", "0056", "00878"],
                "持有股數": [100, 200, 0],
            }
        )
        payload, errors = build_holding_payload(rows)
        self.assertEqual(
            payload,
            [
                {"etf_code": "0056", "held_units": 100},
                {"etf_code": "0056", "held_units": 200},
            ],
        )
        self.assertIn("ETF 代號不可重複：0056", errors)
        self.assertIn("第 3 列持有股數必須是正整數。", errors)

    def test_monthly_rows_keep_missing_values_distinct_from_zero(self) -> None:
        result = {
            "monthly_cash_flow": [
                {
                    "month": month,
                    "selected": month == 1,
                    "gross_cash": None if month == 1 else "0",
                    "after_tax_cash": None if month == 1 else "0",
                    "target_after_tax_cash": "100" if month == 1 else "0",
                    "shortfall": None if month == 1 else "0",
                }
                for month in range(1, 13)
            ]
        }
        rows = build_monthly_rows(result)
        self.assertEqual(rows[0]["尚缺金額"], "無法計算")
        self.assertEqual(rows[1]["尚缺金額"], "0.00 TWD")


if __name__ == "__main__":
    unittest.main()
