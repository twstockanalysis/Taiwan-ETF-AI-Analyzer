from decimal import Decimal
import unittest

from backend.app.models.target_analysis import (
    TargetAnalysisRequest,
)
from backend.app.services.target_analysis_calculator import (
    calculate_current_holding_value,
)


class TestTargetAnalysisHoldingValue(unittest.TestCase):
    @staticmethod
    def _build_request(
        *,
        held_units: int,
        unit_price: str,
    ) -> TargetAnalysisRequest:
        return TargetAnalysisRequest(
            held_units=held_units,
            unit_price=unit_price,
            monthly_after_tax_target="10000",
            analysis_years=10,
        )

    def test_units_are_multiplied_by_unit_price(self):
        request = self._build_request(
            held_units=1000,
            unit_price="35.50",
        )

        result = calculate_current_holding_value(
            request
        )

        self.assertEqual(
            result,
            Decimal("35500.00"),
        )

    def test_fractional_unit_price_is_preserved(self):
        request = self._build_request(
            held_units=1234,
            unit_price="27.35",
        )

        result = calculate_current_holding_value(
            request
        )

        self.assertEqual(
            result,
            Decimal("33749.90"),
        )

    def test_zero_units_produce_zero_value(self):
        request = self._build_request(
            held_units=0,
            unit_price="35.50",
        )

        result = calculate_current_holding_value(
            request
        )

        self.assertEqual(
            result,
            Decimal("0.00"),
        )


if __name__ == "__main__":
    unittest.main()