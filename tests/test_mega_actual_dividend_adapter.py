"""兆豐投信官方 ETF 歷史配息 Adapter 測試。"""

import unittest
from decimal import Decimal

from backend.app.data_sources.mega_actual_dividend_adapter import (
    fetch_mega_dividend_amounts,
    parse_mega_dividend_amounts,
    parse_mega_fund_mapping,
)


class TestMegaActualDividendAdapter(unittest.TestCase):
    def test_resolves_code_to_internal_id_by_official_name(self) -> None:
        mapping = parse_mega_fund_mapping(
            etf_code="00690",
            catalog_html='''<div class="product-detail" data-uid="5">
            <div class="detail-item">00690</div><div class="detail-item">
            <a href="etf_product.aspx?id=5">兆豐臺灣藍籌30ETF基金</a></div></div>''',
            dividend_html='''<select><option selected="selected" value="X001">
            兆豐臺灣藍籌30ETF基金</option></select>''',
        )

        self.assertEqual(mapping.internal_id, "X001")
        self.assertEqual(mapping.etf_code, "00690")

    def test_ignores_official_disclosure_suffix_when_joining_names(self) -> None:
        mapping = parse_mega_fund_mapping(
            etf_code="00982T",
            catalog_html='''<div class="product-detail"><div class="detail-item">
            00982T</div><div class="detail-item">兆豐台美動能股債平衡ETF基金
            (基金之配息來源可能為收益平準金)</div></div>''',
            dividend_html='''<option value="X009">
            兆豐台美動能股債平衡ETF基金</option>''',
        )

        self.assertEqual(mapping.internal_id, "X009")

    def test_parses_amount_and_keeps_missing_composition_empty(self) -> None:
        rows = parse_mega_dividend_amounts(
            etf_code="00690",
            html_text='''<table><tr class="tr-est">
            <td>115年</td><td>2026/05/19</td><td>1.40</td><td>1.95</td>
            <td>2026/05/22</td><td>4</td><td>-</td><td>-</td></tr></table>''',
        )

        self.assertEqual(rows[0].amount_per_unit, Decimal("1.40"))
        self.assertEqual(rows[0].yield_percent, Decimal("1.95"))
        self.assertIsNone(rows[0].dividend_54c_amount)
        self.assertIsNone(rows[0].interest_5a_amount)
        self.assertEqual(rows[0].information_basis, "ACTUAL_AMOUNT_ONLY")

    def test_preserves_official_54c_and_5a_amounts(self) -> None:
        rows = parse_mega_dividend_amounts(
            etf_code="00690",
            html_text='''<tr class="tr-est"><td>115年</td><td>2026/08/19</td>
            <td>1.50</td><td>2.00</td><td>-</td><td>-</td>
            <td>0.40</td><td>0.10</td></tr>''',
        )

        self.assertEqual(rows[0].dividend_54c_amount, Decimal("0.40"))
        self.assertEqual(rows[0].interest_5a_amount, Decimal("0.10"))

    def test_new_fund_may_have_valid_empty_history(self) -> None:
        self.assertEqual(
            parse_mega_dividend_amounts(etf_code="00924", html_text="<table></table>"),
            (),
        )

    def test_network_access_requires_explicit_opt_in(self) -> None:
        with self.assertRaisesRegex(ValueError, "allow_network=True"):
            fetch_mega_dividend_amounts(etf_code="00690")


if __name__ == "__main__":
    unittest.main()
