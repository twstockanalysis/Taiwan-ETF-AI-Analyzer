"""V3-6 整體組合稅務與再投入純計算測試。"""

from decimal import Decimal
from datetime import date
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from backend.app.database.connection import get_connection
from backend.app.database.init_db import initialize_database
from backend.app.models.portfolio_projection import (
    DividendTaxMethod,
    PortfolioHoldingTaxFact,
    PortfolioProjectionRequest,
)
from backend.app.models.tax_reinvestment import (
    ComponentCalculationBasis,
    OfficialComponentAllocation,
    ReinvestmentPolicy,
)
from backend.app.services.portfolio_projection import (
    _HoldingState,
    _annual_tax,
    _holding_fact,
    _project_policy,
)


def _request(**changes) -> PortfolioProjectionRequest:
    values = {
        "target_after_tax_cash_twd": 10_000,
        "target_months": [1],
        "existing_holdings": [],
        "history_years": 3,
        "cash_deduction_rate_pct": 0,
        "projection_years": 1,
        "custom_reinvestment_pct": 50,
        "dividend_tax_method": "COMBINED_WITH_CREDIT",
        "marginal_income_tax_rate_pct": 20,
        "other_income_tax_rate_pct": 0,
        "remaining_annual_dividend_credit_cap_twd": 80_000,
        "supplementary_premium_exempt": False,
    }
    values.update(changes)
    return PortfolioProjectionRequest(**values)


def _fact(mix, payments: int = 4) -> PortfolioHoldingTaxFact:
    return PortfolioHoldingTaxFact(
        etf_code="0050",
        units=1000,
        initial_unit_price=1000,
        initial_value=1_000_000,
        annual_gross_distribution_rate_pct=10,
        annual_gross_distribution_cash=100_000,
        estimated_payments_per_year=payments,
        component_calculation_basis=ComponentCalculationBasis.ACTUAL,
        calculation_component_mix=mix,
    )


class TestPortfolioProjection(unittest.TestCase):
    def test_official_76w_is_excluded_from_personal_tax_and_premium(self) -> None:
        fact = _fact(
            [
                OfficialComponentAllocation(component_code="54C", ratio_pct=50),
                OfficialComponentAllocation(component_code="76W", ratio_pct=50),
            ]
        )
        tax, premium, gross = _annual_tax(
            [_HoldingState(fact=fact, units=fact.units, price=fact.initial_unit_price)],
            _request(),
        )

        self.assertEqual(gross, [Decimal("100000")])
        self.assertEqual(tax, Decimal("5750"))
        self.assertEqual(premium, Decimal("0"))

    def test_supplementary_premium_uses_estimated_per_payment_threshold(self) -> None:
        fact = _fact(
            [OfficialComponentAllocation(component_code="54C", ratio_pct=100)]
        )
        _, premium, _ = _annual_tax(
            [_HoldingState(fact=fact, units=fact.units, price=fact.initial_unit_price)],
            _request(
                marginal_income_tax_rate_pct=0,
                remaining_annual_dividend_credit_cap_twd=0,
            ),
        )

        self.assertEqual(premium, Decimal("2110.0000"))

    def test_reinvested_cash_is_not_counted_twice_in_total_return(self) -> None:
        fact = _fact(
            [OfficialComponentAllocation(component_code="54C", ratio_pct=100)]
        )
        request = _request(
            marginal_income_tax_rate_pct=0,
            remaining_annual_dividend_credit_cap_twd=0,
        )
        no_reinvestment = _project_policy(
            [fact], request, Decimal("10"), Decimal("10"), Decimal("10000"),
            ReinvestmentPolicy.NO_REINVESTMENT,
        )
        full_reinvestment = _project_policy(
            [fact], request, Decimal("10"), Decimal("10"), Decimal("10000"),
            ReinvestmentPolicy.FULL_REINVESTMENT,
        )

        self.assertEqual(no_reinvestment.after_tax_total_gain_loss, Decimal("97890.00"))
        self.assertEqual(full_reinvestment.after_tax_total_gain_loss, Decimal("97890.00"))
        self.assertEqual(full_reinvestment.usable_cash, Decimal("0.00"))
        self.assertEqual(full_reinvestment.ending_value, Decimal("1097890.00"))

    def test_separate_dividend_method_uses_28_percent_without_credit(self) -> None:
        fact = _fact(
            [OfficialComponentAllocation(component_code="54C", ratio_pct=100)]
        )
        tax, _, _ = _annual_tax(
            [_HoldingState(fact=fact, units=fact.units, price=fact.initial_unit_price)],
            _request(
                dividend_tax_method=DividendTaxMethod.SEPARATE_28,
                marginal_income_tax_rate_pct=0,
            ),
        )
        self.assertEqual(tax, Decimal("28000"))

    def test_holding_fact_prefers_actual_mix_and_preserves_explicit_76w_zero(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "fact.db"
            initialize_database(database_path)
            connection = get_connection(database_path)
            try:
                connection.execute(
                    "INSERT INTO etf_master (code, name, is_active, is_bond) "
                    "VALUES ('0050', '元大台灣50', 0, 0);"
                )
                for year in (2024, 2025, 2026):
                    cursor = connection.execute(
                        "INSERT INTO etf_dividend "
                        "(etf_code, source_event_id, payment_date, amount_per_unit, "
                        "currency, source_id) VALUES ('0050', ?, ?, 10, 'TWD', 'TEST');",
                        (f"event-{year}", f"{year}-01-10"),
                    )
                    if year == 2026:
                        dividend_id = cursor.lastrowid
                        connection.execute(
                            "INSERT INTO etf_dividend_component "
                            "(dividend_id, component_code, component_basis, ratio_pct, "
                            "source_id) VALUES (?, '54C', 'ACTUAL', 100, 'TEST');",
                            (dividend_id,),
                        )
                        connection.execute(
                            "INSERT INTO etf_dividend_component "
                            "(dividend_id, component_code, component_basis, ratio_pct, "
                            "source_id) VALUES (?, '76W', 'ACTUAL', 0, 'TEST');",
                            (dividend_id,),
                        )
                connection.commit()
            finally:
                connection.close()

            fact = _holding_fact(
                SimpleNamespace(
                    etf_code="0050",
                    resulting_value=100_000,
                    resulting_shares=1000,
                    reference_price=100,
                ),
                _request(history_years=3),
                database_path,
                date(2026, 8, 25),
            )

        self.assertEqual(fact.component_calculation_basis, "ACTUAL")
        self.assertEqual(fact.annual_gross_distribution_cash, Decimal("10000.00"))
        self.assertEqual(
            [(item.component_code, item.ratio_pct) for item in fact.calculation_component_mix],
            [("54C", Decimal("100.0")), ("76W", Decimal("0.0"))],
        )


if __name__ == "__main__":
    unittest.main()
