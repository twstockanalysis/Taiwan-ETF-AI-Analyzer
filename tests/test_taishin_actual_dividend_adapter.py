"""台新投信官方歷史配息組成表測試。"""

import unittest
from decimal import Decimal

from backend.app.data_sources.taishin_actual_dividend_adapter import (
    fetch_taishin_dividend_compositions,
    parse_taishin_dividend_compositions,
)


class TestTaishinActualDividendAdapter(unittest.TestCase):
    HTML = """
    <div class="card-header SeriesName" id="00936">台新 ETF (00936)</div>
    <table><tbody><tr>
      <td>2024 / 05</td><td>月配</td>
      <td>2024/5/31<br>2024/6/18</td><td>0.25</td><td>1.35</td>
      <td>7.32</td><td>92.68</td><td>0.00</td><td>0.00</td>
      <td>2024/7/8</td>
    </tr></tbody></table>
    <div class="card-header SeriesName" id="00942B">other</div>
    """

    def test_parses_amount_dates_and_actual_composition(self) -> None:
        result = parse_taishin_dividend_compositions(
            etf_code="00936", html_text=self.HTML
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].amount_per_unit, Decimal("0.25"))
        self.assertEqual(result[0].dividend_interest_percent, Decimal("7.32"))
        self.assertEqual(result[0].capital_gain_percent, Decimal("92.68"))
        self.assertEqual(result[0].payment_date.isoformat(), "2024-07-08")
        self.assertEqual(result[0].information_basis, "ACTUAL")

    def test_rejects_invalid_percentage_total(self) -> None:
        with self.assertRaisesRegex(ValueError, "100%"):
            parse_taishin_dividend_compositions(
                etf_code="00936", html_text=self.HTML.replace("92.68", "90")
            )

    def test_network_fetch_requires_explicit_permission(self) -> None:
        with self.assertRaisesRegex(ValueError, "allow_network=True"):
            fetch_taishin_dividend_compositions(etf_code="00936")


if __name__ == "__main__":
    unittest.main()
