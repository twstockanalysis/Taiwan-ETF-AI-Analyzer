"""永豐投信官方 ETF 配息 Adapter 測試。"""

import unittest
from decimal import Decimal

from backend.app.data_sources.sinopac_actual_dividend_adapter import (
    fetch_sinopac_dividend_amounts,
    parse_sinopac_dividend_amounts,
    parse_sinopac_fund_mapping,
)


class TestSinopacActualDividendAdapter(unittest.TestCase):
    def test_resolves_code_to_exact_internal_id(self) -> None:
        mapping = parse_sinopac_fund_mapping(
            etf_code="00930",
            html_text='''<script>if (u.attr("id") != 'B5') { u.remove(); }</script>
            永豐台灣ESG低碳高息40ETF基金（證劵代碼：00930）2026/08/13''',
        )
        self.assertEqual(mapping.fund_id, "B5")
        self.assertEqual(mapping.etf_code, "00930")

    def test_parses_amount_dates_and_principal_split(self) -> None:
        rows = parse_sinopac_dividend_amounts(
            etf_code="00930",
            html_text='''<table id="divtable"><tbody><tr>
            <td>永豐ESG低碳高息</td><td>0.2500</td><td>2026/06/30</td>
            <td>2026/07/27</td><td>2026/08/02</td><td>2026/08/20</td>
            <td>雙月配</td><td>75.00</td><td>25.00</td></tr></tbody></table>''',
        )
        self.assertEqual(rows[0].amount_per_unit, Decimal("0.2500"))
        self.assertEqual(rows[0].distributable_income_percent, Decimal("75.00"))
        self.assertEqual(rows[0].principal_percent, Decimal("25.00"))
        self.assertEqual(
            rows[0].information_basis, "ACTUAL_AMOUNT_AND_PRINCIPAL_SPLIT",
        )

    def test_valid_empty_history_is_supported(self) -> None:
        self.assertEqual(
            parse_sinopac_dividend_amounts(
                etf_code="00999", html_text='<table id="divtable"></table>',
            ),
            (),
        )

    def test_network_access_requires_explicit_opt_in(self) -> None:
        with self.assertRaisesRegex(ValueError, "allow_network=True"):
            fetch_sinopac_dividend_amounts(etf_code="00930")


if __name__ == "__main__":
    unittest.main()
