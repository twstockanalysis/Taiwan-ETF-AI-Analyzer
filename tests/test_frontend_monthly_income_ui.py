"""ETF 詳細頁每月領息顯示測試。"""

import inspect
import unittest

from frontend.pages.etf_detail import (
    build_monthly_income_chart_rows,
    build_monthly_income_rows,
    render_etf_detail,
    render_monthly_income_distribution,
)


class TestFrontendMonthlyIncomeUI(
    unittest.TestCase
):
    """驗證月份分布的顯示語意。"""

    def build_distribution(self) -> dict:
        """建立固定 12 個月的畫面資料。"""

        months = [
            {
                "month": month,
                "event_count": 0,
                "observed_year_count": 0,
                "total_amount_per_unit": None,
                "average_amount_per_event": None,
                "latest_payment_date": None,
            }
            for month in range(1, 13)
        ]

        months[0].update(
            {
                "event_count": 2,
                "observed_year_count": 2,
                "total_amount_per_unit": 1.0,
                "average_amount_per_event": 0.5,
                "latest_payment_date": "2026-01-15",
            }
        )

        return {
            "etf_code": "00918",
            "name": "大華優利高填息30",
            "date_basis": "PAYMENT_DATE",
            "lookback_years": 3,
            "as_of_date": "2026-01-15",
            "window_start_date": "2023-01-16",
            "total_dividend_event_count": 3,
            "dated_dividend_event_count": 2,
            "missing_payment_date_count": 1,
            "analysis_event_count": 2,
            "covered_month_count": 1,
            "covered_month_occurrence_count": 2,
            "analysis_currency": "TWD",
            "has_mixed_currencies": False,
            "total_amount_per_unit": 1.0,
            "months": months,
        }

    def test_rows_always_show_january_to_december(
        self,
    ) -> None:
        """確認表格固定呈現 1–12 月。"""

        rows = build_monthly_income_rows(
            self.build_distribution()
        )

        self.assertEqual(
            len(rows),
            12,
        )

        self.assertEqual(
            [row["月份"] for row in rows],
            [
                f"{month} 月"
                for month in range(1, 13)
            ],
        )

    def test_no_event_month_is_not_a_fake_amount(
        self,
    ) -> None:
        """確認零筆事件不會顯示為零元。"""

        february = build_monthly_income_rows(
            self.build_distribution()
        )[1]

        self.assertEqual(
            february["狀態"],
            "近年無入帳紀錄",
        )

        self.assertEqual(
            february["配息事件"],
            "0 次",
        )

        self.assertEqual(
            february["每單位累計"],
            "—",
        )

    def test_formal_zero_amount_remains_zero(
        self,
    ) -> None:
        """確認有事件的正式零金額不變成缺資料。"""

        distribution = (
            self.build_distribution()
        )

        distribution["months"][0][
            "total_amount_per_unit"
        ] = 0.0

        distribution["months"][0][
            "average_amount_per_event"
        ] = 0.0

        january = build_monthly_income_rows(
            distribution
        )[0]

        self.assertEqual(
            january["每單位累計"],
            "0 TWD",
        )

        self.assertEqual(
            january["單次平均"],
            "0 TWD",
        )

    def test_mixed_currencies_are_not_displayed_as_sum(
        self,
    ) -> None:
        """確認混合幣別以明確文字取代金額。"""

        distribution = (
            self.build_distribution()
        )

        distribution[
            "has_mixed_currencies"
        ] = True
        distribution["analysis_currency"] = None

        january = build_monthly_income_rows(
            distribution
        )[0]

        self.assertEqual(
            january["每單位累計"],
            "不同幣別，未加總",
        )

        self.assertEqual(
            january["單次平均"],
            "不同幣別，未加總",
        )

    def test_chart_keeps_all_months_and_event_counts(
        self,
    ) -> None:
        """確認圖表不省略零事件月份。"""

        rows = build_monthly_income_chart_rows(
            self.build_distribution()
        )

        self.assertEqual(
            len(rows),
            12,
        )

        self.assertEqual(
            rows[0],
            {
                "月份": "1 月",
                "配息事件": 2,
            },
        )

        self.assertEqual(
            rows[1]["配息事件"],
            0,
        )

    def test_detail_does_not_load_or_render_monthly_distribution(
        self,
    ) -> None:
        """確認詳細頁暫停載入及顯示月份分布。"""

        source = inspect.getsource(
            render_etf_detail
        )

        self.assertNotIn(
            "load_etf_monthly_income(",
            source,
        )

        self.assertNotIn(
            "render_monthly_income_distribution(",
            source,
        )


if __name__ == "__main__":
    unittest.main()
