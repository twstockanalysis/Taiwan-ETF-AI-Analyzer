"""復華投信官方 ETF 配息 Adapter 測試。"""

import unittest
from decimal import Decimal

from backend.app.data_sources.fuh_hwa_actual_dividend_adapter import (
    fetch_fuh_hwa_dividend_amounts,
    parse_fuh_hwa_dividend_amounts,
    parse_fuh_hwa_internal_id,
)


class TestFuhHwaActualDividendAdapter(unittest.TestCase):
    def test_resolves_official_internal_id(self) -> None:
        html = '<option value="ETF21"> 00929_復華台灣科技優息 </option>'
        self.assertEqual(
            parse_fuh_hwa_internal_id(etf_code="00929", html_text=html),
            "ETF21",
        )

    def test_parses_history_and_builds_composition_url(self) -> None:
        rows = parse_fuh_hwa_dividend_amounts(
            etf_code="00929",
            internal_id="ETF21",
            html_text='''<tr class="fundListTable-fundCard">
            <td>00929</td><td><p>復華台灣科技優息ETF基金</p></td>
            <td>0.3800</td><td>1.36%</td><td>-8.36%</td>
            <td>2026/07/21</td><td>2026/08/14</td><td>新臺幣</td><td>月配</td></tr>''',
        )
        self.assertEqual(rows[0].amount_per_unit, Decimal("0.3800"))
        self.assertEqual(rows[0].distribution_rate_percent, Decimal("1.36"))
        self.assertTrue(rows[0].composition_document_url.endswith("/202606/ETF21_A.pdf"))
        self.assertEqual(rows[0].information_basis, "ACTUAL_AMOUNT_ONLY")

    def test_ignores_other_etf_rows(self) -> None:
        result = parse_fuh_hwa_dividend_amounts(
            etf_code="00929", internal_id="ETF21",
            html_text='<tr class="fundListTable-fundCard"><td>00731</td></tr>',
        )
        self.assertEqual(result, ())

    def test_network_access_requires_explicit_opt_in(self) -> None:
        with self.assertRaisesRegex(ValueError, "allow_network=True"):
            fetch_fuh_hwa_dividend_amounts(etf_code="00929")


if __name__ == "__main__":
    unittest.main()
