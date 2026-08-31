"""Tests for the immutable V5 planner replay evidence helper."""

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from deployment.v5_planner_replay import replay_frozen_planner_cases


def _value(value: str) -> SimpleNamespace:
    return SimpleNamespace(value=value)


class V5PlannerReplayTests(unittest.TestCase):
    def test_replays_all_frozen_cases_and_serializes_key_evidence(self) -> None:
        result = SimpleNamespace(
            status=_value("TARGET_MET"),
            optimality=_value("BOUNDED_BEST_EFFORT"),
            universe_count=261,
            eligible_count=47,
            total_required_additional_capital="123.45",
            additions=[
                SimpleNamespace(
                    etf_code="0056",
                    additional_shares=3,
                    required_capital="99.00",
                    supported_target_months=[1, 4],
                )
            ],
            monthly_results=[
                SimpleNamespace(
                    month=1,
                    current_after_tax_cash="0.00",
                    added_after_tax_cash="100.00",
                    shortfall="0.00",
                )
            ],
            issues=[],
        )
        response = SimpleNamespace(
            snapshot_id="sha256:test-snapshot",
            plans=[SimpleNamespace(strategy=_value("RECOMMENDED"), result=result)],
            excluded_candidates=[],
            strategy_issues=[],
        )

        with TemporaryDirectory() as temporary_directory:
            database = Path(temporary_directory) / "candidate.db"
            database.write_bytes(b"immutable-v5-candidate")
            with patch(
                "deployment.v5_planner_replay.build_allocation_results",
                return_value=response,
            ) as build:
                report = replay_frozen_planner_cases(
                    database,
                    evaluated_on=date(2026, 8, 30),
                )

        self.assertEqual(build.call_count, 4)
        self.assertEqual(report["evaluated_on"], "2026-08-30")
        self.assertEqual(len(report["cases"]), 4)
        self.assertEqual(report["cases"][0]["case_id"], "zero_holdings")
        self.assertEqual(report["cases"][0]["eligible_count"], 47)
        self.assertEqual(
            report["cases"][0]["additions"][0]["additional_shares"],
            3,
        )
        self.assertEqual(
            report["cases"][0]["request"]["target_months"],
            [1, 4, 7, 10],
        )
        self.assertEqual(len(report["database"]["sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
