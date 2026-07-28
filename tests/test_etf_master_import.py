"""ETF 主資料 SQLite 匯入測試。"""

import json
import tempfile
import unittest
from pathlib import Path

from backend.app.database.connection import (
    get_connection,
)
from backend.app.database.init_db import (
    initialize_database,
)
from backend.app.data_sources.import_etf_master import (
    load_processed_records,
)
from backend.app.models.etf_import import (
    ETFImportRecord,
)
from backend.app.repositories.etf_import_repository import (
    upsert_etf_master,
)


class TestETFMasterImport(unittest.TestCase):
    """測試 ETF 主資料 Upsert 流程。"""

    def setUp(self) -> None:
        """建立獨立測試資料庫。"""

        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.temp_path = Path(
            self.temp_directory.name
        )

        self.database_path = (
            self.temp_path / "test_import.db"
        )

        initialize_database(
            self.database_path
        )

    def tearDown(self) -> None:
        """刪除測試資料庫。"""

        self.temp_directory.cleanup()

    def build_record(
        self,
        code: str = "0050",
        name: str = "元大台灣50",
    ) -> ETFImportRecord:
        """建立合法 ETF 匯入資料。"""

        return ETFImportRecord.model_validate(
            {
                "code": code,
                "name": name,
                "is_active": False,
                "is_bond": False,
                "listing_date": "2003-06-30",
                "fund_size": None,
                "expense_ratio": None,
                "market": "TWSE",
                "source_id": "twse_openapi",
                "source_updated_at": None,
            }
        )

    def test_new_etf_is_inserted(self) -> None:
        """確認新 ETF 可以新增。"""

        summary = upsert_etf_master(
            records=[
                self.build_record(),
            ],
            database_path=self.database_path,
        )

        self.assertEqual(
            summary.inserted_records,
            1,
        )

        self.assertEqual(
            summary.updated_records,
            0,
        )

    def test_existing_etf_is_updated(self) -> None:
        """確認既有 ETF 可以更新。"""

        upsert_etf_master(
            records=[
                self.build_record(),
            ],
            database_path=self.database_path,
        )

        summary = upsert_etf_master(
            records=[
                self.build_record(
                    name="更新後名稱"
                ),
            ],
            database_path=self.database_path,
        )

        self.assertEqual(
            summary.inserted_records,
            0,
        )

        self.assertEqual(
            summary.updated_records,
            1,
        )

        connection = get_connection(
            self.database_path
        )

        try:
            result = connection.execute(
                """
                SELECT name
                FROM etf_master
                WHERE code = ?;
                """,
                ("0050",),
            ).fetchone()

            self.assertEqual(
                result["name"],
                "更新後名稱",
            )

        finally:
            connection.close()

    def test_existing_metrics_are_preserved(
        self,
    ) -> None:
        """確認主資料匯入不清空規模及費用率。"""

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
                    is_bond,
                    listing_date,
                    fund_size,
                    expense_ratio
                )
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    "0050",
                    "舊名稱",
                    0,
                    0,
                    "2003-06-30",
                    5000.0,
                    0.43,
                ),
            )

            connection.commit()

        finally:
            connection.close()

        upsert_etf_master(
            records=[
                self.build_record(
                    name="新名稱"
                ),
            ],
            database_path=self.database_path,
        )

        connection = get_connection(
            self.database_path
        )

        try:
            result = connection.execute(
                """
                SELECT
                    name,
                    fund_size,
                    expense_ratio
                FROM etf_master
                WHERE code = ?;
                """,
                ("0050",),
            ).fetchone()

            self.assertEqual(
                result["name"],
                "新名稱",
            )

            self.assertEqual(
                result["fund_size"],
                5000.0,
            )

            self.assertEqual(
                result["expense_ratio"],
                0.43,
            )

        finally:
            connection.close()

    def test_development_records_are_deleted(
        self,
    ) -> None:
        """確認 M5 開發測試資料會被移除。"""

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
                    "DEV001",
                    "開發測試 ETF",
                    0,
                    0,
                ),
            )

            connection.commit()

        finally:
            connection.close()

        summary = upsert_etf_master(
            records=[
                self.build_record(),
            ],
            database_path=self.database_path,
        )

        self.assertEqual(
            summary.deleted_development_records,
            1,
        )

        connection = get_connection(
            self.database_path
        )

        try:
            result = connection.execute(
                """
                SELECT code
                FROM etf_master
                WHERE code = 'DEV001';
                """
            ).fetchone()

            self.assertIsNone(result)

        finally:
            connection.close()

    def test_duplicate_codes_are_rejected(
        self,
    ) -> None:
        """確認同一批資料不可有重複代號。"""

        with self.assertRaises(
            ValueError
        ):
            upsert_etf_master(
                records=[
                    self.build_record(),
                    self.build_record(),
                ],
                database_path=self.database_path,
            )

    def test_processed_file_is_loaded(
        self,
    ) -> None:
        """確認 processed JSON 可以重新驗證。"""

        file_path = (
            self.temp_path
            / "processed.json"
        )

        payload = [
            self.build_record().model_dump(
                mode="json"
            )
        ]

        file_path.write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        records = load_processed_records(
            file_path
        )

        self.assertEqual(
            len(records),
            1,
        )

        self.assertEqual(
            records[0].code,
            "0050",
        )


if __name__ == "__main__":
    unittest.main()