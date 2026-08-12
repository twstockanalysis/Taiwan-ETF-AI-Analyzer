"""測試 M11-5B 可重現本金風險警示。"""

import unittest
from datetime import date
from decimal import Decimal

from backend.app.models.target_analysis import TargetAnalysisWarningCode
from backend.app.services.principal_risk_warnings import (
    build_principal_risk_warnings,
)


class TestPrincipalRiskWarnings(unittest.TestCase):
    @staticmethod
    def _close(day: str, price: str) -> dict:
        return {
            "trade_date": day,
            "close_price": Decimal(price),
            "source_id": "twse_stock_day",
        }

    @staticmethod
    def _performance(return_pct: str = "-5") -> dict:
        return {
            "period_code": "1Y",
            "return_pct": Decimal(return_pct),
            "as_of_date": date(2026, 8, 7),
            "source_id": "twse_stock_day",
        }

    def test_emits_source_dated_negative_and_persistent_decline(self) -> None:
        warnings = build_principal_risk_warnings(
            etf_code="0056",
            analysis_date=date(2026, 8, 12),
            after_tax_total_return_pct=Decimal("-3.2"),
            selected_performance=self._performance(),
            daily_closes=[
                self._close("2026-05-29", "40"),
                self._close("2026-06-30", "38"),
                self._close("2026-07-31", "36"),
                self._close("2026-08-07", "35"),
            ],
            dividends=[],
            peer_performance=[],
        )
        self.assertEqual(
            [warning.code for warning in warnings],
            [
                TargetAnalysisWarningCode.NEGATIVE_TOTAL_RETURN,
                TargetAnalysisWarningCode.PERSISTENT_PRICE_DECLINE,
            ],
        )
        self.assertEqual(warnings[1].as_of_date, date(2026, 8, 7))
        self.assertEqual(warnings[1].source_id, "twse_stock_day")
        self.assertEqual(warnings[1].evidence["consecutive_months"], 3)

    def test_emits_weak_recovery_after_complete_sixty_day_window(self) -> None:
        warnings = build_principal_risk_warnings(
            etf_code="0056",
            analysis_date=date(2026, 8, 12),
            after_tax_total_return_pct=Decimal("1"),
            selected_performance=self._performance("1"),
            daily_closes=[
                self._close("2026-05-29", "40"),
                self._close("2026-06-01", "36"),
                self._close("2026-07-30", "39"),
            ],
            dividends=[
                {
                    "ex_dividend_date": date(2026, 6, 1),
                    "source_id": "twse_etf_dividend",
                }
            ],
            peer_performance=[],
        )
        self.assertEqual(len(warnings), 1)
        self.assertEqual(
            warnings[0].code, TargetAnalysisWarningCode.WEAK_PRICE_RECOVERY
        )
        self.assertEqual(warnings[0].evidence["window_days"], 60)
        self.assertEqual(
            warnings[0].evidence["dividend_source_id"], "twse_etf_dividend"
        )

    def test_emits_material_peer_underperformance_at_fixed_gap(self) -> None:
        peers = [
            {
                "etf_code": f"00{i}",
                "sort_return_pct": value,
                "sort_as_of_date": date(2026, 8, 7),
                "sort_source_id": "twse_stock_day",
            }
            for i, value in enumerate(["8", "10", "12", "14", "16"], 1)
        ]
        warnings = build_principal_risk_warnings(
            etf_code="0056",
            analysis_date=date(2026, 8, 12),
            after_tax_total_return_pct=Decimal("1"),
            selected_performance=self._performance("2"),
            daily_closes=[],
            dividends=[],
            peer_performance=peers,
        )
        self.assertEqual(len(warnings), 1)
        self.assertEqual(
            warnings[0].code,
            TargetAnalysisWarningCode.MATERIAL_PEER_UNDERPERFORMANCE,
        )
        self.assertEqual(warnings[0].evidence["peer_count"], 5)
        self.assertEqual(
            warnings[0].evidence["underperformance_gap_pct"], Decimal("10")
        )

    def test_missing_or_nonqualifying_facts_do_not_create_warning(self) -> None:
        warnings = build_principal_risk_warnings(
            etf_code="0056",
            analysis_date=date(2026, 8, 12),
            after_tax_total_return_pct=None,
            selected_performance=None,
            daily_closes=[],
            dividends=[],
            peer_performance=[],
        )
        self.assertEqual(warnings, [])


if __name__ == "__main__":
    unittest.main()
