"""網站管理資料總覽測試。"""

import unittest

from frontend.pages.admin_overview import (
    build_freshness_rows,
    build_import_batch_rows,
    format_admin_percentage,
)


class TestFrontendAdminOverview(unittest.TestCase):
    def test_missing_percentage_remains_distinct_from_zero(self) -> None:
        self.assertEqual(format_admin_percentage(None), "尚無資料")
        self.assertEqual(format_admin_percentage(0), "0.00%")

    def test_freshness_rows_keep_missing_dates_visible(self) -> None:
        rows = build_freshness_rows(
            {
                "etfs": {"latest_master_import_at": None},
                "performance": {"latest_as_of_date": "2026-07-30"},
                "dividends": {
                    "latest_event_date": "2026-08-10",
                    "latest_actual_source_document_date": None,
                },
            }
        )
        self.assertEqual(rows[0]["最新資料時間"], "尚未取得")
        self.assertEqual(rows[1]["最新資料時間"], "2026-07-30")
        self.assertEqual(rows[3]["最新資料時間"], "尚未取得")

    def test_import_rows_translate_status_and_preserve_error(self) -> None:
        rows = build_import_batch_rows(
            [
                {
                    "batch_id": 8,
                    "pipeline_name": "dividend_pipeline",
                    "source_id": "issuer",
                    "status": "failed",
                    "started_at": "2026-08-25T02:00:00+00:00",
                    "completed_at": None,
                    "accepted_record_count": 3,
                    "rejected_record_count": 1,
                    "error_message": "來源格式異常",
                }
            ]
        )
        self.assertEqual(rows[0]["狀態"], "失敗")
        self.assertEqual(rows[0]["接受／拒絕"], "3／1")
        self.assertEqual(rows[0]["錯誤"], "來源格式異常")


if __name__ == "__main__":
    unittest.main()
