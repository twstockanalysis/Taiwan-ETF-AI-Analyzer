"""ETF 代號直查型官方成分股 Adapter 測試。"""

import unittest
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from backend.app.data_sources.constituent_pipeline import import_official_constituents
from backend.app.data_sources.direct_constituent_adapters import (
    NOMURA_API_URL,
    fetch_fubon_constituent_snapshot,
    fetch_nomura_constituent_snapshot,
    parse_ctbc_constituent_html,
    parse_fubon_constituent_html,
    parse_nomura_constituent_payload,
    parse_sinopac_constituent_html,
    parse_taishin_constituent_html,
)
from backend.app.database.connection import get_connection
from backend.app.database.init_db import initialize_database


FETCHED_AT = datetime(2026, 8, 14, 9, tzinfo=timezone.utc)
ROWS = """
<tr><td>2330</td><td>台積電</td><td>100</td><td>60</td></tr>
<tr><td>2454</td><td>聯發科</td><td>80</td><td>30</td></tr>
<tr><td>2308</td><td>台達電</td><td>20</td><td>9.5</td></tr>
"""


class TestDirectHtmlConstituentAdapters(unittest.TestCase):
    def test_sinopac(self):
        content = f"""00930 資料日期：2026/08/13
        <table><tr><th>證券代碼</th><th>證券名稱</th><th>股數</th>
        <th>佔基金淨資產之權重(%)</th></tr>{ROWS}</table>"""
        result = parse_sinopac_constituent_html(
            content, etf_code="00930", source_url="https://example.test",
            fetched_at=FETCHED_AT,
        )
        self.assertEqual(result.source_id, "sinopac_official_pcf")
        self.assertEqual(result.as_of_date.isoformat(), "2026-08-13")
        self.assertEqual(len(result.positions), 3)

    def test_taishin_removes_tw_market_suffix(self):
        rows = ROWS.replace("2330", "2330 TT").replace("2454", "2454 TT").replace(
            "2308", "2308 TT"
        ).replace("<td>60</td>", "<td>60%</td>")
        content = f"""00987A <input id="NAV_DATE" value="2026/8/13 上午 12:00:00">
        <table><tr><th>代號</th><th>名稱</th><th>股數</th><th>持股權重</th></tr>
        {rows}</table>"""
        result = parse_taishin_constituent_html(
            content, etf_code="00987A", source_url="https://example.test",
            fetched_at=FETCHED_AT,
        )
        self.assertEqual(result.positions[0].constituent_id, "2330")
        self.assertEqual(result.source_id, "taishin_official_holdings")

    def test_ctbc(self):
        content = f"""股票代號 : 00891
        <span id="Label_AUM01">2026/08/13</span>
        <table><tr><th>股票代碼</th><th>股票名稱</th><th>股數</th><th>權重(%)</th></tr>
        {ROWS}</table>"""
        result = parse_ctbc_constituent_html(
            content, etf_code="00891", source_url="https://example.test",
            fetched_at=FETCHED_AT,
        )
        self.assertEqual(str(sum(item.weight_pct for item in result.positions)), "99.5")

    def test_fubon_uses_fifth_column(self):
        rows = ROWS.replace("<td>60</td>", "<td>1000</td><td>60</td>").replace(
            "<td>30</td>", "<td>900</td><td>30</td>"
        ).replace("<td>9.5</td>", "<td>800</td><td>9.5</td>")
        content = f"""006208 資料日期：2026/08/13
        <table><tr><th>股票代碼</th><th>股票名稱</th><th>股數</th><th>金額</th>
        <th>權重(%)</th></tr>{rows}</table>"""
        result = parse_fubon_constituent_html(
            content, etf_code="006208", source_url="https://example.test",
            fetched_at=FETCHED_AT,
        )
        self.assertEqual(result.positions[0].weight_pct, 60)

    def test_partial_and_wrong_pages_are_rejected(self):
        content = """00930 資料日期：2026/08/13
        <table><tr><th>證券代碼</th><th>證券名稱</th><th>股數</th>
        <th>佔基金淨資產之權重(%)</th></tr>
        <tr><td>2330</td><td>台積電</td><td>100</td><td>60</td></tr></table>"""
        with self.assertRaisesRegex(ValueError, "疑似資料不完整"):
            parse_sinopac_constituent_html(
                content, etf_code="00930", source_url="https://example.test",
                fetched_at=FETCHED_AT,
            )
        with self.assertRaisesRegex(ValueError, "與要求的 00931 不符"):
            parse_sinopac_constituent_html(
                content, etf_code="00931", source_url="https://example.test",
                fetched_at=FETCHED_AT,
            )


