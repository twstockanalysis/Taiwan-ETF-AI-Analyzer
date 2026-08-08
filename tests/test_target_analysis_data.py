from datetime import date
import unittest

from backend.app.models.etf_analysis import PerformancePeriod
from backend.app.services.target_analysis_data import (
    is_dividend_data_stale,
    is_performance_data_stale,
    select_performance_period,
)


class TestTargetAnalysisDataStaleness(unittest.TestCase):
    def test_performance_is_not_stale_at_ten_days(self):
        self.assertFalse(
            is_performance_data_stale(
                performance_date=date(2026, 7, 24),
                as_of_date=date(2026, 8, 3),
            )
        )

    def test_performance_is_stale_after_ten_days(self):
        self.assertTrue(
            is_performance_data_stale(
                performance_date=date(2026, 7, 23),
                as_of_date=date(2026, 8, 3),
            )
        )

    def test_dividend_is_not_stale_at_eighteen_months(self):
        self.assertFalse(
            is_dividend_data_stale(
                latest_payment_date=date(2025, 1, 31),
                as_of_date=date(2026, 7, 31),
            )
        )

    def test_dividend_is_stale_after_eighteen_months(self):
        self.assertTrue(
            is_dividend_data_stale(
                latest_payment_date=date(2025, 1, 31),
                as_of_date=date(2026, 8, 1),
            )
        )


class TestPerformancePeriodSelection(unittest.TestCase):
    def test_exact_period_is_preferred(self):
        selection = select_performance_period(
            history_years=3,
            available_periods=(
                PerformancePeriod.ONE_YEAR,
                PerformancePeriod.THREE_YEARS,
                PerformancePeriod.FIVE_YEARS,
            ),
        )

        self.assertIsNotNone(selection)
        self.assertEqual(
            selection.selected_period,
            PerformancePeriod.THREE_YEARS,
        )
        self.assertFalse(selection.used_fallback)

    def test_nearest_shorter_period_is_used_as_fallback(self):
        selection = select_performance_period(
            history_years=5,
            available_periods=(
                PerformancePeriod.ONE_YEAR,
                PerformancePeriod.THREE_YEARS,
            ),
        )

        self.assertIsNotNone(selection)
        self.assertEqual(
            selection.selected_period,
            PerformancePeriod.THREE_YEARS,
        )
        self.assertTrue(selection.used_fallback)

    def test_longer_period_is_not_used_as_fallback(self):
        selection = select_performance_period(
            history_years=3,
            available_periods=(
                PerformancePeriod.FIVE_YEARS,
            ),
        )

        self.assertIsNone(selection)

    def test_nonstandard_history_uses_shorter_supported_period(self):
        selection = select_performance_period(
            history_years=2,
            available_periods=(
                PerformancePeriod.ONE_YEAR,
                PerformancePeriod.THREE_YEARS,
            ),
        )

        self.assertIsNotNone(selection)
        self.assertEqual(
            selection.selected_period,
            PerformancePeriod.ONE_YEAR,
        )
        self.assertTrue(selection.used_fallback)

    def test_ten_year_history_uses_five_year_fallback(self):
        selection = select_performance_period(
            history_years=10,
            available_periods=(
                PerformancePeriod.ONE_YEAR,
                PerformancePeriod.THREE_YEARS,
                PerformancePeriod.FIVE_YEARS,
            ),
        )

        self.assertIsNotNone(selection)
        self.assertEqual(
            selection.selected_period,
            PerformancePeriod.FIVE_YEARS,
        )
        self.assertTrue(selection.used_fallback)

    def test_no_available_shorter_period_returns_none(self):
        selection = select_performance_period(
            history_years=1,
            available_periods=(),
        )

        self.assertIsNone(selection)


if __name__ == "__main__":
    unittest.main()
