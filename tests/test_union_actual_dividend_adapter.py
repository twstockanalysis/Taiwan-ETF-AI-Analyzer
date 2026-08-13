"""聯邦投信官方 ETF 配息頁測試。"""

import unittest
from decimal import Decimal

from backend.app.data_sources.union_actual_dividend_adapter import (
    fetch_union_dividend_amounts,
    parse_union_dividend_amounts,
)


HTML = """
<table><tbody>
<tr><td data-title="級別">半年配 新台幣</td>
<td data-title="除息日">2026/07/16</td>
<td data-title="每單位配息金額">1.53</td>
<td data-title="配息基準日淨值">23.54</td>
<td data-title="當期配息率(%)">6.5</td>
<td data-title="當期報酬率(含息)">30.79</td></tr>
<tr><td data-title="級別"></td>
<td data-title="除息日">2025/07/16</td>
<td data-title="每單位配息金額">0.38</td>
<td data-title="配息基準日淨值">12.03</td>
<td data-title="當期配息率(%)">3.16</td>
<td data-title="當期報酬率(含息)">-</td></tr>
</tbody></table>
"""


class TestUnionActualDividendAdapter(unittest.TestCase):
    def test_parses_amounts_and_inherits_frequency(self) -> None:
        rows = parse_union_dividend_amounts(etf_code="009804", html=HTML)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].amount_per_unit, Decimal("1.53"))
        self.assertEqual(rows[1].frequency, "半年配 新台幣")
        self.assertIsNone(rows[1].total_return_percent)
        self.assertEqual(rows[0].information_basis, "ACTUAL_AMOUNT_ONLY")

    def test_empty_official_table_is_supported(self) -> None:
        self.assertEqual(
            parse_union_dividend_amounts(etf_code="009804", html="<table></table>"),
            (),
        )

    def test_unknown_etf_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "官方基金編號對照"):
            parse_union_dividend_amounts(etf_code="009825", html=HTML)

    def test_network_access_requires_explicit_opt_in(self) -> None:
        with self.assertRaisesRegex(ValueError, "allow_network=True"):
            fetch_union_dividend_amounts(etf_code="009804")


if __name__ == "__main__":
    unittest.main()
