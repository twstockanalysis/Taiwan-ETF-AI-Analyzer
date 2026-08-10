from decimal import Decimal
from pathlib import Path
import tempfile
import unittest

from backend.app.database.connection import get_connection
from backend.app.database.init_db import initialize_database
from backend.app.models.etf_price import ETFDailyCloseRecord
from backend.app.repositories.daily_close_repository import (
    get_latest_daily_close,
    list_daily_closes,
    upsert_daily_close_records,
)


class TestDailyCloseRepository(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_directory.name) / "daily-close.db"
        initialize_database(self.database_path)
        connection = get_connection(self.database_path)
        connection.execute(
            "INSERT INTO etf_master (code, name) VALUES ('0056', '元大高股息');"
        )
        connection.commit()
        connection.close()

    def tearDown(self):
        self.temp_directory.cleanup()

    def record(self, trade_date: str, close_price: str):
        return ETFDailyCloseRecord(
            etf_code="0056",
            trade_date=trade_date,
            close_price=close_price,
            source_id="twse_stock_day",
        )

    def test_upsert_is_idempotent_and_latest_keeps_source(self):
        first = upsert_daily_close_records(
            [self.record("2026-08-07", "35"), self.record("2026-08-08", "36")],
            self.database_path,
        )
        second = upsert_daily_close_records(
            [self.record("2026-08-08", "36.5")],
            self.database_path,
        )
        self.assertEqual(first.inserted_records, 2)
        self.assertEqual(second.updated_records, 1)
        latest = get_latest_daily_close("0056", self.database_path)
        self.assertEqual(latest["trade_date"], "2026-08-08")
        self.assertEqual(latest["close_price"], Decimal("36.5"))
        self.assertEqual(latest["source_id"], "twse_stock_day")
        self.assertEqual(len(list_daily_closes("0056", self.database_path)), 2)

    def test_missing_close_stays_missing(self):
        self.assertIsNone(get_latest_daily_close("0056", self.database_path))


if __name__ == "__main__":
    unittest.main()
