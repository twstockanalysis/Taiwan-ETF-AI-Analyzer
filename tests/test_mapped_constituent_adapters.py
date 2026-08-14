"""官方目錄對照型 ETF 成分股 Adapter 測試。"""

import unittest
from datetime import datetime, timezone
from io import BytesIO

from openpyxl import Workbook

from backend.app.data_sources.mapped_constituent_adapters import (
    parse_alliancebernstein_constituent_payload,
    parse_alliancebernstein_mapping,
    parse_capital_constituent_html,
    parse_capital_product_url,
    parse_esun_constituent_payload,
    parse_esun_mapping,
    parse_franklin_constituent_payload,
    parse_franklin_latest_query_date,
    parse_franklin_mapping,
    parse_fuh_hwa_assets_link,
    parse_fuh_hwa_constituent_excel,
    parse_mega_constituent_html,
    parse_mega_product_url,
    parse_jpmorgan_constituent_payload,
    parse_jpmorgan_mapping,
    parse_uob_constituent_html,
)


FETCHED_AT = datetime(2026, 8, 14, 9, tzinfo=timezone.utc)


class TestMappedConstituentAdapters(unittest.TestCase):
    def test_jpmorgan_catalog_and_product_data_holdings(self):
        catalog = [
            {"cusip": "TW00000401A1", "ticker": "00401A", "fundType": "etf"},
            {"cusip": "TW00000989A5", "ticker": "00989A", "fundType": "etf"},
        ]
        self.assertEqual(
            parse_jpmorgan_mapping(
                etf_code="00989a", catalog_payload=catalog
            ),
            "TW00000989A5",
        )
        payload = {"fundData": {
            "shareClass": {"exchangeTicker": "00989A"},
            "holdings": {"pcfEquityHoldings": {
                "effectiveDate": "2026-08-13",
                "data": [
                    {"securityTicker": "PANW", "securityIsin": "US6974351057",
                     "securityDescription": "PALO ALTO NETWORKS INC",
                     "marketValuePercent": "60"},
                    {"securityTicker": "GOOG", "securityIsin": "US02079K1079",
                     "securityDescription": "ALPHABET INC-CL C",
                     "marketValuePercent": "30"},
                    {"securityTicker": "NVDA", "securityIsin": "US67066G1040",
                     "securityDescription": "NVIDIA CORP",
                     "marketValuePercent": "9.5"},
                ],
            }},
        }}
        result = parse_jpmorgan_constituent_payload(
            payload, etf_code="00989A", isin="TW00000989A5",
            source_url="https://example.test", fetched_at=FETCHED_AT,
        )
        self.assertEqual(result.as_of_date.isoformat(), "2026-08-13")
        self.assertEqual(result.source_id, "jpmorgan_official_product_data")
        self.assertEqual(result.positions[0].constituent_id, "PANW")

    def test_jpmorgan_wrong_identity_and_partial_rows_are_rejected(self):
        payload = {"fundData": {
            "shareClass": {"exchangeTicker": "00401A"},
            "holdings": {"pcfEquityHoldings": {
                "effectiveDate": "2026-08-13",
                "data": [{
                    "securityTicker": "PANW",
                    "securityDescription": "PALO ALTO NETWORKS INC",
                    "marketValuePercent": "60",
                }],
            }},
        }}
        with self.assertRaisesRegex(ValueError, "與要求的 00989A 不符"):
            parse_jpmorgan_constituent_payload(
                payload, etf_code="00989A", isin="TW00000989A5",
                source_url="https://example.test", fetched_at=FETCHED_AT,
            )
        payload["fundData"]["shareClass"]["exchangeTicker"] = "00989A"
        with self.assertRaisesRegex(ValueError, "疑似資料不完整"):
            parse_jpmorgan_constituent_payload(
                payload, etf_code="00989A", isin="TW00000989A5",
                source_url="https://example.test", fetched_at=FETCHED_AT,
            )

    def test_alliancebernstein_catalog_and_reconciled_equity_holdings(self):
        catalog = {"etfs": [{"fundInfo": {
            "fundNumber": "00404A", "isin": "TW00000404A5",
        }}]}
        self.assertEqual(
            parse_alliancebernstein_mapping(
                etf_code="00404a", catalog_payload=catalog
            ),
            "TW00000404A5",
        )
        payload = {
            "domesticHoldings": [{
                "asOfDate": "08/13/2026",
                "holdingCategory": "holdings-section-equity",
                "isAllocation": True,
                "holdings": [
                    {"holdingCode": "2330", "holding": "台積電",
                     "holdingPerc": "60"},
                    {"holdingCode": "2454", "holding": "聯發科",
                     "holdingPerc": "29.487277"},
                ],
            }],
            "fundAssetTotal": {
                "secID": "00404A",
                "allocationObjSecType": [{
                    "allocationObjSecType": "holdings-section-equity",
                    "percentageUnderlyingSecurities": "89.487277",
                }],
            },
        }
        result = parse_alliancebernstein_constituent_payload(
            payload, etf_code="00404A", isin="TW00000404A5",
            source_url="https://example.test", fetched_at=FETCHED_AT,
        )
        self.assertEqual(result.as_of_date.isoformat(), "2026-08-13")
        self.assertEqual(
            result.source_id, "alliancebernstein_official_holdings_api"
        )
        self.assertEqual(len(result.positions), 2)

    def test_alliancebernstein_identity_and_equity_total_are_required(self):
        payload = {
            "domesticHoldings": [{
                "asOfDate": "08/13/2026",
                "holdingCategory": "holdings-section-equity",
                "holdings": [{
                    "holdingCode": "2330", "holding": "台積電",
                    "holdingPerc": "89.4",
                }],
            }],
            "fundAssetTotal": {
                "secID": "00404A",
                "allocationObjSecType": [{
                    "allocationObjSecType": "holdings-section-equity",
                    "percentageUnderlyingSecurities": "89.5",
                }],
            },
        }
        with self.assertRaisesRegex(ValueError, "股票資產合計不符"):
            parse_alliancebernstein_constituent_payload(
                payload, etf_code="00404A", isin="TW00000404A5",
                source_url="https://example.test", fetched_at=FETCHED_AT,
            )
        payload["fundAssetTotal"]["secID"] = "00980D"
        with self.assertRaisesRegex(ValueError, "與要求的 00404A 不符"):
            parse_alliancebernstein_constituent_payload(
                payload, etf_code="00404A", isin="TW00000404A5",
                source_url="https://example.test", fetched_at=FETCHED_AT,
            )

    def test_mega_catalog_and_holdings(self):
        catalog = """<div class="product-detail"><div class="detail-item">00932</div>
        <div class="detail-item"><a href="etf_product.aspx?id=19">基金</a></div></div>"""
        self.assertTrue(parse_mega_product_url(
            etf_code="00932", catalog_html=catalog
        ).endswith("etf_product.aspx?id=19"))
        rows = "".join(
            f'<div class="fund-info content-list-1"><div class="fund-content">{code}</div>'
            f'<div class="fund-content">{name}</div><div class="fund-content">100</div>'
            f'<div class="fund-content txt-right">{weight}%</div></div>'
            for code, name, weight in [
                ("2330", "台積電", "60"), ("2454", "聯發科", "30"),
                ("2308", "台達電", "9.5"),
            ]
        )
        content = f"""00932 資料來源：兆豐投信，2026/08/13
        <div id="fund_content_list_1">{rows}</div><div id="fund-content-2"></div>"""
        result = parse_mega_constituent_html(
            content, etf_code="00932", source_url="https://example.test",
            fetched_at=FETCHED_AT,
        )
        self.assertEqual(result.source_id, "mega_official_holdings")
        self.assertEqual(len(result.positions), 3)

    def test_fuh_hwa_assets_link_and_excel(self):
        link = parse_fuh_hwa_assets_link(
            detail_html='<a href="/api/assetsExcel/ETF21/20260811">下載</a>',
            internal_id="ETF21",
        )
        self.assertTrue(link.endswith("/api/assetsExcel/ETF21/20260811"))
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(["復華基金（證劵代碼：00929）"])
        sheet.append([])
        sheet.append(["日期: 2026/08/11"])
        sheet.append(["證券代號", "證券名稱", "股數", "金額", "權重(%)"])
        sheet.append(["2330", "台積電", "100", "1000", "60%"])
        sheet.append(["2454", "聯發科", "80", "900", "30%"])
        sheet.append(["2308", "台達電", "20", "800", "9.5%"])
        stream = BytesIO()
        workbook.save(stream)
        result = parse_fuh_hwa_constituent_excel(
            stream.getvalue(), etf_code="00929", source_url=link,
            fetched_at=FETCHED_AT,
        )
        self.assertEqual(result.as_of_date.isoformat(), "2026-08-11")
        self.assertEqual(result.source_id, "fuh_hwa_official_assets_excel")

    def test_capital_catalog_but_partial_holdings_fail_closed(self):
        catalog = '<a href="/etf/product/detail/365/basic">00923</a>'
        url = parse_capital_product_url(etf_code="00923", catalog_html=catalog)
        self.assertTrue(url.endswith("/365/buyback"))
        content = """00923 <h6 class="date">(2026/08/13)</h6> 股票代號
        <div class="tr show-for-medium"><div class="th">2330</div>
        <div class="th">台積電</div><div class="td">73.94%</div></div>"""
        with self.assertRaisesRegex(ValueError, "疑似資料不完整"):
            parse_capital_constituent_html(
                content, etf_code="00923", source_url=url, fetched_at=FETCHED_AT
            )

    def test_uob_stock_table(self):
        rows = """<tr><td>2330</td><td>台積電</td><td>100</td><td>1000</td><td>60</td></tr>
        <tr><td>2454</td><td>聯發科</td><td>80</td><td>900</td><td>30</td></tr>
        <tr><td>2308</td><td>台達電</td><td>20</td><td>800</td><td>9.5</td></tr>"""
        content = f"""00918 資料日期 : 2026/08/10<table><tr><th>股票代號</th>
        <th>股票名稱</th><th>股數</th><th>金額(元)</th>
        <th>佔基金淨資產之權重(%)</th></tr>{rows}</table>"""
        result = parse_uob_constituent_html(
            content, etf_code="00918", source_url="https://example.test",
            fetched_at=FETCHED_AT,
        )
        self.assertEqual(result.source_id, "uob_official_pcf")
        self.assertEqual(result.positions[0].constituent_id, "2330")

    def test_esun_overview_mapping_and_assets(self):
        overview = {"StatusCode": 0, "Entries": [
            {"StcokNo": "009803", "FundNo": "50"}
        ]}
        self.assertEqual(
            parse_esun_mapping(etf_code="009803", overview_payload=overview), "50"
        )
        payload = {"StatusCode": 0, "Entries": {"FundID": "50", "Data": {
            "FundAsset": {"NavDate": "2026/08/13"},
            "Table": [{"TableTitle": "股票", "Rows": [
                ["2330", "台積電", "100", "60"],
                ["2454", "聯發科", "80", "30"],
                ["2308", "台達電", "20", "9.5"],
            ]}],
        }}}
        result = parse_esun_constituent_payload(
            payload, etf_code="009803", fund_id="50",
            source_url="https://example.test", fetched_at=FETCHED_AT,
        )
        self.assertEqual(result.source_id, "esun_official_fund_assets")
        self.assertEqual(len(result.positions), 3)

    def test_unknown_mappings_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "找不到證券代號"):
            parse_mega_product_url(etf_code="00932", catalog_html="")
        with self.assertRaisesRegex(ValueError, "找不到證券代號"):
            parse_esun_mapping(
                etf_code="009803", overview_payload={"StatusCode": 0, "Entries": []}
            )

    def test_franklin_catalog_date_and_holdings(self):
        catalog = [
            {"FundID": "130", "StockCode": "00899"},
            {"FundID": "131", "StockCode": "00905"},
        ]
        self.assertEqual(
            parse_franklin_mapping(etf_code="00905", catalog_payload=catalog),
            "131",
        )
        self.assertEqual(
            parse_franklin_latest_query_date([
                "2026-08-11T16:00:00Z", "2026-08-12T16:00:00Z",
            ]),
            "20260813",
        )
        payload = {
            "FundID": "131",
            "StockCode": "00905",
            "AssetDate": "2026-08-12T16:00:00Z",
            "Secs": [
                {"SecuritiesCode": "2330", "SecuritiesName": "台積電",
                 "WeightingPercentage": "60%"},
                {"SecuritiesCode": "2454", "SecuritiesName": "聯發科",
                 "WeightingPercentage": "30%"},
                {"SecuritiesCode": "2308", "SecuritiesName": "台達電",
                 "WeightingPercentage": "9.5%"},
            ],
        }
        result = parse_franklin_constituent_payload(
            payload, etf_code="00905", fund_id="131",
            source_url="https://example.test", fetched_at=FETCHED_AT,
        )
        self.assertEqual(result.as_of_date.isoformat(), "2026-08-13")
        self.assertEqual(result.source_id, "franklin_official_holdings_api")

    def test_franklin_wrong_identity_and_partial_rows_are_rejected(self):
        payload = {
            "FundID": "131", "StockCode": "00906",
            "AssetDate": "2026-08-12T16:00:00Z", "Secs": [
                {"SecuritiesCode": "2330", "SecuritiesName": "台積電",
                 "WeightingPercentage": "60%"},
            ],
        }
        with self.assertRaisesRegex(ValueError, "與要求的 00905 不符"):
            parse_franklin_constituent_payload(
                payload, etf_code="00905", fund_id="131",
                source_url="https://example.test", fetched_at=FETCHED_AT,
            )
        payload["StockCode"] = "00905"
        with self.assertRaisesRegex(ValueError, "疑似資料不完整"):
            parse_franklin_constituent_payload(
                payload, etf_code="00905", fund_id="131",
                source_url="https://example.test", fetched_at=FETCHED_AT,
            )


if __name__ == "__main__":
    unittest.main()
