from decimal import Decimal
import unittest

from pydantic import ValidationError

from backend.app.models.target_analysis import (
    TargetAnalysisRequest,
)


class TestTargetAnalysisRequestHoldings(unittest.TestCase):
    @staticmethod
    def _valid_values():
        return {
            "held_units": 1000,
            "unit_price": Decimal("35.50"),
            "monthly_after_tax_target": Decimal("20000"),
            "analysis_years": 10,
            "history_years": 3,
            "cash_deduction_rate_pct": Decimal("10"),
        }

    def test_request_declares_holding_inputs_instead_of_capital(
        self,
    ):
        self.assertEqual(
            set(TargetAnalysisRequest.model_fields),
            {
                "held_units",
                "unit_price",
                "monthly_after_tax_target",
                "analysis_years",
                "history_years",
                "cash_deduction_rate_pct",
            },
        )

    def test_valid_holding_inputs_are_accepted(self):
        request = TargetAnalysisRequest(
            **self._valid_values()
        )

        self.assertEqual(request.held_units, 1000)
        self.assertEqual(
            request.unit_price,
            Decimal("35.50"),
        )

    def test_zero_held_units_is_allowed(self):
        values = self._valid_values()
        values["held_units"] = 0

        request = TargetAnalysisRequest(**values)

        self.assertEqual(request.held_units, 0)

    def test_negative_held_units_is_rejected(self):
        values = self._valid_values()
        values["held_units"] = -1

        with self.assertRaises(
            ValidationError
        ) as context:
            TargetAnalysisRequest(**values)

        self.assertEqual(
            {
                error["loc"]
                for error in context.exception.errors()
            },
            {("held_units",)},
        )

    def test_nonpositive_unit_price_is_rejected(self):
        for value in (
            Decimal("0"),
            Decimal("-0.01"),
        ):
            with self.subTest(unit_price=value):
                values = self._valid_values()
                values["unit_price"] = value

                with self.assertRaises(
                    ValidationError
                ) as context:
                    TargetAnalysisRequest(**values)

                self.assertEqual(
                    {
                        error["loc"]
                        for error
                        in context.exception.errors()
                    },
                    {("unit_price",)},
                )

    def test_available_capital_is_no_longer_accepted(
        self,
    ):
        values = self._valid_values()
        values["available_capital"] = Decimal(
            "35500"
        )

        with self.assertRaises(
            ValidationError
        ) as context:
            TargetAnalysisRequest(**values)

        self.assertEqual(
            {
                error["loc"]
                for error in context.exception.errors()
            },
            {("available_capital",)},
        )


if __name__ == "__main__":
    unittest.main()
