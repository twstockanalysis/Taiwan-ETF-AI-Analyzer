"""正式收益分配通知書模型與正規化測試。"""

import unittest
from decimal import Decimal

from pydantic import ValidationError

from backend.app.data_sources.actual_dividend_normalizer import (
    normalize_actual_dividend_payload,
)
from backend.app.data_sources.actual_dividend_notice import (
    ActualDividendNoticeInput,
)


class TestActualDividendModels(
    unittest.TestCase
):
    """驗證正式所得代碼與通知書規則。"""

    def build_notice(self) -> dict:
        """建立合法正式通知書。"""

        return {
            "source_id": (
                "Official_Distribution_Notice"
            ),
            "source_document_id": (
                "notice-00918-2026-Q2"
            ),
            "source_document_url": (
                "https://example.com/"
                "notice-00918-2026-Q2"
            ),
            "source_document_date": (
                "2026-06-30"
            ),
            "information_basis": "ACTUAL",
            "etf_code": "00918",
            "ex_dividend_date": (
                "2026-06-18"
            ),
            "payment_date": (
                "2026-07-10"
            ),
            "amount_per_unit": "0.70",
            "currency": "twd",
            "components": [
                {
                    "component_code": "76w",
                    "amount_per_unit": "0.70",
                    "ratio_pct": "100",
                },
            ],
        }

    def test_actual_76w_is_normalized(
        self,
    ) -> None:
        """確認正式 76W 與來源代碼正規化。"""

        notice = (
            ActualDividendNoticeInput
            .model_validate(
                self.build_notice()
            )
        )

        self.assertEqual(
            notice.source_id,
            "official_distribution_notice",
        )

        self.assertEqual(
            notice.currency,
            "TWD",
        )

        self.assertEqual(
            notice.components[0]
            .component_code,
            "76W",
        )

        self.assertEqual(
            notice.components[0]
            .ratio_pct,
            Decimal("100"),
        )

    def test_estimated_code_is_rejected(
        self,
    ) -> None:
        """正式通知書不得使用預估組成代碼。"""

        payload = self.build_notice()

        payload["components"][0][
            "component_code"
        ] = "EST_REALIZED_CAPITAL_GAIN"

        with self.assertRaises(
            ValidationError
        ):
            ActualDividendNoticeInput.model_validate(
                payload
            )

    def test_estimated_basis_is_rejected(
        self,
    ) -> None:
        """ESTIMATED 文件不能偽裝成正式通知書。"""

        payload = self.build_notice()

        payload[
            "information_basis"
        ] = "ESTIMATED"

        with self.assertRaises(
            ValidationError
        ):
            ActualDividendNoticeInput.model_validate(
                payload
            )

    def test_duplicate_codes_are_rejected(
        self,
    ) -> None:
        """同一文件不得重複所得代碼。"""

        payload = self.build_notice()

        payload["components"].append(
            {
                "component_code": "76W",
                "ratio_pct": "0",
            }
        )

        with self.assertRaises(
            ValidationError
        ):
            ActualDividendNoticeInput.model_validate(
                payload
            )

    def test_invalid_totals_are_rejected(
        self,
    ) -> None:
        """比例或金額合計異常時拒絕。"""

        payload = self.build_notice()

        payload["components"][0][
            "ratio_pct"
        ] = "80"

        with self.assertRaises(
            ValidationError
        ):
            ActualDividendNoticeInput.model_validate(
                payload
            )

    def test_document_normalization_is_partial(
        self,
    ) -> None:
        """單筆錯誤不影響同檔其他通知書。"""

        valid_notice = self.build_notice()

        invalid_notice = self.build_notice()

        invalid_notice["etf_code"] = "00919"

        invalid_notice[
            "source_document_id"
        ] = "invalid"

        invalid_notice[
            "information_basis"
        ] = "ESTIMATED"

        result = (
            normalize_actual_dividend_payload(
                {
                    "schema_version": 1,
                    "notices": [
                        valid_notice,
                        invalid_notice,
                    ],
                }
            )
        )

        self.assertEqual(
            result.raw_notice_count,
            2,
        )

        self.assertEqual(
            len(result.accepted),
            1,
        )

        self.assertEqual(
            len(result.rejected),
            1,
        )


if __name__ == "__main__":
    unittest.main()
