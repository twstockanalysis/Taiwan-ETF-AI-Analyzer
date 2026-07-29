"""ETF 分析資料表 Schema 測試。"""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from backend.app.database.connection import (
    get_connection,
)
from backend.app.database.init_db import (
    initialize_database,
)


class TestAnalysisSchema(unittest.TestCase):
    """測試績效、配息及配息組成資料表。"""

    def setUp(self) -> None:
        """建立獨立臨時資料庫。"""

        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.database_path = (
            Path(self.temp_directory.name)
            / "analysis.db"
        )

        initialize_database(
            self.database_path
        )

        self.connection = get_connection(
            self.database_path
        )

        self.connection.execute(
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
                "00918",
                "大華優利高填息30",
                0,
                0,
            ),
        )

        self.connection.commit()

    def tearDown(self) -> None:
        """關閉並刪除臨時資料庫。"""

        self.connection.close()
        self.temp_directory.cleanup()

    def test_analysis_tables_exist(
        self,
    ) -> None:
        """確認三張分析資料表存在。"""

        rows = self.connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name IN (
                  'etf_performance',
                  'etf_dividend',
                  'etf_dividend_component'
              );
            """
        ).fetchall()

        table_names = {
            row["name"]
            for row in rows
        }

        self.assertEqual(
            table_names,
            {
                "etf_performance",
                "etf_dividend",
                "etf_dividend_component",
            },
        )

    def test_performance_can_be_inserted(
        self,
    ) -> None:
        """確認六個月績效可以寫入。"""

        self.connection.execute(
            """
            INSERT INTO etf_performance (
                etf_code,
                as_of_date,
                period_code,
                return_pct,
                source_id
            )
            VALUES (?, ?, ?, ?, ?);
            """,
            (
                "00918",
                "2026-07-29",
                "6M",
                12.3456,
                "test_source",
            ),
        )

        self.connection.commit()

        row = self.connection.execute(
            """
            SELECT return_pct
            FROM etf_performance
            WHERE etf_code = '00918';
            """
        ).fetchone()

        self.assertAlmostEqual(
            row["return_pct"],
            12.3456,
        )

    def test_invalid_period_is_rejected(
        self,
    ) -> None:
        """確認未知績效期間會被拒絕。"""

        with self.assertRaises(
            sqlite3.IntegrityError
        ):
            self.connection.execute(
                """
                INSERT INTO etf_performance (
                    etf_code,
                    as_of_date,
                    period_code,
                    return_pct,
                    source_id
                )
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    "00918",
                    "2026-07-29",
                    "10M",
                    1.0,
                    "test_source",
                ),
            )

        self.connection.rollback()

    def test_duplicate_performance_is_rejected(
        self,
    ) -> None:
        """確認同來源同日同期間不可重複。"""

        values = (
            "00918",
            "2026-07-29",
            "6M",
            12.0,
            "test_source",
        )

        statement = """
            INSERT INTO etf_performance (
                etf_code,
                as_of_date,
                period_code,
                return_pct,
                source_id
            )
            VALUES (?, ?, ?, ?, ?);
        """

        self.connection.execute(
            statement,
            values,
        )

        self.connection.commit()

        with self.assertRaises(
            sqlite3.IntegrityError
        ):
            self.connection.execute(
                statement,
                values,
            )

        self.connection.rollback()

    def insert_dividend(self) -> int:
        """建立一筆配息事件並回傳 ID。"""

        cursor = self.connection.execute(
            """
            INSERT INTO etf_dividend (
                etf_code,
                source_event_id,
                ex_dividend_date,
                payment_date,
                amount_per_unit,
                currency,
                source_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                "00918",
                "00918-2026-Q3",
                "2026-09-15",
                "2026-10-15",
                0.70,
                "TWD",
                "test_source",
            ),
        )

        self.connection.commit()

        return int(cursor.lastrowid)

    def test_76w_component_can_be_inserted(
        self,
    ) -> None:
        """確認可保存 76W 配息組成。"""

        dividend_id = self.insert_dividend()

        self.connection.execute(
            """
            INSERT INTO etf_dividend_component (
                dividend_id,
                component_code,
                component_name,
                ratio_pct,
                source_id
            )
            VALUES (?, ?, ?, ?, ?);
            """,
            (
                dividend_id,
                "76W",
                "測試配息來源",
                100.0,
                "test_source",
            ),
        )

        self.connection.commit()

        row = self.connection.execute(
            """
            SELECT
                component_code,
                ratio_pct
            FROM etf_dividend_component;
            """
        ).fetchone()

        self.assertEqual(
            row["component_code"],
            "76W",
        )

        self.assertEqual(
            row["ratio_pct"],
            100.0,
        )

    def test_component_requires_value(
        self,
    ) -> None:
        """確認組成必須有金額或比例。"""

        dividend_id = self.insert_dividend()

        with self.assertRaises(
            sqlite3.IntegrityError
        ):
            self.connection.execute(
                """
                INSERT INTO etf_dividend_component (
                    dividend_id,
                    component_code,
                    source_id
                )
                VALUES (?, ?, ?);
                """,
                (
                    dividend_id,
                    "76W",
                    "test_source",
                ),
            )

        self.connection.rollback()

    def test_dividend_delete_cascades_components(
        self,
    ) -> None:
        """確認刪除配息時同步刪除組成。"""

        dividend_id = self.insert_dividend()

        self.connection.execute(
            """
            INSERT INTO etf_dividend_component (
                dividend_id,
                component_code,
                ratio_pct,
                source_id
            )
            VALUES (?, ?, ?, ?);
            """,
            (
                dividend_id,
                "76W",
                100.0,
                "test_source",
            ),
        )

        self.connection.commit()

        self.connection.execute(
            """
            DELETE FROM etf_dividend
            WHERE id = ?;
            """,
            (dividend_id,),
        )

        self.connection.commit()

        count = self.connection.execute(
            """
            SELECT COUNT(*)
            FROM etf_dividend_component;
            """
        ).fetchone()[0]

        self.assertEqual(
            count,
            0,
        )


if __name__ == "__main__":
    unittest.main()