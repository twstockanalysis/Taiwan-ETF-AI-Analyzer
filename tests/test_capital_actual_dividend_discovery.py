"""群益投信 ETF 收益分配期后公告发现测试。"""

import unittest

from backend.app.data_sources.capital_actual_dividend_discovery import (
    build_capital_candidates,
    normalize_capital_etf_code,
    parse_capital_announcement_list,
    parse_capital_article_pdf_url,
    resolve_capital_short_name,
)


class TestCapitalActualDividendDiscovery(unittest.TestCase):
    def test_resolves_short_name_by_stock_number(self) -> None:
        payload = {"code": 200, "data": [
            {"stockNo": "00919", "shortName": "群益台灣精選高息"}
        ]}
        self.assertEqual(
            resolve_capital_short_name(payload, " 00919 "),
            "群益台灣精選高息",
        )

    def test_invalid_code_and_unknown_fund_are_rejected(self) -> None:
        for value in ("../00919", "00919&x=1", ""):
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_capital_etf_code(value)
        with self.assertRaisesRegex(ValueError, "找不到 ETF"):
            resolve_capital_short_name({"code": 200, "data": []}, "00919")

    def test_only_period_after_actual_announcement_is_selected(self) -> None:
        html = """
        <a href="/etf/product/news/1">【期前公告】群益台灣精選高息 2026/08/03</a>
        <a href="/etf/product/news/2">【期後公告】群益台灣精選高息
        2026/07/31 之收益實際配發金額。</a>
        <a href="/etf/product/news/3">【期後公告】群益科技高息成長
        2026/07/31 之收益實際配發金額。</a>
        """
        references, rejections = parse_capital_announcement_list(
            html_text=html, short_name="群益台灣精選高息"
        )
        self.assertEqual(len(references), 1)
        self.assertEqual(references[0].declared_date.isoformat(), "2026-07-31")
        self.assertEqual(len(rejections), 1)
        self.assertIn("期前", rejections[0].reason)

    def test_article_requires_official_pdf_attachment(self) -> None:
        html = '<a href="https://www.capitalfund.com.tw/ECStorge/fund/news/a.pdf">附檔</a>'
        self.assertTrue(parse_capital_article_pdf_url(html).endswith("a.pdf"))
        with self.assertRaisesRegex(ValueError, "找不到官方 PDF"):
            parse_capital_article_pdf_url('<a href="https://example.com/a.pdf">x</a>')

    def test_candidates_remain_unknown_until_pdf_parser(self) -> None:
        refs, _ = parse_capital_announcement_list(
            html_text='<a href="/etf/product/news/2">【期後公告】群益台灣精選高息 2026/07/31 之收益實際配發金額。</a>',
            short_name="群益台灣精選高息",
        )
        candidates = build_capital_candidates(
            etf_code="00919",
            references=refs,
            article_html_by_url={refs[0].article_url: '<a href="/ECStorge/fund/news/after.pdf">附檔</a>'},
        )
        self.assertEqual(candidates[0].information_basis, "UNKNOWN")
        self.assertEqual(candidates[0].source_id, "capital_etf_dividend_document")


if __name__ == "__main__":
    unittest.main()
