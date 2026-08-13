"""街口投信官方 ETF 收益分配資格測試。"""

import unittest

from backend.app.data_sources.jko_dividend_eligibility_adapter import (
    fetch_jko_dividend_eligibility,
    parse_jko_dividend_eligibility,
)


class TestJKODividendEligibilityAdapter(unittest.TestCase):
    def test_parses_official_no_distribution_status(self) -> None:
        result = parse_jko_dividend_eligibility(
            etf_code="00693U",
            source_url="https://ec.jkoam.com/EventArea/promote-00693u.php",
            html_text="<table><tr><td>收益分配</td><td>無</td></tr></table>",
        )
        self.assertFalse(result.distributes_income)
        self.assertEqual(result.official_value, "無")
        self.assertEqual(result.information_basis, "OFFICIAL_PRODUCT_TERMS")

    def test_changed_status_requires_new_verification(self) -> None:
        with self.assertRaisesRegex(ValueError, "需要重新驗證"):
            parse_jko_dividend_eligibility(
                etf_code="00693U",
                source_url="https://ec.jkoam.com/EventArea/promote-00693u.php",
                html_text="<td>收益分配</td><td>年配</td>",
            )

    def test_unknown_product_is_not_assumed_non_distributing(self) -> None:
        with self.assertRaisesRegex(ValueError, "尚未驗證"):
            fetch_jko_dividend_eligibility(
                etf_code="00999", allow_network=True,
            )

    def test_network_access_requires_explicit_opt_in(self) -> None:
        with self.assertRaisesRegex(ValueError, "allow_network=True"):
            fetch_jko_dividend_eligibility(etf_code="00693U")


if __name__ == "__main__":
    unittest.main()
