"""首頁系統資料總覽 Repository 測試。"""

import tempfile
import unittest
from pathlib import Path

from backend.app.database.connection import (
    get_connection,
)
from backend.app.database.init_db import (
    initialize_database,
)
from backend.app.repositories.system_overview_repository import (
    build_system_overview,
)


class TestSystemOverviewRepository(
    unittest.TestCase
):
    """測試首頁統計、日期與最近批次。"""

    def setUp(self) -> None:
        """建立獨立測試資料庫。"""

        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.database_path = (
            Path(self.temp_directory.name)
            / "system_overview.db"
        )

        initialize_database(
            self.database_path
        )

    def tearDown(self) -> None:
        """刪除測試資料庫。"""

        self.temp_directory.cleanup()

    def insert_overview_data(
        self,
    ) -> None:
        """寫入可驗證所有摘要欄位的資料。"""

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
                    is_bond,
                    listing_date
                )
                VALUES (?, ?, ?, ?, ?);
                """,
                [
                    (
                        "0050",
                        "元大台灣50",
                        0,
                        0,
                        "2003-06-30",
                    ),
                    (
                        "00878",
                        "國泰永續高股息",
                        0,
                        0,
                        "2020-07-20",
                    ),
                    (
                        "00980A",
                        "主動式測試ETF",
                        1,
                        0,
                        "2025-05-05",
                    ),
                    (
                        "00679B",
                        "元大美債20年",
                        0,
                        1,
                        "2017-01-11",
                    ),
                ],
            )

            connection.executemany(
                """
                INSERT INTO import_batch (
                    pipeline_name,
                    source_id,
                    endpoint_id,
                    started_at,
                    completed_at,
                    status,
                    raw_record_count,
                    accepted_record_count,
                    rejected_record_count,
                    inserted_record_count,
                    updated_record_count,
                    error_message
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?
                );
                """,
                [
                    (
                        "etf_master_pipeline",
                        "twse_openapi",
                        "twse_fund_master",
                        "2026-07-30T00:00:00+00:00",
                        "2026-07-30T00:05:00+00:00",
                        "success",
                        4,
                        4,
                        0,
                        4,
                        0,
                        None,
                    ),
                    (
                        "performance_pipeline",
                        "twse_stock_day",
                        "multi_period",
                        "2026-07-30T01:00:00+00:00",
                        "2026-07-30T01:10:00+00:00",
                        "success",
                        6,
                        6,
                        0,
                        6,
                        0,
                        None,
                    ),
                    (
                        "dividend_pipeline",
                        "twse_etfortune_dividend",
                        "dividend_events",
                        "2026-07-31T01:00:00+00:00",
                        "2026-07-31T01:01:00+00:00",
                        "failed",
                        2,
                        1,
                        1,
                        0,
                        0,
                        "測試失敗",
                    ),
                    (
                        "actual_dividend_pipeline",
                        "official_notice",
                        "reviewed_json",
                        "2026-07-31T02:00:00+00:00",
                        "2026-07-31T02:02:00+00:00",
                        "success",
                        1,
                        1,
                        0,
                        1,
                        0,
                        None,
                    ),
                ],
            )

            connection.executemany(
                """
                INSERT INTO etf_performance (
                    etf_code,
                    as_of_date,
                    period_code,
                    metric_code,
                    return_pct,
                    source_id
                )
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                [
                    (
                        "0050",
                        "2026-07-30",
                        "1M",
                        "PRICE_RETURN",
                        5.0,
                        "twse_stock_day",
                    ),
                    (
                        "0050",
                        "2026-07-30",
                        "6M",
                        "PRICE_RETURN",
                        20.0,
                        "twse_stock_day",
                    ),
                    (
                        "00878",
                        "2026-07-29",
                        "1M",
                        "PRICE_RETURN",
                        3.0,
                        "twse_stock_day",
                    ),
                    (
                        "00878",
                        "2026-07-29",
                        "3M",
                        "PRICE_RETURN",
                        8.0,
                        "twse_stock_day",
                    ),
                    (
                        "00878",
                        "2026-07-29",
                        "6M",
                        "PRICE_RETURN",
                        12.0,
                        "twse_stock_day",
                    ),
                    (
                        "00878",
                        "2026-07-29",
                        "1Y",
                        "PRICE_RETURN",
                        18.0,
                        "twse_stock_day",
                    ),
                ],
            )

            first_dividend = connection.execute(
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
                VALUES (
                    '00878',
                    'event-1',
                    '2026-07-01',
                    '2026-07-15',
                    '2026-07-21',
                    '2026-08-10',
                    0.7,
                    'TWD',
                    'official'
                );
                """
            )

            second_dividend = connection.execute(
                """
                INSERT INTO etf_dividend (
                    etf_code,
                    source_event_id,
                    announcement_date,
                    ex_dividend_date,
                    amount_per_unit,
                    currency,
                    source_id
                )
                VALUES (
                    '0050',
                    'event-2',
                    '2026-06-01',
                    '2026-06-20',
                    1.0,
                    'TWD',
                    'official'
                );
                """
            )

            connection.execute(
                """
                INSERT INTO
                dividend_source_document (
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
                VALUES (
                    'official_notice',
                    'document-1',
                    1,
                    'https://example.test/document-1',
                    '2026-07-31',
                    '2026-07-31T02:00:00+00:00',
                    'text/html',
                    'ACTUAL',
                    ?,
                    'raw/document-1.html',
                    'raw/document-1.json',
                    'parsed',
                    4
                );
                """,
                (
                    "a" * 64,
                ),
            )

            connection.execute(
                """
                INSERT INTO
                etf_dividend_component (
                    dividend_id,
                    component_code,
                    component_basis,
                    component_name,
                    ratio_pct,
                    source_id,
                    import_batch_id
                )
                VALUES (
                    ?,
                    '76W',
                    'ACTUAL',
                    '實際所得類別 76W',
                    100,
                    'official_notice',
                    4
                );
                """,
                (
                    first_dividend.lastrowid,
                ),
            )

            connection.execute(
                """
                INSERT INTO
                etf_dividend_component (
                    dividend_id,
                    component_code,
                    component_basis,
                    component_name,
                    ratio_pct,
                    source_id
                )
                VALUES (
                    ?,
                    'EST_DIVIDEND',
                    'ESTIMATED',
                    '預估股利所得',
                    100,
                    'twse_etfortune_dividend'
                );
                """,
                (
                    second_dividend.lastrowid,
                ),
            )

            connection.commit()

        finally:
            connection.close()

    def test_empty_database_preserves_missing_semantics(
        self,
    ) -> None:
        """確認空資料庫不偽造日期或 0% 覆蓋率。"""

        overview = build_system_overview(
            self.database_path
        )

        self.assertEqual(
            overview["etfs"]["total_count"],
            0,
        )

        self.assertIsNone(
            overview["performance"][
                "coverage_pct"
            ]
        )

        self.assertIsNone(
            overview["dividends"][
                "actual_76w_coverage_pct"
            ]
        )

        self.assertIsNone(
            overview["dividends"][
                "latest_event_date"
            ]
        )

        self.assertEqual(
            [
                item["period_code"]
                for item in overview[
                    "performance"
                ]["periods"]
            ],
            [
                "1M",
                "3M",
                "6M",
                "1Y",
            ],
        )

    def test_overview_counts_dates_and_coverage(
        self,
    ) -> None:
        """確認分類、績效與配息摘要一致。"""

        self.insert_overview_data()

        overview = build_system_overview(
            self.database_path,
            recent_batch_limit=3,
        )

        etfs = overview["etfs"]

        self.assertEqual(
            (
                etfs["total_count"],
                etfs["active_count"],
                etfs["passive_count"],
                etfs["bond_count"],
                etfs["non_bond_count"],
            ),
            (
                4,
                1,
                3,
                1,
                3,
            ),
        )

        self.assertEqual(
            etfs["latest_master_import_at"],
            "2026-07-30T00:05:00+00:00",
        )

        performance = overview[
            "performance"
        ]

        self.assertEqual(
            performance["etf_count"],
            2,
        )

        self.assertEqual(
            performance["coverage_pct"],
            50.0,
        )

        self.assertEqual(
            performance[
                "latest_as_of_date"
            ],
            "2026-07-30",
        )

        period_counts = {
            item["period_code"]: (
                item["etf_count"]
            )
            for item in performance[
                "periods"
            ]
        }

        self.assertEqual(
            period_counts,
            {
                "1M": 2,
                "3M": 1,
                "6M": 2,
                "1Y": 1,
            },
        )

        dividends = overview[
            "dividends"
        ]

        self.assertEqual(
            dividends["event_count"],
            2,
        )

        self.assertEqual(
            dividends[
                "latest_event_date"
            ],
            "2026-08-10",
        )

        self.assertEqual(
            dividends[
                "actual_component_coverage_pct"
            ],
            50.0,
        )

        self.assertEqual(
            dividends[
                "actual_76w_coverage_pct"
            ],
            50.0,
        )

        self.assertEqual(
            dividends[
                "source_document_coverage_pct"
            ],
            50.0,
        )

        self.assertEqual(
            dividends[
                (
                    "latest_actual_"
                    "source_document_date"
                )
            ],
            "2026-07-31",
        )

        recent_batches = overview[
            "recent_import_batches"
        ]

        self.assertEqual(
            len(recent_batches),
            3,
        )

        self.assertEqual(
            recent_batches[0][
                "pipeline_name"
            ],
            "actual_dividend_pipeline",
        )

        self.assertEqual(
            recent_batches[1]["status"],
            "failed",
        )

        self.assertEqual(
            recent_batches[1][
                "error_message"
            ],
            "測試失敗",
        )

    def test_recent_batch_limit_is_validated(
        self,
    ) -> None:
        """確認最近批次上限不可超出契約。"""

        with self.assertRaises(
            ValueError
        ):
            build_system_overview(
                self.database_path,
                recent_batch_limit=0,
            )

        with self.assertRaises(
            ValueError
        ):
            build_system_overview(
                self.database_path,
                recent_batch_limit=21,
            )


if __name__ == "__main__":
    unittest.main()
