"""富邦投信 ETF 收益分配文件發現測試。"""

import unittest

from backend.app.data_sources.fubon_actual_dividend_discovery import (
    normalize_fubon_etf_code,
    parse_fubon_dividend_documents,
    resolve_fubon_fund_id,
)


class TestFubonActualDividendDiscovery(unittest.TestCase):
    def test_resolves_fund_id_from_official_list(self) -> None:
        html = """
        <a href="/asset-management/fund/info/fund?Fd=40">台灣釆吉50基金</a>
        證券代號： 006208 證券簡稱：富邦台50
        <a href="/asset-management/fund/info/value?Fd=40">淨值</a>
        """
        self.assertEqual(resolve_fubon_fund_id(html, "006208"), "40")

    def test_code_validation_blocks_query_injection(self) -> None:
        self.assertEqual(normalize_fubon_etf_code(" 006208 "), "006208")
        for value in ("006208&Fd=1", "../006208", ""):
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_fubon_etf_code(value)

    def test_official_dividend_pdf_is_unknown_candidate(self) -> None:
        html = """
        <a href="https://etrade.fsit.com.tw/case/news/fund_service/a.pdf">
        ‧2025/11/14 富邦台灣釆吉50證券投資信託基金收益分配公告</a>
        """
        candidates = parse_fubon_dividend_documents(
            html_text=html, etf_code="006208"
        )
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].information_basis, "UNKNOWN")
        self.assertEqual(candidates[0].declared_date.isoformat(), "2025-11-14")

    def test_preannouncement_and_external_pdf_are_rejected(self) -> None:
        html = """
        <a href="https://etrade.fsit.com.tw/case/news/fund_service/a.pdf">
        2025/10/31 富邦基金收益分配期前公告</a>
        <a href="https://example.com/a.pdf">
        2025/11/14 富邦基金收益分配公告</a>
        """
        self.assertEqual(
            parse_fubon_dividend_documents(html_text=html, etf_code="006208"),
            (),
        )

    def test_document_limit_is_bounded(self) -> None:
        with self.assertRaises(ValueError):
            parse_fubon_dividend_documents(
                html_text="<div></div>", etf_code="006208", max_documents=21
            )


if __name__ == "__main__":
    unittest.main()
