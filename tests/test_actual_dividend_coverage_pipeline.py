"""正式配息覆蓋率 Pipeline 測試。"""

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from backend.app.database.connection import (
    get_connection,
)
from backend.app.database.init_db import (
    initialize_database,
)
from backend.app.data_sources.actual_dividend_coverage_pipeline import (
    run_actual_dividend_coverage_pipeline,
)


class TestActualDividendCoveragePipeline(
    unittest.TestCase
):
    """驗證佇列同步與品質報告產物。"""

    def setUp(self) -> None:
        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.temp_path = Path(
            self.temp_directory.name
        )

        self.database_path = (
            self.temp_path / "coverage.db"
        )

        self.output_root = (
            self.temp_path / "reports"
        )

        self.run_at = datetime(
            2026,
            7,
            31,
            1,
            0,
            tzinfo=timezone.utc,
        )

        initialize_database(
            self.database_path
        )

        self.insert_test_data()

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def insert_test_data(self) -> None:
        connection = get_connection(
            self.database_path
        )

        try:
            connection.execute(
                """
                INSERT INTO etf_master (
                    code,
                    name,
                    is_active,
                    is_bond
                )
                VALUES (?, ?, ?, ?);
                """,
                (
                    "00918",
                    "大華優利高填息30",
                    0,
                    0,
                ),
            )

            connection.executemany(
                """
                INSERT INTO etf_dividend (
                    id,
                    etf_code,
                    source_event_id,
                    ex_dividend_date,
                    amount_per_unit,
                    currency,
                    source_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                [
                    (
                        1,
                        "00918",
                        "event-2025",
                        "2025-12-18",
                        0.7,
                        "TWD",
                        "twse_etfortune_dividend",
                    ),
                    (
                        2,
                        "00918",
                        "event-2026",
                        "2026-03-18",
                        0.7,
                        "TWD",
                        "twse_etfortune_dividend",
                    ),
                ],
            )

            connection.execute(
                """
                INSERT INTO etf_dividend_component (
                    dividend_id,
                    component_code,
                    component_basis,
                    ratio_pct,
                    source_id
                )
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    1,
                    "EST_REALIZED_CAPITAL_GAIN",
                    "ESTIMATED",
                    100.0,
                    "twse_etfortune_dividend",
                ),
            )

            connection.commit()

        finally:
            connection.close()

    def test_pipeline_saves_queue_and_report(
        self,
    ) -> None:
        """Pipeline 會建立佇列快照與品質報告。"""

        result = (
            run_actual_dividend_coverage_pipeline(
                database_path=(
                    self.database_path
                ),
                output_root=(
                    self.output_root
                ),
                run_at=self.run_at,
            )
        )

        self.assertEqual(
            result.coverage_summary[
                "total_dividend_count"
            ],
            2,
        )

        self.assertEqual(
            result.review_queue_count,
            4,
        )

        self.assertEqual(
            result.queue_sync_summary
            .created_item_count,
            4,
        )

        self.assertTrue(
            result.queue_snapshot_path.exists()
        )

        self.assertTrue(
            result.quality_report_path.exists()
        )

        report = json.loads(
            result.quality_report_path
            .read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(
            report["coverage"][
                "actual_76w_event_count"
            ],
            0,
        )

        self.assertEqual(
            report["by_etf"][0][
                "etf_code"
            ],
            "00918",
        )

        years = {
            item["event_year"]
            for item in report["by_year"]
        }

        self.assertEqual(
            years,
            {
                "2025",
                "2026",
            },
        )

        self.assertIn(
            "EST_REALIZED_CAPITAL_GAIN",
            report["notes"],
        )

    def test_pipeline_is_idempotent(
        self,
    ) -> None:
        """重跑 Pipeline 不會建立重複佇列。"""

        first = (
            run_actual_dividend_coverage_pipeline(
                database_path=(
                    self.database_path
                ),
                output_root=(
                    self.output_root
                ),
                run_at=self.run_at,
            )
        )

        second = (
            run_actual_dividend_coverage_pipeline(
                database_path=(
                    self.database_path
                ),
                output_root=(
                    self.output_root
                ),
                run_at=datetime(
                    2026,
                    7,
                    31,
                    2,
                    0,
                    tzinfo=timezone.utc,
                ),
            )
        )

        self.assertEqual(
            first.review_queue_count,
            second.review_queue_count,
        )

        self.assertEqual(
            second.queue_sync_summary
            .created_item_count,
            0,
        )


if __name__ == "__main__":
    unittest.main()
