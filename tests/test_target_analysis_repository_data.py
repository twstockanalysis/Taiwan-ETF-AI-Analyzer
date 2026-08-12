from datetime import date
import unittest
from unittest.mock import patch

from backend.app.models.target_analysis import (
    TargetAnalysisWarningCode,
)
from backend.app.services import target_analysis_data


class TestTargetAnalysisRepositoryData(unittest.TestCase):
    def _monthly_income(self):
        return {
            "etf_code": "0056",
            "lookback_years": 3,
            "event_count": 4,
            "covered_month_occurrence_count": 4,
            "analysis_currency": "TWD",
            "has_mixed_currencies": False,
            "total_amount_per_unit": 4.8,
            "months": [],
        }

    def _dividends(self):
        return [
            {
                "payment_date": "2026-07-01",
                "amount_per_unit": 1.2,
                "currency": "TWD",
                "yield_pct": 2.5,
            },
            {
                "payment_date": "2025-07-01",
                "amount_per_unit": 1.2,
                "currency": "TWD",
                "yield_pct": 2.4,
            },
            {
                "payment_date": "2024-07-01",
                "amount_per_unit": 1.2,
                "currency": "TWD",
                "yield_pct": 2.3,
            },
            {
                "payment_date": "2023-08-03",
                "amount_per_unit": 1.2,
                "currency": "TWD",
                "yield_pct": 2.2,
            },
        ]

    def _performance(self):
        return [
            {
                "as_of_date": "2026-07-29",
                "period_code": "3Y",
                "metric_code": "PRICE_RETURN",
                "return_pct": 18.5,
                "source_id": "twse_stock_day",
            },
            {
                "as_of_date": "2026-07-29",
                "period_code": "5Y",
                "metric_code": "TOTAL_RETURN",
                "return_pct": 30.0,
                "source_id": "other_source",
            },
        ]

    def _load(
        self,
        *,
        monthly_income=None,
        dividends=None,
        performance=None,
        history_years=3,
    ):
        monthly_value = (
            self._monthly_income()
            if monthly_income is None
            else monthly_income
        )
        dividend_value = (
            self._dividends()
            if dividends is None
            else dividends
        )
        performance_value = (
            self._performance()
            if performance is None
            else performance
        )

        with (
            patch(
                "backend.app.repositories."
                "monthly_income_repository."
                "build_monthly_income_distribution",
                return_value=monthly_value,
            ) as monthly_mock,
            patch(
                "backend.app.repositories."
                "dividend_repository."
                "list_etf_dividends",
                return_value=dividend_value,
            ) as dividend_mock,
            patch(
                "backend.app.repositories."
                "performance_repository."
                "list_latest_etf_performance",
                return_value=performance_value,
            ) as performance_mock,
            patch(
                "backend.app.repositories.daily_close_repository."
                "list_daily_closes",
                return_value=[],
            ),
            patch(
                "backend.app.repositories.etf_repository.get_etf_by_code",
                return_value={"code": "0056", "is_bond": False},
            ),
            patch(
                "backend.app.repositories.performance_repository."
                "list_latest_multi_period_performance_ranking",
                return_value=[],
            ),
        ):
            result = (
                target_analysis_data
                .load_target_analysis_data(
                    etf_code="0056",
                    database_path="sample.db",
                    history_years=history_years,
                    as_of_date=date(2026, 8, 3),
                )
            )

        return (
            result,
            monthly_mock,
            dividend_mock,
            performance_mock,
        )

    @staticmethod
    def _warning_codes(result):
        return {
            warning.code
            for warning in result.warnings
        }

    @staticmethod
    def _unavailable_fields(result):
        return {
            item.field
            for item in result.unavailable_fields
        }

    def test_repositories_are_loaded_and_exact_price_return_is_selected(
        self,
    ):
        (
            result,
            monthly_mock,
            dividend_mock,
            performance_mock,
        ) = self._load()

        monthly_mock.assert_called_once_with(
            etf_code="0056",
            database_path="sample.db",
            lookback_years=3,
        )
        dividend_mock.assert_called_once_with(
            etf_code="0056",
            database_path="sample.db",
            limit=200,
            offset=0,
        )
        performance_mock.assert_called_once_with(
            etf_code="0056",
            database_path="sample.db",
        )

        self.assertIsNotNone(
            result.selected_performance
        )
        self.assertEqual(
            result.selected_performance[
                "metric_code"
            ],
            "PRICE_RETURN",
        )
        self.assertEqual(
            result.selected_performance[
                "period_code"
            ],
            "3Y",
        )

    def test_missing_required_dividend_fields_are_reported(
        self,
    ):
        cases = (
            ("yield_pct", "dividend_yield_pct"),
            ("payment_date", "payment_date"),
        )

        for missing_field, unavailable_field in cases:
            with self.subTest(
                missing_field=missing_field
            ):
                dividends = self._dividends()
                dividends[0][missing_field] = None

                result, *_ = self._load(
                    dividends=dividends
                )

                self.assertIn(
                    TargetAnalysisWarningCode
                    .INCOMPLETE_DIVIDEND_DATA,
                    self._warning_codes(result),
                )
                self.assertIn(
                    unavailable_field,
                    self._unavailable_fields(result),
                )

    def test_mixed_currencies_are_reported(self):
        monthly_income = self._monthly_income()
        monthly_income["analysis_currency"] = None
        monthly_income[
            "has_mixed_currencies"
        ] = True

        dividends = self._dividends()
        dividends[0]["currency"] = "USD"

        result, *_ = self._load(
            monthly_income=monthly_income,
            dividends=dividends,
        )

        self.assertIn(
            TargetAnalysisWarningCode.MIXED_CURRENCY,
            self._warning_codes(result),
        )
        self.assertIn(
            "analysis_currency",
            self._unavailable_fields(result),
        )

    def test_insufficient_dividend_history_is_reported(
        self,
    ):
        result, *_ = self._load(
            dividends=self._dividends()[:2],
        )

        self.assertIn(
            TargetAnalysisWarningCode
            .INSUFFICIENT_DIVIDEND_HISTORY,
            self._warning_codes(result),
        )

    def test_shorter_performance_period_uses_fallback(
        self,
    ):
        performance = [
            {
                "as_of_date": "2026-07-29",
                "period_code": "1Y",
                "metric_code": "PRICE_RETURN",
                "return_pct": 8.5,
                "source_id": "twse_stock_day",
            }
        ]

        result, *_ = self._load(
            performance=performance,
        )

        self.assertEqual(
            result.selected_performance[
                "period_code"
            ],
            "1Y",
        )
        self.assertIn(
            TargetAnalysisWarningCode
            .PERFORMANCE_PERIOD_FALLBACK,
            self._warning_codes(result),
        )
        self.assertIn(
            TargetAnalysisWarningCode
            .INSUFFICIENT_PERFORMANCE_HISTORY,
            self._warning_codes(result),
        )

    def test_stale_dividend_and_performance_are_reported(
        self,
    ):
        dividends = self._dividends()
        for item in dividends:
            item["payment_date"] = "2024-12-01"

        performance = [
            {
                "as_of_date": "2026-07-20",
                "period_code": "3Y",
                "metric_code": "PRICE_RETURN",
                "return_pct": 5.0,
                "source_id": "twse_stock_day",
            }
        ]

        result, *_ = self._load(
            dividends=dividends,
            performance=performance,
        )

        codes = self._warning_codes(result)

        self.assertIn(
            TargetAnalysisWarningCode
            .STALE_DIVIDEND_DATA,
            codes,
        )
        self.assertIn(
            TargetAnalysisWarningCode
            .STALE_PERFORMANCE_DATA,
            codes,
        )

    def test_longer_performance_period_is_not_selected(
        self,
    ):
        performance = [
            {
                "as_of_date": "2026-07-29",
                "period_code": "5Y",
                "metric_code": "PRICE_RETURN",
                "return_pct": 25.0,
                "source_id": "twse_stock_day",
            }
        ]

        result, *_ = self._load(
            performance=performance,
            history_years=3,
        )

        self.assertIsNone(
            result.selected_performance
        )
        self.assertIn(
            TargetAnalysisWarningCode
            .INSUFFICIENT_PERFORMANCE_HISTORY,
            self._warning_codes(result),
        )
        self.assertIn(
            "performance_return_pct",
            self._unavailable_fields(result),
        )


if __name__ == "__main__":
    unittest.main()
