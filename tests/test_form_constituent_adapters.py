"""官方 HTML 表單型 ETF 成分股 Adapter 測試。"""

import unittest
from datetime import datetime, timezone

from backend.app.data_sources.form_constituent_adapters import (
    parse_union_constituent_html,
    parse_union_form_contract,
    resolve_union_query_date,
)


FETCHED_AT = datetime(2026, 8, 14, 9, tzinfo=timezone.utc)


def _union_html(*, code: str = "009804", total: str = "9.5") -> str:
    return f"""
    <form action="/CustCenter/BuyBackList" method="post">
      <select name="FundNo">
        <option value=009804>聯邦台灣精彩50ETF基金</option>
        <option value=009825>聯邦美國金融創新ETF基金</option>
      </select>
      <input type="date" name="sDate" value="2026-08-14" />
      <button type="submit">查詢</button>
      <h2>聯邦 ETF 基金 ( {code} )</h2>
      <span><b>資料日期： 2026-08-13</b></span>
      <table><thead><tr><th>股票代號</th><th>股票名稱</th><th>股數</th>
      <th>權重(%)</th></tr></thead><tbody>
      <tr><td>2330</td><td>台積電</td><td>100</td><td>60</td></tr>
      <tr><td>2454</td><td>聯發科</td><td>80</td><td>30</td></tr>
      <tr><td>2308</td><td>台達電</td><td>20</td><td>{total}</td></tr>
      </tbody></table>
    </form>
    """


class TestFormConstituentAdapters(unittest.TestCase):
    def test_union_form_contract_discovers_all_current_codes_and_date(self):
        codes, query_date = parse_union_form_contract(_union_html())
        self.assertEqual(codes, frozenset({"009804", "009825"}))
        self.assertEqual(query_date, "2026-08-14")
        with self.assertRaisesRegex(ValueError, "找不到 ETF：009999"):
            resolve_union_query_date(_union_html(), etf_code="009999")

    def test_union_stock_table_is_parsed(self):
        result = parse_union_constituent_html(
            _union_html(), etf_code="009804",
            source_url="https://www.usitc.com.tw/CustCenter/BuyBackList",
            fetched_at=FETCHED_AT,
        )
        self.assertEqual(result.as_of_date.isoformat(), "2026-08-13")
        self.assertEqual(result.source_id, "union_official_buyback_holdings")
        self.assertEqual(len(result.positions), 3)
        self.assertEqual(result.positions[0].constituent_id, "2330")

    def test_union_changed_form_identity_and_partial_rows_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "表單契約已變更"):
            parse_union_form_contract(_union_html().replace('method="post"', ''))
        with self.assertRaisesRegex(ValueError, "與要求的 009804 不符"):
            parse_union_constituent_html(
                _union_html(code="009825"), etf_code="009804",
                source_url="https://example.test", fetched_at=FETCHED_AT,
            )
        with self.assertRaisesRegex(ValueError, "疑似資料不完整"):
            parse_union_constituent_html(
                _union_html(total="0").replace(
                    "<td>30</td>", "<td>29</td>"
                ), etf_code="009804",
                source_url="https://example.test", fetched_at=FETCHED_AT,
            )


if __name__ == "__main__":
    unittest.main()
