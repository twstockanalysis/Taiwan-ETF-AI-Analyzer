"""V3 一般股票型 ETF 產品範圍測試。"""

import unittest

from backend.app.services.etf_product_scope import (
    unsupported_allocation_product_reason,
)


class TestETFProductScope(unittest.TestCase):
    def test_regular_equity_etf_is_supported(self) -> None:
        self.assertIsNone(
            unsupported_allocation_product_reason("0050", "元大台灣50", False)
        )

    def test_active_equity_suffix_a_is_not_excluded_by_code(self) -> None:
        self.assertIsNone(
            unsupported_allocation_product_reason(
                "00981A", "主動式台灣股票ETF", False
            )
        )

    def test_special_product_types_are_explicitly_classified(self) -> None:
        self.assertEqual(
            unsupported_allocation_product_reason("00632R", "元大台灣50反1", False),
            "LEVERAGED_INVERSE_OR_FUTURES",
        )
        self.assertEqual(
            unsupported_allocation_product_reason("00720B", "元大投資級公司債", True),
            "BOND_OR_FIXED_INCOME",
        )
        self.assertEqual(
            unsupported_allocation_product_reason("00980T", "平衡型ETF", False),
            "MULTI_ASSET",
        )


if __name__ == "__main__":
    unittest.main()
