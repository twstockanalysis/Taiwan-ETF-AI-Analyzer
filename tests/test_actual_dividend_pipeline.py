"""正式收益分配通知書完整 Pipeline 測試。"""

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from backend.app.database.connection import (
    get_connection,
)
from backend.app.database.init_db import (
    initialize_database,
)
from backend.app.data_sources.actual_dividend_pipeline import (
    run_actual_dividend_pipeline,
)
from backend.app.repositories.import_batch_repository import (
    get_latest_import_batch,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "actual_dividend_notice_sample.json"
)


class TestActualDividendPipeline(
    unittest.TestCase
):
    """驗證 ACTUAL 所得代碼正式匯入。"""

    def setUp(self) -> None:
        """建立臨時資料庫及輸出目錄。"""

        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.temp_path = Path(
            self.temp_directory.name
        )

        self.database_path = (
            self.temp_path / "actual.db"
        )

        self.input_path = (
            self.temp_path / "notice.json"
        )

        self.input_path.write_text(
            FIXTURE_PATH.read_text(
                encoding="utf-8"
            ),
            encoding="utf-8",
        )

        self.raw_root = (
            self.temp_path / "raw"
        )

        self.processed_root = (
            self.temp_path / "processed"
        )

        self.rejected_root = (
            self.temp_path / "rejected"
        )

        self.report_root = (
            self.temp_path / "reports"
        )

        self.run_at = datetime(
            2026,
            7,
            30,
            12,
            0,
            tzinfo=timezone.utc,
        )

        initialize_database(
            self.database_path
        )

        self.insert_event()

    def tearDown(self) -> None:
        """清除臨時資料。"""

        self.temp_directory.cleanup()

    def insert_event(self) -> None:
        """建立待匹配 ETF 與 TWSE 配息事件。"""

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
                    "00878",
                    "國泰永續高股息",
                    0,
                    0,
                ),
            )

            connection.execute(
                """
                INSERT INTO etf_dividend (
                    etf_code,
                    source_event_id,
                    announcement_date,
                    ex_dividend_date,
                    record_date,
                    payment_date,
                    amount_per_unit,
                    currency,
                    source_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    "00878",
                    (
                        "twse_etfortune_dividend:"
                        "00878:2023-08-16"
                    ),
                    "2023-08-10",
                    "2023-08-16",
                    "2023-08-22",
                    "2023-09-11",
                    0.35,
                    "TWD",
                    "twse_etfortune_dividend",
                ),
            )

            connection.commit()

        finally:
            connection.close()

    def run_pipeline(self):
        """使用固定 JSON 執行 Pipeline。"""

        return run_actual_dividend_pipeline(
            input_path=self.input_path,
            database_path=self.database_path,
            raw_output_root=self.raw_root,
            processed_output_root=(
                self.processed_root
            ),
            rejected_output_root=(
                self.rejected_root
            ),
            report_output_root=(
                self.report_root
            ),
            run_at=self.run_at,
        )

    def test_actual_components_are_imported(
        self,
    ) -> None:
        """76W 與 54C 以 ACTUAL 寫入。"""

        result = self.run_pipeline()

        self.assertEqual(
            result.raw_notice_count,
            1,
        )

        self.assertEqual(
            result.accepted_notice_count,
            1,
        )

        self.assertEqual(
            result.accepted_component_count,
            2,
        )

        self.assertEqual(
            result.inserted_component_count,
            2,
        )

        self.assertTrue(
            result.raw_snapshot_path.exists()
        )

        self.assertTrue(
            result.processed_path.exists()
        )

        self.assertTrue(
            result.rejected_path.exists()
        )

        self.assertTrue(
            result.quality_report_path.exists()
        )

        connection = get_connection(
            self.database_path
        )

        try:
            rows = connection.execute(
                """
                SELECT
                    component_code,
                    component_basis,
                    ratio_pct,
                    source_id
                FROM etf_dividend_component
                ORDER BY component_code;
                """
            ).fetchall()

            summary_row = connection.execute(
                """
                SELECT
                    distribution_period,
                    distribution_period_source_id,
                    yield_pct,
                    yield_basis,
                    yield_source_id,
                    reference_trade_date,
                    reference_close_price
                FROM etf_dividend_summary_metric;
                """
            ).fetchone()

        finally:
            connection.close()

        self.assertEqual(
            {
                (
                    row["component_code"],
                    row["component_basis"],
                )
                for row in rows
            },
            {
                ("54C", "ACTUAL"),
                ("76W", "ACTUAL"),
            },
        )

        self.assertTrue(
            all(
                row["source_id"]
                == (
                    "official_distribution_notice"
                )
                for row in rows
            )
        )

        self.assertIsNotNone(
            summary_row
        )
        self.assertEqual(
            summary_row[
                "distribution_period"
            ],
            "2023Q2",
        )
        self.assertEqual(
            summary_row["yield_pct"],
            1.75,
        )
        self.assertEqual(
            summary_row["yield_basis"],
            "OFFICIAL",
        )
        self.assertIsNone(
            summary_row[
                "reference_trade_date"
            ]
        )

    def test_repeated_import_updates_in_place(
        self,
    ) -> None:
        """相同來源重複匯入不產生重複資料。"""

        first_result = self.run_pipeline()
        second_result = self.run_pipeline()

        self.assertEqual(
            first_result.inserted_component_count,
            2,
        )

        self.assertEqual(
            second_result.inserted_component_count,
            0,
        )

        self.assertEqual(
            second_result.updated_component_count,
            2,
        )

        connection = get_connection(
            self.database_path
        )

        try:
            count = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM etf_dividend_component;
                """
            ).fetchone()["total"]

        finally:
            connection.close()

        self.assertEqual(
            count,
            2,
        )

    def test_estimated_notice_is_rejected(
        self,
    ) -> None:
        """預估文件不得產生 ACTUAL 組成。"""

        payload = json.loads(
            self.input_path.read_text(
                encoding="utf-8"
            )
        )

        payload["notices"][0][
            "information_basis"
        ] = "ESTIMATED"

        self.input_path.write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        result = self.run_pipeline()

        self.assertEqual(
            result.accepted_notice_count,
            0,
        )

        self.assertEqual(
            result.accepted_component_count,
            0,
        )

        self.assertEqual(
            result.rejected_notice_count,
            1,
        )

        connection = get_connection(
            self.database_path
        )

        try:
            count = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM etf_dividend_component;
                """
            ).fetchone()["total"]

        finally:
            connection.close()

        self.assertEqual(
            count,
            0,
        )

    def test_missing_event_is_rejected(
        self,
    ) -> None:
        """找不到既有配息事件時留下拒絕產物。"""

        payload = json.loads(
            self.input_path.read_text(
                encoding="utf-8"
            )
        )

        payload["notices"][0][
            "ex_dividend_date"
        ] = "2023-08-17"

        self.input_path.write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        result = self.run_pipeline()

        rejected = json.loads(
            result.rejected_path.read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(
            rejected[0]["category"],
            "missing_dividend_event",
        )

        batch = get_latest_import_batch(
            self.database_path
        )

        self.assertEqual(
            batch["status"],
            "success",
        )

    def test_quality_report_counts_actual_76w(
        self,
    ) -> None:
        """品質報告只計算正式 76W。"""

        result = self.run_pipeline()

        report = json.loads(
            result.quality_report_path
            .read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(
            report["actual_76w_count"],
            1,
        )

        self.assertEqual(
            report[
                "accepted_component_count"
            ],
            2,
        )

        self.assertIn(
            "EST_REALIZED_CAPITAL_GAIN",
            report["notes"],
        )

    @patch(
        "backend.app.data_sources."
        "actual_dividend_pipeline."
        "upsert_dividend_component_records"
    )
    def test_import_failure_marks_batch_failed(
        self,
        mock_upsert,
    ) -> None:
        """資料庫匯入錯誤會保留 failed 批次。"""

        mock_upsert.side_effect = RuntimeError(
            "模擬正式配息匯入失敗"
        )

        with self.assertRaises(
            RuntimeError
        ):
            self.run_pipeline()

        batch = get_latest_import_batch(
            self.database_path
        )

        self.assertEqual(
            batch["status"],
            "failed",
        )

        self.assertIn(
            "模擬正式配息匯入失敗",
            batch["error_message"],
        )


if __name__ == "__main__":
    unittest.main()
