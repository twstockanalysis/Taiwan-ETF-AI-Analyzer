"""第一金投信官方 ETF 配息公告探索測試。"""

import unittest

from backend.app.data_sources.first_actual_dividend_discovery import (
    discover_first_dividend_documents,
    parse_first_dividend_notices,
    parse_first_fund_name,
)


class TestFirstActualDividendDiscovery(unittest.TestCase):
    def test_resolves_etf_code_from_double_encoded_fund_data(self) -> None:
        source = """&amp;quot;cName&amp;quot;: &amp;quot;第一金台股趨勢優選主動式ETF基金&amp;quot;,
        &amp;quot;cETFStockCode&amp;quot;: &amp;quot;00994A&amp;quot;"""
        self.assertEqual(
            parse_first_fund_name(etf_code="00994A", html_text=source),
            "第一金台股趨勢優選主動式ETF基金",
        )

    def test_accepts_amount_notice_and_rejects_pre_distribution(self) -> None:
        result = parse_first_dividend_notices(
            etf_code="00994A",
            fund_name="第一金台股趨勢優選主動式ETF基金",
            html_text="""
            <a href="https://www.fsitc.com.tw/Files/EDM/period_20260615092511600742.pdf">
            【配息金額公告】第一金台股趨勢優選主動式ETF證券投資信託基金收益分配金額公告</a>
            <a href="https://www.fsitc.com.tw/Files/EDM/pre.pdf">
            【配息期前公告】第一金台股趨勢優選主動式ETF證券投資信託基金</a>
            """,
        )
        self.assertEqual(len(result.candidates), 1)
        self.assertEqual(result.candidates[0].declared_date.isoformat(), "2026-06-15")
        self.assertEqual(result.candidates[0].information_basis, "UNKNOWN")
        self.assertEqual(len(result.rejections), 1)

    def test_does_not_match_other_fund(self) -> None:
        result = parse_first_dividend_notices(
            etf_code="00994A",
            fund_name="第一金台股趨勢優選主動式ETF基金",
            html_text="""<a href="https://www.fsitc.com.tw/Files/EDM/other.pdf">
            【配息金額公告】第一金臺灣工業菁英30ETF收益分配金額公告</a>""",
        )
        self.assertEqual(result.candidates, ())

    def test_network_access_requires_explicit_opt_in(self) -> None:
        with self.assertRaisesRegex(ValueError, "allow_network=True"):
            discover_first_dividend_documents(etf_code="00994A")


if __name__ == "__main__":
    unittest.main()