class TestNomuraConstituentAdapter(unittest.TestCase):
    @staticmethod
    def payload():
        return {
            "StatusCode": 0,
            "Entries": {
                "FundID": "00944",
                "Data": {"Table": [{
                    "TableTitle": "股票",
                    "Rows": [
                        ["2330", "台積電", "100", "60"],
                        ["2454", "聯發科", "80", "30"],
                        ["2308", "台達電", "20", "9.5"],
                    ],
                    "NavDate": "2026/08/13",
                }]},
            },
        }

    def test_parses_stock_table(self):
        result = parse_nomura_constituent_payload(
            self.payload(), etf_code="00944", source_url="https://example.test",
            fetched_at=FETCHED_AT,
        )
        self.assertEqual(result.source_id, "nomura_official_fund_assets")
        self.assertEqual(len(result.positions), 3)

    @patch("backend.app.data_sources.direct_constituent_adapters.httpx.post")
    def test_fetch_posts_etf_code(self, mock_post):
        response = Mock()
        response.json.return_value = self.payload()
        response.raise_for_status.return_value = None
        mock_post.return_value = response
        result = fetch_nomura_constituent_snapshot("00944", fetched_at=FETCHED_AT)
        self.assertEqual(result.etf_code, "00944")
        self.assertEqual(mock_post.call_args.args[0], NOMURA_API_URL)
        self.assertEqual(mock_post.call_args.kwargs["json"]["FundID"], "00944")


class TestFubonConstituentFetch(unittest.TestCase):
    @patch("backend.app.data_sources.direct_constituent_adapters._get")
    def test_follows_official_assets_link(self, mock_get):
        pcf = Mock()
        pcf.url = "https://websys.fsit.com.tw/FubonETF/Trade/Pcf.aspx?stkId=006208"
        pcf.text = '<a href="Assets.aspx?stkId=006208&amp;ddate=2026/08/14">基金資產</a>'
        assets = Mock()
        assets.url = "https://websys.fsit.com.tw/FubonETF/Trade/Assets.aspx?stkId=006208"
        rows = ROWS.replace("<td>60</td>", "<td>1000</td><td>60</td>").replace(
            "<td>30</td>", "<td>900</td><td>30</td>"
        ).replace("<td>9.5</td>", "<td>800</td><td>9.5</td>")
        assets.text = f"""006208 資料日期：2026/08/13<table><tr>
        <th>股票代碼</th><th>股票名稱</th><th>股數</th><th>金額</th><th>權重(%)</th>
        </tr>{rows}</table>"""
        mock_get.side_effect = [pcf, assets]
        result = fetch_fubon_constituent_snapshot("006208", fetched_at=FETCHED_AT)
        self.assertEqual(result.etf_code, "006208")
        self.assertIn("Assets.aspx", mock_get.call_args_list[1].args[0])


class TestOfficialConstituentPipeline(unittest.TestCase):
    def test_dispatches_direct_source_and_persists_snapshot(self):
        content = f"""00930 資料日期：2026/08/13
        <table><tr><th>證券代碼</th><th>證券名稱</th><th>股數</th>
        <th>佔基金淨資產之權重(%)</th></tr>{ROWS}</table>"""
        snapshot = parse_sinopac_constituent_html(
            content, etf_code="00930", source_url="https://example.test",
            fetched_at=FETCHED_AT,
        )
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "constituents.db"
            initialize_database(database_path)
            connection = get_connection(database_path)
            connection.execute(
                "INSERT INTO etf_master (code, name) VALUES ('00930', '永豐ESG低碳高息');"
            )
            connection.commit()
            connection.close()
            with patch.dict(
                "backend.app.data_sources.constituent_pipeline."
                "DIRECT_CONSTITUENT_FETCHERS",
                {"sinopac": Mock(return_value=snapshot)},
                clear=True,
            ):
                result = import_official_constituents(
                    " SINOPAC ", "00930", database_path
                )
            self.assertEqual(result.constituent_count, 3)
            self.assertEqual(str(result.total_weight_pct), "99.5")

    def test_rejects_unknown_issuer(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "constituents.db"
            initialize_database(database_path)
            connection = get_connection(database_path)
            connection.execute(
                "INSERT INTO etf_master (code, name) VALUES ('00930', '永豐ESG低碳高息');"
            )
            connection.commit()
            connection.close()
            with self.assertRaisesRegex(ValueError, "尚未支援"):
                import_official_constituents("unknown", "00930", database_path)


if __name__ == "__main__":
    unittest.main()
