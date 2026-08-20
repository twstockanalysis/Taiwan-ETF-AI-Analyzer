"""V2-12 isolated calculation-candidate readiness tests."""

from datetime import date, datetime, timezone
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from backend.app.database.connection import get_connection
from backend.app.database.init_db import initialize_database
from backend.app.models.etf_constituent import ETFConstituentSnapshotCreate
from backend.app.repositories.etf_constituent_repository import (
    save_constituent_snapshot,
)
from deployment.calculation_candidate import (
    evaluate_calculation_candidate,
    prepare_calculation_candidate,
)


class TestCalculationCandidate(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_directory.name)
        self.database_path = self.root / "candidate.db"
        initialize_database(self.database_path)

    def tearDown(self):
        self.temp_directory.cleanup()

    def _insert_ready_etf(self) -> None:
        connection = get_connection(self.database_path)
        connection.execute(
            """
            INSERT INTO etf_master (code, name, is_active, is_bond)
            VALUES ('0050', '元大台灣50', 0, 0);
            """
        )
        connection.executemany(
            """
            INSERT INTO etf_performance (
                etf_code, as_of_date, period_code, metric_code,
                return_pct, source_id
            ) VALUES ('0050', '2026-08-20', ?, 'PRICE_RETURN', 1, 'twse_stock_day');
            """,
            [(period,) for period in ("1M", "3M", "6M", "1Y")],
        )
        connection.execute(
            """
            INSERT INTO etf_daily_close (
                etf_code, trade_date, close_price, source_id
            ) VALUES ('0050', '2026-08-20', 50, 'twse_stock_day');
            """
        )
        cursor = connection.execute(
            """
            INSERT INTO etf_dividend (
                etf_code, source_event_id, payment_date,
                amount_per_unit, currency, source_id
            ) VALUES ('0050', 'event-1', '2026-08-15', 1, 'TWD', 'TEST');
            """
        )
        connection.execute(
            """
            INSERT INTO etf_dividend_component (
                dividend_id, component_code, component_basis,
                ratio_pct, source_id
            ) VALUES (?, 'EST_DIVIDEND_INCOME', 'ESTIMATED', 100, 'TEST');
            """,
            (int(cursor.lastrowid),),
        )
        connection.commit()
        connection.close()
        save_constituent_snapshot(
            ETFConstituentSnapshotCreate(
                etf_code="0050",
                as_of_date=date(2026, 8, 20),
                source_id="issuer_official_holdings",
                source_url="https://example.test/holdings",
                fetched_at=datetime(2026, 8, 20, tzinfo=timezone.utc),
                positions=[
                    {
                        "constituent_id": "2330",
                        "constituent_name": "台積電",
                        "weight_pct": 90,
                    }
                ],
            ),
            self.database_path,
        )

    def test_ready_requires_every_calculation_data_family(self):
        self._insert_ready_etf()

        result = evaluate_calculation_candidate(
            self.database_path,
            etf_codes=["0050"],
            evaluated_on=date(2026, 8, 20),
        )

        self.assertEqual(result["decision"], "READY")
        self.assertEqual(result["ready_etf_count"], 1)
        self.assertEqual(result["items"][0]["component_basis"], "ESTIMATED_FALLBACK")
        self.assertTrue(result["items"][0]["core_ready"])
        self.assertTrue(result["items"][0]["overlap_ready"])
        self.assertEqual(result["items"][0]["reasons"], [])

    def test_missing_snapshot_is_explicit_overlap_gap(self):
        self._insert_ready_etf()
        connection = get_connection(self.database_path)
        connection.execute("DELETE FROM etf_constituent_snapshot;")
        connection.commit()
        connection.close()

        result = evaluate_calculation_candidate(
            self.database_path,
            etf_codes=["0050"],
            evaluated_on=date(2026, 8, 20),
        )

        self.assertEqual(result["decision"], "CORE_READY")
        self.assertEqual(result["exit_code"], 0)
        self.assertTrue(result["items"][0]["core_ready"])
        self.assertFalse(result["items"][0]["overlap_ready"])
        self.assertIn(
            "CONSTITUENT_MISSING_SNAPSHOT",
            result["items"][0]["reasons"],
        )

    def test_missing_core_performance_is_no_go(self):
        self._insert_ready_etf()
        connection = get_connection(self.database_path)
        connection.execute(
            """
            DELETE FROM etf_performance
            WHERE etf_code = '0050' AND period_code = '1Y';
            """
        )
        connection.commit()
        connection.close()

        result = evaluate_calculation_candidate(
            self.database_path,
            etf_codes=["0050"],
            evaluated_on=date(2026, 8, 20),
        )

        self.assertEqual(result["decision"], "NO_GO")
        self.assertEqual(result["exit_code"], 1)
        self.assertFalse(result["items"][0]["core_ready"])
        self.assertIn("MISSING_PERFORMANCE_1Y", result["items"][0]["reasons"])

    def test_prepare_refuses_to_overwrite_candidate_before_network_work(self):
        source = self.root / "source.db"
        source.write_bytes(self.database_path.read_bytes())

        with self.assertRaises(FileExistsError):
            prepare_calculation_candidate(
                source,
                self.database_path,
                self.root / "artifacts",
                etf_codes=["0050"],
            )

        artifacts = self.root / "existing-artifacts"
        artifacts.mkdir()
        with self.assertRaises(FileExistsError):
            prepare_calculation_candidate(
                source,
                self.root / "new-candidate.db",
                artifacts,
                etf_codes=["0050"],
            )

    @patch("deployment.calculation_candidate.run_constituent_batch_pipeline")
    @patch("deployment.calculation_candidate.run_dividend_pipeline")
    @patch("deployment.calculation_candidate.run_multi_period_performance_pipeline")
    def test_prepare_copies_migrates_and_reports_without_source_mutation(
        self,
        mock_performance,
        mock_dividend,
        mock_constituents,
    ):
        self._insert_ready_etf()
        source_size = self.database_path.stat().st_size
        candidate = self.root / "prepared.db"
        mock_performance.return_value = SimpleNamespace(
            candidate_count=1,
            successful_count=4,
            insufficient_history_count=0,
            failed_count=0,
            period_summaries=(),
        )
        mock_dividend.return_value = SimpleNamespace(
            accepted_dividend_count=1,
            accepted_component_count=1,
            rejected_record_count=0,
        )
        mock_constituents.return_value = {
            "eligible_automated_count": 1,
            "imported_count": 0,
            "unchanged_count": 1,
            "failed_count": 0,
            "results": [],
            "quality": {"decision": "READY"},
        }

        result = prepare_calculation_candidate(
            self.database_path,
            candidate,
            self.root / "artifacts",
            etf_codes=["0050"],
            evaluated_on=date(2026, 8, 20),
            request_interval_seconds=0,
            inter_etf_interval_seconds=0,
        )

        self.assertTrue(candidate.is_file())
        self.assertEqual(self.database_path.stat().st_size, source_size)
        self.assertEqual(result["calculation_data"]["decision"], "READY")
        self.assertEqual(result["candidate_database"], "prepared.db")
        mock_performance.assert_called_once()
        mock_dividend.assert_called_once()
        mock_constituents.assert_called_once()


if __name__ == "__main__":
    unittest.main()
