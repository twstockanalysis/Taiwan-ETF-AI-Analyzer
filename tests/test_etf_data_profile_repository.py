"""ETF 詳細頁資料概況 Repository 測試。"""

import tempfile
import unittest
from pathlib import Path

from backend.app.database.connection import (
    get_connection,
)
from backend.app.database.init_db import (
    initialize_database,
)
from backend.app.repositories.etf_data_profile_repository import (
    build_etf_data_profile,
)


class TestETFDataProfileRepository(
    unittest.TestCase
):
    """測試 ETF 資料來源與新鮮度查詢。"""

    def setUp(self) -> None:
        """建立獨立測試資料庫。"""

        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.database_path = (
            Path(self.temp_directory.name)
            / "etf_data_profile.db"
        )

        initialize_database(
            self.database_path
        )

    def tearDown(self) -> None:
        """移除測試資料庫。"""

        self.temp_directory.cleanup()

    def insert_etf(
        self,
        code: str = "0050",
    ) -> None:
        """新增測試 ETF 主資料。"""

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
                    is_bond,
                    listing_date
                )
                VALUES (
                    ?,
                    '元大台灣50',
                    0,
                    0,
                    '2003-06-30'
                );
                """,
                (
                    code,
                ),
            )

            connection.commit()

        finally:
            connection.close()

    def test_missing_etf_returns_none(
        self,
    ) -> None:
        """確認不存在 ETF 不建立資料概況。"""

        self.assertIsNone(
            build_etf_data_profile(
                "UNKNOWN",
                self.database_path,
            )
        )

    def test_empty_profile_preserves_missing_dates(
        self,
    ) -> None:
        """確認只有主資料時，其餘區塊維持空值。"""

        self.insert_etf()

        profile = build_etf_data_profile(
            "0050",
            self.database_path,
        )

        self.assertIsNotNone(
            profile
        )

        assert profile is not None

        self.assertEqual(
            profile["master"]["sources"][0][
                "source_id"
            ],
            "twse_openapi",
        )

        self.assertEqual(
            profile["performance"][
                "record_count"
            ],
            0,
        )

        self.assertEqual(
            profile["performance"][
                "available_periods"
            ],
            [],
        )

        self.assertIsNone(
            profile["performance"][
                "latest_as_of_date"
            ]
        )

        self.assertEqual(
            profile["dividends"][
                "event_count"
            ],
            0,
        )

        self.assertEqual(
            profile["actual_dividend"][
                "actual_76w_event_count"
            ],
            0,
        )

    def test_profile_uses_etf_specific_data(
        self,
    ) -> None:
        """確認來源、日期與正式 76W 統計來自指定 ETF。"""

        self.insert_etf()

        connection = get_connection(
            self.database_path
        )

        try:
            connection.executescript(
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
                VALUES
                    (
                        1,
                        'etf_master_pipeline',
                        'twse_openapi',
                        'twse_fund_master',
                        '2026-07-30T00:00:00+00:00',
                        '2026-07-30T00:05:00+00:00',
                        'success'
                    ),
                    (
                        2,
                        'performance_pipeline',
                        'twse_stock_day',
                        'twse_stock_day',
                        '2026-07-30T01:00:00+00:00',
                        '2026-07-30T01:05:00+00:00',
                        'success'
                    ),
                    (
                        3,
                        'dividend_pipeline',
                        'twse_etfortune_dividend',
                        'twse_etfortune_dividend',
                        '2026-07-30T02:00:00+00:00',
                        '2026-07-30T02:05:00+00:00',
                        'success'
                    ),
                    (
                        4,
                        'actual_dividend_pipeline',
                        'cathay_actual_dividend_announcement',
                        'cathay_announcement',
                        '2026-07-30T03:00:00+00:00',
                        '2026-07-30T03:05:00+00:00',
                        'success'
                    );

                INSERT INTO etf_performance (
                    etf_code,
                    as_of_date,
                    period_code,
                    metric_code,
                    return_pct,
                    source_id,
                    import_batch_id
                )
                VALUES
                    (
                        '0050',
                        '2026-07-30',
                        '1M',
                        'PRICE_RETURN',
                        5,
                        'twse_stock_day',
                        2
                    ),
                    (
                        '0050',
                        '2026-07-30',
                        '6M',
                        'PRICE_RETURN',
                        12,
                        'twse_stock_day',
                        2
                    );

                INSERT INTO etf_dividend (
                    id,
                    etf_code,
                    source_event_id,
                    ex_dividend_date,
                    payment_date,
                    amount_per_unit,
                    currency,
                    source_id,
                    import_batch_id
                )
                VALUES
                    (
                        1,
                        '0050',
                        '0050-2026-1',
                        '2026-07-15',
                        '2026-08-10',
                        1.2,
                        'TWD',
                        'twse_etfortune_dividend',
                        3
                    );

                INSERT INTO etf_dividend_component (
                    dividend_id,
                    component_code,
                    component_basis,
                    component_name,
                    ratio_pct,
                    source_id,
                    import_batch_id
                )
                VALUES
                    (
                        1,
                        '76W',
                        'ACTUAL',
                        '國內財產交易所得',
                        100,
                        'cathay_actual_dividend_announcement',
                        4
                    );

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
                VALUES (
                    'cathay_actual_dividend_announcement',
                    'announcement-1',
                    1,
                    'https://www.cathaysite.com.tw/announcement/1',
                    '2026-07-20',
                    '2026-07-20T00:00:00+00:00',
                    'text/html',
                    'ACTUAL',
                    'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                    'data/raw/a.html',
                    'data/raw/a.json',
                    'parsed',
                    4
                );
                """
            )

            connection.commit()

        finally:
            connection.close()

        profile = build_etf_data_profile(
            "0050",
            self.database_path,
        )

        assert profile is not None

        self.assertEqual(
            profile["master"][
                "latest_import_at"
            ],
            "2026-07-30T00:05:00+00:00",
        )

        self.assertEqual(
            profile["performance"][
                "available_periods"
            ],
            [
                "1M",
                "6M",
            ],
        )

        self.assertEqual(
            profile["performance"][
                "latest_as_of_date"
            ],
            "2026-07-30",
        )

        self.assertEqual(
            profile["dividends"][
                "latest_event_date"
            ],
            "2026-08-10",
        )

        actual = profile[
            "actual_dividend"
        ]

        self.assertEqual(
            actual[
                "actual_component_event_count"
            ],
            1,
        )

        self.assertEqual(
            actual[
                "actual_76w_event_count"
            ],
            1,
        )

        self.assertEqual(
            actual[
                "source_document_event_count"
            ],
            1,
        )

        self.assertEqual(
            actual[
                "latest_source_document_date"
            ],
            "2026-07-20",
        )

        self.assertEqual(
            actual["sources"][0][
                "display_name"
            ],
            "國泰證券投資信託股份有限公司",
        )


if __name__ == "__main__":
    unittest.main()
