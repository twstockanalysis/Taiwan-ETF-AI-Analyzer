"""Tests for the V5 full-database and planner readiness audit."""

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from backend.app.database.connection import get_connection
from backend.app.database.init_db import initialize_database
from deployment.v5_full_database_audit import (
    _reference_etf_evidence,
    _request,
    _summarize_case,
    _summarize_case_safely,
    build_audit_cases,
)


def _value(value: str) -> SimpleNamespace:
    return SimpleNamespace(value=value)


class V5FullDatabaseAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.database = Path(self.temporary_directory.name) / "audit.db"
        initialize_database(self.database)
        connection = get_connection(self.database)
        try:
            connection.executemany(
                """
                INSERT INTO etf_master (
                    code, name, is_active, is_bond, listing_date
                ) VALUES (?, ?, ?, 0, '2020-01-01');
                """,
                [
                    ("0050", "ETF 0050", 0),
                    ("00878", "ETF 00878", 0),
                    ("00929", "ETF 00929", 0),
                    ("00632R", "ETF 00632R", 0),
                    ("MISSING", "Missing price ETF", 0),
                ],
            )
            connection.executemany(
                """
                INSERT INTO etf_daily_close (
                    etf_code, trade_date, close_price, source_id
                ) VALUES (?, '2026-09-01', 10, 'TEST');
                """,
                [
                    ("0050",),
                    ("00878",),
                    ("00929",),
                    ("00632R",),
                ],
            )
            connection.commit()
        finally:
            connection.close()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_builds_complete_matrix_and_selects_missing_price_case(self) -> None:
        cases = build_audit_cases(self.database)

        self.assertEqual(len(cases), 8)
        self.assertEqual(cases[0][0], "zero_holdings_quarterly_100")
        self.assertEqual(cases[3][0], "zero_holdings_all_months_3000")
        self.assertEqual(
            cases[-1][1].existing_holdings[0].etf_code,
            "MISSING",
        )

    def test_case_summary_keeps_all_exclusions_and_five_etf_gate(self) -> None:
        additions = [
            SimpleNamespace(
                etf_code=f"ETF{index}",
                additional_shares=index,
                required_capital="100",
                supported_target_months=[1],
            )
            for index in range(1, 7)
        ]
        result = SimpleNamespace(
            status=_value("TARGET_MET"),
            optimality=_value("BOUNDED_BEST_EFFORT"),
            universe_count=263,
            eligible_count=47,
            total_required_additional_capital="600",
            additions=additions,
            monthly_results=[
                SimpleNamespace(
                    month=1,
                    current_after_tax_cash="0",
                    added_after_tax_cash="100",
                    shortfall="0",
                )
            ],
            issues=[],
        )
        response = SimpleNamespace(
            snapshot_id="sha256:test",
            plans=[SimpleNamespace(strategy=_value("RECOMMENDED"), result=result)],
            excluded_candidates=[
                SimpleNamespace(
                    reasons=[
                        SimpleNamespace(
                            kind=_value("EXCLUDE"),
                            code="STALE_DATA",
                        ),
                        SimpleNamespace(
                            kind=_value("EXCLUDE"),
                            code="MISSING_REFERENCE_PRICE",
                        ),
                    ]
                ),
                SimpleNamespace(
                    reasons=[
                        SimpleNamespace(
                            kind=_value("EXCLUDE"),
                            code="STALE_DATA",
                        )
                    ]
                ),
            ],
            strategy_issues=[],
        )

        with patch(
            "deployment.v5_full_database_audit.build_allocation_results",
            return_value=response,
        ):
            summary = _summarize_case(
                "case",
                _request("100", [1], []),
                self.database,
                date(2026, 9, 1),
            )

        self.assertEqual(summary["added_etf_count"], 6)
        self.assertFalse(summary["within_v5_max_five_added_etfs"])
        self.assertEqual(
            summary["exclusion_codes"][0],
            {"code": "STALE_DATA", "count": 2},
        )
        self.assertEqual(len(summary["exclusion_codes"]), 2)

    def test_safe_case_summary_records_allocator_exception(self) -> None:
        with patch(
            "deployment.v5_full_database_audit.build_allocation_results",
            side_effect=AttributeError("zero overlap cannot be quantized"),
        ):
            summary = _summarize_case_safely(
                "case",
                _request("100", [1], []),
                self.database,
                date(2026, 9, 1),
            )

        self.assertEqual(summary["status"], "ERROR")
        self.assertEqual(summary["plan_count"], 0)
        self.assertEqual(summary["eligible_count"], 0)
        self.assertEqual(summary["error"]["type"], "AttributeError")
        self.assertIn("zero overlap", summary["error"]["message"])

    def test_00929_evidence_separates_paid_and_future_payments(self) -> None:
        connection = get_connection(self.database)
        try:
            connection.executemany(
                """
                INSERT INTO etf_dividend (
                    etf_code, source_event_id, payment_date,
                    amount_per_unit, currency, source_id
                ) VALUES ('00929', ?, ?, ?, 'TWD', 'TEST');
                """,
                [
                    ("paid", "2026-08-14", 0.38),
                    ("future", "2026-09-14", 0.38),
                ],
            )
            connection.commit()
        finally:
            connection.close()
        candidate = SimpleNamespace(
            etf_code="00929",
            eligible_for_addition=False,
            reasons=[SimpleNamespace(code="FUTURE_DIVIDEND_DATA")],
            latest_payment_date=date(2026, 9, 14),
        )
        index = SimpleNamespace(
            response=SimpleNamespace(candidates=[candidate])
        )

        with patch(
            "deployment.v5_full_database_audit.build_market_eligibility_index",
            return_value=index,
        ):
            evidence = _reference_etf_evidence(
                self.database,
                date(2026, 9, 1),
                "00929",
            )

        self.assertEqual(evidence["paid_event_count_as_of_evaluation"], 1)
        self.assertEqual(
            evidence["future_scheduled_payment_event_count"],
            1,
        )
        self.assertEqual(
            evidence["is_active_field_semantics"],
            "ACTIVELY_MANAGED_ETF_NOT_LISTING_STATUS",
        )
        self.assertIn("FUTURE_DIVIDEND_DATA", evidence["reason_codes"])


if __name__ == "__main__":
    unittest.main()
