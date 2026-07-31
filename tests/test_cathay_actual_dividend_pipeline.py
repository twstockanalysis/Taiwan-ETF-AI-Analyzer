"""國泰實際配息公告完整 Pipeline 測試。"""

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
from backend.app.data_sources.cathay_actual_dividend_pipeline import (
    run_cathay_actual_dividend_pipeline,
)
from backend.app.repositories.dividend_source_document_repository import (
    get_dividend_source_document,
    list_dividend_source_document_versions,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "cathay_actual_dividend_5141.html"
)

SOURCE_URL = (
    "https://www.cathaysite.com.tw/"
    "announcement/5141"
)


class TestCathayActualDividendPipeline(
    unittest.TestCase
):
    """驗證快照、文件登錄與 M8-4A 轉接。"""

    def setUp(self) -> None:
        """建立臨時資料庫與配息事件。"""

        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.temp_path = Path(
            self.temp_directory.name
        )

        self.database_path = (
            self.temp_path / "cathay.db"
        )

        self.source_root = (
            self.temp_path / "source"
        )

        self.generated_root = (
            self.temp_path / "generated"
        )

        self.actual_raw_root = (
            self.temp_path / "actual_raw"
        )

        self.actual_processed_root = (
            self.temp_path / "actual_processed"
        )

        self.actual_rejected_root = (
            self.temp_path / "actual_rejected"
        )

        self.actual_report_root = (
            self.temp_path / "actual_report"
        )

        self.run_at = datetime(
            2026,
            7,
            30,
            12,
            0,
            tzinfo=timezone.utc,
        )

        self.html_text = (
            FIXTURE_PATH.read_text(
                encoding="utf-8"
            )
        )

        initialize_database(
            self.database_path
        )

        self.insert_event()

    def tearDown(self) -> None:
        """刪除臨時資源。"""

        self.temp_directory.cleanup()

    def insert_event(self) -> None:
        """建立 00878 與既有 TWSE 配息事件。"""

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

    def run_pipeline(
        self,
        html_text: str | None = None,
    ):
        """使用固定 HTML 執行來源 Pipeline。"""

        return (
            run_cathay_actual_dividend_pipeline(
                source_document_url=(
                    SOURCE_URL
                ),
                etf_code="00878",
                html_text=(
                    html_text
                    if html_text is not None
                    else self.html_text
                ),
                database_path=(
                    self.database_path
                ),
                source_snapshot_root=(
                    self.source_root
                ),
                generated_input_root=(
                    self.generated_root
                ),
                actual_raw_output_root=(
                    self.actual_raw_root
                ),
                actual_processed_output_root=(
                    self.actual_processed_root
                ),
                actual_rejected_output_root=(
                    self.actual_rejected_root
                ),
                actual_report_output_root=(
                    self.actual_report_root
                ),
                run_at=self.run_at,
            )
        )

    def test_source_document_and_actual_components(
        self,
    ) -> None:
        """官方文件與 54C、76W 一併保存。"""

        result = self.run_pipeline()

        self.assertTrue(
            result.source_snapshot_path.exists()
        )

        self.assertTrue(
            result.generated_input_path.exists()
        )

        self.assertEqual(
            result.source_document_version,
            1,
        )

        self.assertTrue(
            result.source_document_is_new_version
        )

        self.assertEqual(
            result.actual_pipeline
            .accepted_component_count,
            2,
        )

        document = (
            get_dividend_source_document(
                (
                    result
                    .source_document_database_id
                ),
                self.database_path,
            )
        )

        self.assertEqual(
            document["parse_status"],
            "parsed",
        )

        self.assertEqual(
            document["information_basis"],
            "ACTUAL",
        )

        self.assertEqual(
            document["source_document_date"],
            "2023-08-15",
        )

        self.assertEqual(
            document["import_batch_id"],
            result.actual_pipeline.batch_id,
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
                    source_id
                FROM etf_dividend_component
                ORDER BY component_code;
                """
            ).fetchall()

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
                    "cathay_actual_dividend_"
                    "announcement"
                )
                for row in rows
            )
        )

    def test_same_html_reuses_document_version(
        self,
    ) -> None:
        """相同 HTML 不建立重複來源版本。"""

        first = self.run_pipeline()
        second = self.run_pipeline()

        self.assertEqual(
            (
                first
                .source_document_database_id
            ),
            (
                second
                .source_document_database_id
            ),
        )

        self.assertFalse(
            second.source_document_is_new_version
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
            len(versions),
            1,
        )

    def test_changed_html_creates_new_version(
        self,
    ) -> None:
        """官方內容改變時保留第二版快照。"""

        self.run_pipeline()

        changed_html = self.html_text.replace(
            "<main>",
            "<main>\n<!-- official revision -->",
        )

        second = self.run_pipeline(
            changed_html
        )

        self.assertTrue(
            second.source_document_is_new_version
        )

        self.assertEqual(
            second.source_document_version,
            2,
        )

    def test_estimated_document_is_registered_rejected(
        self,
    ) -> None:
        """預估頁面留下 rejected 文件狀態。"""

        estimated_html = (
            self.html_text.replace(
                "實際配發金額組成如下",
                "預估收益分配組成占比如下",
            )
        )

        with self.assertRaisesRegex(
            ValueError,
            "預估語意",
        ):
            self.run_pipeline(
                estimated_html
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
            versions[0]["parse_status"],
            "rejected",
        )

        self.assertIn(
            "預估語意",
            versions[0]["parse_error"],
        )


if __name__ == "__main__":
    unittest.main()
