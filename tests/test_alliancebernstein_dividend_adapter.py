import unittest
from decimal import Decimal

from backend.app.data_sources.alliancebernstein_dividend_adapter import (
    fetch_alliancebernstein_dividends, parse_alliancebernstein_dividends,
    resolve_alliancebernstein_isin,
)


class TestAllianceBernsteinDividendAdapter(unittest.TestCase):
    def test_accepts_valid_pre_distribution_response(self) -> None:
        result = parse_alliancebernstein_dividends(
            isin="TW00000404A5",
            payload={"asOfDate": None, "nextDistributionDate": "2026-09-15T00:00:00", "distributions": []},
        )
        self.assertEqual(result.distributions, ())
        self.assertEqual(result.next_distribution_date.isoformat(), "2026-09-15")

    def test_parses_actual_amount_without_composition_inference(self) -> None:
        result = parse_alliancebernstein_dividends(
            isin="TW00000404A5",
            payload={"asOfDate": "2026-10-01T00:00:00", "nextDistributionDate": None, "distributions": [{"exDate": "2026-09-15T00:00:00", "payDate": "2026-10-08T00:00:00", "distributionValue": 0.25, "distributionYield": 1.2}]},
        )
        self.assertEqual(result.distributions[0].amount_per_unit, Decimal("0.25"))
        self.assertEqual(result.distributions[0].information_basis, "ACTUAL_AMOUNT_ONLY")

    def test_network_fetch_requires_explicit_permission(self) -> None:
        with self.assertRaisesRegex(ValueError, "allow_network=True"):
            fetch_alliancebernstein_dividends(etf_code="00404A")

    def test_resolves_isin_from_official_fund_link(self) -> None:
        isin = resolve_alliancebernstein_isin(
            etf_code="00404A",
            html_text="""
            <a href="/fund/active-etf.-.TW00000404A5.html">00404A 檔案</a>
            """,
        )
        self.assertEqual(isin, "TW00000404A5")


if __name__ == "__main__":
    unittest.main()
