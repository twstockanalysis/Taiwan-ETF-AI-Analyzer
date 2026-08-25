"""V3-4 多種配置結果服務測試。"""

from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from backend.app.models.allocation_results import AllocationResultsRequest
from backend.app.models.integer_allocation import (
    IntegerAllocationAssumptions,
    IntegerAllocationResponse,
)
from backend.app.services.allocation_results import build_allocation_results


_SNAPSHOT = "sha256:" + "a" * 64


def allocation_result(code: str) -> IntegerAllocationResponse:
    additions = []
    capital = Decimal("0")
    if code:
        additions = [
            {
                "etf_code": code,
                "name": f"ETF {code}",
                "additional_shares": 100,
                "reference_price": 20,
                "reference_price_as_of": "2026-01-01",
                "reference_price_source_id": "TEST",
                "estimated_transaction_cost": 0,
                "required_capital": 2000,
                "supported_target_months": [1],
            }
        ]
        capital = Decimal("2000")
    return IntegerAllocationResponse(
        status="TARGET_MET",
        optimality="BOUNDED_BEST_EFFORT" if code else "PROVED_OPTIMAL",
        analysis_date=date(2026, 1, 1),
        snapshot_id=_SNAPSHOT,
        target_after_tax_cash_twd=100,
        target_months=[1],
        assumptions=IntegerAllocationAssumptions(
            cash_deduction_rate_pct=0,
            max_candidate_allocation_pct=20,
        ),
        universe_count=3,
        eligible_count=3,
        additions=additions,
        total_required_additional_capital=capital,
        monthly_results=[
            {
                "month": 1,
                "current_after_tax_cash": 0,
                "added_after_tax_cash": 100,
                "modeled_after_tax_cash": 100,
                "target_after_tax_cash": 100,
                "shortfall": 0,
            }
        ],
    )


def candidate(code: str, total_return: str):
    return SimpleNamespace(
        quality_score=Decimal("80"),
        public_item=SimpleNamespace(
            etf_code=code,
            estimated_after_tax_total_return_pct=Decimal(total_return),
        ),
    )


class TestAllocationResults(unittest.TestCase):
    def setUp(self) -> None:
        self.request = AllocationResultsRequest(
            target_after_tax_cash_twd=100,
            target_months=[1],
            existing_holdings=[],
            history_years=3,
            cash_deduction_rate_pct=0,
        )
        self.candidates = (
            candidate("0050", "12"),
            candidate("0056", "8"),
            candidate("00878", "6"),
        )
        self.built_index = SimpleNamespace(
            response=SimpleNamespace(snapshot_id=_SNAPSHOT, candidates=[]),
            ranked_eligible_candidates=self.candidates,
        )

    @patch("backend.app.services.allocation_results._pair_overlap_averages")
    @patch("backend.app.services.allocation_results.build_integer_allocation")
    @patch("backend.app.services.allocation_results.build_market_eligibility_index")
    def test_returns_distinct_recommended_balanced_and_focused_plans(
        self,
        build_index,
        build_integer,
        pair_averages,
    ) -> None:
        build_index.return_value = self.built_index
        pair_averages.return_value = {
            "0050": Decimal("60"),
            "0056": Decimal("20"),
            "00878": Decimal("10"),
        }
        build_integer.side_effect = [
            allocation_result("0050"),
            allocation_result("00878"),
            allocation_result("0056"),
        ]

        response = build_allocation_results(
            self.request,
            Path("unused.db"),
            as_of_date=date(2026, 1, 1),
        )

        self.assertEqual(
            [plan.label for plan in response.plans],
            ["推薦配置", "平衡配置", "集中配置"],
        )
        serialized = str(response.model_dump(mode="json"))
        self.assertNotIn("quality_score", serialized)
        self.assertNotIn("confidence", serialized)

    @patch("backend.app.services.allocation_results._pair_overlap_averages")
    @patch("backend.app.services.allocation_results.build_integer_allocation")
    @patch("backend.app.services.allocation_results.build_market_eligibility_index")
    def test_returns_fewer_plans_instead_of_fabricating_styles(
        self,
        build_index,
        build_integer,
        pair_averages,
    ) -> None:
        build_index.return_value = self.built_index
        pair_averages.return_value = {}
        build_integer.return_value = allocation_result("0050")

        response = build_allocation_results(
            self.request,
            Path("unused.db"),
            as_of_date=date(2026, 1, 1),
        )

        self.assertEqual(len(response.plans), 1)
        self.assertIn(
            "ALTERNATIVE_OVERLAP_DATA_UNAVAILABLE",
            {issue.code for issue in response.strategy_issues},
        )


if __name__ == "__main__":
    unittest.main()
