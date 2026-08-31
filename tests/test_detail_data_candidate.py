"""Isolated V5-1 candidate orchestration tests."""

import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from backend.app.database.connection import get_connection
from backend.app.database.init_db import initialize_database
from deployment.detail_data_candidate import prepare_detail_data_candidate


class TestDetailDataCandidate(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_directory.name)
        self.source = self.root / "source.db"
        self.candidate = self.root / "candidate.db"
        self.artifacts = self.root / "artifacts"
        initialize_database(self.source)
        connection = get_connection(self.source)
        try:
            connection.execute(
                """
                INSERT INTO etf_master (
                    code, name, is_active, is_bond, listing_date
                ) VALUES ('0050', '元大台灣50', 0, 0, '2003-06-30');
                """
            )
            connection.commit()
        finally:
            connection.close()

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    @patch("deployment.detail_data_candidate.run_actual_dividend_coverage_pipeline")
    @patch("deployment.detail_data_candidate.run_dividend_yield_pipeline")
    @patch("deployment.detail_data_candidate.run_dividend_pipeline")
    @patch("deployment.detail_data_candidate.run_multi_period_performance_pipeline")
    @patch("deployment.detail_data_candidate.run_etf_master_pipeline")
    def test_candidate_is_copied_refreshed_and_manifested(
        self,
        master,
        performance,
        dividend,
        dividend_yield,
        actual,
    ) -> None:
        master.return_value = SimpleNamespace(
            raw_record_count=1,
            accepted_record_count=1,
            rejected_record_count=0,
            inserted_record_count=0,
            updated_record_count=1,
        )
        performance.return_value = SimpleNamespace(
            candidate_count=1,
            successful_count=0,
            insufficient_history_count=4,
            failed_count=0,
            period_summaries=(),
        )
        dividend.return_value = SimpleNamespace(
            raw_record_count=0,
            accepted_dividend_count=0,
            accepted_component_count=0,
            rejected_record_count=0,
        )
        dividend_yield.return_value = SimpleNamespace(
            candidate_count=0,
            calculated_count=0,
            failed_count=0,
            failures=(),
        )
        actual.return_value = SimpleNamespace(
            coverage_summary={"total_dividend_count": 0},
            review_queue_count=0,
        )

        result = prepare_detail_data_candidate(
            self.source,
            self.candidate,
            self.artifacts,
            evaluated_on=date(2026, 8, 30),
            request_interval_seconds=0,
            inter_etf_interval_seconds=0,
        )

        self.assertTrue(self.source.is_file())
        self.assertTrue(self.candidate.is_file())
        self.assertNotEqual(
            result["source_database"]["sha256"],
            "",
        )
        self.assertEqual(
            result["candidate_database"]["integrity_check"],
            "ok",
        )
        self.assertTrue(
            (self.artifacts / "candidate_manifest.json").is_file()
        )
        self.assertTrue(
            (self.artifacts / "detail_page_coverage.report.json").is_file()
        )
        self.assertTrue(performance.call_args.kwargs["include_bond"])
        self.assertTrue(dividend_yield.call_args.kwargs["prefer_cached_prices"])

    def test_candidate_refuses_existing_target(self) -> None:
        self.candidate.write_bytes(b"occupied")
        with self.assertRaises(FileExistsError):
            prepare_detail_data_candidate(
                self.source,
                self.candidate,
                self.artifacts,
            )


if __name__ == "__main__":
    unittest.main()
