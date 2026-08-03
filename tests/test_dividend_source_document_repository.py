"""正式配息來源文件 Migration 與 Repository 測試。"""

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
from backend.app.database.migrate_dividend_source_document import (
    migrate_dividend_source_document,
)
from backend.app.models.dividend_source_document import (
    SourceDocumentInformationBasis,
    SourceDocumentParseStatus,
)
from backend.app.repositories.dividend_source_document_repository import (
    get_dividend_source_document,
    list_dividend_source_document_versions,
    register_dividend_source_document,
    update_dividend_source_document_result,
)


class TestDividendSourceDocumentRepository(
    unittest.TestCase
):
    """驗證來源文件版本與解析狀態。"""

    def setUp(self) -> None:
        """建立臨時資料庫。"""

        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.database_path = (
            Path(self.temp_directory.name)
            / "source_document.db"
        )

        initialize_database(
            self.database_path
        )

        self.downloaded_at = datetime(
            2026,
            7,
            30,
            12,
            0,
            tzinfo=timezone.utc,
        )

    def tearDown(self) -> None:
        """刪除臨時資料庫。"""

        self.temp_directory.cleanup()

    def register(
        self,
        checksum: str,
    ):
        """登錄一個來源文件版本。"""

        return register_dividend_source_document(
            source_id=(
                "cathay_actual_dividend_announcement"
            ),
            source_document_id=(
                "cathay-announcement-5141"
            ),
            source_url=(
                "https://www.cathaysite.com.tw/"
                "announcement/5141"
            ),
            downloaded_at=(
                self.downloaded_at
            ),
            content_type="text/html",
            checksum_sha256=checksum,
            snapshot_path=(
                f"raw/{checksum}.html"
            ),
            metadata_path=(
                f"raw/{checksum}.meta.json"
            ),
            database_path=(
                self.database_path
            ),
        )

    def test_initialize_database_creates_table(
        self,
    ) -> None:
        """初始化後來源文件資料表存在。"""

        connection = get_connection(
            self.database_path
        )

        try:
            row = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name = (
                      'dividend_source_document'
                  );
                """
            ).fetchone()

        finally:
            connection.close()

        self.assertIsNotNone(
            row
        )

        self.assertFalse(
            migrate_dividend_source_document(
                self.database_path
            )
        )

    def test_same_checksum_reuses_version(
        self,
    ) -> None:
        """相同內容不建立重複版本。"""

        first = self.register(
            "a" * 64
        )

        second = self.register(
            "a" * 64
        )

        self.assertTrue(
            first.is_new_version
        )

        self.assertFalse(
            second.is_new_version
        )

        self.assertEqual(
            first.document_id,
            second.document_id,
        )

        self.assertEqual(
            first.version_number,
            1,
        )

    def test_changed_checksum_creates_version_two(
        self,
    ) -> None:
        """內容雜湊改變時保留新版。"""

        self.register(
            "a" * 64
        )

        second = self.register(
            "b" * 64
        )

        self.assertTrue(
            second.is_new_version
        )

        self.assertEqual(
            second.version_number,
            2,
        )

        versions = (
            list_dividend_source_document_versions(
                (
                    "cathay_actual_dividend_"
                    "announcement"
                ),
                "cathay-announcement-5141",
                self.database_path,
            )
        )

        self.assertEqual(
            [
                row["version_number"]
                for row in versions
            ],
            [
                2,
                1,
            ],
        )

    def test_parse_result_is_persisted(
        self,
    ) -> None:
        """解析狀態及 ACTUAL 日期可以更新。"""

        registration = self.register(
            "c" * 64
        )

        update_dividend_source_document_result(
            document_id=(
                registration.document_id
            ),
            parse_status=(
                SourceDocumentParseStatus
                .PARSED
            ),
            information_basis=(
                SourceDocumentInformationBasis
                .ACTUAL
            ),
            source_document_date=(
                self.downloaded_at.date()
            ),
            database_path=(
                self.database_path
            ),
        )

        row = get_dividend_source_document(
            registration.document_id,
            self.database_path,
        )

        self.assertEqual(
            row["parse_status"],
            "parsed",
        )

        self.assertEqual(
            row["information_basis"],
            "ACTUAL",
        )

        self.assertEqual(
            row["source_document_date"],
            "2026-07-30",
        )


if __name__ == "__main__":
    unittest.main()
