"""Portable dividend-yield collaboration bundle tests."""

import json
import tempfile
import unittest
from pathlib import Path

from backend.app.database.connection import get_connection
from backend.app.database.init_db import initialize_database
from deployment.dividend_yield_bundle import (
    export_dividend_yield_bundle,
    import_dividend_yield_bundle,
)


class TestDividendYieldBundle(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.source = self.root / "source.db"
        self.target = self.root / "target.db"
        self.bundle = self.root / "dividend-yields.json"
        self.manifest = self.root / "dividend-yields.manifest.json"
        for database in (self.source, self.target):
            initialize_database(database)
            self._seed_event(database)

        connection = get_connection(self.source)
        try:
            connection.execute(
                """
                INSERT INTO etf_dividend_summary_metric (
                    dividend_id,
                    yield_pct,
                    yield_basis,
                    yield_source_id,
                    reference_trade_date,
                    reference_close_price
                )
                VALUES (
                    1,
                    2.0,
                    'CALCULATED',
                    'twse_stock_day',
                    '2026-03-19',
                    25.0
                );
                """
            )
            connection.commit()
        finally:
            connection.close()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    @staticmethod
    def _seed_event(database: Path) -> None:
        connection = get_connection(database)
        try:
            connection.execute(
                """
                INSERT INTO etf_master (
                    code, name, is_active, is_bond
                )
                VALUES ('00918', '測試 ETF', 1, 0);
                """
            )
            connection.execute(
                """
                INSERT INTO etf_dividend (
                    id,
                    etf_code,
                    source_event_id,
                    ex_dividend_date,
                    payment_date,
                    amount_per_unit,
                    currency,
                    source_id
                )
                VALUES (
                    1,
                    '00918',
                    'event-1',
                    '2026-03-20',
                    '2026-04-15',
                    0.5,
                    'TWD',
                    'official'
                );
                """
            )
            connection.commit()
        finally:
            connection.close()

    def test_round_trip_uses_stable_event_key(self) -> None:
        manifest = export_dividend_yield_bundle(
            self.source,
            self.bundle,
            self.manifest,
        )
        self.assertEqual(manifest["record_count"], 1)
        self.assertEqual(
            manifest["yield_basis_counts"],
            {"CALCULATED": 1},
        )

        summary = import_dividend_yield_bundle(
            self.target,
            self.bundle,
            self.manifest,
        )
        self.assertEqual(summary["inserted_records"], 1)

        connection = get_connection(self.target)
        try:
            row = connection.execute(
                """
                SELECT
                    yield_pct,
                    yield_basis,
                    yield_source_id,
                    reference_trade_date,
                    reference_close_price
                FROM etf_dividend_summary_metric
                WHERE dividend_id = 1;
                """
            ).fetchone()
        finally:
            connection.close()

        self.assertEqual(row["yield_pct"], 2.0)
        self.assertEqual(row["yield_basis"], "CALCULATED")
        self.assertEqual(row["yield_source_id"], "twse_stock_day")
        self.assertEqual(row["reference_trade_date"], "2026-03-19")
        self.assertEqual(row["reference_close_price"], 25.0)

    def test_tampered_bundle_is_rejected_before_write(self) -> None:
        export_dividend_yield_bundle(
            self.source,
            self.bundle,
            self.manifest,
        )
        payload = json.loads(self.bundle.read_text(encoding="utf-8"))
        payload["records"][0]["yield_pct"] = "99"
        self.bundle.write_text(
            json.dumps(payload),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "SHA-256"):
            import_dividend_yield_bundle(
                self.target,
                self.bundle,
                self.manifest,
            )

        connection = get_connection(self.target)
        try:
            count = connection.execute(
                "SELECT COUNT(*) FROM etf_dividend_summary_metric;"
            ).fetchone()[0]
        finally:
            connection.close()
        self.assertEqual(count, 0)

    def test_fingerprint_mismatch_is_rejected_before_write(self) -> None:
        export_dividend_yield_bundle(
            self.source,
            self.bundle,
            self.manifest,
        )
        connection = get_connection(self.target)
        try:
            connection.execute(
                "UPDATE etf_dividend SET amount_per_unit = 0.6 WHERE id = 1;"
            )
            connection.commit()
        finally:
            connection.close()

        with self.assertRaisesRegex(ValueError, "fingerprint mismatch"):
            import_dividend_yield_bundle(
                self.target,
                self.bundle,
                self.manifest,
            )

        connection = get_connection(self.target)
        try:
            count = connection.execute(
                "SELECT COUNT(*) FROM etf_dividend_summary_metric;"
            ).fetchone()[0]
        finally:
            connection.close()
        self.assertEqual(count, 0)
