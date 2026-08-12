"""M10-4 ACTUAL 組成資料選擇測試。"""

from decimal import Decimal
import unittest

from backend.app.services.tax_reinvestment_data import (
    select_calculation_component_mix,
    select_latest_complete_actual_mix,
)


class TestTaxReinvestmentData(unittest.TestCase):
    def test_selects_latest_complete_event_and_preserves_zero(self) -> None:
        rows = [
            {
                "dividend_id": 2,
                "source_event_id": "new-incomplete",
                "payment_date": "2026-06-01",
                "component_code": "54C",
                "component_name": "股利",
                "ratio_pct": None,
            },
            {
                "dividend_id": 1,
                "source_event_id": "complete",
                "payment_date": "2026-03-01",
                "component_code": "54C",
                "component_name": "股利",
                "ratio_pct": 100,
            },
            {
                "dividend_id": 1,
                "source_event_id": "complete",
                "payment_date": "2026-03-01",
                "component_code": "76W",
                "component_name": "國內財產交易",
                "ratio_pct": 0,
            },
        ]

        result = select_latest_complete_actual_mix(rows)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.dividend_id, 1)
        self.assertEqual(result.source_event_id, "complete")
        self.assertEqual(result.mix[1].ratio_pct, Decimal("0"))

    def test_missing_complete_event_remains_none(self) -> None:
        result = select_latest_complete_actual_mix(
            [
                {
                    "dividend_id": 1,
                    "source_event_id": "incomplete",
                    "ratio_pct": 80,
                }
            ]
        )
        self.assertIsNone(result)

    def test_actual_is_preferred_over_newer_estimated_event(self) -> None:
        rows = [
            {
                "dividend_id": 2,
                "source_event_id": "estimated-new",
                "payment_date": "2026-06-01",
                "component_basis": "ESTIMATED",
                "component_code": "EST_DIVIDEND",
                "ratio_pct": 100,
            },
            {
                "dividend_id": 1,
                "source_event_id": "actual-old",
                "payment_date": "2026-03-01",
                "component_basis": "ACTUAL",
                "component_code": "54C",
                "ratio_pct": 100,
            },
        ]

        result = select_calculation_component_mix(rows)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.basis, "ACTUAL")
        self.assertEqual(result.source_event_id, "actual-old")

    def test_estimated_is_used_when_actual_is_unavailable(self) -> None:
        rows = [
            {
                "dividend_id": 2,
                "source_event_id": "estimated",
                "payment_date": "2026-06-01",
                "component_basis": "ESTIMATED",
                "component_code": "EST_DIVIDEND",
                "component_name": "股利所得",
                "ratio_pct": 26,
            },
            {
                "dividend_id": 2,
                "source_event_id": "estimated",
                "payment_date": "2026-06-01",
                "component_basis": "ESTIMATED",
                "component_code": "EST_REALIZED_CAPITAL_GAIN",
                "component_name": "已實現資本利得",
                "ratio_pct": 74,
            },
        ]

        result = select_calculation_component_mix(rows)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.basis, "ESTIMATED_FALLBACK")
        self.assertEqual(
            [item.component_code for item in result.mix],
            ["EST_DIVIDEND", "EST_REALIZED_CAPITAL_GAIN"],
        )


if __name__ == "__main__":
    unittest.main()
