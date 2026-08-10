"""ETF 六個月績效 Pipeline 測試。"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from datetime import date

from backend.app.database.connection import (
    get_connection,
)
from backend.app.database.init_db import (
    initialize_database,
)
from backend.app.data_sources.performance_pipeline import (
    run_six_month_performance_pipeline,
)
from backend.app.models.etf_price import (
    ETFDailyCloseRecord,
)


class TestPerformancePipeline(
    unittest.TestCase
):
    """測試六個月績效批次流程。"""

    def setUp(self) -> None:
        """建立臨時資料庫及輸出目錄。"""

        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.temp_path = Path(
            self.temp_directory.name
        )

        self.database_path = (
            self.temp_path
            / "performance_pipeline.db"
        )

        self.processed_root = (
            self.temp_path / "processed"
        )

        self.rejected_root = (
            self.temp_path / "rejected"
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
                ],
            )

            connection.commit()

        finally:
            connection.close()

    def tearDown(self) -> None:
        """清除臨時資料。"""

        self.temp_directory.cleanup()

    def build_price_record(
        self,
        code: str,
        trade_date: str,
        close_price: str,
    ) -> ETFDailyCloseRecord:
        """建立價格測試資料。"""

        return (
            ETFDailyCloseRecord
            .model_validate(
                {
                    "etf_code": code,
                    "trade_date": trade_date,
                    "close_price": close_price,
                    "source_id": (
                        "twse_stock_day"
                    ),
                }
            )
        )

    @patch(
        "backend.app.data_sources."
        "performance_pipeline."
        "fetch_price_history"
    )
    def test_pipeline_imports_valid_return(
        self,
        mock_fetch,
    ) -> None:
        """確認成功績效寫入 SQLite。"""

        def fake_fetch(
            etf_code,
            **kwargs,
        ):
            if etf_code == "0050":
                return [
                    self.build_price_record(
                        "0050",
                        "2026-01-29",
                        "100",
                    ),
                    self.build_price_record(
                        "0050",
                        "2026-07-29",
                        "120",
                    ),
                ]

            return [
                self.build_price_record(
                    "00980A",
                    "2026-05-01",
                    "100",
                ),
                self.build_price_record(
                    "00980A",
                    "2026-07-29",
                    "110",
                ),
            ]

        mock_fetch.side_effect = fake_fetch

        result = (
            run_six_month_performance_pipeline(
                database_path=(
                    self.database_path
                ),
                end_date=date(
                    2026,
                    7,
                    29
                ),
                request_interval_seconds=0,
                inter_etf_interval_seconds=0,
                processed_output_root=(
                    self.processed_root
                ),
                rejected_output_root=(
                    self.rejected_root
                ),
                save_raw_snapshots=False,
            )
        )

        self.assertEqual(
            result.candidate_count,
            2,
        )

        self.assertEqual(
            result.successful_count,
            1,
        )

        self.assertEqual(
            result.insufficient_history_count,
            1,
        )

        connection = get_connection(
            self.database_path
        )

        try:
            row = connection.execute(
                """
                SELECT
                    etf_code,
                    return_pct
                FROM etf_performance;
                """
            ).fetchone()

            self.assertEqual(
                row["etf_code"],
                "0050",
            )

            self.assertEqual(
                row["return_pct"],
                20.0,
            )

            latest_close = connection.execute(
                """
                SELECT trade_date, close_price, source_id
                FROM etf_daily_close
                WHERE etf_code = '0050'
                ORDER BY trade_date DESC
                LIMIT 1;
                """
            ).fetchone()
            self.assertEqual(latest_close["trade_date"], "2026-07-29")
            self.assertEqual(latest_close["close_price"], 120.0)
            self.assertEqual(latest_close["source_id"], "twse_stock_day")

        finally:
            connection.close()

        report = json.loads(
            result.report_path.read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(
            report["successful_count"],
            1,
        )

        self.assertFalse(
            report["includes_distributions"]
        )


if __name__ == "__main__":
    unittest.main()
