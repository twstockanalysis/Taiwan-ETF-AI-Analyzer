"""正式配息覆蓋率與審核佇列 Repository 測試。"""

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
from backend.app.models.dividend_quality import (
    DividendReviewIssueType,
    DividendReviewStatus,
)
from backend.app.repositories.dividend_quality_repository import (
    build_actual_dividend_coverage_summary,
    count_dividend_review_queue,
    get_dividend_review_queue_item,
    list_dividend_review_queue,
    set_dividend_review_queue_status,
    synchronize_dividend_review_queue,
)


class TestDividendQualityRepository(
    unittest.TestCase
):
    """驗證覆蓋率、缺資料語意與佇列同步。"""

    def setUp(self) -> None:
        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.database_path = (
            Path(self.temp_directory.name)
            / "quality.db"
        )

        self.run_at = datetime(
            2026,
            7,
            31,
            0,
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
        """建立四種正式配息覆蓋情境。"""

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
                INSERT INTO import_batch (
                    id,
                    pipeline_name,
                    source_id,
                    endpoint_id,
                    started_at,
                    completed_at,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    1,
                    "actual_dividend_pipeline",
                    "cathay_actual_dividend_announcement",
                    "actual_dividend_json_import",
                    "2026-07-31T00:00:00+00:00",
                    "2026-07-31T00:01:00+00:00",
                    "success",
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
                        "00878",
                        "event-estimated",
                        "2026-02-18",
                        0.4,
                        "TWD",
                        "twse_etfortune_dividend",
                    ),
                    (
                        2,
                        "00878",
                        "event-zero-76w",
                        "2026-05-18",
                        0.4,
                        "TWD",
                        "twse_etfortune_dividend",
                    ),
                    (
                        3,
                        "00878",
                        "event-actual-no-document",
                        "2026-08-18",
                        0.4,
                        "TWD",
                        "twse_etfortune_dividend",
                    ),
                    (
                        4,
                        "00878",
                        "event-empty",
                        "2026-11-18",
                        0.4,
                        "TWD",
                        "twse_etfortune_dividend",
                    ),
                ],
            )

            connection.executemany(
                """
                INSERT INTO etf_dividend_component (
                    dividend_id,
                    component_code,
                    component_basis,
                    component_name,
                    ratio_pct,
                    source_id,
                    import_batch_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                [
                    (
                        1,
                        "EST_REALIZED_CAPITAL_GAIN",
                        "ESTIMATED",
                        "已實現資本利得",
                        100.0,
                        "twse_etfortune_dividend",
                        None,
                    ),
                    (
                        2,
                        "76W",
                        "ACTUAL",
                        "財產交易（國內）所得",
                        0.0,
                        "cathay_actual_dividend_announcement",
                        1,
                    ),
                    (
                        3,
                        "54C",
                        "ACTUAL",
                        "境內股利所得",
                        100.0,
                        "manual_actual_dividend_notice",
                        None,
                    ),
                ],
            )

            connection.execute(
                """
                INSERT INTO dividend_source_document (
                    source_id,
                    source_document_id,
                    version_number,
                    source_url,
                    source_document_date,
                    downloaded_at,
                    content_type,
                    information_basis,
                    checksum_sha256,
                    snapshot_path,
                    metadata_path,
                    parse_status,
                    import_batch_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    "cathay_actual_dividend_announcement",
                    "document-1",
                    1,
                    "https://www.cathaysite.com.tw/announcement/1",
                    "2026-05-20",
                    "2026-07-31T00:00:00+00:00",
                    "text/html",
                    "ACTUAL",
                    "a" * 64,
                    "raw/document-1.html",
                    "raw/document-1.meta.json",
                    "parsed",
                    1,
                ),
            )

            connection.commit()

        finally:
            connection.close()

    def test_coverage_counts_and_zero_76w(
        self,
    ) -> None:
        """正式揭露 0% 仍視為已有 76W 紀錄。"""

        summary = (
            build_actual_dividend_coverage_summary(
                self.database_path
            )
        )

        self.assertEqual(
            summary["total_dividend_count"],
            4,
        )

        self.assertEqual(
            summary[
                "estimated_component_event_count"
            ],
            1,
        )

        self.assertEqual(
            summary[
                "actual_component_event_count"
            ],
            2,
        )

        self.assertEqual(
            summary["actual_76w_event_count"],
            1,
        )

        self.assertEqual(
            summary[
                "source_document_event_count"
            ],
            1,
        )

        self.assertEqual(
            summary[
                "missing_actual_component_event_count"
            ],
            2,
        )

        self.assertEqual(
            summary[
                "missing_source_document_event_count"
            ],
            3,
        )

        self.assertEqual(
            summary[
                "actual_component_coverage_pct"
            ],
            50.0,
        )

        self.assertEqual(
            summary["actual_76w_coverage_pct"],
            25.0,
        )

        self.assertEqual(
            summary[
                "source_document_coverage_pct"
            ],
            25.0,
        )

    def test_estimated_realized_gain_is_not_76w(
        self,
    ) -> None:
        """預估已實現資本利得不計入正式 76W。"""

        summary = (
            build_actual_dividend_coverage_summary(
                database_path=(
                    self.database_path
                ),
                etf_code="00878",
            )
        )

        self.assertEqual(
            summary["actual_76w_event_count"],
            1,
        )

    def test_empty_coverage_preserves_null_rate(
        self,
    ) -> None:
        """沒有配息事件時覆蓋率不是 0%。"""

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
                    "0050",
                    "元大台灣50",
                    0,
                    0,
                ),
            )

            connection.commit()

        finally:
            connection.close()

        summary = (
            build_actual_dividend_coverage_summary(
                database_path=(
                    self.database_path
                ),
                etf_code="0050",
            )
        )

        self.assertEqual(
            summary["total_dividend_count"],
            0,
        )

        self.assertIsNone(
            summary[
                "actual_component_coverage_pct"
            ]
        )

        self.assertIsNone(
            summary["actual_76w_coverage_pct"]
        )

    def test_queue_sync_is_idempotent(
        self,
    ) -> None:
        """相同事件與缺失不建立重複佇列。"""

        first = (
            synchronize_dividend_review_queue(
                database_path=(
                    self.database_path
                ),
                run_at=self.run_at,
            )
        )

        second = (
            synchronize_dividend_review_queue(
                database_path=(
                    self.database_path
                ),
                run_at=self.run_at,
            )
        )

        self.assertEqual(
            first.created_item_count,
            5,
        )

        self.assertEqual(
            second.created_item_count,
            0,
        )

        self.assertEqual(
            count_dividend_review_queue(
                self.database_path
            ),
            5,
        )

        covered_items = (
            list_dividend_review_queue(
                database_path=(
                    self.database_path
                ),
                etf_code="00878",
                limit=20,
            )
        )

        self.assertTrue(
            all(
                item["dividend_id"] != 2
                for item in covered_items
            )
        )

    def test_supplying_actual_data_resolves_issue(
        self,
    ) -> None:
        """補入正式組成後對應缺失會自動解決。"""

        synchronize_dividend_review_queue(
            database_path=self.database_path,
            run_at=self.run_at,
        )

        connection = get_connection(
            self.database_path
        )

        try:
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
                    "54C",
                    "ACTUAL",
                    100.0,
                    "manual_actual_dividend_notice",
                ),
            )

            connection.commit()

        finally:
            connection.close()

        sync_result = (
            synchronize_dividend_review_queue(
                database_path=(
                    self.database_path
                ),
                run_at=datetime(
                    2026,
                    8,
                    1,
                    tzinfo=timezone.utc,
                ),
            )
        )

        self.assertEqual(
            sync_result.resolved_item_count,
            1,
        )

        resolved = (
            list_dividend_review_queue(
                database_path=(
                    self.database_path
                ),
                etf_code="00878",
                issue_type=(
                    DividendReviewIssueType
                    .MISSING_ACTUAL_COMPONENTS
                ),
                status=(
                    DividendReviewStatus
                    .RESOLVED
                ),
                limit=20,
            )
        )

        self.assertEqual(
            [
                item["dividend_id"]
                for item in resolved
            ],
            [1],
        )

    def test_skipped_missing_item_stays_skipped(
        self,
    ) -> None:
        """仍缺資料的 SKIPPED 項目不會重開。"""

        synchronize_dividend_review_queue(
            database_path=self.database_path,
            run_at=self.run_at,
        )

        item = next(
            row
            for row in (
                list_dividend_review_queue(
                    database_path=(
                        self.database_path
                    ),
                    issue_type=(
                        DividendReviewIssueType
                        .MISSING_ACTUAL_COMPONENTS
                    ),
                    limit=20,
                )
            )
            if row["dividend_id"] == 4
        )

        set_dividend_review_queue_status(
            queue_id=item["queue_id"],
            status=(
                DividendReviewStatus.SKIPPED
            ),
            notes="目前無公開正式文件",
            database_path=self.database_path,
            changed_at=self.run_at,
        )

        synchronize_dividend_review_queue(
            database_path=self.database_path,
            run_at=datetime(
                2026,
                8,
                1,
                tzinfo=timezone.utc,
            ),
        )

        updated = (
            get_dividend_review_queue_item(
                item["queue_id"],
                self.database_path,
            )
        )

        self.assertEqual(
            updated["status"],
            "SKIPPED",
        )

        self.assertEqual(
            updated["notes"],
            "目前無公開正式文件",
        )

    def test_queue_filters_and_pagination(
        self,
    ) -> None:
        """狀態、缺失類型與分頁總數一致。"""

        synchronize_dividend_review_queue(
            database_path=self.database_path,
            run_at=self.run_at,
        )

        total = count_dividend_review_queue(
            database_path=self.database_path,
            status="PENDING",
            issue_type=(
                "MISSING_SOURCE_DOCUMENT"
            ),
        )

        rows = list_dividend_review_queue(
            database_path=self.database_path,
            status="PENDING",
            issue_type=(
                "MISSING_SOURCE_DOCUMENT"
            ),
            limit=1,
            offset=1,
        )

        self.assertEqual(
            total,
            3,
        )

        self.assertEqual(
            len(rows),
            1,
        )


if __name__ == "__main__":
    unittest.main()
