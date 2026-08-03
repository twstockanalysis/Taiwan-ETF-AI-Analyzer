"""ETF 績效 Repository 測試。"""

import tempfile
import unittest
from pathlib import Path

from backend.app.database.connection import (
    get_connection,
)
from backend.app.database.init_db import (
    initialize_database,
)
from backend.app.models.etf_analysis import (
    ETFPerformanceImportRecord,
)
from backend.app.repositories.performance_repository import (
    list_latest_performance_ranking,
    upsert_performance_records,
)


class TestPerformanceRepository(
    unittest.TestCase
):
    """測試 ETF 績效 Upsert 與排行榜。"""

    def setUp(self) -> None:
        """建立臨時資料庫。"""

        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.database_path = (
            Path(self.temp_directory.name)
            / "performance.db"
        )

        initialize_database(
            self.database_path
        )

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
                        "00980A",
                        "主動式測試ETF",
                        1,
                        0,
                        "2025-05-05",
                    ),
                    (
                        "00679B",
                        "債券測試ETF",
                        0,
                        1,
                        "2017-01-17",
                    ),
                ],
            )

            connection.commit()

        finally:
            connection.close()

    def tearDown(self) -> None:
        """清除臨時資料。"""

        self.temp_directory.cleanup()

    def build_record(
        self,
        code: str,
        as_of_date: str,
        return_pct: str,
    ) -> ETFPerformanceImportRecord:
        """建立績效測試資料。"""

        return (
            ETFPerformanceImportRecord
            .model_validate(
                {
                    "etf_code": code,
                    "as_of_date": as_of_date,
                    "period_code": "6M",
                    "return_pct": return_pct,
                    "source_id": (
                        "twse_stock_day"
                    ),
                }
            )
        )

    def test_new_records_are_inserted(
        self,
    ) -> None:
        """確認新績效可以新增。"""

        summary = (
            upsert_performance_records(
                records=[
                    self.build_record(
                        "0050",
                        "2026-07-29",
                        "20",
                    ),
                ],
                database_path=(
                    self.database_path
                ),
            )
        )

        self.assertEqual(
            summary.inserted_records,
            1,
        )

        self.assertEqual(
            summary.updated_records,
            0,
        )

    def test_existing_record_is_updated(
        self,
    ) -> None:
        """確認同一績效鍵值可以更新。"""

        record = self.build_record(
            "0050",
            "2026-07-29",
            "20",
        )

        upsert_performance_records(
            records=[record],
            database_path=self.database_path,
        )

        summary = (
            upsert_performance_records(
                records=[
                    self.build_record(
                        "0050",
                        "2026-07-29",
                        "21.5",
                    ),
                ],
                database_path=(
                    self.database_path
                ),
            )
        )

        self.assertEqual(
            summary.inserted_records,
            0,
        )

        self.assertEqual(
            summary.updated_records,
            1,
        )

    def test_ranking_uses_latest_record(
        self,
    ) -> None:
        """確認每檔 ETF 只取最新績效。"""

        upsert_performance_records(
            records=[
                self.build_record(
                    "0050",
                    "2026-06-30",
                    "50",
                ),
                self.build_record(
                    "0050",
                    "2026-07-29",
                    "10",
                ),
                self.build_record(
                    "00980A",
                    "2026-07-29",
                    "15",
                ),
            ],
            database_path=self.database_path,
        )

        rows = list_latest_performance_ranking(
            database_path=self.database_path,
        )

        self.assertEqual(
            rows[0]["etf_code"],
            "00980A",
        )

        self.assertEqual(
            rows[1]["etf_code"],
            "0050",
        )

        self.assertEqual(
            rows[1]["return_pct"],
            10.0,
        )

    def test_bond_etf_is_excluded(
        self,
    ) -> None:
        """確認排行榜預設排除債券 ETF。"""

        upsert_performance_records(
            records=[
                self.build_record(
                    "0050",
                    "2026-07-29",
                    "10",
                ),
                self.build_record(
                    "00679B",
                    "2026-07-29",
                    "99",
                ),
            ],
            database_path=self.database_path,
        )

        rows = list_latest_performance_ranking(
            database_path=self.database_path,
        )

        codes = {
            row["etf_code"]
            for row in rows
        }

        self.assertEqual(
            codes,
            {
                "0050",
            },
        )


if __name__ == "__main__":
    unittest.main()