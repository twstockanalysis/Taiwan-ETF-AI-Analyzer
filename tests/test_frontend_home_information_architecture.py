"""V3-8 首頁資訊架構測試。"""

import unittest

from frontend.pages.home import build_home_data_dates, format_overview_percentage


class TestFrontendHomeInformationArchitecture(unittest.TestCase):
    def test_missing_percentage_is_not_zero(self) -> None:
        self.assertEqual(format_overview_percentage(None), "尚無資料")
        self.assertEqual(format_overview_percentage(0), "0.00%")

    def test_home_uses_public_data_dates_only(self) -> None:
        dates = build_home_data_dates(
            {
                "performance": {"latest_as_of_date": "2026-07-30"},
                "dividends": {"latest_event_date": "2026-08-10"},
                "api_status": "healthy",
                "database_type": "SQLite",
                "recent_import_batches": [{"batch_id": 8}],
            }
        )

        self.assertEqual(
            dates,
            ["績效資料至 2026-07-30", "配息事件至 2026-08-10"],
        )
        self.assertNotIn("FastAPI", " ".join(dates))
        self.assertNotIn("SQLite", " ".join(dates))
        self.assertNotIn("batch", " ".join(dates).lower())

    def test_missing_dates_remain_missing(self) -> None:
        dates = build_home_data_dates(
            {
                "performance": {"latest_as_of_date": None},
                "dividends": {"latest_event_date": None},
            }
        )
        self.assertEqual(
            dates,
            ["績效資料至 尚未取得", "配息事件至 尚未取得"],
        )


if __name__ == "__main__":
    unittest.main()
