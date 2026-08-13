"""大華銀投信官方 ETF 歷史配息金額測試。"""

import unittest
from decimal import Decimal

from backend.app.data_sources.uob_actual_dividend_adapter import (
    fetch_uob_dividend_amounts,
    parse_uob_dividend_amounts,
    parse_uob_fund_detail_url,
    parse_uob_fund_name,
)


class TestUOBActualDividendAdapter(unittest.TestCase):
    def test_resolves_official_fund_id_and_name(self) -> None:
        url = parse_uob_fund_detail_url(
            etf_code="00918",
            html_text='<a href="/fund/etf/88329556#dividends">配息</a>',
        )
        self.assertEqual(url, "https://www.uobam.com.tw/fund/etf/88329556")
        self.assertEqual(parse_uob_fund_name("<h1>大華優利高填息30</h1>"), "大華優利高填息30")

    def test_parses_actual_amount_without_inventing_composition(self) -> None:
        result = parse_uob_dividend_amounts(
            etf_code="00918",
            fund_name="大華優利高填息30",
            html_text="""
            <div class="result"><div class="item"><div class="head">
            <div class="name">大華優利高填息30</div></div>
            <table><tr><td>新台幣</td><td>1.26</td><td>2026/05/31</td>
            <td>2026/06/18</td><td>2026/07/14</td><td>每季</td></tr></table>
            """,
        )
        self.assertEqual(result[0].amount_per_unit, Decimal("1.26"))
        self.assertEqual(result[0].information_basis, "ACTUAL_AMOUNT_ONLY")

    def test_network_fetch_requires_explicit_permission(self) -> None:
        with self.assertRaisesRegex(ValueError, "allow_network=True"):
            fetch_uob_dividend_amounts(etf_code="00918")


if __name__ == "__main__":
    unittest.main()
