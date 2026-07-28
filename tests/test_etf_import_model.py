"""ETF 匯入資料模型測試。"""

import unittest

from pydantic import ValidationError

from backend.app.data_sources.registry import (
    Market,
)
from backend.app.models.etf_import import (
    ETFImportRecord,
)


class TestETFImportRecord(unittest.TestCase):
    """測試 ETF 匯入資料正規化及驗證。"""

    def build_valid_record(
        self,
        **overrides: object,
    ) -> ETFImportRecord:
        """建立合法測試資料。"""

        values: dict[str, object] = {
            "code": "00918",
            "name": "大華優利高填息30",
            "is_active": False,
            "is_bond": False,
            "listing_date": "2022-11-24",
            "fund_size": 100.0,
            "expense_ratio": 0.50,
            "market": "TWSE",
            "source_id": "twse_openapi",
        }

        values.update(overrides)

        return ETFImportRecord.model_validate(
            values
        )

    def test_valid_record_can_be_created(
        self,
    ) -> None:
        """確認合法資料可以通過驗證。"""

        record = self.build_valid_record()

        self.assertEqual(
            record.code,
            "00918",
        )
        self.assertEqual(
            record.market,
            Market.TWSE,
        )

    def test_code_is_normalized(
        self,
    ) -> None:
        """確認 ETF 代號會去空白並轉大寫。"""

        record = self.build_valid_record(
            code=" 00980a ",
        )

        self.assertEqual(
            record.code,
            "00980A",
        )

    def test_source_id_is_normalized(
        self,
    ) -> None:
        """確認來源識別碼會轉小寫。"""

        record = self.build_valid_record(
            source_id=" TWSE_OPENAPI ",
        )

        self.assertEqual(
            record.source_id,
            "twse_openapi",
        )

    def test_listing_date_is_parsed(
        self,
    ) -> None:
        """確認日期文字可以轉成 date。"""

        record = self.build_valid_record()

        self.assertEqual(
            record.listing_date.isoformat(),
            "2022-11-24",
        )

    def test_invalid_code_is_rejected(
        self,
    ) -> None:
        """確認不合法 ETF 代號被拒絕。"""

        with self.assertRaises(
            ValidationError
        ):
            self.build_valid_record(
                code="00918-TEST",
            )

    def test_negative_fund_size_is_rejected(
        self,
    ) -> None:
        """確認基金規模不可為負數。"""

        with self.assertRaises(
            ValidationError
        ):
            self.build_valid_record(
                fund_size=-1,
            )

    def test_unknown_market_is_rejected(
        self,
    ) -> None:
        """確認未知市場被拒絕。"""

        with self.assertRaises(
            ValidationError
        ):
            self.build_valid_record(
                market="UNKNOWN",
            )

    def test_extra_field_is_rejected(
        self,
    ) -> None:
        """確認未定義欄位會被拒絕。"""

        with self.assertRaises(
            ValidationError
        ):
            self.build_valid_record(
                issuer="測試投信",
            )


if __name__ == "__main__":
    unittest.main()