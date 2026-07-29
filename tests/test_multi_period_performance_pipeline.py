"""ETF 多期間績效 Pipeline 測試。"""

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from backend.app.database.connection import (
    get_connection,
)
from backend.app.database.init_db import (
    initialize_database,
)
from backend.app.data_sources.performance_pipeline import (
    run_multi_period_performance_pipeline,
)
from backend.app.models.etf_price import (
    ETFDailyCloseRecord,
)


class TestMultiPeriodPerformancePipeline(
    unittest.TestCase
):
    """測試多期間績效批次流程。"""

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
            / "multi_period_pipeline.db"
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
                        "00999A",
                        "新上市測試ETF",
                        1,
                        0,
                        "2026-05-01",
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
    def test_pipeline_downloads_once_for_all_periods(
        self,
        mock_fetch,
    ) -> None:
        """確認每檔只下載一次並建立四個期間。"""

        mock_fetch.return_value = [
            self.build_price_record(
                "0050",
                "2025-07-29",
                "80",
            ),
            self.build_price_record(
                "0050",
                "2026-01-29",
                "100",
            ),
            self.build_price_record(
                "0050",
                "2026-04-29",
                "110",
            ),
            self.build_price_record(
                "0050",
                "2026-06-29",
                "120",
            ),
            self.build_price_record(
                "0050",
                "2026-07-29",
                "132",
            ),
        ]

        result = (
            run_multi_period_performance_pipeline(
                database_path=(
                    self.database_path
                ),
                end_date=date(
                    2026,
                    7,
                    29,
                ),
                codes=["0050"],
                periods=[
                    "1M",
                    "3M",
                    "6M",
                    "1Y",
                ],
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

        mock_fetch.assert_called_once()

        self.assertEqual(
            mock_fetch.call_args.kwargs[
                "month_count"
            ],
            14,
        )

        self.assertEqual(
            result.candidate_count,
            1,
        )

        self.assertEqual(
            result.successful_count,
            4,
        )

        self.assertEqual(
            result.insufficient_history_count,
            0,
        )

        connection = get_connection(
            self.database_path
        )

        try:
            rows = connection.execute(
                """
                SELECT
                    period_code,
                    metric_code,
                    return_pct
                FROM etf_performance
                WHERE etf_code = ?
                ORDER BY CASE period_code
                    WHEN '1M' THEN 1
                    WHEN '3M' THEN 2
                    WHEN '6M' THEN 3
                    WHEN '1Y' THEN 4
                    ELSE 99
                END;
                """,
                ("0050",),
            ).fetchall()

        finally:
            connection.close()

        self.assertEqual(
            [row["period_code"] for row in rows],
            ["1M", "3M", "6M", "1Y"],
        )

        self.assertTrue(
            all(
                row["metric_code"]
                == "PRICE_RETURN"
                for row in rows
            )
        )

        self.assertEqual(
            [row["return_pct"] for row in rows],
            [10.0, 20.0, 32.0, 65.0],
        )

        report = json.loads(
            result.report_path.read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(
            report["period_codes"],
            ["1M", "3M", "6M", "1Y"],
        )

        self.assertEqual(
            report["download_month_count"],
            14,
        )

    @patch(
        "backend.app.data_sources."
        "performance_pipeline."
        "fetch_price_history"
    )
    def test_new_etf_keeps_short_period_return(
        self,
        mock_fetch,
    ) -> None:
        """確認新 ETF 保留短期績效。"""

        mock_fetch.return_value = [
            self.build_price_record(
                "00999A",
                "2026-06-29",
                "100",
            ),
            self.build_price_record(
                "00999A",
                "2026-07-29",
                "110",
            ),
        ]

        result = (
            run_multi_period_performance_pipeline(
                database_path=(
                    self.database_path
                ),
                end_date=date(
                    2026,
                    7,
                    29,
                ),
                codes=["00999A"],
                periods=[
                    "1M",
                    "3M",
                    "6M",
                    "1Y",
                ],
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
            1,
        )

        self.assertEqual(
            result.successful_count,
            1,
        )

        self.assertEqual(
            result.insufficient_history_count,
            3,
        )

        summary_by_period = {
            summary.period_code.value: summary
            for summary in result.period_summaries
        }

        self.assertEqual(
            summary_by_period[
                "1M"
            ].successful_count,
            1,
        )

        self.assertEqual(
            summary_by_period[
                "1M"
            ].coverage_pct,
            100.0,
        )

        for period_code in (
            "3M",
            "6M",
            "1Y",
        ):
            self.assertEqual(
                summary_by_period[
                    period_code
                ].insufficient_history_count,
                1,
            )

        connection = get_connection(
            self.database_path
        )

        try:
            rows = connection.execute(
                """
                SELECT
                    period_code,
                    return_pct
                FROM etf_performance
                WHERE etf_code = ?;
                """,
                ("00999A",),
            ).fetchall()

        finally:
            connection.close()

        self.assertEqual(
            len(rows),
            1,
        )

        self.assertEqual(
            rows[0]["period_code"],
            "1M",
        )

        self.assertEqual(
            rows[0]["return_pct"],
            10.0,
        )


if __name__ == "__main__":
    unittest.main()
