"""M11-2 目前持倉整體分析服務測試。"""

from datetime import date, datetime
from decimal import Decimal
from unittest import TestCase
from unittest.mock import patch

from backend.app.models.target_analysis import (
    TargetAnalysisStatus,
    TargetAnalysisUnavailableField,
    TargetAnalysisWarning,
    TargetAnalysisWarningCode,
)
from backend.app.services.current_holding_analysis import (
    analyze_current_holdings,
    annualize_price_return,
)
from backend.app.services.target_analysis_data import TargetAnalysisData


def _conditions(deduction: str | None = "10") -> dict:
    return {
        "monthly_after_tax_target": Decimal("1000"),
        "analysis_years": 5,
        "history_years": 3,
        "cash_deduction_rate_pct": (
            Decimal(deduction) if deduction is not None else None
        ),
        "currency": "TWD",
        "updated_at": datetime(2026, 8, 9, 12, 0),
    }


def _holding(code: str, price: str) -> dict:
    return {
        "etf_code": code,
        "name": f"ETF {code}",
        "is_active": False,
        "is_bond": False,
        "held_units": 100,
        "unit_price": Decimal(price),
        "price_as_of_date": None,
        "currency": "TWD",
        "updated_at": datetime(2026, 8, 9, 12, 0),
    }


def _data(
    total_per_unit: str | None,
    period: str | None,
    return_pct: str | None,
) -> TargetAnalysisData:
    performance = None
    if period is not None and return_pct is not None:
        performance = {
            "period_code": period,
            "return_pct": Decimal(return_pct),
            "as_of_date": date(2026, 8, 9),
        }
    return TargetAnalysisData(
        monthly_income={
            "analysis_currency": "TWD",
            "has_mixed_currencies": False,
            "window_start_date": date(2023, 8, 9),
            "as_of_date": date(2026, 8, 9),
            "total_amount_per_unit": (
                Decimal(total_per_unit) if total_per_unit is not None else None
            ),
        },
        dividends=[],
        selected_performance=performance,
        warnings=[],
        unavailable_fields=[],
    )


