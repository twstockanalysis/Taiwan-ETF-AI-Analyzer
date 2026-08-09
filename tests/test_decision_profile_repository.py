"""M11-1 決策條件與手動持有部位 Repository 測試。"""

from decimal import Decimal
from pathlib import Path
import sqlite3
import tempfile
import unittest

from backend.app.database.connection import get_connection
from backend.app.database.init_db import initialize_database
from backend.app.models.decision_profile import (
    ManualHoldingUpsert,
    UserConditionsUpsert,
)
from backend.app.repositories.decision_profile_repository import (
    delete_manual_holding,
    get_user_conditions,
    list_manual_holdings,
    upsert_manual_holding,
    upsert_user_conditions,
)


class TestDecisionProfileRepository(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = (
            Path(self.temp_directory.name) / "decision-profile.db"
        )
        initialize_database(self.database_path)
        connection = get_connection(self.database_path)
        connection.execute(
            """
            INSERT INTO etf_master (code, name, is_active, is_bond)
            VALUES ('0056', '元大高股息', 0, 0);
            """
        )
        connection.commit()
        connection.close()

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_schema_creates_profile_and_holding_tables(self):
        connection = get_connection(self.database_path)
        rows = connection.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table'
              AND name IN ('decision_profile', 'manual_holding');
            """
        ).fetchall()
        connection.close()
        self.assertEqual(
            {row["name"] for row in rows},
            {"decision_profile", "manual_holding"},
        )

    def test_conditions_upsert_preserves_missing_and_formal_zero(self):
        self.assertIsNone(get_user_conditions(self.database_path))
        result = upsert_user_conditions(
            UserConditionsUpsert(
                monthly_after_tax_target="0",
                analysis_years=10,
                history_years=3,
                cash_deduction_rate_pct=None,
            ),
            self.database_path,
        )
        self.assertEqual(
            result["monthly_after_tax_target"], Decimal("0.0")
        )
        self.assertIsNone(result["cash_deduction_rate_pct"])

        updated = upsert_user_conditions(
            UserConditionsUpsert(
                monthly_after_tax_target="3000",
                analysis_years=20,
                history_years=5,
                cash_deduction_rate_pct="0",
            ),
            self.database_path,
        )
        self.assertEqual(updated["cash_deduction_rate_pct"], Decimal("0.0"))

    def test_manual_holding_can_be_upserted_and_deleted(self):
        created = upsert_manual_holding(
            "0056",
            ManualHoldingUpsert(
                held_units=1000,
                unit_price="35.5",
                price_as_of_date="2026-08-09",
            ),
            self.database_path,
        )
        self.assertEqual(created["etf_code"], "0056")
        self.assertEqual(created["unit_price"], Decimal("35.5"))
        self.assertFalse(created["is_active"])

        updated = upsert_manual_holding(
            "0056",
            ManualHoldingUpsert(held_units=1200, unit_price="36"),
            self.database_path,
        )
        self.assertEqual(updated["held_units"], 1200)
        self.assertEqual(len(list_manual_holdings(self.database_path)), 1)
        self.assertTrue(delete_manual_holding("0056", self.database_path))
        self.assertFalse(delete_manual_holding("0056", self.database_path))

    def test_database_rejects_zero_units(self):
        connection = get_connection(self.database_path)
        with self.assertRaises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO manual_holding (etf_code, held_units, unit_price)
                VALUES ('0056', 0, 35.5);
                """
            )
        connection.close()

    def test_initialize_upgrades_existing_database_without_losing_etfs(self):
        connection = get_connection(self.database_path)
        connection.execute("DROP TABLE manual_holding;")
        connection.execute("DROP TABLE decision_profile;")
        connection.commit()
        connection.close()
        initialize_database(self.database_path)
        connection = get_connection(self.database_path)
        etf = connection.execute(
            "SELECT code FROM etf_master WHERE code = '0056';"
        ).fetchone()
        tables = connection.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table'
              AND name IN ('decision_profile', 'manual_holding');
            """
        ).fetchall()
        connection.close()
        self.assertEqual(etf["code"], "0056")
        self.assertEqual(len(tables), 2)


if __name__ == "__main__":
    unittest.main()
