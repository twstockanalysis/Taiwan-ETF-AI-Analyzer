"""元大投信官方 PCF 成分股 Adapter 測試。"""

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from backend.app.data_sources.constituent_pipeline import import_yuanta_constituents
from backend.app.data_sources.yuanta_constituent_adapter import (
    API_URL,
    SOURCE_ID,
    fetch_yuanta_constituent_snapshot,
    parse_yuanta_constituent_payload,
)
from backend.app.database.connection import get_connection
from backend.app.database.init_db import initialize_database


FIXTURE = Path(__file__).parent / "fixtures" / "yuanta_0050_constituents.json"
FETCHED_AT = datetime(2026, 8, 13, 9, tzinfo=timezone.utc)


def load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class TestYuantaConstituentAdapter(unittest.TestCase):
    def test_parses_all_stock_weights_and_excludes_futures(self):
        result = parse_yuanta_constituent_payload(
            load_fixture(),
            etf_code="0050",
            source_url="https://www.yuantaetfs.com/product/detail/0050/ratio",
            fetched_at=FETCHED_AT,
        )

        self.assertEqual(result.as_of_date.isoformat(), "2026-08-13")
        self.assertEqual(result.source_id, SOURCE_ID)
        self.assertEqual(len(result.positions), 3)
        self.assertEqual(
            [item.constituent_id for item in result.positions],
            ["2330", "2454", "2308"],
        )
        self.assertEqual(str(result.positions[0].weight_pct), "57.85")
        self.assertNotIn("TX", {item.constituent_id for item in result.positions})

    def test_wrong_etf_and_partial_payload_are_rejected(self):
        wrong_etf_payload = load_fixture()
        wrong_etf_payload["PCF"]["markcd"] = "0099"
        with self.assertRaisesRegex(ValueError, "與要求的 0050 不符"):
            parse_yuanta_constituent_payload(
                wrong_etf_payload,
                etf_code="0050",
                source_url="https://example.test",
                fetched_at=FETCHED_AT,
            )

        payload = load_fixture()
        payload["FundWeights"]["StockWeights"] = [
            payload["FundWeights"]["StockWeights"][0]
        ]
        with self.assertRaisesRegex(ValueError, "疑似資料不完整"):
            parse_yuanta_constituent_payload(
                payload,
                etf_code="0050",
                source_url="https://example.test",
                fetched_at=FETCHED_AT,
            )

    @patch("backend.app.data_sources.yuanta_constituent_adapter.httpx.get")
    def test_fetch_uses_official_api_and_pcf_parameters(self, mock_get):
        response = Mock()
        response.json.return_value = load_fixture()
        response.raise_for_status.return_value = None
        mock_get.return_value = response

        result = fetch_yuanta_constituent_snapshot("0050", fetched_at=FETCHED_AT)

        self.assertEqual(result.etf_code, "0050")
        self.assertEqual(mock_get.call_args.args[0], API_URL)
        params = mock_get.call_args.kwargs["params"]
        self.assertEqual(params["FuncId"], "PCF/Daily")
        self.assertEqual(params["ticker"], "0050")
        self.assertIn("verify", mock_get.call_args.kwargs)

    @patch(
        "backend.app.data_sources.constituent_pipeline."
        "fetch_yuanta_constituent_snapshot"
    )
    def test_pipeline_saves_validated_snapshot(self, mock_fetch):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "constituents.db"
            initialize_database(database_path)
            connection = get_connection(database_path)
            connection.execute(
                "INSERT INTO etf_master (code, name) VALUES ('0050', '元大台灣50');"
            )
            connection.commit()
            connection.close()
            payload = load_fixture()
            mock_fetch.return_value = parse_yuanta_constituent_payload(
                payload,
                etf_code="0050",
                source_url="https://www.yuantaetfs.com/product/detail/0050/ratio",
                fetched_at=FETCHED_AT,
            )

            result = import_yuanta_constituents("0050", database_path)

            self.assertEqual(result.constituent_count, 3)
            self.assertEqual(str(result.total_weight_pct), "99.71")


if __name__ == "__main__":
    unittest.main()
