"""正式配息資料品質 API 測試。"""

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.api.dependencies import (
    get_database_path,
)
from backend.app.database.connection import (
    get_connection,
)
from backend.app.database.init_db import (
    initialize_database,
)
from backend.app.main import create_app
from backend.app.repositories.dividend_quality_repository import (
    synchronize_dividend_review_queue,
)


class TestDividendQualityAPI(
    unittest.TestCase
):
    """驗證覆蓋率與待處理佇列 API。"""

    def setUp(self) -> None:
        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.database_path = (
            Path(self.temp_directory.name)
            / "quality_api.db"
        )

        initialize_database(
            self.database_path
        )

        self.insert_test_data()

        synchronize_dividend_review_queue(
            database_path=self.database_path,
            run_at=datetime(
                2026,
                7,
                31,
                tzinfo=timezone.utc,
            ),
        )

        self.application = create_app()

        self.application.dependency_overrides[
            get_database_path
        ] = lambda: self.database_path

        self.client = TestClient(
            self.application
        )

    def tearDown(self) -> None:
        self.client.close()
        self.application.dependency_overrides = {}
        self.temp_directory.cleanup()

    def insert_test_data(self) -> None:
        connection = get_connection(
            self.database_path
        )

        try:
            connection.executemany(
                """
                INSERT INTO etf_master (
                    code,
                    name,
                    is_active,
                    is_bond
                )
                VALUES (?, ?, ?, ?);
                """,
                [
                    (
                        "00918",
                        "大華優利高填息30",
                        0,
                        0,
                    ),
                    (
                        "0050",
                        "元大台灣50",
                        0,
                        0,
                    ),
                ],
            )

            connection.execute(
                """
                INSERT INTO import_batch (
                    id,
                    pipeline_name,
                    source_id,
                    endpoint_id,
                    started_at,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    1,
                    "actual_dividend_pipeline",
                    "official_notice",
                    "actual_dividend_json_import",
                    "2026-07-31T00:00:00+00:00",
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
                        "00918",
                        "event-estimated",
                        "2026-03-18",
                        0.7,
                        "TWD",
                        "twse_etfortune_dividend",
                    ),
                    (
                        2,
                        "00918",
                        "event-actual",
                        "2026-06-18",
                        0.7,
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
                    ratio_pct,
                    source_id,
                    import_batch_id
                )
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                [
                    (
                        1,
                        "EST_REALIZED_CAPITAL_GAIN",
                        "ESTIMATED",
                        100.0,
                        "twse_etfortune_dividend",
                        None,
                    ),
                    (
                        2,
                        "76W",
                        "ACTUAL",
                        0.0,
                        "official_notice",
                        1,
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
                    downloaded_at,
                    content_type,
                    information_basis,
                    checksum_sha256,
                    snapshot_path,
                    metadata_path,
                    parse_status,
                    import_batch_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    "official_notice",
                    "document-1",
                    1,
                    "https://example.com/document-1",
                    "2026-07-31T00:00:00+00:00",
                    "text/html",
                    "ACTUAL",
                    "b" * 64,
                    "raw/document-1.html",
                    "raw/document-1.meta.json",
                    "parsed",
                    1,
                ),
            )

            connection.commit()

        finally:
            connection.close()

    def test_coverage_endpoint(
        self,
    ) -> None:
        response = self.client.get(
            (
                "/api/v1/data-quality/dividends/"
                "actual-coverage"
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            data["total_dividend_count"],
            2,
        )

        self.assertEqual(
            data[
                "actual_component_event_count"
            ],
            1,
        )

        self.assertEqual(
            data["actual_76w_event_count"],
            1,
        )

        self.assertEqual(
            data[
                "source_document_event_count"
            ],
            1,
        )

        self.assertEqual(
            data["actual_76w_coverage_pct"],
            50.0,
        )

    def test_etf_without_dividends_returns_null_rates(
        self,
    ) -> None:
        response = self.client.get(
            (
                "/api/v1/data-quality/dividends/"
                "actual-coverage"
            ),
            params={
                "etf_code": "0050",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            data["total_dividend_count"],
            0,
        )

        self.assertIsNone(
            data[
                "actual_component_coverage_pct"
            ]
        )

    def test_missing_etf_returns_404(
        self,
    ) -> None:
        response = self.client.get(
            (
                "/api/v1/data-quality/dividends/"
                "actual-coverage"
            ),
            params={
                "etf_code": "UNKNOWN",
            },
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_review_queue_filters_and_detail(
        self,
    ) -> None:
        response = self.client.get(
            (
                "/api/v1/data-quality/dividends/"
                "review-queue"
            ),
            params={
                "status": "PENDING",
                "etf_code": "00918",
                "issue_type": (
                    "MISSING_ACTUAL_COMPONENTS"
                ),
                "limit": 1,
                "offset": 0,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            data["total"],
            1,
        )

        queue_id = data["items"][0][
            "queue_id"
        ]

        detail = self.client.get(
            (
                "/api/v1/data-quality/dividends/"
                f"review-queue/{queue_id}"
            )
        )

        self.assertEqual(
            detail.status_code,
            200,
        )

        self.assertEqual(
            detail.json()["queue_id"],
            queue_id,
        )

    def test_missing_queue_item_returns_404(
        self,
    ) -> None:
        response = self.client.get(
            (
                "/api/v1/data-quality/dividends/"
                "review-queue/999"
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_invalid_filters_return_422(
        self,
    ) -> None:
        invalid_status = self.client.get(
            (
                "/api/v1/data-quality/dividends/"
                "review-queue"
            ),
            params={
                "status": "UNKNOWN",
            },
        )

        invalid_limit = self.client.get(
            (
                "/api/v1/data-quality/dividends/"
                "review-queue"
            ),
            params={
                "limit": 0,
            },
        )

        self.assertEqual(
            invalid_status.status_code,
            422,
        )

        self.assertEqual(
            invalid_limit.status_code,
            422,
        )

    def test_openapi_contains_quality_paths(
        self,
    ) -> None:
        paths = self.application.openapi()[
            "paths"
        ]

        expected = {
            (
                "/api/v1/data-quality/dividends/"
                "actual-coverage"
            ),
            (
                "/api/v1/data-quality/dividends/"
                "review-queue"
            ),
            (
                "/api/v1/data-quality/dividends/"
                "review-queue/{queue_id}"
            ),
        }

        self.assertTrue(
            expected.issubset(
                paths
            )
        )


if __name__ == "__main__":
    unittest.main()