class TestCurrentHoldingAnalysis(TestCase):
    def test_period_return_is_annualized_before_portfolio_weighting(self):
        self.assertEqual(
            annualize_price_return(
                {"period_code": "3Y", "return_pct": Decimal("33.1")}
            ),
            Decimal("10.000000"),
        )

    @patch(
        "backend.app.services.current_holding_analysis.load_target_analysis_data"
    )
    @patch(
        "backend.app.services.current_holding_analysis.list_manual_holdings"
    )
    @patch(
        "backend.app.services.current_holding_analysis.get_user_conditions"
    )
    def test_aggregates_holdings_and_runs_one_portfolio_target(
        self,
        get_conditions,
        list_holdings,
        load_data,
    ):
        get_conditions.return_value = _conditions()
        list_holdings.return_value = [
            _holding("0056", "10"),
            _holding("00878", "20"),
        ]
        load_data.side_effect = [
            _data("6", "3Y", "33.1"),
            _data("12", "1Y", "20"),
        ]

        result = analyze_current_holdings(
            "ignored.db",
            as_of_date=date(2026, 8, 9),
        )

        self.assertEqual(result.status, TargetAnalysisStatus.AVAILABLE)
        self.assertEqual(result.total_current_value, Decimal("3000"))
        self.assertEqual(
            [item.annual_gross_distribution_cash for item in result.holdings],
            [Decimal("200"), Decimal("400")],
        )
        self.assertEqual(
            result.portfolio_analysis.cash_flow.gross_distribution_cash,
            Decimal("600.00"),
        )
        self.assertEqual(
            result.portfolio_analysis.cash_flow.after_tax_usable_cash,
            Decimal("540.00"),
        )
        self.assertEqual(
            result.portfolio_analysis.scenario_estimate.ending_holding_value,
            Decimal("6484.18"),
        )
        self.assertEqual(load_data.call_count, 2)

    @patch(
        "backend.app.services.current_holding_analysis.load_target_analysis_data"
    )
    @patch(
        "backend.app.services.current_holding_analysis.list_manual_holdings"
    )
    @patch(
        "backend.app.services.current_holding_analysis.get_user_conditions"
    )
    def test_missing_one_holding_input_does_not_become_partial_zero(
        self,
        get_conditions,
        list_holdings,
        load_data,
    ):
        get_conditions.return_value = _conditions(None)
        list_holdings.return_value = [_holding("0056", "10")]
        missing = _data("6", None, None)
        missing.warnings.append(
            TargetAnalysisWarning(
                code=TargetAnalysisWarningCode.INSUFFICIENT_PERFORMANCE_HISTORY,
                message="沒有價格報酬資料。",
                affected_fields=["performance_return_pct"],
            )
        )
        missing.unavailable_fields.append(
            TargetAnalysisUnavailableField(
                field="performance_return_pct",
                reason="沒有價格報酬資料",
            )
        )
        load_data.return_value = missing

        result = analyze_current_holdings("ignored.db")

        self.assertEqual(result.status, TargetAnalysisStatus.PARTIAL)
        self.assertIsNone(
            result.portfolio_analysis.scenario_estimate.ending_holding_value
        )
        self.assertIsNone(
            result.portfolio_analysis.cash_flow.after_tax_usable_cash
        )
        fields = {item.field for item in result.unavailable_fields}
        self.assertIn("holdings.0056.performance_return_pct", fields)
        self.assertIn("ending_holding_value", fields)

    @patch(
        "backend.app.services.current_holding_analysis.load_target_analysis_data"
    )
    @patch(
        "backend.app.services.current_holding_analysis.list_manual_holdings"
    )
    @patch(
        "backend.app.services.current_holding_analysis.get_user_conditions"
    )
    def test_non_twd_distribution_is_not_added_to_twd_portfolio(
        self,
        get_conditions,
        list_holdings,
        load_data,
    ):
        get_conditions.return_value = _conditions("0")
        list_holdings.return_value = [_holding("0056", "10")]
        usd_data = _data("6", "1Y", "5")
        usd_data.monthly_income["analysis_currency"] = "USD"
        load_data.return_value = usd_data

        result = analyze_current_holdings("ignored.db")

        self.assertEqual(result.status, TargetAnalysisStatus.PARTIAL)
        self.assertIsNone(
            result.holdings[0].annual_gross_distribution_cash
        )
        self.assertIn(
            TargetAnalysisWarningCode.MIXED_CURRENCY,
            {item.code for item in result.holdings[0].warnings},
        )
        self.assertIsNone(
            result.portfolio_analysis.cash_flow.gross_distribution_cash
        )

    @patch(
        "backend.app.services.current_holding_analysis.load_target_analysis_data"
    )
    @patch(
        "backend.app.services.current_holding_analysis.list_manual_holdings"
    )
    @patch(
        "backend.app.services.current_holding_analysis.get_user_conditions"
    )
    def test_missing_official_close_blocks_value_dependent_result(
        self,
        get_conditions,
        list_holdings,
        load_data,
    ):
        get_conditions.return_value = _conditions()
        holding = _holding("0056", "10")
        holding["unit_price"] = None
        holding["price_as_of_date"] = None
        holding["price_source_id"] = None
        list_holdings.return_value = [holding]
        load_data.return_value = _data("6", "1Y", "5")

        result = analyze_current_holdings("ignored.db")

        self.assertEqual(result.status, TargetAnalysisStatus.PARTIAL)
        self.assertIsNone(result.total_current_value)
        self.assertIsNone(result.holdings[0].current_value)
        self.assertIsNone(result.portfolio_analysis)
        self.assertIn(
            "total_current_value",
            {item.field for item in result.unavailable_fields},
        )

    @patch(
        "backend.app.services.current_holding_analysis.list_manual_holdings",
        return_value=[],
    )
    @patch(
        "backend.app.services.current_holding_analysis.get_user_conditions",
        return_value=None,
    )
    def test_missing_conditions_returns_explicit_unavailable(
        self,
        _get_conditions,
        _list_holdings,
    ):
        result = analyze_current_holdings("ignored.db")
        self.assertEqual(result.status, TargetAnalysisStatus.UNAVAILABLE)
        self.assertIsNone(result.portfolio_analysis)
        self.assertEqual(result.unavailable_fields[0].field, "conditions")

    @patch(
        "backend.app.services.current_holding_analysis.list_manual_holdings",
        return_value=[],
    )
    @patch(
        "backend.app.services.current_holding_analysis.get_user_conditions",
        return_value=_conditions(),
    )
    def test_missing_holdings_returns_explicit_unavailable(
        self,
        _get_conditions,
        _list_holdings,
    ):
        result = analyze_current_holdings("ignored.db")
        self.assertEqual(result.status, TargetAnalysisStatus.UNAVAILABLE)
        self.assertEqual(result.unavailable_fields[0].field, "holdings")
