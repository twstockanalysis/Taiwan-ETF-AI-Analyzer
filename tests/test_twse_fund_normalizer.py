"""TWSE 基金基本資料正規化測試。"""

import unittest
from datetime import date

from backend.app.data_sources.normalizers.twse_fund_master import (
    normalize_twse_fund_record,
    normalize_twse_fund_records,
    parse_listing_date,
)


class TestTWSEFundNormalizer(
    unittest.TestCase
):
    """測試 TWSE ETF 正規化規則。"""

    def build_record(
        self,
        **overrides: object,
    ) -> dict:
        """建立合法 ETF 測試紀錄。"""

        record: dict[str, object] = {
            "基金代號": "00918",
            "基金簡稱": (
                "大華優利高填息30 ETF"
            ),
            "基金類型": (
                "指數股票型基金"
            ),
            "上市日期": "2022/11/24",
        }

        record.update(overrides)

        return record

    def test_passive_etf_is_normalized(
        self,
    ) -> None:
        """確認一般 ETF 可正常轉換。"""

        record = normalize_twse_fund_record(
            self.build_record()
        )

        self.assertEqual(
            record.code,
            "00918",
        )
        self.assertFalse(
            record.is_active
        )
        self.assertFalse(
            record.is_bond
        )

    def test_active_etf_is_detected(
        self,
    ) -> None:
        """確認主動式 ETF 可被辨識。"""

        record = normalize_twse_fund_record(
            self.build_record(
                基金代號="00980A",
                基金簡稱=(
                    "主動野村臺灣優選 ETF"
                ),
                基金類型=(
                    "主動式交易所交易基金"
                ),
            )
        )

        self.assertTrue(
            record.is_active
        )

    def test_bond_etf_is_detected(
        self,
    ) -> None:
        """確認債券 ETF 可被辨識。"""

        record = normalize_twse_fund_record(
            self.build_record(
                基金代號="00679B",
                基金簡稱=(
                    "元大美債20年 ETF"
                ),
            )
        )

        self.assertTrue(
            record.is_bond
        )

    def test_non_etf_is_rejected(
        self,
    ) -> None:
        """確認一般基金不會被接受。"""

        with self.assertRaises(
            ValueError
        ):
            normalize_twse_fund_record(
                {
                    "基金代號": "FUND001",
                    "基金簡稱": "一般開放式基金",
                    "基金類型": "股票型基金",
                }
            )

    def test_gregorian_date_is_parsed(
        self,
    ) -> None:
        """確認西元日期格式。"""

        result = parse_listing_date(
            "2022/11/24"
        )

        self.assertEqual(
            result,
            date(2022, 11, 24),
        )

    def test_roc_date_is_parsed(
        self,
    ) -> None:
        """確認民國日期格式。"""

        result = parse_listing_date(
            "111/11/24"
        )

        self.assertEqual(
            result,
            date(2022, 11, 24),
        )

    def test_missing_code_is_rejected(
        self,
    ) -> None:
        """確認缺少 ETF 代號被拒絕。"""

        with self.assertRaises(
            ValueError
        ):
            normalize_twse_fund_record(
                self.build_record(
                    基金代號="",
                )
            )

    def test_batch_result_has_counts(
        self,
    ) -> None:
        """確認批次接受與拒絕結果。"""

        result = (
            normalize_twse_fund_records(
                [
                    self.build_record(),
                    {
                        "基金代號": "F001",
                        "基金簡稱": (
                            "一般股票型基金"
                        ),
                        "基金類型": (
                            "股票型基金"
                        ),
                    },
                ]
            )
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