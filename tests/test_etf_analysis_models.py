"""ETF 分析資料模型測試。"""

import unittest
from datetime import date
from decimal import Decimal

from pydantic import ValidationError

from backend.app.models.etf_analysis import (
    ETFDividendComponentImportRecord,
    ETFDividendImportRecord,
    ETFPerformanceImportRecord,
    PerformancePeriod,
)


class TestETFAnalysisModels(
    unittest.TestCase
):
    """測試績效與配息資料模型。"""

    def test_six_month_performance(
        self,
    ) -> None:
        """確認六個月績效資料可建立。"""

        record = (
            ETFPerformanceImportRecord
            .model_validate(
                {
                    "etf_code": "00918",
                    "as_of_date": "2026-07-29",
                    "period_code": "6M",
                    "return_pct": "12.3456",
                    "source_id": "official",
                }
            )
        )

        self.assertEqual(
            record.period_code,
            PerformancePeriod.SIX_MONTHS,
        )

        self.assertEqual(
            record.return_pct,
            Decimal("12.3456"),
        )

    def test_etf_code_is_normalized(
        self,
    ) -> None:
        """確認 ETF 代號轉大寫。"""

        record = (
            ETFPerformanceImportRecord
            .model_validate(
                {
                    "etf_code": " 00980a ",
                    "as_of_date": "2026-07-29",
                    "period_code": "6M",
                    "return_pct": "1",
                    "source_id": "official",
                }
            )
        )

        self.assertEqual(
            record.etf_code,
            "00980A",
        )

    def test_invalid_period_is_rejected(
        self,
    ) -> None:
        """確認未知期間被拒絕。"""

        with self.assertRaises(
            ValidationError
        ):
            ETFPerformanceImportRecord.model_validate(
                {
                    "etf_code": "00918",
                    "as_of_date": "2026-07-29",
                    "period_code": "10M",
                    "return_pct": "1",
                    "source_id": "official",
                }
            )

    def test_valid_dividend_event(
        self,
    ) -> None:
        """確認合法配息事件。"""

        record = (
            ETFDividendImportRecord
            .model_validate(
                {
                    "etf_code": "00918",
                    "source_event_id": (
                        "00918-2026-Q3"
                    ),
                    "ex_dividend_date": (
                        "2026-09-15"
                    ),
                    "payment_date": (
                        "2026-10-15"
                    ),
                    "amount_per_unit": "0.70",
                    "currency": "twd",
                    "source_id": "official",
                }
            )
        )

        self.assertEqual(
            record.currency,
            "TWD",
        )

        self.assertEqual(
            record.payment_date,
            date(2026, 10, 15),
        )

    def test_dividend_requires_date(
        self,
    ) -> None:
        """確認配息事件必須有日期。"""

        with self.assertRaises(
            ValidationError
        ):
            ETFDividendImportRecord.model_validate(
                {
                    "etf_code": "00918",
                    "source_event_id": (
                        "00918-unknown"
                    ),
                    "amount_per_unit": "0.70",
                    "source_id": "official",
                }
            )

    def test_payment_before_ex_date_is_rejected(
        self,
    ) -> None:
        """確認發放日不可早於除息日。"""

        with self.assertRaises(
            ValidationError
        ):
            ETFDividendImportRecord.model_validate(
                {
                    "etf_code": "00918",
                    "source_event_id": (
                        "00918-invalid"
                    ),
                    "ex_dividend_date": (
                        "2026-10-15"
                    ),
                    "payment_date": (
                        "2026-09-15"
                    ),
                    "amount_per_unit": "0.70",
                    "source_id": "official",
                }
            )

    def test_76w_code_is_preserved(
        self,
    ) -> None:
        """確認 76W 代碼正規化。"""

        record = (
            ETFDividendComponentImportRecord
            .model_validate(
                {
                    "etf_code": "00918",
                    "dividend_source_event_id": (
                        "00918-2026-Q3"
                    ),
                    "component_code": "76w",
                    "ratio_pct": "100",
                    "source_id": "official",
                }
            )
        )

        self.assertEqual(
            record.component_code,
            "76W",
        )

        self.assertEqual(
            record.ratio_pct,
            Decimal("100"),
        )

    def test_component_requires_amount_or_ratio(
        self,
    ) -> None:
        """確認配息組成必須有數值。"""

        with self.assertRaises(
            ValidationError
        ):
            ETFDividendComponentImportRecord.model_validate(
                {
                    "etf_code": "00918",
                    "dividend_source_event_id": (
                        "00918-2026-Q3"
                    ),
                    "component_code": "76W",
                    "source_id": "official",
                }
            )

    def test_ratio_over_100_is_rejected(
        self,
    ) -> None:
        """確認配息比例不得超過 100%。"""

        with self.assertRaises(
            ValidationError
        ):
            ETFDividendComponentImportRecord.model_validate(
                {
                    "etf_code": "00918",
                    "dividend_source_event_id": (
                        "00918-2026-Q3"
                    ),
                    "component_code": "76W",
                    "ratio_pct": "100.1",
                    "source_id": "official",
                }
            )


if __name__ == "__main__":
    unittest.main()