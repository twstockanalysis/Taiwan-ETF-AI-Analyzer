"""ETF 主資料完整 Pipeline 測試。"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.app.database.connection import (
    get_connection,
)
from backend.app.data_sources.etf_master_pipeline import (
    run_etf_master_pipeline,
)
from backend.app.repositories.import_batch_repository import (
    get_latest_import_batch,
)


class TestETFMasterPipeline(
    unittest.TestCase
):
    """測試 ETF 主資料 Pipeline。"""

    def setUp(self) -> None:
        """建立臨時目錄。"""

        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.temp_path = Path(
            self.temp_directory.name
        )

        self.database_path = (
            self.temp_path / "pipeline.db"
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

    def tearDown(self) -> None:
        """刪除臨時資料。"""

        self.temp_directory.cleanup()

    @patch(
        "backend.app.data_sources."
        "etf_master_pipeline."
        "fetch_json_records"
    )
    def test_successful_pipeline(
        self,
        mock_fetch,
    ) -> None:
        """確認完整流程成功。"""

        mock_fetch.return_value = [
            {
                "基金代號": "0050",
                "基金簡稱": (
                    "元大台灣50 ETF"
                ),
                "基金類型": (
                    "指數股票型基金"
                ),
                "上市日期": "2003/06/30",
            },
            {
                "基金代號": "FUND01",
                "基金簡稱": (
                    "一般開放式基金"
                ),
                "基金類型": (
                    "股票型基金"
                ),
            },
        ]

        result = run_etf_master_pipeline(
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
        )

        self.assertEqual(
            result.raw_record_count,
            2,
        )

        self.assertEqual(
            result.accepted_record_count,
            1,
        )

        self.assertEqual(
            result.rejected_record_count,
            1,
        )

        connection = get_connection(
            self.database_path
        )

        try:
            row = connection.execute(
                """
                SELECT code
                FROM etf_master
                WHERE code = '0050';
                """
            ).fetchone()

            self.assertIsNotNone(row)

        finally:
            connection.close()

        batch = get_latest_import_batch(
            self.database_path
        )

        self.assertEqual(
            batch["status"],
            "success",
        )

        report = json.loads(
            result.quality_report_path.read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(
            report["accepted_record_count"],
            1,
        )

        self.assertEqual(
            report["rejected_record_count"],
            1,
        )

    @patch(
        "backend.app.data_sources."
        "etf_master_pipeline."
        "fetch_json_records"
    )
    def test_failed_pipeline_is_recorded(
        self,
        mock_fetch,
    ) -> None:
        """確認錯誤會寫入失敗批次。"""

        mock_fetch.side_effect = RuntimeError(
            "模擬下載失敗"
        )

        with self.assertRaises(
            RuntimeError
        ):
            run_etf_master_pipeline(
                database_path=(
                    self.database_path
                ),
                raw_output_root=(
                    self.raw_root
                ),
                processed_output_root=(
                    self.processed_root
                ),
                rejected_output_root=(
                    self.rejected_root
                ),
                report_output_root=(
                    self.report_root
                ),
            )

        batch = get_latest_import_batch(
            self.database_path
        )

        self.assertEqual(
            batch["status"],
            "failed",
        )

        self.assertIn(
            "模擬下載失敗",
            batch["error_message"],
        )


if __name__ == "__main__":
    unittest.main()