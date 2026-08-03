"""正式通知書配息事件匹配器測試。"""

import tempfile
import unittest
from pathlib import Path

from backend.app.database.connection import (
    get_connection,
)
from backend.app.database.init_db import (
    initialize_database,
)
from backend.app.data_sources.actual_dividend_matcher import (
    match_actual_dividend_notices,
)
from backend.app.data_sources.actual_dividend_notice import (
    ActualDividendNoticeInput,
)


class TestActualDividendMatcher(
    unittest.TestCase
):
    """驗證唯一、安全的配息事件匹配。"""

    def setUp(self) -> None:
        """建立 ETF 與配息事件。"""

        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.database_path = (
            Path(self.temp_directory.name)
            / "actual_matcher.db"
        )

        initialize_database(
            self.database_path
        )

        connection = get_connection(
            self.database_path
        )

        try:
            connection.execute(
                """
                INSERT INTO etf_master (
                    code,
                    name,
                    is_active,
                    is_bond
                )
                VALUES (?, ?, ?, ?);
                """,
                (
                    "00878",
                    "國泰永續高股息",
                    0,
                    0,
                ),
            )

            connection.execute(
                """
                INSERT INTO etf_dividend (
                    etf_code,
                    source_event_id,
                    ex_dividend_date,
                    record_date,
                    payment_date,
                    amount_per_unit,
                    currency,
                    source_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    "00878",
                    (
                        "twse_etfortune_dividend:"
                        "00878:2023-08-16"
                    ),
                    "2023-08-16",
                    "2023-08-22",
                    "2023-09-11",
                    0.35,
                    "TWD",
                    "twse_etfortune_dividend",
                ),
            )

            connection.commit()

        finally:
            connection.close()

    def tearDown(self) -> None:
        """刪除臨時資料庫。"""

        self.temp_directory.cleanup()

    def build_notice(
        self,
        amount: str = "0.35",
        payment_date: str = "2023-09-11",
    ) -> ActualDividendNoticeInput:
        """建立合法正式通知書。"""

        return (
            ActualDividendNoticeInput
            .model_validate(
                {
                    "source_id": "notice",
                    "source_document_id": (
                        "notice-00878-2023-08"
                    ),
                    "source_document_url": (
                        "https://example.com/"
                        "notice"
                    ),
                    "source_document_date": (
                        "2023-08-15"
                    ),
                    "information_basis": (
                        "ACTUAL"
                    ),
                    "etf_code": "00878",
                    "ex_dividend_date": (
                        "2023-08-16"
                    ),
                    "record_date": (
                        "2023-08-22"
                    ),
                    "payment_date": (
                        payment_date
                    ),
                    "amount_per_unit": amount,
                    "components": [
                        {
                            "component_code": (
                                "76W"
                            ),
                            "ratio_pct": "100",
                        },
                    ],
                }
            )
        )

    def test_unique_event_is_matched(
        self,
    ) -> None:
        """ETF、除息日與金額唯一時接受。"""

        result = (
            match_actual_dividend_notices(
                notices=[
                    self.build_notice(),
                ],
                database_path=(
                    self.database_path
                ),
            )
        )

        self.assertEqual(
            len(result.matched),
            1,
        )

        self.assertEqual(
            len(result.rejected),
            0,
        )

        self.assertEqual(
            result.matched[0]
            .dividend_source_event_id,
            (
                "twse_etfortune_dividend:"
                "00878:2023-08-16"
            ),
        )

    def test_amount_mismatch_is_rejected(
        self,
    ) -> None:
        """配息金額不同時拒絕。"""

        result = (
            match_actual_dividend_notices(
                notices=[
                    self.build_notice(
                        amount="0.36"
                    ),
                ],
                database_path=(
                    self.database_path
                ),
            )
        )

        self.assertEqual(
            len(result.matched),
            0,
        )

        self.assertEqual(
            result.rejected[0].category,
            "amount_mismatch",
        )

    def test_payment_date_mismatch_is_rejected(
        self,
    ) -> None:
        """輔助日期不一致時拒絕。"""

        result = (
            match_actual_dividend_notices(
                notices=[
                    self.build_notice(
                        payment_date=(
                            "2023-09-12"
                        )
                    ),
                ],
                database_path=(
                    self.database_path
                ),
            )
        )

        self.assertEqual(
            result.rejected[0].category,
            "event_metadata_mismatch",
        )

    def test_ambiguous_event_is_rejected(
        self,
    ) -> None:
        """匹配到多個來源事件時不得自行選擇。"""

        connection = get_connection(
            self.database_path
        )

        try:
            connection.execute(
                """
                INSERT INTO etf_dividend (
                    etf_code,
                    source_event_id,
                    ex_dividend_date,
                    record_date,
                    payment_date,
                    amount_per_unit,
                    currency,
                    source_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    "00878",
                    "second-source-event",
                    "2023-08-16",
                    "2023-08-22",
                    "2023-09-11",
                    0.35,
                    "TWD",
                    "second_source",
                ),
            )

            connection.commit()

        finally:
            connection.close()

        result = (
            match_actual_dividend_notices(
                notices=[
                    self.build_notice(),
                ],
                database_path=(
                    self.database_path
                ),
            )
        )

        self.assertEqual(
            result.rejected[0].category,
            "ambiguous_dividend_event",
        )


if __name__ == "__main__":
    unittest.main()
