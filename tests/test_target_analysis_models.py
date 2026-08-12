from decimal import Decimal
import unittest

from pydantic import ValidationError

from backend.app.models.target_analysis import (
    TargetAnalysisRequest,
    TargetAnalysisStatus,
    TargetAnalysisUnavailableField,
    TargetAnalysisWarning,
    TargetAnalysisWarningCode,
)


class TestTargetAnalysisRequest(unittest.TestCase):
    def test_valid_request_uses_documented_defaults(self):
        request = TargetAnalysisRequest(
            held_units=1000,
            unit_price="35.50",
            monthly_after_tax_target="10000",
            analysis_years=10,
        )

        self.assertEqual(request.held_units, 1000)
        self.assertEqual(request.unit_price, Decimal("35.50"))
        self.assertEqual(
            request.monthly_after_tax_target,
            Decimal("10000"),
        )
        self.assertEqual(request.analysis_years, 10)
        self.assertEqual(request.history_years, 3)
        self.assertIsNone(
            request.cash_deduction_rate_pct
        )

    def test_explicit_zero_cash_deduction_rate_is_preserved(self):
        request = TargetAnalysisRequest(
            held_units=1000,
            unit_price="35.50",
            monthly_after_tax_target="10000",
            analysis_years=10,
            cash_deduction_rate_pct="0",
        )

        self.assertEqual(
            request.cash_deduction_rate_pct,
            Decimal("0"),
        )
    def test_boundary_values_are_accepted(self):
        request = TargetAnalysisRequest(
            held_units=0,
            unit_price="0.01",
            monthly_after_tax_target="0",
            analysis_years=50,
            history_years=10,
            cash_deduction_rate_pct="100",
        )

        self.assertEqual(request.held_units, 0)
        self.assertEqual(request.unit_price, Decimal("0.01"))
        self.assertEqual(request.analysis_years, 50)
        self.assertEqual(request.history_years, 10)
        self.assertEqual(
            request.cash_deduction_rate_pct,
            Decimal("100"),
        )

    def test_invalid_request_values_are_rejected(self):
        invalid_cases = (
            {"held_units": -1},
            {"unit_price": "0"},
            {"unit_price": "-0.01"},
            {"monthly_after_tax_target": "-1"},
            {"analysis_years": 0},
            {"analysis_years": 51},
            {"history_years": 0},
            {"history_years": 11},
            {"cash_deduction_rate_pct": "-0.01"},
            {"cash_deduction_rate_pct": "100.01"},
        )

        base_values = {
            "held_units": 1000,
            "unit_price": "35.50",
            "monthly_after_tax_target": "10000",
            "analysis_years": 10,
        }

        for overrides in invalid_cases:
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValidationError):
                    TargetAnalysisRequest(
                        **(base_values | overrides)
                    )

    def test_unknown_request_fields_are_rejected(self):
        with self.assertRaises(ValidationError):
            TargetAnalysisRequest(
                held_units=1000,
                unit_price="35.50",
                monthly_after_tax_target="10000",
                analysis_years=10,
                unsupported_option=True,
            )

class TestTargetAnalysisContractEnums(unittest.TestCase):
    def test_status_values_are_stable(self):
        self.assertEqual(
            {status.value for status in TargetAnalysisStatus},
            {"AVAILABLE", "PARTIAL", "UNAVAILABLE"},
        )

    def test_warning_code_values_are_stable(self):
        self.assertEqual(
            {code.value for code in TargetAnalysisWarningCode},
            {
                "NEGATIVE_TOTAL_RETURN",
                "PERSISTENT_PRICE_DECLINE",
                "WEAK_PRICE_RECOVERY",
                "MATERIAL_PEER_UNDERPERFORMANCE",
                "INSUFFICIENT_DIVIDEND_HISTORY",
                "INSUFFICIENT_PERFORMANCE_HISTORY",
                "STALE_DIVIDEND_DATA",
                "STALE_PERFORMANCE_DATA",
                "INCOMPLETE_DIVIDEND_DATA",
                "MIXED_CURRENCY",
                "PERFORMANCE_PERIOD_FALLBACK",
                "HISTORICAL_RESULTS_NOT_GUARANTEED",
            },
        )


class TestTargetAnalysisQualificationModels(unittest.TestCase):
    def test_warning_preserves_affected_fields(self):
        warning = TargetAnalysisWarning(
            code=TargetAnalysisWarningCode.STALE_DIVIDEND_DATA,
            message="Dividend data is stale.",
            affected_fields=["annual_cash_flow"],
        )

        self.assertEqual(
            warning.code,
            TargetAnalysisWarningCode.STALE_DIVIDEND_DATA,
        )
        self.assertEqual(
            warning.affected_fields,
            ["annual_cash_flow"],
        )

    def test_unavailable_field_requires_reason(self):
        unavailable = TargetAnalysisUnavailableField(
            field="required_capital",
            reason="Dividend yield history is incomplete.",
        )

        self.assertEqual(unavailable.field, "required_capital")

        for values in (
            {"field": "", "reason": "Missing data."},
            {"field": "required_capital", "reason": ""},
        ):
            with self.subTest(values=values):
                with self.assertRaises(ValidationError):
                    TargetAnalysisUnavailableField(**values)


if __name__ == "__main__":
    unittest.main()
