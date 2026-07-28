"""匯入批次 Repository 測試。"""

import tempfile
import unittest
from pathlib import Path

from backend.app.database.init_db import (
    initialize_database,
)
from backend.app.repositories.import_batch_repository import (
    ImportBatchCompletion,
    create_import_batch,
    get_import_batch,
    mark_import_batch_failed,
    mark_import_batch_success,
)


class TestImportBatchRepository(
    unittest.TestCase
):
    """測試匯入批次狀態。"""

    def setUp(self) -> None:
        """建立臨時資料庫。"""

        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.database_path = (
            Path(self.temp_directory.name)
            / "test_import_batch.db"
        )

        initialize_database(
            self.database_path
        )

    def tearDown(self) -> None:
        """刪除臨時資料庫。"""

        self.temp_directory.cleanup()

    def create_batch(self) -> int:
        """建立測試批次。"""

        return create_import_batch(
            pipeline_name=(
                "etf_master_pipeline"
            ),
            source_id="twse_openapi",
            endpoint_id="twse_fund_master",
            database_path=self.database_path,
        )

    def test_batch_starts_as_running(
        self,
    ) -> None:
        """確認新批次狀態為 running。"""

        batch_id = self.create_batch()

        batch = get_import_batch(
            batch_id,
            self.database_path,
        )

        self.assertIsNotNone(batch)
        self.assertEqual(
            batch["status"],
            "running",
        )

    def test_batch_can_be_completed(
        self,
    ) -> None:
        """確認批次可以標記為成功。"""

        batch_id = self.create_batch()

        completion = ImportBatchCompletion(
            raw_record_count=100,
            accepted_record_count=80,
            rejected_record_count=20,
            inserted_record_count=70,
            updated_record_count=10,
            deleted_development_record_count=2,
            checksum_sha256="abc123",
            raw_snapshot_path="raw.json",
            processed_snapshot_path=(
                "processed.json"
            ),
            rejected_snapshot_path=(
                "rejected.json"
            ),
            quality_report_path=(
                "report.json"
            ),
        )

        mark_import_batch_success(
            batch_id=batch_id,
            completion=completion,
            database_path=self.database_path,
        )

        batch = get_import_batch(
            batch_id,
            self.database_path,
        )

        self.assertEqual(
            batch["status"],
            "success",
        )

        self.assertEqual(
            batch["accepted_record_count"],
            80,
        )

        self.assertEqual(
            batch["inserted_record_count"],
            70,
        )

    def test_batch_can_be_failed(
        self,
    ) -> None:
        """確認批次可以標記為失敗。"""

        batch_id = self.create_batch()

        mark_import_batch_failed(
            batch_id=batch_id,
            error_message="測試錯誤",
            database_path=self.database_path,
            raw_record_count=10,
        )

        batch = get_import_batch(
            batch_id,
            self.database_path,
        )

        self.assertEqual(
            batch["status"],
            "failed",
        )

        self.assertEqual(
            batch["error_message"],
            "測試錯誤",
        )


if __name__ == "__main__":
    unittest.main()