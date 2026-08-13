"""ETF 成分股快照與加權重疊基礎測試。"""

import sqlite3
import tempfile
import unittest
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from pydantic import ValidationError

from backend.app.database.connection import get_connection
from backend.app.database.init_db import initialize_database
from backend.app.models.etf_constituent import (
    ETFConstituentPosition,
    ETFConstituentSnapshotCreate,
)
from backend.app.repositories.etf_constituent_repository import (
    get_latest_constituent_snapshot,
    save_constituent_snapshot,
)
from backend.app.services.constituent_overlap import (
    calculate_weighted_overlap,
)


class TestETFConstituentFoundation(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_directory.name) / "constituents.db"
        initialize_database(self.database_path)
        connection = get_connection(self.database_path)
        connection.executemany(
            "INSERT INTO etf_master (code, name) VALUES (?, ?);",
            [("0050", "元大台灣50"), ("006208", "富邦台50")],
        )
        connection.commit()
        connection.close()

    def tearDown(self):
        self.temp_directory.cleanup()

    @staticmethod
    def payload(etf_code: str, positions):
        return ETFConstituentSnapshotCreate(
            etf_code=etf_code,
            as_of_date=date(2026, 8, 13),
            source_id="issuer_official_holdings",
            source_url="https://example.test/holdings",
            fetched_at=datetime(2026, 8, 13, 8, tzinfo=timezone.utc),
            positions=positions,
        )

    def test_snapshot_is_saved_with_source_date_and_weights(self):
        result = save_constituent_snapshot(
            self.payload(
                "0050",
                [
                    {
                        "constituent_id": "2330",
                        "constituent_name": "台積電",
                        "weight_pct": "55.5",
                        "rank": 1,
                    },
                    {
                        "constituent_id": "2317",
                        "constituent_name": "鴻海",
                        "weight_pct": "6.5",
                        "rank": 2,
                    },
                ],
            ),
            self.database_path,
        )

        self.assertEqual(result.etf_code, "0050")
        self.assertEqual(result.total_weight_pct, Decimal("62.0"))
        self.assertEqual(result.constituent_count, 2)
        latest = get_latest_constituent_snapshot("0050", self.database_path)
        self.assertEqual(latest.id, result.id)
        self.assertEqual(latest.positions[0].constituent_id, "2330")

    def test_same_source_and_date_cannot_overwrite_snapshot(self):
        payload = self.payload(
            "0050",
            [{"constituent_id": "2330", "constituent_name": "台積電", "weight_pct": 50}],
        )
        save_constituent_snapshot(payload, self.database_path)

        with self.assertRaises(sqlite3.IntegrityError):
            save_constituent_snapshot(payload, self.database_path)

    def test_weighted_overlap_uses_smaller_disclosed_weight(self):
        left = save_constituent_snapshot(
            self.payload(
                "0050",
                [
                    {"constituent_id": "2330", "constituent_name": "台積電", "weight_pct": 55},
                    {"constituent_id": "2317", "constituent_name": "鴻海", "weight_pct": 8},
                ],
            ),
            self.database_path,
        )
        right = save_constituent_snapshot(
            self.payload(
                "006208",
                [
                    {"constituent_id": "2330", "constituent_name": "台積電", "weight_pct": 60},
                    {"constituent_id": "2454", "constituent_name": "聯發科", "weight_pct": 7},
                ],
            ),
            self.database_path,
        )

        result = calculate_weighted_overlap(left, right)

        self.assertEqual(result.overlap_pct, Decimal("55.000000"))
        self.assertEqual(result.shared_constituent_count, 1)
        self.assertEqual(result.shared_constituents[0].constituent_id, "2330")
        self.assertEqual(result.method, "SUM_MIN_DISCLOSED_WEIGHTS_V1")

    def test_duplicate_constituent_and_excess_total_are_rejected(self):
        with self.assertRaises(ValidationError):
            self.payload(
                "0050",
                [
                    {"constituent_id": "2330", "constituent_name": "台積電", "weight_pct": 60},
                    {"constituent_id": "2330", "constituent_name": "台積電", "weight_pct": 40},
                ],
            )
        with self.assertRaises(ValidationError):
            self.payload(
                "0050",
                [
                    {"constituent_id": "2330", "constituent_name": "台積電", "weight_pct": 60},
                    {"constituent_id": "2317", "constituent_name": "鴻海", "weight_pct": 41},
                ],
            )


if __name__ == "__main__":
    unittest.main()
