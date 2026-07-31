"""Streamlit 首頁系統總覽顯示測試。"""

import unittest

from frontend.pages.home import (
    build_freshness_rows,
    build_import_batch_rows,
    format_import_error,
    format_overview_percentage,
)


def build_overview() -> dict:
    """建立首頁顯示 Helper 使用的資料。"""

    return {
        "api_status": "healthy",
        "database_type": "SQLite",
        "etfs": {
            "total_count": 4,
            "active_count": 1,
            "passive_count": 3,
            "bond_count": 1,
            "non_bond_count": 3,
            "latest_master_import_at": (
                "2026-07-30T00:05:00+00:00"
            ),
        },
        "performance": {
            "metric_code": "PRICE_RETURN",
            "source_id": "twse_stock_day",
            "etf_count": 2,
            "total_etf_count": 4,
            "coverage_pct": 50.0,
            "latest_as_of_date": "2026-07-30",
            "periods": [],
        },
        "dividends": {
            "event_count": 2,
            "etf_count": 2,
            "latest_event_date": "2026-08-10",
            "actual_component_event_count": 1,
            "actual_76w_event_count": 1,
            "source_document_event_count": 1,
            "actual_component_coverage_pct": (
                50.0
            ),
            "actual_76w_coverage_pct": 50.0,
            "source_document_coverage_pct": (
                50.0
            ),
            (
                "latest_actual_"
                "source_document_date"
            ): "2026-07-31",
        },
        "recent_import_batches": [],
    }


class TestFrontendHomeOverview(
    unittest.TestCase
):
    """驗證首頁格式化與表格契約。"""

    def test_missing_percentage_is_not_zero(
        self,
    ) -> None:
        """確認缺少覆蓋率不顯示 0%。"""

        self.assertEqual(
            format_overview_percentage(
                None
            ),
            "尚無資料",
        )

        self.assertEqual(
            format_overview_percentage(
                0
            ),
            "0.00%",
        )

    def test_freshness_rows_use_real_dates(
        self,
    ) -> None:
        """確認首頁使用 API 日期而非今天日期。"""

        rows = build_freshness_rows(
            build_overview()
        )

        values = {
            row["資料集"]: (
                row["最新資料時間"]
            )
            for row in rows
        }

        self.assertEqual(
            values["市價績效"],
            "2026-07-30",
        )

        self.assertEqual(
            values["配息事件"],
            "2026-08-10",
        )

        self.assertEqual(
            values["正式來源文件"],
            "2026-07-31",
        )

    def test_import_rows_use_string_columns(
        self,
    ) -> None:
        """確認匯入批次表格避免混合 Arrow 型別。"""

        rows = build_import_batch_rows(
            [
                {
                    "batch_id": 8,
                    "pipeline_name": (
                        "dividend_pipeline"
                    ),
                    "source_id": (
                        "twse_etfortune_dividend"
                    ),
                    "endpoint_id": (
                        "dividend_events"
                    ),
                    "started_at": (
                        "2026-07-31T01:00:00+00:00"
                    ),
                    "completed_at": (
                        "2026-07-31T01:01:00+00:00"
                    ),
                    "status": "failed",
                    "raw_record_count": 2,
                    "accepted_record_count": 1,
                    "rejected_record_count": 1,
                    "inserted_record_count": 0,
                    "updated_record_count": 0,
                    "error_message": "測試失敗",
                },
            ]
        )

        self.assertEqual(
            rows[0]["批次"],
            "#8",
        )

        self.assertEqual(
            rows[0]["狀態"],
            "失敗",
        )

        self.assertEqual(
            rows[0]["原始"],
            "2",
        )

        self.assertTrue(
            all(
                isinstance(value, str)
                for value in rows[0].values()
            )
        )

    def test_long_import_error_is_shortened(
        self,
    ) -> None:
        """確認首頁不讓錯誤訊息撐開整張表格。"""

        result = format_import_error(
            "x" * 120
        )

        self.assertEqual(
            len(result),
            101,
        )

        self.assertTrue(
            result.endswith("…")
        )


if __name__ == "__main__":
    unittest.main()
