"""V5 detailed-page coverage ledger tests."""

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from backend.app.database.connection import get_connection
from backend.app.database.init_db import initialize_database
from backend.app.data_sources.detail_page_coverage import (
    build_detail_page_coverage,
    write_coverage_report,
)


class TestDetailPageCoverage(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_directory.name)
        self.database = self.root / "detail.db"
        initialize_database(self.database)

        connection = get_connection(self.database)
        try:
            connection.executemany(
                """
                INSERT INTO etf_master (
                    code, name, is_active, is_bond, listing_date,
                    fund_size, expense_ratio
                ) VALUES (?, ?, 0, 0, ?, ?, ?);
                """,
                [
                    ("0050", "完整ETF", "2003-06-30", 100, 0.4),
                    ("0051", "缺資料ETF", "2006-06-30", None, None),
                ],
            )
            connection.execute(
                """
                INSERT INTO etf_daily_close
                    (etf_code, trade_date, close_price, source_id)
                VALUES ('0050', '2026-08-28', 50, 'twse_stock_day');
                """
            )
            connection.executemany(
                """
                INSERT INTO etf_performance (
                    etf_code, as_of_date, period_code, metric_code,
                    return_pct, source_id
                ) VALUES ('0050', '2026-08-28', ?, 'PRICE_RETURN', 1, 'twse_stock_day');
                """,
                [(period,) for period in ("1M", "3M", "6M", "1Y")],
            )
            connection.execute(
                """
                INSERT INTO etf_dividend (
                    id, etf_code, source_event_id, ex_dividend_date,
                    payment_date, amount_per_unit, currency, source_id
                ) VALUES (
                    1, '0050', 'event-1', '2026-07-01', '2026-07-31',
                    1, 'TWD', 'twse_etfortune_dividend'
                );
                """
            )
            connection.execute(
                """
                INSERT INTO etf_dividend_summary_metric (
                    dividend_id, distribution_period,
                    distribution_period_source_id, yield_pct, yield_basis,
                    yield_source_id, reference_trade_date,
                    reference_close_price
                ) VALUES (
                    1, '2026Q2', 'official_notice', 2, 'CALCULATED',
                    'twse_stock_day', '2026-06-30', 50
                );
                """
            )
            connection.executemany(
                """
                INSERT INTO etf_dividend_component (
                    dividend_id, component_code, component_basis,
                    ratio_pct, source_id
                ) VALUES (1, ?, ?, ?, ?);
                """,
                [
                    ("EST_DIVIDEND", "ESTIMATED", 100, "twse_etfortune_dividend"),
                    ("76W", "ACTUAL", 0, "official_notice"),
                ],
            )
            connection.execute(
                """
                INSERT INTO dividend_source_review_queue (
                    dividend_id, issue_type, status, last_evaluated_at
                ) VALUES (1, 'MISSING_SOURCE_DOCUMENT', 'PENDING', '2026-08-30T00:00:00Z');
                """
            )
            connection.commit()
        finally:
            connection.close()

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_report_keeps_available_unavailable_and_formal_zero_distinct(self) -> None:
        report = build_detail_page_coverage(
            self.database,
            generated_at=datetime(2026, 8, 30, tzinfo=timezone.utc),
        )

        self.assertEqual(report["universe_count"], 2)
        self.assertEqual(report["database"]["integrity_check"], "ok")
        self.assertEqual(report["database"]["foreign_key_violation_count"], 0)
        self.assertEqual(report["field_coverage"]["price_return_1y"]["available_count"], 1)
        self.assertEqual(report["field_coverage"]["fund_size"]["unavailable_count"], 1)

        complete = report["items"][0]
        missing = report["items"][1]
        self.assertEqual(complete["fields"]["actual_76w"]["status"], "AVAILABLE")
        self.assertEqual(complete["counts"]["actual_76w_event"], 1)
        self.assertEqual(missing["fields"]["actual_76w"]["status"], "UNAVAILABLE")
        self.assertEqual(
            missing["fields"]["actual_76w"]["reason"],
            "NO_REVIEWED_ACTUAL_76W_DISCLOSURE",
        )

    def test_report_writer_refuses_overwrite(self) -> None:
        report = build_detail_page_coverage(self.database)
        output = self.root / "coverage.json"
        write_coverage_report(report, output)
        with self.assertRaises(FileExistsError):
            write_coverage_report(report, output)


if __name__ == "__main__":
    unittest.main()
