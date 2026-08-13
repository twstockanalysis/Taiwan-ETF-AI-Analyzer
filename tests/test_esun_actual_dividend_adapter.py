"""玉山投信官方 ETF 配息 API 測試。"""

import unittest
from decimal import Decimal

from backend.app.data_sources.esun_actual_dividend_adapter import (
    fetch_esun_dividend_amounts,
    parse_esun_dividend_amounts,
)


class TestEsunActualDividendAdapter(unittest.TestCase):
    def test_maps_exchange_code_and_parses_actual_amount(self) -> None:
        rows = parse_esun_dividend_amounts(
            etf_code="009803",
            overview_payload={"Entries": [{"FundNo": "50", "StcokNo": "009803"}]},
            yield_payload={"Entries": [{
                "CNo": "50", "CFullName": "玉山臺灣市值動能50 ETF基金",
                "CInterestDt": "2026-05-29T00:00:00",
                "CLastSubscriptionDt": "2026-06-12T00:00:00",
                "CExDividendDt": "2026-06-15T00:00:00",
                "CReleaseDt": "2026-07-07T00:00:00",
                "CInterestOfUnit": "0.50", "CInterestOfMonth": "2.32%",
                "CCgDividendTypeStr": "季配型",
            }]},
        )
        self.assertEqual(rows[0].fund_no, "50")
        self.assertEqual(rows[0].amount_per_unit, Decimal("0.50"))
        self.assertEqual(rows[0].distribution_rate_percent, Decimal("2.32"))
        self.assertEqual(rows[0].information_basis, "ACTUAL_AMOUNT_ONLY")

    def test_ignores_other_fund_histories(self) -> None:
        self.assertEqual(parse_esun_dividend_amounts(
            etf_code="009803",
            overview_payload={"Entries": [{"FundNo": "50", "StcokNo": "009803"}]},
            yield_payload={"Entries": [{"CNo": "52"}]},
        ), ())

    def test_unknown_exchange_code_returns_empty(self) -> None:
        self.assertEqual(parse_esun_dividend_amounts(
            etf_code="009999", overview_payload={"Entries": []},
            yield_payload={"Entries": []},
        ), ())

    def test_network_access_requires_explicit_opt_in(self) -> None:
        with self.assertRaisesRegex(ValueError, "allow_network=True"):
            fetch_esun_dividend_amounts(etf_code="009803")


if __name__ == "__main__":
    unittest.main()
