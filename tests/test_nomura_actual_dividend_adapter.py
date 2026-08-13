"""野村投信官方 ETF 配息 API 測試。"""

import unittest
from decimal import Decimal

from backend.app.data_sources.nomura_actual_dividend_adapter import (
    fetch_nomura_dividend_amounts,
    parse_nomura_dividend_amounts,
)


class TestNomuraActualDividendAdapter(unittest.TestCase):
    def test_parses_actual_amount_and_dates(self) -> None:
        rows = parse_nomura_dividend_amounts(
            etf_code="00944",
            payload={"Entries": [{
                "CFundNo": "00944",
                "CShortName": "野村趨勢動能高息",
                "YieldData": [{
                    "CBaseDate": "2026/07",
                    "CValuationDate": "2026/06/30",
                    "CExDate": "2026/07/16",
                    "CPayableDate": "2026/08/13",
                    "CPerShare": "0.1090",
                    "CDvdSetting": 12,
                    "CCurrentDy": 0.00502,
                }],
            }]},
        )
        self.assertEqual(rows[0].amount_per_unit, Decimal("0.1090"))
        self.assertEqual(rows[0].distribution_rate_percent, Decimal("0.50200"))
        self.assertEqual(rows[0].frequency_per_year, 12)
        self.assertEqual(rows[0].information_basis, "ACTUAL_AMOUNT_ONLY")

    def test_ignores_non_target_entry(self) -> None:
        self.assertEqual(
            parse_nomura_dividend_amounts(
                etf_code="00944",
                payload={"Entries": [{"CFundNo": "00960", "YieldData": []}]},
            ),
            (),
        )

    def test_valid_empty_entries_are_supported(self) -> None:
        self.assertEqual(
            parse_nomura_dividend_amounts(
                etf_code="00999A", payload={"Entries": []},
            ),
            (),
        )

    def test_network_access_requires_explicit_opt_in(self) -> None:
        with self.assertRaisesRegex(ValueError, "allow_network=True"):
            fetch_nomura_dividend_amounts(etf_code="00944")


if __name__ == "__main__":
    unittest.main()
