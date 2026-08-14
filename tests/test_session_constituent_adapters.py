"""需官方 session 的 ETF 成分股 Adapter 測試。"""

import unittest
from datetime import datetime, timezone

from backend.app.data_sources.session_constituent_adapters import (
    parse_allianz_constituent_payload,
    parse_allianz_mapping,
    parse_hnh_constituent_payload,
    parse_hnh_system_token,
)


FETCHED_AT = datetime(2026, 8, 14, 9, tzinfo=timezone.utc)


class TestSessionConstituentAdapters(unittest.TestCase):
    def test_hnh_token_and_fractional_pcf_weights(self):
        self.assertEqual(
            parse_hnh_system_token({
                "ResultCode": "00", "access_token": "public-token",
                "expires_in": 1801,
            }),
            "public-token",
        )
        payload = {
            "ResultCode": "00",
            "Data": {
                "pcf": [{"ETFID": "009808", "BalDate": "2026-08-13"}],
                "StockList": [
                    {"StockNo": "2330", "StockName": "台積電", "Weight": "0.6"},
                    {"StockNo": "2454", "StockName": "聯發科", "Weight": "0.3"},
                    {"StockNo": "2308", "StockName": "台達電", "Weight": "0.095"},
                ],
            },
        }
        result = parse_hnh_constituent_payload(
            payload, etf_code="009808", source_url="https://example.test",
            fetched_at=FETCHED_AT,
        )
        self.assertEqual(result.as_of_date.isoformat(), "2026-08-13")
        self.assertEqual(result.source_id, "hnh_official_pcf_api")
        self.assertEqual(result.positions[0].weight_pct, 60)

    def test_hnh_invalid_token_identity_and_partial_rows_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "token 回應失敗"):
            parse_hnh_system_token({"ResultCode": "99"})
        with self.assertRaisesRegex(ValueError, "token 缺少有效期"):
            parse_hnh_system_token({
                "ResultCode": "00", "access_token": "token", "expires_in": 0,
            })
        payload = {
            "ResultCode": "00",
            "Data": {
                "pcf": [{"ETFID": "009809", "BalDate": "2026-08-13"}],
                "StockList": [
                    {"StockNo": "2330", "StockName": "台積電", "Weight": "0.6"},
                ],
            },
        }
        with self.assertRaisesRegex(ValueError, "與要求的 009808 不符"):
            parse_hnh_constituent_payload(
                payload, etf_code="009808", source_url="https://example.test",
                fetched_at=FETCHED_AT,
            )
        payload["Data"]["pcf"][0]["ETFID"] = "009808"
        with self.assertRaisesRegex(ValueError, "疑似資料不完整"):
            parse_hnh_constituent_payload(
                payload, etf_code="009808", source_url="https://example.test",
                fetched_at=FETCHED_AT,
            )

    def test_allianz_catalog_and_reconciled_stock_table(self):
        catalog = {"StatusCode": 0, "Entries": [
            {"CSecuritiesCode": "00984A", "CFundNo": "E0001"},
            {"CSecuritiesCode": "00993A", "CFundNo": "E0002"},
        ]}
        self.assertEqual(
            parse_allianz_mapping(etf_code="00984a", catalog_payload=catalog),
            "E0001",
        )
        payload = {"StatusCode": 0, "Entries": {
            "FundID": "E0001",
            "Data": {
                "FundAsset": {"NavDate": "2026/08/13", "PCFDate": "2026/08/14"},
                "Table": [{
                    "TableTitle": "股票 (99.50%)",
                    "Rows": [
                        ["1", "2330", "台積電", "100", "60"],
                        ["2", "2454", "聯發科", "80", "30"],
                        ["3", "2308", "台達電", "20", "9.5"],
                    ],
                }],
            },
        }}
        result = parse_allianz_constituent_payload(
            payload, etf_code="00984A", fund_id="E0001",
            source_url="https://example.test", fetched_at=FETCHED_AT,
        )
        self.assertEqual(result.as_of_date.isoformat(), "2026-08-13")
        self.assertEqual(result.source_id, "allianz_official_fund_assets")
        self.assertEqual(len(result.positions), 3)

    def test_allianz_bad_mapping_empty_asset_and_total_mismatch_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "總覽 API 回應失敗"):
            parse_allianz_mapping(etf_code="00984A", catalog_payload=[])
        with self.assertRaisesRegex(ValueError, "找不到唯一證券代號"):
            parse_allianz_mapping(
                etf_code="00984A", catalog_payload={"StatusCode": 0, "Entries": []}
            )
        empty_payload = {
            "StatusCode": 0,
            "Entries": {"FundID": "E0004", "Data": {
                "FundAsset": None, "Table": [],
            }},
        }
        with self.assertRaisesRegex(ValueError, "尚無可用基金資產"):
            parse_allianz_constituent_payload(
                empty_payload, etf_code="00412A", fund_id="E0004",
                source_url="https://example.test", fetched_at=FETCHED_AT,
            )
        payload = {"StatusCode": 0, "Entries": {
            "FundID": "E0001", "Data": {
                "FundAsset": {"NavDate": "2026/08/13"},
                "Table": [{
                    "TableTitle": "股票 (99.60%)",
                    "Rows": [
                        ["1", "2330", "台積電", "100", "60"],
                        ["2", "2454", "聯發科", "80", "30"],
                        ["3", "2308", "台達電", "20", "9.5"],
                    ],
                }],
            },
        }}
        with self.assertRaisesRegex(ValueError, "股票權重合計不符"):
            parse_allianz_constituent_payload(
                payload, etf_code="00984A", fund_id="E0001",
                source_url="https://example.test", fetched_at=FETCHED_AT,
            )


if __name__ == "__main__":
    unittest.main()
