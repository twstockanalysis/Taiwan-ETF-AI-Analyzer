"""TWSE ETF 配息正規化測試。"""

import unittest
from datetime import date
from pathlib import Path

from backend.app.data_sources.dividend_normalizer import (
    normalize_twse_dividend_html,
    parse_roc_date,
)
from backend.app.models.etf_analysis import (
    DividendComponentBasis,
    ETFDividendComponentImportRecord,
    EstimatedDividendComponent,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "twse_etf_dividend_sample.html"
)


class TestDividendNormalizer(
    unittest.TestCase
):
    """測試配息事件與預估組成。"""

    def setUp(self) -> None:
        self.html_text = (
            FIXTURE_PATH.read_text(
                encoding="utf-8"
            )
        )

    def test_roc_date_is_converted(
        self,
    ) -> None:
        self.assertEqual(
            parse_roc_date(
                "115年07月21日"
            ),
            date(2026, 7, 21),
        )

        self.assertEqual(
            parse_roc_date(
                "115/07/21"
            ),
            date(2026, 7, 21),
        )

    def test_events_and_components_are_normalized(
        self,
    ) -> None:
        result = (
            normalize_twse_dividend_html(
                self.html_text
            )
        )

        self.assertEqual(
            len(result.dividends),
            2,
        )

        self.assertEqual(
            len(result.components),
            10,
        )

        self.assertEqual(
            len(result.rejected),
            1,
        )

        first_event = result.dividends[0]

        self.assertEqual(
            first_event.etf_code,
            "0050",
        )

        self.assertEqual(
            first_event.ex_dividend_date,
            date(2026, 7, 21),
        )

        self.assertEqual(
            first_event.source_event_id,
            (
                "twse_etfortune_dividend:"
                "0050:2026-07-21"
            ),
        )

    def test_realized_capital_gain_is_not_76w(
        self,
    ) -> None:
        result = (
            normalize_twse_dividend_html(
                self.html_text
            )
        )

        component_codes = {
            record.component_code
            for record in result.components
        }

        self.assertIn(
            EstimatedDividendComponent
            .REALIZED_CAPITAL_GAIN
            .value,
            component_codes,
        )

        self.assertNotIn(
            "76W",
            component_codes,
        )

        self.assertTrue(
            all(
                record.component_basis
                == DividendComponentBasis.ESTIMATED
                for record in result.components
            )
        )

    def test_100_percent_estimated_gain_stays_estimated(
        self,
    ) -> None:
        result = (
            normalize_twse_dividend_html(
                self.html_text
            )
        )

        record = next(
            item
            for item in result.components
            if (
                item.etf_code == "00930"
                and item.component_code
                == (
                    EstimatedDividendComponent
                    .REALIZED_CAPITAL_GAIN
                    .value
                )
            )
        )

        self.assertEqual(
            str(record.ratio_pct),
            "100.00",
        )

        self.assertEqual(
            record.component_basis,
            DividendComponentBasis.ESTIMATED,
        )

    def test_existing_76w_defaults_to_actual(
        self,
    ) -> None:
        record = (
            ETFDividendComponentImportRecord
            .model_validate(
                {
                    "etf_code": "00918",
                    "dividend_source_event_id": (
                        "official:00918:2026-Q3"
                    ),
                    "component_code": "76W",
                    "ratio_pct": "100",
                    "source_id": "official",
                }
            )
        )

        self.assertEqual(
            record.component_basis,
            DividendComponentBasis.ACTUAL,
        )

    def test_partial_component_disclosure_is_rejected(
        self,
    ) -> None:
        invalid_html = self.html_text.replace(
            "(5)其他所得占比 0.00 %",
            "",
            1,
        )

        result = (
            normalize_twse_dividend_html(
                invalid_html
            )
        )

        self.assertEqual(
            len(result.dividends),
            1,
        )

        self.assertEqual(
            len(result.rejected),
            2,
        )

        self.assertTrue(
            any(
                "預估配息組成欄位不完整"
                in issue.reason
                for issue in result.rejected
            )
        )


if __name__ == "__main__":
    unittest.main()
