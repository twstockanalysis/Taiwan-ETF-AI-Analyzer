"""Streamlit 共用格式化工具測試。"""

import unittest

from frontend.ui.formatters import (
    asset_type_label,
    format_amount,
    format_iso_date,
    format_iso_datetime,
    format_number,
    format_optional_text,
    format_percentage,
    format_source_references,
    management_type_label,
    truncate_text,
)


class TestFrontendFormatters(
    unittest.TestCase
):
    """驗證跨頁面共用格式化語意。"""

    def test_percentage_keeps_missing_and_zero_distinct(
        self,
    ) -> None:
        """確認缺值與正式零值不會混淆。"""

        self.assertEqual(
            format_percentage(
                None,
                missing_text="尚未取得",
            ),
            "尚未取得",
        )

        self.assertEqual(
            format_percentage(0),
            "0.00%",
        )

        self.assertEqual(
            format_percentage(
                5.125,
                signed=True,
            ),
            "+5.12%",
        )

    def test_number_and_amount_formats_are_stable(
        self,
    ) -> None:
        """確認數字、單位及幣別格式一致。"""

        self.assertEqual(
            format_number(
                5000,
                suffix=" 億元",
            ),
            "5,000.00 億元",
        )

        self.assertEqual(
            format_amount(
                0.7000,
                "twd",
            ),
            "0.7 TWD",
        )

        self.assertEqual(
            format_number(
                "bad",
                invalid_text="格式異常",
            ),
            "格式異常",
        )

    def test_optional_date_and_datetime(
        self,
    ) -> None:
        """確認日期缺值與 ISO 日期時間顯示。"""

        self.assertEqual(
            format_iso_date(
                None,
                missing_text="尚無資料",
            ),
            "尚無資料",
        )

        self.assertEqual(
            format_iso_datetime(
                "2026-07-31T12:34:56+00:00",
                utc_label=True,
                timespec=None,
            ),
            "2026-07-31 12:34:56 UTC",
        )

        self.assertEqual(
            format_optional_text(
                "   ",
            ),
            "—",
        )

    def test_classification_labels(
        self,
    ) -> None:
        """確認 ETF 分類標籤跨頁一致。"""

        self.assertEqual(
            management_type_label(True),
            "主動式",
        )

        self.assertEqual(
            management_type_label(False),
            "被動式",
        )

        self.assertEqual(
            asset_type_label(True),
            "債券",
        )

        self.assertEqual(
            asset_type_label(False),
            "非債券",
        )

    def test_source_references_and_truncation(
        self,
    ) -> None:
        """確認來源名稱與錯誤摘要格式。"""

        self.assertEqual(
            format_source_references(
                [
                    {
                        "source_id": "twse_openapi",
                        "display_name": "證交所 OpenAPI",
                    },
                    {
                        "source_id": "manual",
                        "display_name": "manual",
                    },
                ]
            ),
            (
                "證交所 OpenAPI (twse_openapi)"
                "、manual"
            ),
        )

        self.assertEqual(
            truncate_text(
                "abcdef",
                maximum_length=4,
            ),
            "abcd…",
        )


if __name__ == "__main__":
    unittest.main()
